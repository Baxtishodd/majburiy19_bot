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


@router.message(Command("antiad"))
async def cmd_antiad(message: Message):
    """
    /antiad on  — reklamaga qarshi filterni yoqish
    /antiad off — o'chirish
    """
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    await ensure_group_settings(message.chat.id)

    args = message.text.split(maxsplit=1)
    arg = args[1].strip().lower() if len(args) > 1 else ""

    if arg not in ("on", "off"):
        await message.answer(
            "❗️ To'g'ri foydalanish:\n"
            "/antiad on — yoqish\n"
            "/antiad off — o'chirish"
        )
        return

    enabled = arg == "on"
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE group_settings SET antiads_enabled = %s WHERE group_id = %s",
                (enabled, message.chat.id)
            )

    if enabled:
        await message.answer(
            "✅ Anti-reklama filtri <b>yoqildi!</b>\n\n"
            "🔍 Aniqlanadi:\n"
            "• Linklar (http, t.me, @username)\n"
            "• Forward qilingan xabarlar\n\n"
            "Reklama topilsa — o'chiriladi va foydalanuvchiga habar beriladi.\n"
            "Qo'shimcha matn qo'shish uchun: /antiadtext",
            parse_mode="HTML"
        )
    else:
        await message.answer("🔴 Anti-reklama filtri <b>o'chirildi!</b>", parse_mode="HTML")


@router.message(Command("antiadtext"))
async def cmd_antiadtext(message: Message):
    """
    /antiadtext <matn> — ogohlantirish xabariga qo'shimcha matn
    /antiadtext 0      — matnni o'chirish
    """
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
                    "UPDATE group_settings SET antiads_text = NULL WHERE group_id = %s",
                    (message.chat.id,)
                )
                await message.answer("🗑 Ogohlantirish matni o'chirildi!")
            elif arg:
                await cur.execute(
                    "UPDATE group_settings SET antiads_text = %s WHERE group_id = %s",
                    (arg, message.chat.id)
                )
                await message.answer(
                    f"✅ Ogohlantirish matni saqlandi!\n\n"
                    f"Ko'rinishi:\n"
                    f"🚫 [foydalanuvchi] reklama tarqatmang!\n"
                    f"{arg}",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❗️ To'g'ri foydalanish:\n"
                    "/antiadtext Guruh qoidalari: ... — matn qo'shish\n"
                    "/antiadtext 0 — matnni o'chirish\n\n"
                    "Ogohlantirish ko'rinishi:\n"
                    "🚫 [foydalanuvchi] reklama tarqatmang!\n"
                    "<i>[sizning matningiz]</i>",
                    parse_mode="HTML"
                )
