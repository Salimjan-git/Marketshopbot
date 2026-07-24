import logging

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database import create_tables
from handlers import admin, admin_manage, catalog, start
from handlers.cart import register_handlers as register_cart_handlers


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main() -> None:
    create_tables()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    admin_manage.register_handlers(app)
    admin.register_handlers(app)
    start.register_handlers(app)
    catalog.register_handlers(app)
    register_cart_handlers(app)

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()