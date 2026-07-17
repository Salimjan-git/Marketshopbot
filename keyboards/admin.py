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
                KeyboardButton("📂 Категорияҳо"),
                KeyboardButton("🏷 Брендҳо"),
            ],
            [
                KeyboardButton("📱 Моделҳо"),
                KeyboardButton("🛍 Товарҳо"),
            ],
            [
                KeyboardButton("📦 Все заказы"),
                KeyboardButton("📊 Статистика"),
            ],
            [KeyboardButton("🔙 Главное меню")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def admin_categories_keyboard(
    categories: list,
    prefix: str = "admin_category",
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                category["name"],
                callback_data=f"{prefix}_{category['id']}",
            )
        ]
        for category in categories
    ]
    keyboard.append([
        InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(keyboard)


def admin_brands_keyboard(
    brands: list,
    prefix: str = "admin_product_brand",
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                brand["name"],
                callback_data=f"{prefix}_{brand['id']}",
            )
        ]
        for brand in brands
    ]
    keyboard.append([
        InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(keyboard)


def admin_models_keyboard(models: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                model["name"],
                callback_data=f"admin_product_model_{model['id']}",
            )
        ]
        for model in models
    ]
    keyboard.append([
        InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(keyboard)


def condition_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🆕 Нав",
                callback_data="admin_condition_new",
            ),
            InlineKeyboardButton(
                "♻️ Б/у",
                callback_data="admin_condition_used",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="admin_cancel",
            )
        ],
    ])



def imei_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ IMEI дорад",
                callback_data="admin_imei_yes",
            ),
            InlineKeyboardButton(
                "❌ IMEI надорад",
                callback_data="admin_imei_no",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="admin_cancel",
            )
        ],
    ])

def finish_images_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Суратҳо тамом",
                callback_data="admin_images_finished",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="admin_cancel",
            )
        ],
    ])


def confirm_product_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Сохранить",
                callback_data="admin_product_save",
            ),
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="admin_cancel",
            ),
        ]
    ])


def orders_admin_keyboard(orders: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"Заказ #{order['id']} — {order['status']}",
                callback_data=f"admin_order_{order['id']}",
            )
        ]
        for order in orders[:30]
    ])


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Подтвердить",
                callback_data=f"admin_status_confirmed_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ В обработке",
                callback_data=f"admin_status_processing_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🚚 Отправлен",
                callback_data=f"admin_status_shipped_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "📬 Доставлен",
                callback_data=f"admin_status_delivered_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отменить заказ",
                callback_data=f"admin_status_cancelled_{order_id}",
            )
        ],
    ])


# =========================================================
# MANAGE CATEGORIES
# =========================================================

def categories_manage_keyboard(categories: list) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                category["name"],
                callback_data=f"admin_category_manage_{category['id']}",
            )
        ]
        for category in categories
    ]
    return InlineKeyboardMarkup(keyboard)


def category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ Изменить",
                callback_data=f"admin_category_edit_{category_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить",
                callback_data=f"admin_category_delete_{category_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 К категориям",
                callback_data="admin_categories_list",
            )
        ],
    ])


def confirm_delete_category_keyboard(
    category_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=(
                    f"admin_category_delete_confirm_{category_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"admin_category_manage_{category_id}",
            )
        ],
    ])


# =========================================================
# MANAGE BRANDS
# =========================================================

def brands_manage_keyboard(brands: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{brand.get('category_name', '—')} — {brand['name']}",
                callback_data=f"admin_brand_manage_{brand['id']}",
            )
        ]
        for brand in brands
    ])


def brand_actions_keyboard(brand_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ Изменить",
                callback_data=f"admin_brand_edit_{brand_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить",
                callback_data=f"admin_brand_delete_{brand_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 К брендам",
                callback_data="admin_brands_list",
            )
        ],
    ])


def confirm_delete_brand_keyboard(brand_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=f"admin_brand_delete_confirm_{brand_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"admin_brand_manage_{brand_id}",
            )
        ],
    ])


# =========================================================
# MANAGE MODELS
# =========================================================

def models_manage_keyboard(models: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{model.get('brand_name', '')} — {model['name']}",
                callback_data=f"admin_model_manage_{model['id']}",
            )
        ]
        for model in models
    ])


def model_actions_keyboard(model_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ Изменить",
                callback_data=f"admin_model_edit_{model_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить",
                callback_data=f"admin_model_delete_{model_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 К моделям",
                callback_data="admin_models_list",
            )
        ],
    ])


def confirm_delete_model_keyboard(model_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=f"admin_model_delete_confirm_{model_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"admin_model_manage_{model_id}",
            )
        ],
    ])


# =========================================================
# MANAGE PRODUCTS
# =========================================================

def products_manage_keyboard(products: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                (
                    f"{product['title']} — "
                    f"{float(product['price']):.2f} сомонӣ"
                ),
                callback_data=f"admin_product_manage_{product['id']}",
            )
        ]
        for product in products
    ])


def product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ Изменить",
                callback_data=f"admin_product_edit_{product_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить",
                callback_data=f"admin_product_delete_{product_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 К товарам",
                callback_data="admin_products_list",
            )
        ],
    ])


def confirm_delete_product_keyboard(
    product_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=f"admin_product_delete_confirm_{product_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"admin_product_manage_{product_id}",
            )
        ],
    ])