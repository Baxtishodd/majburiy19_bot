from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import get_pool

router = Router()


async def is_admin(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


async def ensure_group_settings(group_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO group_settings (group_id) VALUES (%s)",
                (group_id,)
            )


@router.message(Command("add"))
async def cmd_add(message: Message):
    """/add, /add 10, /add off"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    await ensure_group_settings(message.chat.id)
    args = message.text.split(maxsplit=1)
    arg = args[1].strip() if len(args) > 1 else ""

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if arg.lower() == "off":
                await cur.execute(
                    "UPDATE group_settings SET force_add_enabled = FALSE WHERE group_id = %s",
                    (message.chat.id,)
                )
                await message.answer("🔴 Majburiy odam qo'shish <b>o'chirildi!</b>", parse_mode="HTML")

            elif arg.isdigit():
                count = int(arg)
                await cur.execute(
                    """UPDATE group_settings
                       SET force_add_enabled = TRUE, force_add_count = %s
                       WHERE group_id = %s""",
                    (count, message.chat.id)
                )
                await message.answer(
                    f"✅ Majburiy odam qo'shish <b>yoqildi!</b>\n"
                    f"🎯 Maqsad: <b>{count} ta odam</b>",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❗️ To'g'ri foydalanish:\n"
                    "/add 10 — yoqish (10 ta)\n"
                    "/add off — o'chirish"
                )


@router.message(Command("textforce"))
async def cmd_textforce(message: Message):
    """/textforce <matn> yoki /textforce 0"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    await ensure_group_settings(message.chat.id)
    args = message.text.split(maxsplit=1)
    arg = args[1].strip() if len(args) > 1 else ""

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if arg == "0":
                await cur.execute(
                    "UPDATE group_settings SET force_text = NULL WHERE group_id = %s",
                    (message.chat.id,)
                )
                await message.answer("🗑 Majburiy matn o'chirildi!")
            elif arg:
                await cur.execute(
                    "UPDATE group_settings SET force_text = %s WHERE group_id = %s",
                    (arg, message.chat.id)
                )
                await message.answer(
                    f"✅ Majburiy matn saqlandi:\n\n{arg}",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❗️ To'g'ri foydalanish:\n"
                    "/textforce *Salom* — matn qo'shish\n"
                    "/textforce 0 — matnni o'chirish"
                )


@router.message(Command("text_time"))
async def cmd_text_time(message: Message):
    """/text_time <soniya>"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    await ensure_group_settings(message.chat.id)
    args = message.text.split(maxsplit=1)
    arg = args[1].strip() if len(args) > 1 else ""

    if not arg.isdigit():
        await message.answer(
            "❗️ To'g'ri foydalanish:\n"
            "/text_time 30 — 30 soniyadan keyin o'chadi\n"
            "/text_time 0 — avtomatik o'chirmaslik"
        )
        return

    seconds = int(arg)
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE group_settings SET force_text_delete_after = %s WHERE group_id = %s",
                (seconds, message.chat.id)
            )

    if seconds == 0:
        await message.answer("✅ Matn avtomatik o'chirilmaydi!")
    else:
        await message.answer(f"⏱ Matn <b>{seconds} soniya</b>dan keyin o'chadi!", parse_mode="HTML")


@router.message(Command("deforce"))
async def cmd_deforce(message: Message):
    """/deforce id yoki reply"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    target_id = None
    target_name = None

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.full_name
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1 and args[1].strip().lstrip("-").isdigit():
            target_id = int(args[1].strip())
            target_name = str(target_id)
        else:
            await message.answer("❗️ ID kiriting yoki biror xabarga reply qiling!")
            return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (message.chat.id, target_id)
            )

    await message.answer(
        f"✅ <b>{target_name}</b> ning majburiy a'zolik ma'lumotlari tozalandi!",
        parse_mode="HTML"
    )


@router.message(Command("priv"))
async def cmd_priv(message: Message):
    """/priv id yoki reply — imtiyoz berish"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            try:
                uid = int(args[1].strip())
                # Foydalanuvchini promote qilish
                await message.bot.promote_chat_member(
                    message.chat.id,
                    uid,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                )
                await message.answer(f"✅ Foydalanuvchi <b>{uid}</b> ga imtiyoz berildi!", parse_mode="HTML")
                return
            except Exception as e:
                await message.answer(f"❌ Xatolik: {e}")
                return
        else:
            await message.answer("❗️ ID kiriting yoki biror xabarga reply qiling!")
            return

    try:
        await message.bot.promote_chat_member(
            message.chat.id,
            target.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
        )
        await message.answer(
            f"✅ <b>{target.full_name}</b> ga imtiyoz berildi!",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
