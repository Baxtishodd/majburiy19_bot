import asyncio
import logging
from datetime import datetime
from database import get_pool

logger = logging.getLogger(__name__)


async def run_scheduler(bot):
    """Har 30 soniyada rejalashtirilgan postlarni tekshiradi va yuboradi"""
    logger.info("🕒 Scheduler ishga tushdi!")

    while True:
        try:
            await _check_and_send(bot)
        except Exception as e:
            logger.error(f"Scheduler xatolik: {e}")
        await asyncio.sleep(30)


async def _check_and_send(bot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT id, message_text, message_type, file_id, target_type
                   FROM scheduled_posts
                   WHERE sent = FALSE AND scheduled_at <= %s""",
                (datetime.now(),)
            )
            posts = await cur.fetchall()

    for post in posts:
        post_id, text, msg_type, file_id, target_type = post
        logger.info(f"📤 Post #{post_id} yuborilmoqda...")

        # Maqsadga qarab chatlarni olish
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                if target_type == "groups":
                    await cur.execute(
                        "SELECT chat_id FROM bot_chats WHERE chat_type IN ('group','supergroup')"
                    )
                elif target_type == "channels":
                    await cur.execute(
                        "SELECT chat_id FROM bot_chats WHERE chat_type = 'channel'"
                    )
                elif target_type == "users":
                    await cur.execute("SELECT id FROM users")
                else:  # all
                    await cur.execute("SELECT chat_id FROM bot_chats")
                chats = [r[0] for r in await cur.fetchall()]

        sent = 0
        fail = 0
        total_audience = 0

        for chat_id in chats:
            try:
                if msg_type == "text":
                    await bot.send_message(chat_id, text, parse_mode="HTML")
                elif msg_type == "photo":
                    await bot.send_photo(chat_id, file_id, caption=text, parse_mode="HTML")
                elif msg_type == "video":
                    await bot.send_video(chat_id, file_id, caption=text, parse_mode="HTML")
                elif msg_type == "document":
                    await bot.send_document(chat_id, file_id, caption=text, parse_mode="HTML")
                elif msg_type == "animation":
                    await bot.send_animation(chat_id, file_id, caption=text, parse_mode="HTML")
                sent += 1
                # Auditoriyani hisoblash
                try:
                    count = await bot.get_chat_member_count(chat_id)
                    total_audience += count
                except Exception:
                    total_audience += 1
            except Exception as e:
                logger.warning(f"Chat {chat_id} ga yuborib bo'lmadi: {e}")
                fail += 1
            await asyncio.sleep(0.05)

        # Natijani saqlash (total_audience bilan)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE scheduled_posts SET sent=TRUE, sent_count=%s, fail_count=%s, total_audience=%s WHERE id=%s",
                    (sent, fail, total_audience, post_id)
                )

        logger.info(f"✅ Post #{post_id}: {sent} ta yuborildi, {fail} ta xatolik, {total_audience} auditoriya")
