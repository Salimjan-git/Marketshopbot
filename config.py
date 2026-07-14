import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN дар файли .env ёфт нашуд"
    )

BOT_TOKEN = BOT_TOKEN.strip()

DB_NAME = os.getenv(
    "DB_NAME",
    "marketplace.db",
).strip()

ADMIN_IDS = {
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
}