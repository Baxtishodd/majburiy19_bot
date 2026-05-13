import asyncio
import logging

from flask import Flask, jsonify, request
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from database import create_pool, init_db
from handlers import start, stats, force, subscription, members, admin, antiad_cmd, check_sub
from scheduler import run_scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

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

# ─── Startup: DB + Webhook + Scheduler ───────────────────────────────────────

async def _startup():
    await create_pool()
    await init_db()
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(run_scheduler(bot))
    logger.info(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")

asyncio.get_event_loop().run_until_complete(_startup())

# ─── Flask app ────────────────────────────────────────────────────────────────

application = Flask(__name__)


@application.get("/")
def healthcheck():
    return jsonify({"ok": True, "bot": "majburiy19"})


@application.post(WEBHOOK_PATH)
def telegram_webhook():
    data = request.get_json(silent=True) or {}
    update = Update(**data)
    asyncio.get_event_loop().run_until_complete(
        dp.feed_update(bot=bot, update=update)
    )
    return jsonify({"ok": True})
