"""
Ahost cPanel Passenger WSGI entry point.
"""
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
from database import create_pool, init_db
from handlers import start, stats, force, subscription, members, admin, antiad_cmd, check_sub
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_app():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

    async def startup():
        await create_pool()
        await init_db()
        await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
        asyncio.create_task(run_scheduler(bot))

    loop.run_until_complete(startup())

    aio_app = web.Application()

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    ).register(aio_app, path=WEBHOOK_PATH)

    setup_application(aio_app, dp, bot=bot)

    return aio_app


application = create_app()
