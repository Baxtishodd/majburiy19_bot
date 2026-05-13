import asyncio
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from database import get_pool

router = Router()


async def get_or_create_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            row = await cur.fetchone()
            if not row:
                await cur.execute(
                    "INSERT INTO users (id, username, full_name, referrer_id) VALUES (%s, %s, %s, %s)",
                    (user_id, username, full_name, referrer_id)
                )
                if referrer_id:
                    await cur.execute(
                        "UPDATE users SET referral_count = referral_count + 1 WHERE id = %s",
                        (referrer_id,)
                    )
            else:
                await cur.execute(
                    "UPDATE users SET username = %s, full_name = %s WHERE id = %s",
                    (username, full_name, user_id)
                )


async def register_chat(chat_id: int, title: str, chat_type: str, username: str = None):
    """Guruh yoki kanalni bot_chats jadvaliga saqlash"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO bot_chats (chat_id, chat_title, chat_type, username)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE chat_title=%s, chat_type=%s, username=%s""",
                (chat_id, title, chat_type, username, title, chat_type, username)
            )
            # group_settings ga ham qo'shish
            await cur.execute(
                "INSERT IGNORE INTO group_settings (group_id, group_title) VALUES (%s, %s)",
                (chat_id, title)
            )


@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    """Bot guruh yoki kanalga qo'shilganda yoki o'chirilganda"""
    new_status = event.new_chat_member.status
    chat = event.chat

    if new_status in ("member", "administrator"):
        # Bot qo'shildi — ro'yxatga olish
        await register_chat(
            chat_id=chat.id,
            title=chat.title or str(chat.id),
            chat_type=chat.type,
            username=chat.username,
        )
    elif new_status in ("left", "kicked"):
        # Bot o'chirildi — ro'yxatdan chiqarish
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM bot_chats WHERE chat_id = %s", (chat.id,))


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_new_member(event: ChatMemberUpdated):
    new_user = event.new_chat_member.user
    group_id = event.chat.id
    added_by = event.from_user

    if new_user.is_bot:
        return

    await register_chat(
        chat_id=group_id,
        title=event.chat.title or str(group_id),
        chat_type=event.chat.type,
        username=event.chat.username,
    )
    await get_or_create_user(new_user.id, new_user.username or "", new_user.full_name)

    pool = await get_pool()

    real_referrer_id = None
    if added_by and added_by.id != new_user.id:
        real_referrer_id = added_by.id
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT IGNORE INTO group_referrals (group_id, user_id, referrer_id) VALUES (%s, %s, %s)",
                        (group_id, new_user.id, added_by.id)
                    )
                except Exception:
                    pass

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT force_add_enabled, force_add_count, force_text, force_text_delete_after FROM group_settings WHERE group_id = %s",
                (group_id,)
            )
            settings = await cur.fetchone()

    if not settings or not settings[0]:
        return

    force_count = settings[1]
    force_text = settings[2]
    delete_after = settings[3]

    if force_count <= 0:
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (group_id, new_user.id)
            )
            row = await cur.fetchone()
            new_user_count = row[0] if row else 0

    if new_user_count < force_count:
        remaining = force_count - new_user_count
        text = (
            f"👋 <b>{new_user.full_name}</b> guruhga xush kelibsiz!\n\n"
            f"⚠️ Guruhda yozishingiz uchun <b>{remaining} ta</b> odam qo'shishingiz kerak!\n"
            f"📊 Holat: <b>{new_user_count}/{force_count}</b>"
        )
        if force_text:
            text += f"\n\n{force_text}"
        try:
            msg = await event.answer(text, parse_mode="HTML")
            if delete_after and delete_after > 0:
                await asyncio.sleep(delete_after)
                await msg.delete()
        except Exception:
            pass
        return

    if real_referrer_id:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                    (group_id, real_referrer_id)
                )
                ref_row = await cur.fetchone()
                referrer_count = ref_row[0] if ref_row else 0

        if referrer_count < force_count:
            remaining = force_count - referrer_count
            text = (
                f"✅ <b>{new_user.full_name}</b> guruhga qo'shildi!\n"
                f"👤 Qo'shgan: <b>{added_by.full_name}</b>\n"
                f"📊 Holat: <b>{referrer_count}/{force_count}</b>\n"
                f"⏳ Qoldi: <b>{remaining} ta</b>"
            )
            if force_text:
                text += f"\n\n{force_text}"
            try:
                msg = await event.answer(text, parse_mode="HTML")
                if delete_after and delete_after > 0:
                    await asyncio.sleep(delete_after)
                    await msg.delete()
            except Exception:
                pass
