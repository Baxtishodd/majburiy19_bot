import asyncio
import logging

from flask import Flask, jsonify, request
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBHOOK_SECRET
from database import create_pool, init_db
from handlers import start, stats, force, subscription, members, admin, antiad_cmd, check_sub
from scheduler import run_scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Event loop — Passenger uchun yangi loop ──────────────────────────────────
try:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        raise RuntimeError
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ─── Bot va Dispatcher ────────────────────────────────────────────────────────
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(start.router)
dp.include_router(admin.router)
dp.include_router(stats.router)
dp.include_router(force.router)
dp.include_router(subscription.router)
dp.include_router(antiad_cmd.router)
dp.include_router(members.router)
dp.include_router(check_sub.router)

# ─── Startup ──────────────────────────────────────────────────────────────────
_startup_done = False


async def _startup():
    global _startup_done
    if _startup_done:
        return
    await create_pool(force=True)
    await init_db()
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    _startup_done = True
    logger.info(f"✅ Webhook: {WEBHOOK_URL}")

loop.run_until_complete(_startup())

# Scheduler alohida threadda ishlatiladi — loop ni bloklamasin
import threading

def _run_scheduler():
    sch_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(sch_loop)
    scheduler_bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    sch_loop.run_until_complete(run_scheduler(scheduler_bot))

scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
if not scheduler_thread.is_alive():
    scheduler_thread.start()

# ─── Flask ────────────────────────────────────────────────────────────────────
application = Flask(__name__)


@application.get("/")
def healthcheck():
    return jsonify({"ok": True, "bot": "majburiy19"})


@application.post(WEBHOOK_PATH)
def telegram_webhook():
    data = request.get_json(silent=True) or {}
    try:
        update = Update(**data)
        loop.run_until_complete(dp.feed_update(bot=bot, update=update))
    except Exception as e:
        logger.error(f"Update xatosi: {e}")
    return jsonify({"ok": True})
