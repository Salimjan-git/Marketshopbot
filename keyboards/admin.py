from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ Добавить товар")],
            [
                KeyboardButton("📂 Добавить категорию"),
                KeyboardButton("🏷 Добавить бренд"),
            ],
            [KeyboardButton("📱 Добавить модель")],
            [
                KeyboardButton("📦 Все заказы"),
                KeyboardButton("📊 Статистика"),
            ],
            [KeyboardButton("🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def admin_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(c["name"], callback_data=f"admin_category_{c['id']}")]
        for c in categories
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(keyboard)


def admin_brands_keyboard(brands: list, prefix: str = "admin_product_brand") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(b["name"], callback_data=f"{prefix}_{b['id']}")]
        for b in brands
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(keyboard)


def admin_models_keyboard(models: list) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(m["name"], callback_data=f"admin_product_model_{m['id']}")]
        for m in models
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(keyboard)


def condition_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆕 Нав", callback_data="admin_condition_new"),
            InlineKeyboardButton("♻️ Б/у", callback_data="admin_condition_used"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")],
    ])


def finish_images_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Суратҳо тамом", callback_data="admin_images_finished")],
        [InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")],
    ])


def confirm_product_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Сохранить", callback_data="admin_product_save"),
            InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel"),
        ]
    ])


def orders_admin_keyboard(orders: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Заказ #{o['id']} — {o['status']}", callback_data=f"admin_order_{o['id']}")]
        for o in orders[:30]
    ])


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_status_confirmed_{order_id}")],
        [InlineKeyboardButton("⚙️ В обработке", callback_data=f"admin_status_processing_{order_id}")],
        [InlineKeyboardButton("🚚 Отправлен", callback_data=f"admin_status_shipped_{order_id}")],
        [InlineKeyboardButton("📬 Доставлен", callback_data=f"admin_status_delivered_{order_id}")],
        [InlineKeyboardButton("❌ Отменить заказ", callback_data=f"admin_status_cancelled_{order_id}")],
        [InlineKeyboardButton("🔙 К заказам", callback_data="admin_orders")],
    ])