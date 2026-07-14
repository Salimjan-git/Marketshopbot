from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("➕ Добавить товар"),
            ],
            [
                KeyboardButton("📂 Добавить категорию"),
                KeyboardButton("🏷 Добавить бренд"),
            ],
            [
                KeyboardButton("📱 Добавить модель"),
            ],

            # Идоракунӣ: update/delete
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
            [
                KeyboardButton("🔙 Главное меню"),
            ],
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
    
    
# =========================================================
# MANAGE BRANDS
# =========================================================

def brands_manage_keyboard(brands: list) -> InlineKeyboardMarkup:
    keyboard = []

    for brand in brands:
        keyboard.append([
            InlineKeyboardButton(
                brand["name"],
                callback_data=f"admin_brand_manage_{brand['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "➕ Добавить бренд",
            callback_data="admin_brand_add",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


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


def confirm_delete_brand_keyboard(
    brand_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=(
                    f"admin_brand_delete_confirm_{brand_id}"
                ),
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
    keyboard = []

    for model in models:
        keyboard.append([
            InlineKeyboardButton(
                f"{model['brand_name']} — {model['name']}",
                callback_data=f"admin_model_manage_{model['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "➕ Добавить модель",
            callback_data="admin_model_add",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


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


def confirm_delete_model_keyboard(
    model_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=(
                    f"admin_model_delete_confirm_{model_id}"
                ),
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
# MANAGE MODELS
# =========================================================

def models_manage_keyboard(models: list) -> InlineKeyboardMarkup:
    keyboard = []

    for model in models:
        keyboard.append([
            InlineKeyboardButton(
                f"{model['brand_name']} — {model['name']}",
                callback_data=f"admin_model_manage_{model['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "➕ Добавить модель",
            callback_data="admin_model_add",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


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


def confirm_delete_model_keyboard(
    model_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, удалить",
                callback_data=(
                    f"admin_model_delete_confirm_{model_id}"
                ),
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
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                (
                    f"{product['title']} — "
                    f"{float(product['price']):.2f} сомонӣ"
                ),
                callback_data=f"admin_product_manage_{product['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "➕ Добавить товар",
            callback_data="admin_product_add",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


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
                callback_data=(
                    f"admin_product_delete_confirm_{product_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"admin_product_manage_{product_id}",
            )
        ],
    ])