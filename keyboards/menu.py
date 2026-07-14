from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


# =========================================================
# MAIN MENU
# =========================================================

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛍 Каталог")],
            [
                KeyboardButton("🛒 Корзина"),
                KeyboardButton("📦 Мои заказы"),
            ],
            [KeyboardButton("ℹ️ О нас")],
        ],
        resize_keyboard=True,
    )


# =========================================================
# CATEGORIES
# =========================================================

def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                category["name"],
                callback_data=f"category_{category['id']}",
            )
        ]
        for category in categories
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Назад",
            callback_data="back_to_main",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# BRANDS
# =========================================================

def brands_keyboard(brands: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                brand["name"],
                callback_data=f"brand_{brand['id']}",
            )
        ]
        for brand in brands
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба категорияҳо",
            callback_data="back_to_categories",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# MODELS
# =========================================================

def models_keyboard(models: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                model["name"],
                callback_data=f"model_{model['id']}",
            )
        ]
        for model in models
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба брендҳо",
            callback_data="back_to_brands",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# PRODUCTS / ADS
# =========================================================

def products_keyboard(
    products: list,
    page: int = 0,
    items_per_page: int = 5,
) -> InlineKeyboardMarkup:
    keyboard = []

    start = page * items_per_page
    end = min(start + items_per_page, len(products))

    for product in products[start:end]:
        final_price = max(
            0,
            float(product["price"]) - float(product["discount"] or 0),
        )

        storage = product.get("storage") or "—"
        color = product.get("color") or "—"

        text = (
            f"{product['title']} | "
            f"{storage} | {color} | "
            f"{final_price:.2f} сомонӣ"
        )

        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"product_{product['id']}",
            )
        ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"products_page_{page - 1}",
            )
        )

    if end < len(products):
        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"products_page_{page + 1}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба моделҳо",
            callback_data="back_to_models",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# PRODUCT DETAILS
# =========================================================

def product_detail_keyboard(
    product_id: int,
    image_index: int = 0,
    images_count: int = 1,
) -> InlineKeyboardMarkup:
    keyboard = []

    if images_count > 1:
        image_buttons = []

        if image_index > 0:
            image_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Сурат",
                    callback_data=(
                        f"product_image_{product_id}_{image_index - 1}"
                    ),
                )
            )

        if image_index < images_count - 1:
            image_buttons.append(
                InlineKeyboardButton(
                    "Сурат ➡️",
                    callback_data=(
                        f"product_image_{product_id}_{image_index + 1}"
                    ),
                )
            )

        if image_buttons:
            keyboard.append(image_buttons)

    keyboard.append([
        InlineKeyboardButton(
            "🛒 Добавить в корзину",
            callback_data=f"add_to_cart_{product_id}",
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба эълонҳо",
            callback_data="back_to_products",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# CART
# =========================================================

def cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    keyboard = []

    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(
                (
                    f"{item['name']} x{item['quantity']} = "
                    f"{float(item['total']):.2f} сомонӣ"
                ),
                callback_data=f"cart_item_{item['product_id']}",
            )
        ])

    if cart_items:
        keyboard.append([
            InlineKeyboardButton(
                "✅ Оформить заказ",
                callback_data="checkout",
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                "🗑 Очистить корзину",
                callback_data="clear_cart",
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "🛍 Перейти в каталог",
                callback_data="back_to_categories",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Главное меню",
            callback_data="back_to_main",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# ORDER DETAILS
# =========================================================

def order_detail_keyboard(
    order_id: int,
    status: str | None = None,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📋 Статус заказа",
                callback_data=f"order_status_{order_id}",
            )
        ]
    ]

    # Танҳо заказҳои анҷомнаёфтаро бекор кардан мумкин аст
    if status not in {"cancelled", "delivered"}:
        keyboard.append([
            InlineKeyboardButton(
                "❌ Отменить заказ",
                callback_data=f"cancel_order_{order_id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Мои заказы",
            callback_data="my_orders",
        )
    ])

    return InlineKeyboardMarkup(keyboard)