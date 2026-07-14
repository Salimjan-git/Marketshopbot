from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def brands_list_keyboard(brands: list) -> InlineKeyboardMarkup:
    keyboard = []

    for brand in brands:
        keyboard.append([
            InlineKeyboardButton(
                text=brand["name"],
                callback_data=f"admin_brand_manage_{brand['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Панели admin",
            callback_data="admin_back_to_panel",
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