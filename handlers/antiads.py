import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, MEMBER, LEFT, KICKED
from database import get_pool

router = Router()

# ESLATMA: Anti-reklama filtri check_sub.py dagi group_message_filter ichida
# ishlaydi. Bu faylda faqat yordamchi funksiyalar qoldi.
# Takroriy F.chat.type handler o'chirildi — conflict oldini olish uchun.

AD_PATTERNS = [
    r"https?://\S+",
    r"t\.me/\S+",
    r"@[a-zA-Z0-9_]{5,}",
    r"telegram\.me/\S+",
]
AD_REGEX = re.compile("|".join(AD_PATTERNS), re.IGNORECASE)

_bot_warning_ids: set[int] = set()


def is_ad_message(message: Message) -> bool:
    if message.forward_origin:
        return True
    text = message.text or message.caption or ""
    if AD_REGEX.search(text):
        return True
    return False


async def get_antiads_settings(group_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT antiads_enabled, antiads_text FROM group_settings WHERE group_id = %s",
                (group_id,)
            )
            return await cur.fetchone()
