import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import create_pool, init_db
from handlers import start, stats, force, subscription, members, admin, antiad_cmd, check_sub
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    # FSM uchun MemoryStorage (admin panel holatlari)
    dp = Dispatcher(storage=MemoryStorage())

    await create_pool()
    await init_db()
    logger.info("✅ Ma'lumotlar bazasi ulandi!")

    # Handlerlarni ro'yxatdan o'tkazish (tartib muhim!)
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)
    dp.include_router(force.router)
    dp.include_router(subscription.router)
    dp.include_router(antiad_cmd.router)
    dp.include_router(members.router)
    dp.include_router(check_sub.router)

    # Schedulerni background task sifatida ishga tushirish
    asyncio.create_task(run_scheduler(bot))

    logger.info("🚀 Bot ishga tushdi!")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
