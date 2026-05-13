import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "majburiy19_bot")

ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]

# Webhook sozlamalari
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://bunyodkoritp.uz/majburiybot")
WEBHOOK_PATH     = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET", "majburiy19-bot-secret")
WEBHOOK_URL      = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 8011))
