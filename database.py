import aiomysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

pool = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        autocommit=True,
        charset="utf8mb4",
    )


async def get_pool():
    return pool


async def init_db():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    referrer_id BIGINT DEFAULT NULL,
                    referral_count INT DEFAULT 0,
                    balance INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS group_settings (
                    group_id BIGINT PRIMARY KEY,
                    group_title VARCHAR(255) DEFAULT NULL,
                    force_add_enabled BOOLEAN DEFAULT FALSE,
                    force_add_count INT DEFAULT 0,
                    force_text TEXT DEFAULT NULL,
                    force_text_delete_after INT DEFAULT 0,
                    antiads_enabled BOOLEAN DEFAULT FALSE,
                    antiads_text TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            for col, definition in [
                ("antiads_enabled", "BOOLEAN DEFAULT FALSE"),
                ("antiads_text", "TEXT DEFAULT NULL"),
                ("group_title", "VARCHAR(255) DEFAULT NULL"),
            ]:
                try:
                    await cur.execute(
                        f"ALTER TABLE group_settings ADD COLUMN {col} {definition}"
                    )
                except Exception:
                    pass

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS force_channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    channel_username VARCHAR(255),
                    UNIQUE KEY unique_gc (group_id, channel_id)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS group_referrals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    referrer_id BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_ugr (group_id, user_id)
                )
            """)

            # Bot ulangan barcha guruh/kanallar ro'yxati
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_chats (
                    chat_id BIGINT PRIMARY KEY,
                    chat_title VARCHAR(255),
                    chat_type VARCHAR(50),
                    username VARCHAR(255),
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Rejalashtirilgan va yuborilgan postlar jadvali
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_id BIGINT NOT NULL,
                    message_text TEXT,
                    message_type VARCHAR(50) DEFAULT 'text',
                    file_id VARCHAR(255) DEFAULT NULL,
                    parse_mode VARCHAR(20) DEFAULT 'HTML',
                    target_type VARCHAR(20) DEFAULT 'all',
                    scheduled_at DATETIME NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    sent_count INT DEFAULT 0,
                    fail_count INT DEFAULT 0,
                    total_audience INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # total_audience ustunini eski jadvalga qo'shish (agar mavjud bo'lmasa)
            try:
                await cur.execute(
                    "ALTER TABLE scheduled_posts ADD COLUMN total_audience INT DEFAULT 0"
                )
            except Exception:
                pass

            # Adminlar jadvali (DB ga qo'shimcha adminlar)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_admins (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255) DEFAULT NULL,
                    full_name VARCHAR(255) DEFAULT NULL,
                    added_by BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
