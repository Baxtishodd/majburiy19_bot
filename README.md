# 🤖 Majburiy19 Bot

> Telegram guruhlar uchun **majburiy odam qo'shish**, **majburiy obuna** va **anti-reklama** tizimi

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![aiogram](https://img.shields.io/badge/aiogram-3.15-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?logo=mysql)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Imkoniyatlar

- 👥 **Majburiy odam qo'shish** — foydalanuvchi guruhga N ta odam qo'shmasdan xabar yubora olmaydi
- 📢 **Majburiy kanal obunasi** — belgilangan kanallarga obuna bo'lmasdan xabar yubora olmaydi
- 🚫 **Anti-reklama** — guruhda link va reklama xabarlarini avtomatik o'chirish
- 📊 **Referral statistikasi** — kim nechta odam qo'shganini kuzatish
- 📬 **Post yuborish** — guruh va kanallarga rejalashtirilgan post yuborish
- 📥 **Excel hisobot** — superadmin uchun to'liq ma'lumot eksporti

---

## 📋 Talablar

- Python **3.11+**
- MySQL **8.0+**
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))

---

## ⚙️ O'rnatish

### 1. Reponi klonlash

```bash
git clone https://github.com/SIZNING_USERNAME/majburiy19_bot.git
cd majburiy19_bot
```

### 2. Virtual muhit va kutubxonalar

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. `.env` fayl sozlash

```bash
cp .env.example .env
```

`.env` faylini to'ldiring:

```env
BOT_TOKEN=your_bot_token_here

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=majburiy19_bot

ADMIN_IDS=123456789,987654321
```

> ⚠️ `ADMIN_IDS` — vergul bilan ajratilgan Telegram user ID lar. Birinchi ID **superadmin** hisoblanadi.

### 4. MySQL bazasini yaratish

```sql
CREATE DATABASE majburiy19_bot
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Bot ishga tushganda barcha jadvallar avtomatik yaratiladi.

### 5. Ishga tushirish

```bash
python main.py
```

---

## 🚀 Server (Production) deploy

### Systemd service (Linux)

```bash
sudo nano /etc/systemd/system/majburiy19.service
```

```ini
[Unit]
Description=Majburiy19 Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/majburiy19_bot
ExecStart=/home/ubuntu/majburiy19_bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable majburiy19
sudo systemctl start majburiy19

# Holat tekshirish
sudo systemctl status majburiy19

# Loglarni ko'rish
sudo journalctl -u majburiy19 -f
```

---

## 📁 Fayl tuzilmasi

```
majburiy19_bot/
├── main.py              # Entry point
├── config.py            # Sozlamalar va ADMIN_IDS
├── database.py          # MySQL ulanish, pool va jadvallar
├── scheduler.py         # Rejalashtirilgan post yuborish
├── requirements.txt
├── .env                 # Maxfiy sozlamalar (gitga yuklanmaydi)
├── .env.example         # .env namunasi
├── .gitignore
└── handlers/
    ├── __init__.py
    ├── start.py         # /start — foydalanuvchi ro'yxatga olish
    ├── admin.py         # Admin panel, post yuborish, Excel hisobot
    ├── stats.py         # /mymembers, /yourmembers, /top, /delson, /clean, /plus
    ├── force.py         # /add, /textforce, /text_time, /deforce, /priv
    ├── subscription.py  # /set, /unlink — majburiy obuna sozlash
    ├── members.py       # Yangi a'zo qo'shilganda referral hisoblash
    ├── check_sub.py     # Guruh xabar filtri (obuna + force add + antiad)
    ├── antiads.py       # Anti-reklama yordamchi funksiyalar
    └── antiad_cmd.py    # /antiad buyrug'i
```

---

## 📌 Buyruqlar

### 👤 Foydalanuvchi buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/mymembers` | Siz qo'shgan odamlar soni |
| `/yourmembers` | Reply qilingan odamning qo'shganlari |
| `/top` | Eng ko'p odam qo'shgan Top 10 |

### 🔧 Guruh admin buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/add N` | N ta odam qo'shishni majburiy qilish |
| `/add off` | Majburiy qo'shishni o'chirish |
| `/textforce [matn]` | Ogohlantirish matni qo'shish |
| `/textforce 0` | Ogohlantirish matnini o'chirish |
| `/text_time N` | Matn avtomatik o'chish vaqti (soniya) |
| `/deforce` | Majburiy qo'shish ma'lumotini tozalash |
| `/plus` | Referralni boshqa foydalanuvchiga o'tkazish |
| `/priv @user` | Foydalanuvchiga imtiyoz berish |
| `/delson` | Guruh referral ma'lumotlarini noldan boshlash |
| `/clean` | Reply foydalanuvchi referralini 0 ga tenglash |
| `/set @kanal` | Majburiy obuna kanali qo'shish |
| `/unlink` | Barcha majburiy kanallarni o'chirish |
| `/antiad on/off` | Anti-reklama yoqish/o'chirish |

### 👑 Superadmin

| Imkoniyat | Tavsif |
|-----------|--------|
| Admin panel | Post yuborish, statistika, admin boshqaruvi |
| Excel hisobot | Foydalanuvchilar, guruhlar, kanallar, postlar, oylik statistika |

---

## 📊 Excel hisobot varaqlari

Superadmin admin paneldan `📥 Excel hisobot` orqali yuklab oladi:

| Varaq | Ma'lumotlar |
|-------|-------------|
| Foydalanuvchilar | ID, username, ism, referral soni, balans, sana |
| Guruhlar | Chat ID, nomi, username, qo'shilgan sana |
| Kanallar | Chat ID, nomi, username, qo'shilgan sana |
| Chop etilgan postlar | ID, admin, turi, auditoriya, yuborilgan/xato soni |
| Oylik hisobot | Oy, yangi userlar, postlar, auditoriya |

---

## 🔒 Xavfsizlik

- `.env` fayli **hech qachon** gitga yuklanmaydi
- Bot tokeni faqat `.env` da saqlanadi
- Superadmin va admin huquqlari alohida ajratilgan
- Guruh adminlari filtrlari chetlab o'tiladi

---

## 📄 Litsenziya

MIT License — [LICENSE](LICENSE) faylini ko'ring.
