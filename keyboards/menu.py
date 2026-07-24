from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


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
        is_persistent=True,
    )


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
            "🔙 Главное меню",
            callback_data="back_to_main",
        )
    ])
    return InlineKeyboardMarkup(keyboard)


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


def products_keyboard(
    products: list,
    page: int = 0,
    items_per_page: int = 5,
) -> InlineKeyboardMarkup:
    keyboard = []
    start = page * items_per_page
    end = min(start + items_per_page, len(products))

    for product in products[start:end]:
        storage = product.get("storage") or "—"
        color = product.get("color") or "—"
        final_price = max(
            0,
            float(product["price"]) - float(product.get("discount") or 0),
        )

        keyboard.append([
            InlineKeyboardButton(
                (
                    f"{product['title']} | {storage} | "
                    f"{color} | {final_price:.2f} сомонӣ"
                ),
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


def cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    keyboard = []

    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(
                (
                    f"{item['name']} × {item['quantity']} = "
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


def checkout_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💵 Нақдӣ",
                callback_data="checkout_payment_cash",
            ),
            InlineKeyboardButton(
                "🌐 Онлайн",
                callback_data="checkout_payment_online",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Бекор кардан",
                callback_data="checkout_cancel",
            )
        ],
    ])


def payment_banks_keyboard(banks: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                f"🏦 {bank['name']}",
                callback_data=f"checkout_bank_{bank['id']}",
            )
        ]
        for bank in banks
    ]
    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба тарзи пардохт",
            callback_data="checkout_back_payment",
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            "❌ Бекор кардан",
            callback_data="checkout_cancel",
        )
    ])
    return InlineKeyboardMarkup(keyboard)


def payment_methods_keyboard(methods: list) -> InlineKeyboardMarkup:
    labels = {
        "card": "💳",
        "phone": "📱",
        "qr": "🔳",
    }
    keyboard = [
        [
            InlineKeyboardButton(
                f"{labels.get(method['method_type'], '💰')} {method['title']}",
                callback_data=f"checkout_method_{method['id']}",
            )
        ]
        for method in methods
    ]
    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба бонкҳо",
            callback_data="checkout_back_banks",
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            "❌ Бекор кардан",
            callback_data="checkout_cancel",
        )
    ])
    return InlineKeyboardMarkup(keyboard)


def online_order_created_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🧾 Чекро фиристодан",
                callback_data=f"upload_receipt_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "📦 Мои заказы",
                callback_data="my_orders",
            )
        ],
        [
            InlineKeyboardButton(
                "🛍 Ба каталог",
                callback_data="back_to_categories",
            )
        ],
    ])


def cash_order_created_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📦 Мои заказы",
                callback_data="my_orders",
            )
        ],
        [
            InlineKeyboardButton(
                "🛍 Ба каталог",
                callback_data="back_to_categories",
            )
        ],
    ])


def order_detail_keyboard(
    order_id: int,
    status: str | None = None,
    payment_method: str | None = None,
    payment_status: str | None = None,
) -> InlineKeyboardMarkup:
    keyboard = []

    if (
        payment_method == "online"
        and payment_status in {"pending_receipt", "rejected"}
        and status != "cancelled"
    ):
        keyboard.append([
            InlineKeyboardButton(
                "🧾 Фиристодани чек",
                callback_data=f"upload_receipt_{order_id}",
            )
        ])

    if status not in {"cancelled", "shipped", "delivered"}:
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