import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "majburiy19_bot")

ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]

# Webhook — xuddi uzum bot uslubida
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET", BOT_TOKEN).strip()
WEBHOOK_PATH     = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL      = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
