from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_pool

router = Router()


async def save_user(user):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO users (id, username, full_name)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE username=%s, full_name=%s""",
                (user.id, user.username or "", user.full_name,
                 user.username or "", user.full_name)
            )


@router.message(CommandStart())
async def cmd_start(message: Message):
    # Faqat private chatda ishlaydi
    if message.chat.type != "private":
        return

    # Foydalanuvchini DBga saqlash
    await save_user(message.from_user)

    await message.answer(
        f"👋 Salom, <b>{message.from_user.full_name}</b>!\n\n"
        "🤖 <b>Botimizning buyruqlari!</b>\n\n"
        "📊 <b>Statistika buyruqlari:</b>\n"
        "/mymembers — Siz qo'shgan odamlar soni\n"
        "/yourmembers — Reply qilingan odamning qo'shganlari\n"
        "/top — Eng ko'p odam qo'shgan 10 talik\n"
        "/delson — Barcha ma'lumotlarni tozalash\n"
        "/clean — Reply foydalanuvchi ma'lumotini 0 ga tenglash\n\n"
        "👥 <b>Majburiy odam qo'shish:</b>\n"
        "/add — Majburiy odam qo'shishni yoqadi\n"
        "/add 10 — 10 ta odam qo'shishni yoqish\n"
        "/add off — O'chirish\n"
        "/textforce — Qo'shimcha matn qo'shish\n"
        "/textforce 0 — Matnni o'chirish\n"
        "/text_time — Matn avtomatik o'chish vaqti\n"
        "/deforce — Ma'lumotni tozalash\n"
        "/plus — Referralni boshqaga o'tkazish\n"
        "/priv — Foydalanuvchiga imtiyoz berish\n\n"
        "🔖 <b>Majburiy a'zolik:</b>\n"
        "/set @kanal — Kanal/guruh sozlash\n"
        "/unlink — Kanallarni o'chirish",
        parse_mode="HTML"
    )
