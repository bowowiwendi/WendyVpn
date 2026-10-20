from kyt import *
from importlib import import_module
from kyt.modules import ALL_MODULES
for module_name in ALL_MODULES:
	imported_module = import_module("kyt.modules." + module_name)

import asyncio
try:
	asyncio.ensure_future(__import__("kyt.modules.p2p_pay", fromlist=["payment_poller"]).payment_poller())
except:
	pass
try:
	asyncio.ensure_future(__import__("kyt.modules.backup_db", fromlist=["db_backup_scheduler"]).db_backup_scheduler())
except:
	pass

bot.run_until_disconnected()

