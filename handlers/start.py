from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
)

from database import get_or_create_user
from keyboards.menu import main_menu_keyboard


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    db_user = get_or_create_user(
    telegram_id=user.id,
    full_name=user.full_name,
    username=user.username,
)

    context.user_data["user_id"] = db_user["id"]
    text = f"""
👋 Салом, {user.first_name}!

Ба Marketplace хуш омадед.

Дар ин ҷо метавонед:

📱 Смартфон
🎧 Наушник
⌚ Smart Watch
📱 Чехол
🔋 Power Bank
🔌 Аксессуарҳо

харидорӣ намоед.
"""

    await update.message.reply_text(
        text=text,
        reply_markup=main_menu_keyboard(),
    )


def register_handlers(app):
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )