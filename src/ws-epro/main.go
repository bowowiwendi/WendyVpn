// ws-epro — WebSocket-to-TCP relay (SSH/OpenVPN over HTTP upgrade).
//
// Clean-room reimplementation written for the WendyVpn repository.
//
// The original "ws" binary shipped in files/ was a closed-source build
// (Go, module "ws-epro", banner "ws-epro (v1.2.1)") whose source was
// never published, so it could not be recompiled for ARM64. This
// implementation reproduces its observable behaviour, which was
// documented by black-box probing of the original binary:
//
//   - CLI: a single flag, -f <config file> (default "config.yml").
//   - On start it prints the banner "ws-epro (v1.2.1)" and then a
//     "list porting [{target :listen} ...]" line.
//   - If the config file does not exist it dies via log.Fatal with
//     the message "config file not exists" (after printing the banner).
//   - Config is the same YAML subset as cfg_conf_js/tun.conf:
//     a top-level "verbose: N" and a "listen:" list of entries with
//     target_host / target_port / listen_port keys.
//   - For every connection it consumes the client's HTTP request
//     headers, immediately answers the literal bytes
//     "HTTP/1.1 101 Switching Protocols\r\n\r\n" (no extra headers,
//     exactly like the original), then dials the target and relays
//     raw bytes in both directions. The 101 answer is sent before
//     dialing, so a dead target still yields a 101 followed by a
//     closed connection, exactly like the original.
//   - Bytes a client pipelines in the same read as its HTTP headers
//     are discarded, matching the original.
//   - Logging (stdout, ANSI colours always on):
//       verbose 0/1: session lines only
//         #NNN :port: client <addr> request <request line>   (green)
//         #NNN :port: opened :port >>>> host:port            (green)
//         #NNN :port: closed (X bytes send, Y bytes received) (green)
//         #NNN :port: check remote tcp fail: <error>          (red)
//       verbose 2: additionally, per relayed chunk
//         #NNN :port: >>>> N bytes sent     (green) + hex dump (blue)
//         #NNN :port: <<<< N bytes received (green) + hex dump (blue)
//
// Only the Go standard library is used, so the binary is fully
// static (CGO disabled) and architecture-portable:
//
//	GOOS=linux GOARCH=amd64 go build -o ws .
//	GOOS=linux GOARCH=arm64 go build -o ws .
package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

// version is the version string shown in the banner. It is kept at
// 1.2.1 so logs and tooling that parse the banner behave exactly as
// they did with the original binary.
const version = "1.2.1"

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

type Listen struct {
	TargetHost string
	TargetPort int
	ListenPort int
}

// Target returns "host:port" of the relay destination.
func (l Listen) Target() string {
	return net.JoinHostPort(l.TargetHost, strconv.Itoa(l.TargetPort))
}

// Addr returns the listen address in ":port" form, as printed by the
// original binary in its "list porting" line.
func (l Listen) Addr() string {
	return ":" + strconv.Itoa(l.ListenPort)
}

type Config struct {
	Verbose int
	Listens []Listen
}

// loadConfig parses the small YAML subset used by tun.conf:
//
//	verbose: 0
//	listen:
//	- target_host: 127.0.0.1
//	  target_port: 143
//	  listen_port: 10015
//
// Blank lines and lines starting with '#' are ignored. Unknown keys
// are ignored, mirroring the lenient YAML decoding of the original.
func loadConfig(path string) (*Config, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	cfg := &Config{}
	var cur *Listen
	flush := func() {
		if cur != nil {
			cfg.Listens = append(cfg.Listens, *cur)
			cur = nil
		}
	}

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), 1024*1024)
	inListen := false
	for sc.Scan() {
		line := sc.Text()
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		if !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "\t") && !strings.HasPrefix(trimmed, "-") {
			// Top-level key.
			key, val, ok := splitKV(trimmed)
			if !ok {
				continue
			}
			switch key {
			case "verbose":
				cfg.Verbose, _ = strconv.Atoi(val)
				inListen = false
			case "listen":
				inListen = true
			default:
				inListen = false
			}
			continue
		}
		if !inListen {
			continue
		}
		if strings.HasPrefix(trimmed, "-") {
			flush()
			cur = &Listen{}
			trimmed = strings.TrimSpace(strings.TrimPrefix(trimmed, "-"))
			if trimmed == "" {
				continue
			}
		}
		if cur == nil {
			continue
		}
		key, val, ok := splitKV(trimmed)
		if !ok {
			continue
		}
		switch key {
		case "target_host":
			cur.TargetHost = val
		case "target_port":
			cur.TargetPort, _ = strconv.Atoi(val)
		case "listen_port":
			cur.ListenPort, _ = strconv.Atoi(val)
		}
	}
	flush()
	return cfg, sc.Err()
}

func splitKV(s string) (string, string, bool) {
	i := strings.Index(s, ":")
	if i < 0 {
		return "", "", false
	}
	return strings.TrimSpace(s[:i]), strings.TrimSpace(s[i+1:]), true
}

// ---------------------------------------------------------------------------
// Coloured logging (same palette as the original: green info,
// red errors, blue hex dumps; colour codes are always emitted).
// ---------------------------------------------------------------------------

const (
	colGreen = "\x1b[32m"
	colRed   = "\x1b[31m"
	colBlue  = "\x1b[34m"
	colReset = "\x1b[0m"
)

func logLine(id int64, listenPort int, colour, format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	fmt.Printf("#%03d :%d: %s%s%s\n", id, listenPort, colour, msg, colReset)
}

// ---------------------------------------------------------------------------
// Proxy
// ---------------------------------------------------------------------------

var connCounter int64

type proxy struct {
	cfg     *Config
	listen  Listen
	verbose int
}

func (p *proxy) serve(ln net.Listener) {
	for {
		client, err := ln.Accept()
		if err != nil {
			return
		}
		id := atomic.AddInt64(&connCounter, 1)
		go p.handle(id, client)
	}
}

func (p *proxy) handle(id int64, client net.Conn) {
	lp := p.listen.ListenPort
	defer client.Close()

	// Consume the client's HTTP request: request line + headers up
	// to the blank line. Anything already buffered past the headers
	// is dropped, matching the original binary.
	br := bufio.NewReader(client)
	requestLine, err := br.ReadString('\n')
	if err != nil {
		return
	}
	requestLine = strings.TrimRight(requestLine, "\r\n")
	for {
		line, err := br.ReadString('\n')
		if err != nil {
			return
		}
		if line == "\r\n" || line == "\n" {
			break
		}
	}
	logLine(id, lp, colGreen, "client %s request %s", client.RemoteAddr(), requestLine)

	// Answer the upgrade exactly like the original: status line only.
	if _, err := io.WriteString(client, "HTTP/1.1 101 Switching Protocols\r\n\r\n"); err != nil {
		return
	}

	target, err := net.DialTimeout("tcp", p.listen.Target(), 30*time.Second)
	if err != nil {
		logLine(id, lp, colRed, "check remote tcp fail: %s", err)
		return
	}
	defer target.Close()
	logLine(id, lp, colGreen, "opened :%d >>>> %s", lp, p.listen.Target())

	var sent, received int64 // sent: client->target, received: target->client
	done := make(chan struct{}, 2)

	relay := func(dst, src net.Conn, total *int64, arrow string, verb string) {
		defer func() { done <- struct{}{} }()
		buf := make([]byte, 32*1024)
		for {
			n, rerr := src.Read(buf)
			if n > 0 {
				chunk := buf[:n]
				if _, werr := dst.Write(chunk); werr != nil {
					return
				}
				atomic.AddInt64(total, int64(n))
				if p.verbose >= 2 {
					logLine(id, lp, colGreen, "%s %d bytes %s", arrow, n, verb)
					logLine(id, lp, colBlue, "%x", chunk)
				}
			}
			if rerr != nil {
				return
			}
		}
	}

	go relay(target, client, &sent, ">>>>", "sent")
	go relay(client, target, &received, "<<<<", "received")
	<-done
	// One direction ended: tear down both sides so the other
	// relay goroutine exits too.
	client.Close()
	target.Close()
	<-done

	logLine(id, lp, colGreen, "closed (%d bytes send, %d bytes received)",
		atomic.LoadInt64(&sent), atomic.LoadInt64(&received))
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

func main() {
	configPath := flag.String("f", "config.yml", "config file path, default: config.yml")
	flag.Parse()

	fmt.Printf("ws-epro (v%s)\n", version)

	if _, err := os.Stat(*configPath); err != nil {
		// The original reports a missing config with this exact
		// message through the standard logger (with date prefix).
		log.Fatal("config file not exists")
	}
	cfg, err := loadConfig(*configPath)
	if err != nil {
		log.Fatal(err)
	}
	if len(cfg.Listens) == 0 {
		log.Fatal("no listen data")
	}

	// "list porting [{target :listen} ...]"
	parts := make([]string, len(cfg.Listens))
	for i, l := range cfg.Listens {
		parts[i] = "{" + l.Target() + " " + l.Addr() + "}"
	}
	fmt.Printf("list porting [%s]\n\n", strings.Join(parts, " "))

	for _, l := range cfg.Listens {
		ln, err := net.Listen("tcp", l.Addr())
		if err != nil {
			log.Fatalf("listen %s fail: %s", l.Addr(), err)
		}
		p := &proxy{cfg: cfg, listen: l, verbose: cfg.Verbose}
		go p.serve(ln)
	}

	select {}
}
