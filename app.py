import logging

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database import create_tables
from handlers import (
    admin,
    admin_manage,
    cart,
    catalog,
    start,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)




def main():
    create_tables()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    admin.register_handlers(app)
    admin_manage.register_handlers(app)
    cart.register_handlers(app)
    start.register_handlers(app)
    catalog.register_handlers(app)
    print("🤖 Бот запущен...")

    app.run_polling()


if __name__ == "__main__":
    main()