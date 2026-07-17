from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from database import get_or_create_user
from keyboards.menu import main_menu_keyboard


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or not update.message:
        return

    db_user = get_or_create_user(
        telegram_id=user.id,
        full_name=user.full_name,
        username=user.username,
    )

    context.user_data["user_id"] = int(db_user["id"])

    text = (
        f"👋 Салом, {user.first_name}!\n\n"
        "Ба Marketplace хуш омадед.\n\n"
        "📱 Смартфон\n"
        "🎧 Наушник\n"
        "⌚ Smart Watch\n"
        "📱 Чехол\n"
        "🔋 Power Bank\n"
        "🔌 Аксессуарҳо"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=main_menu_keyboard(),
    )


def register_handlers(app: Application) -> None:
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )