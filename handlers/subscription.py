from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import get_pool

router = Router()


async def is_admin(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


@router.message(Command("set"))
async def cmd_set(message: Message):
    """/set @username — majburiy a'zolik kanali/guruhini sozlash"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❗️ To'g'ri foydalanish:\n"
            "/set @KanalUsername"
        )
        return

    channel_username = args[1].strip()
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username

    try:
        chat = await message.bot.get_chat(channel_username)
        channel_id = chat.id
    except Exception:
        await message.answer(f"❌ Kanal/guruh topilmadi: {channel_username}\nBot u yerda admin bo'lishi kerak!")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO force_channels (group_id, channel_id, channel_username)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE channel_username = %s""",
                (message.chat.id, channel_id, channel_username, channel_username)
            )

    await message.answer(
        f"✅ Majburiy a'zolik kanali/guruhi sozlandi:\n"
        f"📢 <b>{chat.title}</b> ({channel_username})",
        parse_mode="HTML"
    )


@router.message(Command("unlink"))
async def cmd_unlink(message: Message):
    """/unlink — sozlangan kanallarni o'chirish"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT channel_username FROM force_channels WHERE group_id = %s",
                (message.chat.id,)
            )
            rows = await cur.fetchall()

            if not rows:
                await message.answer("📭 Hech qanday kanal/guruh sozlanmagan!")
                return

            await cur.execute(
                "DELETE FROM force_channels WHERE group_id = %s",
                (message.chat.id,)
            )

    channels = ", ".join(r[0] for r in rows)
    await message.answer(
        f"🗑 Quyidagi kanallar o'chirildi:\n<b>{channels}</b>",
        parse_mode="HTML"
    )
