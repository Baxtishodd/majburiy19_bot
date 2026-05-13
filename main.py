import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import (BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH,
                    WEBHOOK_SECRET, WEBAPP_HOST, WEBAPP_PORT)
from database import create_pool, init_db, close_pool
from handlers import start, stats, force, subscription, members, admin, antiad_cmd, check_sub
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await create_pool(force=True)
    await init_db()
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logger.info(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    await close_pool()
    logger.info("🛑 Webhook o'chirildi")


def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)
    dp.include_router(force.router)
    dp.include_router(subscription.router)
    dp.include_router(antiad_cmd.router)
    dp.include_router(members.router)
    dp.include_router(check_sub.router)

    app = web.Application()

    async def start_scheduler(app):
        asyncio.create_task(run_scheduler(bot))

    app.on_startup.append(start_scheduler)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    logger.info(f"🚀 Bot ishga tushdi | {WEBAPP_HOST}:{WEBAPP_PORT}")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == "__main__":
    main()
