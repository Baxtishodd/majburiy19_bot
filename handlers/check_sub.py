import re
import asyncio
from time import monotonic
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_pool
from handlers.members import register_chat

router = Router()

# ─── Reklama aniqlash ─────────────────────────────────────────────────────────

AD_PATTERNS = [
    r"https?://\S+",
    r"t\.me/\S+",
    r"@[a-zA-Z0-9_]{5,}",
    r"telegram\.me/\S+",
]
AD_REGEX = re.compile("|".join(AD_PATTERNS), re.IGNORECASE)

_bot_warning_ids: set[int] = set()
_chat_sync_cache: dict[int, float] = {}
CHAT_SYNC_TTL_SECONDS = 600


def is_ad_message(message: Message) -> bool:
    if message.forward_origin:
        return True
    text = message.text or message.caption or ""
    return bool(AD_REGEX.search(text))


async def sync_chat_if_needed(message: Message):
    now = monotonic()
    last_synced = _chat_sync_cache.get(message.chat.id, 0)
    if now - last_synced < CHAT_SYNC_TTL_SECONDS:
        return

    _chat_sync_cache[message.chat.id] = now
    try:
        await register_chat(
            chat_id=message.chat.id,
            title=message.chat.title or str(message.chat.id),
            chat_type=message.chat.type,
            username=message.chat.username,
        )
    except Exception:
        _chat_sync_cache.pop(message.chat.id, None)


# ─── DB yordamchi funksiyalar ─────────────────────────────────────────────────

async def get_antiads_settings(group_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT antiads_enabled, antiads_text FROM group_settings WHERE group_id = %s",
                (group_id,)
            )
            return await cur.fetchone()


async def get_unsubscribed_channels(bot, user_id: int, group_id: int) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT channel_id, channel_username FROM force_channels WHERE group_id = %s",
                (group_id,)
            )
            channels = await cur.fetchall()

    not_subscribed = []
    for channel_id, username in channels:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in ("member", "administrator", "creator"):
                raise Exception("not subscribed")
        except Exception:
            try:
                chat = await bot.get_chat(channel_id)
                title = chat.title or username
                if username and username.startswith("@"):
                    link = f"https://t.me/{username.lstrip('@')}"
                elif chat.invite_link:
                    link = chat.invite_link
                else:
                    link = await bot.export_chat_invite_link(channel_id)
            except Exception:
                title = username or str(channel_id)
                link = f"https://t.me/{username.lstrip('@')}" if username else None

            not_subscribed.append({"title": title, "link": link})

    return not_subscribed


async def get_force_add_info(user_id: int, group_id: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT force_add_enabled, force_add_count FROM group_settings WHERE group_id = %s",
                (group_id,)
            )
            settings = await cur.fetchone()
            if not settings or not settings[0] or settings[1] <= 0:
                return None

            force_count = settings[1]
            await cur.execute(
                "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (group_id, user_id)
            )
            row = await cur.fetchone()
            current = row[0] if row else 0

            if current >= force_count:
                return None

            return {"current": current, "required": force_count, "remaining": force_count - current}


def build_sub_keyboard(channels: list[dict], group_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        if ch["link"]:
            builder.button(text=f"📢 {ch['title']}", url=ch["link"])
    builder.button(text="✅ Obuna bo'ldim", callback_data=f"check_sub:{group_id}")
    builder.button(text="👥 Guruhga odam ko'paytirish", url=f"https://t.me/{bot_username}")
    builder.adjust(1)
    return builder.as_markup()


def build_force_add_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Guruhga odam ko'paytirish", url=f"https://t.me/{bot_username}")
    builder.adjust(1)
    return builder.as_markup()


# ─── Kirdi / Chiqdi xabarlarini o'chirish ────────────────────────────────────

@router.message(F.new_chat_members)
async def delete_join_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


@router.message(F.left_chat_member)
async def delete_left_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


# ─── Asosiy filtr (barcha xabarlar) ──────────────────────────────────────────

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_message_filter(message: Message):
    if not message.from_user:
        return

    await sync_chat_if_needed(message)

    # Bot o'zi yuborgan xabarlarni o'tkazib yuborish
    if message.message_id in _bot_warning_ids:
        return

    user = message.from_user
    group_id = message.chat.id

    # Adminlarni o'tkazib yuborish
    try:
        member = await message.bot.get_chat_member(group_id, user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        return

    # ── 1. Majburiy kanal obunasi ──────────────────────────────────────────
    not_subscribed = await get_unsubscribed_channels(message.bot, user.id, group_id)
    if not_subscribed:
        try:
            await message.delete()
        except Exception:
            pass
        bot_me = await message.bot.get_me()
        keyboard = build_sub_keyboard(not_subscribed, group_id, bot_me.username)
        channels_list = "\n".join([f"• {ch['title']}" for ch in not_subscribed])
        try:
            warn_msg = await message.answer(
                f"⚠️ <b>{user.full_name}</b>, xabar yuborish uchun\n"
                f"avval quyidagi kanallarga obuna bo'ling:\n\n"
                f"{channels_list}\n\n"
                f"Obuna bo'lgach <b>✅ Obuna bo'ldim</b> tugmasini bosing!",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            _bot_warning_ids.add(warn_msg.message_id)
            await asyncio.sleep(60)
            await warn_msg.delete()
            _bot_warning_ids.discard(warn_msg.message_id)
        except Exception:
            pass
        return  # Qolgan tekshiruvlarga o'tmaymiz

    # ── 2. Majburiy odam qo'shish ──────────────────────────────────────────
    force_info = await get_force_add_info(user.id, group_id)
    if force_info:
        try:
            await message.delete()
        except Exception:
            pass
        bot_me = await message.bot.get_me()
        try:
            warn_msg = await message.answer(
                f"⚠️ <b>{user.full_name}</b>, xabar yuborish uchun guruhga\n"
                f"<b>{force_info['remaining']} ta</b> odam qo'shishingiz kerak!\n\n"
                f"📊 Holat: <b>{force_info['current']}/{force_info['required']}</b>",
                parse_mode="HTML",
                reply_markup=build_force_add_keyboard(bot_me.username)
            )
            _bot_warning_ids.add(warn_msg.message_id)
            await asyncio.sleep(60)
            await warn_msg.delete()
            _bot_warning_ids.discard(warn_msg.message_id)
        except Exception:
            pass
        return  # Reklama tekshiruviga o'tmaymiz

    # ── 3. Anti-reklama ────────────────────────────────────────────────────
    settings = await get_antiads_settings(group_id)
    if not settings or not settings[0]:
        return

    if not is_ad_message(message):
        return

    try:
        await message.delete()
    except Exception:
        return

    antiads_text = settings[1]
    user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
    warn_text = f"🚫 {user_link} reklama tarqatmang!"
    if antiads_text:
        warn_text += f"\n{antiads_text}"

    try:
        warn_msg = await message.answer(warn_text, parse_mode="HTML")
        _bot_warning_ids.add(warn_msg.message_id)
        await asyncio.sleep(30)
        await warn_msg.delete()
        _bot_warning_ids.discard(warn_msg.message_id)
    except Exception:
        pass


# ─── "Obuna bo'ldim" callback ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("check_sub:"))
async def callback_check_sub(call: CallbackQuery):
    group_id = int(call.data.split(":")[1])
    user = call.from_user

    not_subscribed = await get_unsubscribed_channels(call.bot, user.id, group_id)

    if not_subscribed:
        bot_me = await call.bot.get_me()
        keyboard = build_sub_keyboard(not_subscribed, group_id, bot_me.username)
        channels_list = "\n".join([f"• {ch['title']}" for ch in not_subscribed])
        await call.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        try:
            await call.message.edit_text(
                f"⚠️ <b>{user.full_name}</b>, xabar yuborish uchun\n"
                f"avval quyidagi kanallarga obuna bo'ling:\n\n"
                f"{channels_list}\n\n"
                f"Obuna bo'lgach <b>✅ Obuna bo'ldim</b> tugmasini bosing!",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            pass
    else:
        await call.answer("✅ Tekshirildi! Endi xabar yubora olasiz.", show_alert=True)
        try:
            await call.message.delete()
        except Exception:
            pass
