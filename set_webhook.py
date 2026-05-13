import asyncio
from aiogram import Bot
from config import BOT_TOKEN, WEBHOOK_URL


async def main():
    if not WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_BASE_URL is not set in .env")

    bot = Bot(token=BOT_TOKEN)

    result = await bot.set_webhook(url=WEBHOOK_URL)
    info = await bot.get_webhook_info()

    no_error = "yo'q"
    print(f"Webhook URL:           {WEBHOOK_URL}")
    print(f"set_webhook result:    {result}")
    print(f"Webhook info URL:      {info.url}")
    print(f"Pending updates:       {info.pending_update_count}")
    print(f"Last error:            {info.last_error_message or no_error}")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
