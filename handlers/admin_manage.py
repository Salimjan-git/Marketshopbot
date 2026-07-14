import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS
from database import (
    delete_brand,
    delete_model,
    delete_product,
    get_brand,
    get_brands,
    get_model,
    get_models_by_brand,
    get_product,
    get_products,
    update_brand,
    update_model,
    update_product,
)
from keyboards.admin import (
    admin_menu_keyboard,
    brand_actions_keyboard,
    brands_manage_keyboard,
    confirm_delete_brand_keyboard,
    confirm_delete_model_keyboard,
    confirm_delete_product_keyboard,
    model_actions_keyboard,
    models_manage_keyboard,
    product_actions_keyboard,
    products_manage_keyboard,
)


(
    EDIT_BRAND_NAME,
    EDIT_MODEL_NAME,
    EDIT_PRODUCT_TITLE,
    EDIT_PRODUCT_PRICE,
) = range(4)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def deny_access(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer(
            "❌ Шумо администратор нестед.",
            show_alert=True,
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Шумо ҳуқуқи администратор надоред."
        )


# =========================================================
# BRANDS
# =========================================================

async def show_brands(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    brands = get_brands()

    if not brands:
        await update.message.reply_text(
            "🏷 Ҳоло ягон бренд нест.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        "🏷 Рӯйхати брендҳо:",
        reply_markup=brands_manage_keyboard(brands),
    )


async def show_brands_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    brands = get_brands()

    await query.edit_message_text(
        "🏷 Рӯйхати брендҳо:",
        reply_markup=brands_manage_keyboard(brands),
    )


async def show_brand_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    brand_id = int(
        query.data.removeprefix("admin_brand_manage_")
    )

    brand = get_brand(brand_id)

    if not brand:
        await query.edit_message_text("❌ Бренд ёфт нашуд.")
        return

    await query.edit_message_text(
        f"🏷 Бренд\n\nID: {brand['id']}\nНом: {brand['name']}",
        reply_markup=brand_actions_keyboard(brand_id),
    )


async def edit_brand_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    brand_id = int(
        query.data.removeprefix("admin_brand_edit_")
    )

    brand = get_brand(brand_id)

    if not brand:
        await query.edit_message_text("❌ Бренд ёфт нашуд.")
        return ConversationHandler.END

    context.user_data["edit_brand_id"] = brand_id

    await query.edit_message_text(
        f"✏️ Номи ҳозира: {brand['name']}\n\n"
        "Номи навро нависед:"
    )

    return EDIT_BRAND_NAME


async def edit_brand_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    brand_id = context.user_data.get("edit_brand_id")
    name = update.message.text.strip()

    if not brand_id:
        return ConversationHandler.END

    try:
        update_brand(
            brand_id=brand_id,
            name=name,
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Бренд бо чунин ном аллакай вуҷуд дорад."
        )
        return EDIT_BRAND_NAME

    context.user_data.pop("edit_brand_id", None)

    await update.message.reply_text(
        "✅ Бренд навсозӣ шуд.",
        reply_markup=admin_menu_keyboard(),
    )

    return ConversationHandler.END


async def delete_brand_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    brand_id = int(
        query.data.removeprefix("admin_brand_delete_")
    )

    brand = get_brand(brand_id)

    await query.edit_message_text(
        f"⚠️ Бренди «{brand['name']}»-ро нест мекунед?",
        reply_markup=confirm_delete_brand_keyboard(brand_id),
    )


async def delete_brand_execute(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    brand_id = int(
        query.data.removeprefix(
            "admin_brand_delete_confirm_"
        )
    )

    delete_brand(brand_id)

    await query.edit_message_text(
        "✅ Бренд нест карда шуд."
    )


# =========================================================
# MODELS
# =========================================================

async def show_models(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    brands = get_brands()
    models = []

    for brand in brands:
        models.extend(get_models_by_brand(brand["id"]))

    if not models:
        await update.message.reply_text(
            "📱 Ҳоло ягон модел нест.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        "📱 Рӯйхати моделҳо:",
        reply_markup=models_manage_keyboard(models),
    )


async def show_models_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    brands = get_brands()
    models = []

    for brand in brands:
        models.extend(get_models_by_brand(brand["id"]))

    await query.edit_message_text(
        "📱 Рӯйхати моделҳо:",
        reply_markup=models_manage_keyboard(models),
    )


async def show_model_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    model_id = int(
        query.data.removeprefix("admin_model_manage_")
    )

    model = get_model(model_id)

    if not model:
        await query.edit_message_text("❌ Модел ёфт нашуд.")
        return

    await query.edit_message_text(
        (
            f"📱 Модел\n\n"
            f"ID: {model['id']}\n"
            f"Бренд: {model['brand_name']}\n"
            f"Ном: {model['name']}"
        ),
        reply_markup=model_actions_keyboard(model_id),
    )


async def edit_model_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    model_id = int(
        query.data.removeprefix("admin_model_edit_")
    )

    model = get_model(model_id)

    if not model:
        await query.edit_message_text("❌ Модел ёфт нашуд.")
        return ConversationHandler.END

    context.user_data["edit_model_id"] = model_id
    context.user_data["edit_model_brand_id"] = model["brand_id"]

    await query.edit_message_text(
        f"✏️ Номи ҳозира: {model['name']}\n\n"
        "Номи навро нависед:"
    )

    return EDIT_MODEL_NAME


async def edit_model_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    model_id = context.user_data.get("edit_model_id")
    brand_id = context.user_data.get("edit_model_brand_id")
    name = update.message.text.strip()

    if not model_id or not brand_id:
        return ConversationHandler.END

    try:
        update_model(
            model_id=model_id,
            brand_id=brand_id,
            name=name,
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Ин модел аллакай вуҷуд дорад."
        )
        return EDIT_MODEL_NAME

    context.user_data.pop("edit_model_id", None)
    context.user_data.pop("edit_model_brand_id", None)

    await update.message.reply_text(
        "✅ Модел навсозӣ шуд.",
        reply_markup=admin_menu_keyboard(),
    )

    return ConversationHandler.END


async def delete_model_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    model_id = int(
        query.data.removeprefix("admin_model_delete_")
    )

    model = get_model(model_id)

    await query.edit_message_text(
        f"⚠️ Модели «{model['name']}»-ро нест мекунед?",
        reply_markup=confirm_delete_model_keyboard(model_id),
    )


async def delete_model_execute(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    model_id = int(
        query.data.removeprefix(
            "admin_model_delete_confirm_"
        )
    )

    delete_model(model_id)

    await query.edit_message_text(
        "✅ Модел нест карда шуд."
    )


# =========================================================
# PRODUCTS
# =========================================================

async def show_products(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    products = get_products()

    if not products:
        await update.message.reply_text(
            "🛍 Ҳоло ягон товар нест.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        "🛍 Рӯйхати товарҳо:",
        reply_markup=products_manage_keyboard(products),
    )


async def show_products_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    products = get_products()

    await query.edit_message_text(
        "🛍 Рӯйхати товарҳо:",
        reply_markup=products_manage_keyboard(products),
    )


async def show_product_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(
        query.data.removeprefix("admin_product_manage_")
    )

    product = get_product(product_id)

    if not product:
        await query.edit_message_text("❌ Товар ёфт нашуд.")
        return

    await query.edit_message_text(
        (
            f"🛍 Товар\n\n"
            f"ID: {product['id']}\n"
            f"Ном: {product['title']}\n"
            f"Бренд: {product['brand_name']}\n"
            f"Модел: {product['model_name']}\n"
            f"Нарх: {float(product['price']):.2f} сомонӣ"
        ),
        reply_markup=product_actions_keyboard(product_id),
    )


async def edit_product_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    product_id = int(
        query.data.removeprefix("admin_product_edit_")
    )

    product = get_product(product_id)

    if not product:
        await query.edit_message_text("❌ Товар ёфт нашуд.")
        return ConversationHandler.END

    context.user_data["edit_product"] = product

    await query.edit_message_text(
        f"✏️ Номи ҳозира: {product['title']}\n\n"
        "Номи навро нависед:"
    )

    return EDIT_PRODUCT_TITLE


async def edit_product_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    product = context.user_data.get("edit_product")
    title = update.message.text.strip()

    if not product:
        return ConversationHandler.END

    product["title"] = title

    await update.message.reply_text(
        f"💰 Нархи ҳозира: {float(product['price']):.2f}\n\n"
        "Нархи навро нависед:"
    )

    return EDIT_PRODUCT_PRICE


async def edit_product_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    product = context.user_data.get("edit_product")

    try:
        price = float(
            update.message.text.strip().replace(",", ".")
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Нарх бояд рақам бошад."
        )
        return EDIT_PRODUCT_PRICE

    update_product(
        product_id=product["id"],
        category_id=product["category_id"],
        brand_id=product["brand_id"],
        model_id=product["model_id"],
        title=product["title"],
        price=price,
        description=product.get("description"),
        condition=product["condition"],
        ram=product.get("ram"),
        storage=product.get("storage"),
        color=product.get("color"),
        discount=float(product.get("discount") or 0),
        stock=int(product.get("stock") or 1),
        city=product.get("city"),
        warranty=product.get("warranty"),
        battery_health=product.get("battery_health"),
        sim_type=product.get("sim_type"),
    )

    context.user_data.pop("edit_product", None)

    await update.message.reply_text(
        "✅ Товар навсозӣ шуд.",
        reply_markup=admin_menu_keyboard(),
    )

    return ConversationHandler.END


async def delete_product_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(
        query.data.removeprefix("admin_product_delete_")
    )

    product = get_product(product_id)

    await query.edit_message_text(
        f"⚠️ Товари «{product['title']}»-ро нест мекунед?",
        reply_markup=confirm_delete_product_keyboard(product_id),
    )


async def delete_product_execute(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(
        query.data.removeprefix(
            "admin_product_delete_confirm_"
        )
    )

    delete_product(product_id)

    await query.edit_message_text(
        "✅ Товар нест карда шуд."
    )


# =========================================================
# REGISTER
# =========================================================

def register_handlers(app: Application) -> None:
    edit_brand_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                edit_brand_start,
                pattern=r"^admin_brand_edit_\d+$",
            )
        ],
        states={
            EDIT_BRAND_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_brand_name,
                )
            ]
        },
        fallbacks=[],
        allow_reentry=True,
    )

    edit_model_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                edit_model_start,
                pattern=r"^admin_model_edit_\d+$",
            )
        ],
        states={
            EDIT_MODEL_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_model_name,
                )
            ]
        },
        fallbacks=[],
        allow_reentry=True,
    )

    edit_product_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                edit_product_start,
                pattern=r"^admin_product_edit_\d+$",
            )
        ],
        states={
            EDIT_PRODUCT_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_product_title,
                )
            ],
            EDIT_PRODUCT_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_product_price,
                )
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(edit_brand_conversation, group=-2)
    app.add_handler(edit_model_conversation, group=-2)
    app.add_handler(edit_product_conversation, group=-2)

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^🏷 Брендҳо$"),
            show_brands,
        ),
        group=-2,
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📱 Моделҳо$"),
            show_models,
        ),
        group=-2,
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^🛍 Товарҳо$"),
            show_products,
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_brands_callback,
            pattern=r"^admin_brands_list$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_brand_details,
            pattern=r"^admin_brand_manage_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_brand_confirm,
            pattern=r"^admin_brand_delete_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_brand_execute,
            pattern=r"^admin_brand_delete_confirm_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_models_callback,
            pattern=r"^admin_models_list$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_model_details,
            pattern=r"^admin_model_manage_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_model_confirm,
            pattern=r"^admin_model_delete_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_model_execute,
            pattern=r"^admin_model_delete_confirm_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_products_callback,
            pattern=r"^admin_products_list$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_product_details,
            pattern=r"^admin_product_manage_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_product_confirm,
            pattern=r"^admin_product_delete_\d+$",
        ),
        group=-2,
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_product_execute,
            pattern=r"^admin_product_delete_confirm_\d+$",
        ),
        group=-2,
    )