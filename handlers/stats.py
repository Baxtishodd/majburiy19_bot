from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_pool

router = Router()


async def is_admin(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


@router.message(Command("mymembers"))
async def cmd_mymembers(message: Message):
    """Foydalanuvchi qo'shgan odamlar soni"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (message.chat.id, message.from_user.id)
            )
            row = await cur.fetchone()
            count = row[0] if row else 0

    user = message.from_user
    await message.answer(
        f"📊 <b>{user.full_name}</b>\n"
        f"👥 Siz qo'shgan odamlar: <b>{count} ta</b>",
        parse_mode="HTML"
    )


@router.message(Command("yourmembers"))
async def cmd_yourmembers(message: Message):
    """Reply qilingan odamning guruhga qo'shgan odamlar soni"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not message.reply_to_message:
        await message.answer("❗️ Iltimos, biror foydalanuvchining xabariga reply qiling!")
        return

    target = message.reply_to_message.from_user
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (message.chat.id, target.id)
            )
            row = await cur.fetchone()
            count = row[0] if row else 0

    await message.answer(
        f"📈 <b>{target.full_name}</b>\n"
        f"👥 Guruhga qo'shgan odamlar: <b>{count} ta</b>",
        parse_mode="HTML"
    )


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Eng ko'p odam qo'shgan 10 talik"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT r.referrer_id, u.full_name, u.username, COUNT(*) as cnt
                   FROM group_referrals r
                   LEFT JOIN users u ON u.id = r.referrer_id
                   WHERE r.group_id = %s
                   GROUP BY r.referrer_id
                   ORDER BY cnt DESC
                   LIMIT 10""",
                (message.chat.id,)
            )
            rows = await cur.fetchall()

    if not rows:
        await message.answer("📭 Hali hech kim odam qo'shmagan!")
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>Eng ko'p odam qo'shganlar:</b>\n\n"
    for i, (uid, full_name, username, cnt) in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = full_name or username or str(uid)
        text += f"{medal} <b>{name}</b> — <b>{cnt} ta</b>\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("delson"))
async def cmd_delson(message: Message):
    """Guruhga odam qo'shganlarni barchasini tozalash"""
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
                "DELETE FROM group_referrals WHERE group_id = %s",
                (message.chat.id,)
            )

    await message.answer("🗑 Barcha referral ma'lumotlari tozalandi!")


@router.message(Command("clean"))
async def cmd_clean(message: Message):
    """Reply qilingan foydalanuvchining ma'lumotlarini 0 ga tenglash"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not await is_admin(message):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    if not message.reply_to_message:
        await message.answer("❗️ Iltimos, biror foydalanuvchining xabariga reply qiling!")
        return

    target = message.reply_to_message.from_user
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (message.chat.id, target.id)
            )

    await message.answer(
        f"🧹 <b>{target.full_name}</b> ning ma'lumotlari 0 ga tenglandi!",
        parse_mode="HTML"
    )


@router.message(Command("plus"))
async def cmd_plus(message: Message):
    """O'z balini boshqa foydalanuvchiga o'tkazish"""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    if not message.reply_to_message:
        await message.answer("❗️ Iltimos, biror foydalanuvchining xabariga reply qiling!")
        return

    sender = message.from_user
    target = message.reply_to_message.from_user

    if sender.id == target.id:
        await message.answer("❌ O'zingizga o'tkaza olmaysiz!")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Sender referral sonini olish
            await cur.execute(
                "SELECT COUNT(*) FROM group_referrals WHERE group_id = %s AND referrer_id = %s",
                (message.chat.id, sender.id)
            )
            row = await cur.fetchone()
            sender_count = row[0] if row else 0

            if sender_count == 0:
                await message.answer("❌ Sizda o'tkazish uchun referrallar yo'q!")
                return

            # Barcha referrallarni targetga o'tkazish
            await cur.execute(
                """UPDATE group_referrals SET referrer_id = %s
                   WHERE group_id = %s AND referrer_id = %s""",
                (target.id, message.chat.id, sender.id)
            )

    await message.answer(
        f"✅ <b>{sender.full_name}</b> ning <b>{sender_count} ta</b> referrali\n"
        f"➡️ <b>{target.full_name}</b> ga o'tkazildi!",
        parse_mode="HTML"
    )
