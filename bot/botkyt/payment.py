"""Bayar.gg Payment Gateway Integration"""
import aiohttp
import secrets
import config


async def create_qris_payment(amount: int, user_id: int) -> dict:
    """
    Create QRIS payment via bayar.gg
    Returns: {"success": bool, "payment_id": str, "qris_url": str, "qris_image": str}
    """
    if amount > config.BAYAR_MAX_AMOUNT:
        return {"success": False, "error": f"Maksimal Rp {config.BAYAR_MAX_AMOUNT:,}"}
    
    if amount < 1000:
        return {"success": False, "error": "Minimal Rp 1.000"}
    
    payment_id = f"WVP-{user_id}-{secrets.token_hex(4).upper()}"
    
    headers = {
        "X-API-Key": config.BAYAR_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": amount,
        "payment_method": "qris",
        "callback_url": "",  # Will be handled via polling
        "external_id": payment_id,
        "use_qris_converter": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.BAYAR_API_URL}/create-payment.php",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                data = await response.json()
                
                if response.status == 200 and data.get("success"):
                    return {
                        "success": True,
                        "payment_id": payment_id,
                        "bayar_id": data.get("data", {}).get("id", ""),
                        "qris_url": data.get("data", {}).get("qris_url", ""),
                        "qris_image": data.get("data", {}).get("qris_image", ""),
                        "amount": amount
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Gagal membuat pembayaran")
                    }
    except aiohttp.ClientError as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


async def check_payment_status(payment_id: str) -> dict:
    """
    Check payment status via bayar.gg
    Returns: {"success": bool, "status": str, "paid": bool}
    """
    headers = {
        "X-API-Key": config.BAYAR_API_KEY
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.BAYAR_API_URL}/check-payment.php",
                headers=headers,
                params={"id": payment_id},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    status = data.get("data", {}).get("status", "pending")
                    return {
                        "success": True,
                        "status": status,
                        "paid": status in ("paid", "completed", "success")
                    }
                else:
                    return {
                        "success": False,
                        "status": "unknown",
                        "paid": False
                    }
    except Exception as e:
        return {"success": False, "status": "error", "paid": False, "error": str(e)}
