import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS
from database import (
    add_brand,
    add_category,
    add_model,
    add_product,
    add_product_image,
    get_all_orders,
    get_all_users,
    get_brands,
    get_brands_by_category,
    get_categories,
    get_models_by_brand,
    get_order_details,
    get_products,
    update_order_status,
)
from keyboards.admin import (
    admin_brands_keyboard,
    admin_categories_keyboard,
    admin_menu_keyboard,
    admin_models_keyboard,
    condition_keyboard,
    confirm_product_keyboard,
    finish_images_keyboard,
    imei_keyboard,
    order_status_keyboard,
    orders_admin_keyboard,
)
from keyboards.menu import main_menu_keyboard


(
    ADD_CATEGORY_NAME,
    ADD_BRAND_CATEGORY,
    ADD_BRAND_NAME,
    ADD_MODEL_CATEGORY,
    ADD_MODEL_BRAND,
    ADD_MODEL_NAME,
    PRODUCT_CATEGORY,
    PRODUCT_BRAND,
    PRODUCT_MODEL,
    PRODUCT_TITLE,
    PRODUCT_DESCRIPTION,
    PRODUCT_CONDITION,
    PRODUCT_RAM,
    PRODUCT_STORAGE,
    PRODUCT_COLOR,
    PRODUCT_IMEI,
    PRODUCT_WARRANTY,
    PRODUCT_PRICE,
    PRODUCT_IMAGES,
    PRODUCT_CONFIRM,
) = range(20)


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


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    await update.message.reply_text(
        "👨‍💼 Панели администратор",
        reply_markup=admin_menu_keyboard(),
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏠 Менюи асосӣ",
        reply_markup=main_menu_keyboard(),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    context.user_data.pop("new_model", None)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            if query.message.photo:
                await query.edit_message_caption(
                    caption="❌ Амалиёт бекор карда шуд."
                )
            else:
                await query.edit_message_text(
                    "❌ Амалиёт бекор карда шуд."
                )
        except Exception:
            pass
        await query.message.reply_text(
            "👨‍💼 Панели администратор",
            reply_markup=admin_menu_keyboard(),
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Амалиёт бекор карда шуд.",
            reply_markup=admin_menu_keyboard(),
        )

    return ConversationHandler.END


# ===================== CATEGORY =====================

async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END

    await update.message.reply_text(
        "📂 Номи категорияро нависед.\n"
        "Мисол: 📱 Смартфоны\n\n"
        "Бекор кардан: /cancel"
    )
    return ADD_CATEGORY_NAME


async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Ном хеле кӯтоҳ аст.")
        return ADD_CATEGORY_NAME

    try:
        category_id = add_category(name=name)
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Ин категория аллакай вуҷуд дорад.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"✅ Категория илова шуд.\nID: {category_id}\nНом: {name}",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


# ===================== BRAND =====================

async def add_brand_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END

    categories = get_categories()

    if not categories:
        await update.message.reply_text(
            "❌ Аввал категория илова кунед.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["new_brand"] = {}

    await update.message.reply_text(
        "📂 Категорияи брендро интихоб кунед:",
        reply_markup=admin_categories_keyboard(
            categories,
            prefix="admin_brand_category",
        ),
    )
    return ADD_BRAND_CATEGORY


async def add_brand_category_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    try:
        category_id = int(
            query.data.removeprefix("admin_brand_category_")
        )
    except ValueError:
        return ConversationHandler.END

    context.user_data["new_brand"] = {
        "category_id": category_id,
    }

    await query.edit_message_text(
        "🏷 Номи брендро нависед.\n\n"
        "Мисол: JBL, Apple, Baseus ё Anker"
    )
    return ADD_BRAND_NAME


async def add_brand_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    name = update.message.text.strip()
    brand_data = context.user_data.get("new_brand", {})

    if len(name) < 2:
        await update.message.reply_text("❌ Ном хеле кӯтоҳ аст.")
        return ADD_BRAND_NAME

    category_id = brand_data.get("category_id")

    if not category_id:
        await update.message.reply_text(
            "❌ Категория интихоб нашудааст.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    try:
        brand_id = add_brand(
            category_id=category_id,
            name=name,
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Ин бренд дар ҳамин категория аллакай вуҷуд дорад.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data.pop("new_brand", None)

    await update.message.reply_text(
        f"✅ Бренд илова шуд.\nID: {brand_id}\nНом: {name}",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


# ===================== MODEL =====================

async def add_model_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END

    categories = get_categories()

    if not categories:
        await update.message.reply_text(
            "❌ Аввал категория илова кунед.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["new_model"] = {}

    await update.message.reply_text(
        "📂 Категорияи моделро интихоб кунед:",
        reply_markup=admin_categories_keyboard(
            categories,
            prefix="admin_model_category",
        ),
    )
    return ADD_MODEL_CATEGORY


async def add_model_category_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    try:
        category_id = int(
            query.data.removeprefix("admin_model_category_")
        )
    except ValueError:
        return ConversationHandler.END

    brands = get_brands_by_category(category_id)

    if not brands:
        await query.edit_message_text(
            "❌ Барои ин категория ҳоло бренд нест.\n"
            "Аввал бренд илова кунед."
        )
        return ConversationHandler.END

    context.user_data["new_model"] = {
        "category_id": category_id,
    }

    await query.edit_message_text(
        "🏷 Брендро интихоб кунед:",
        reply_markup=admin_brands_keyboard(
            brands,
            prefix="admin_model_brand",
        ),
    )
    return ADD_MODEL_BRAND


async def add_model_brand_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    try:
        brand_id = int(
            query.data.removeprefix("admin_model_brand_")
        )
    except ValueError:
        return ConversationHandler.END

    model_data = context.user_data.setdefault("new_model", {})
    model_data["brand_id"] = brand_id

    await query.edit_message_text(
        "📱 Номи моделро нависед.\n"
        "Мисол: Galaxy S24 Ultra, Tune 520BT ё Watch 6"
    )
    return ADD_MODEL_NAME


async def add_model_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    name = update.message.text.strip()
    model_data = context.user_data.get("new_model", {})

    if len(name) < 2:
        await update.message.reply_text(
            "❌ Номи модел хеле кӯтоҳ аст."
        )
        return ADD_MODEL_NAME

    brand_id = model_data.get("brand_id")

    if not brand_id:
        await update.message.reply_text(
            "❌ Бренд интихоб нашудааст.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    try:
        model_id = add_model(
            brand_id=brand_id,
            name=name,
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Ин модел барои ҳамин бренд аллакай вуҷуд дорад.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data.pop("new_model", None)

    await update.message.reply_text(
        f"✅ Модел илова шуд.\nID: {model_id}\nНом: {name}",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


# ===================== PRODUCT =====================

def new_product(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("new_product", {"images": []})


async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END

    categories = get_categories()
    if not categories:
        await update.message.reply_text(
            "❌ Аввал категория илова кунед.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["new_product"] = {"images": []}
    await update.message.reply_text(
        "📂 Категорияро интихоб кунед:",
        reply_markup=admin_categories_keyboard(categories),
    )
    return PRODUCT_CATEGORY


async def product_category_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.removeprefix("admin_category_"))
    new_product(context)["category_id"] = category_id

    brands = get_brands_by_category(category_id)
    if not brands:
        await query.edit_message_text(
            "❌ Барои ин категория ҳоло бренд нест.\n"
            "Аввал бренд илова кунед."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "🏷 Брендро интихоб кунед:",
        reply_markup=admin_brands_keyboard(
            brands,
            prefix="admin_product_brand",
        ),
    )
    return PRODUCT_BRAND


async def product_brand_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    brand_id = int(query.data.removeprefix("admin_product_brand_"))
    new_product(context)["brand_id"] = brand_id

    models = get_models_by_brand(brand_id)
    if not models:
        await query.edit_message_text(
            "❌ Барои ин бренд модел нест.\n"
            "Аввал «📱 Добавить модель»-ро истифода баред."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "📱 Моделро интихоб кунед:",
        reply_markup=admin_models_keyboard(models),
    )
    return PRODUCT_MODEL


async def product_model_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    model_id = int(query.data.removeprefix("admin_product_model_"))
    new_product(context)["model_id"] = model_id

    await query.edit_message_text(
        "📝 Номи эълонро нависед.\n"
        "Мисол: Samsung Galaxy S24 Ultra 12/256GB"
    )
    return PRODUCT_TITLE


async def product_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if len(title) < 3:
        await update.message.reply_text("❌ Ном хеле кӯтоҳ аст.")
        return PRODUCT_TITLE

    new_product(context)["title"] = title
    await update.message.reply_text("📄 Тавсифи маҳсулотро нависед.")
    return PRODUCT_DESCRIPTION


async def product_description_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    description = update.message.text.strip()
    if len(description) < 3:
        await update.message.reply_text("❌ Тавсиф хеле кӯтоҳ аст.")
        return PRODUCT_DESCRIPTION

    new_product(context)["description"] = description
    await update.message.reply_text(
        "📦 Ҳолати маҳсулотро интихоб кунед:",
        reply_markup=condition_keyboard(),
    )
    return PRODUCT_CONDITION


async def product_condition_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    condition = query.data.removeprefix("admin_condition_")
    if condition not in {"new", "used"}:
        return PRODUCT_CONDITION

    new_product(context)["condition"] = condition
    await query.edit_message_text(
        "🧠 RAM-ро нависед.\n"
        "Мисол: 8 GB\n"
        "Агар лозим набошад: -"
    )
    return PRODUCT_RAM


async def product_ram_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    new_product(context)["ram"] = None if value == "-" else value
    await update.message.reply_text(
        "💾 Хотираро нависед.\n"
        "Мисол: 128 GB, 256 GB ё 1 TB"
    )
    return PRODUCT_STORAGE


async def product_storage_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("❌ Хотираро нависед.")
        return PRODUCT_STORAGE

    new_product(context)["storage"] = value
    await update.message.reply_text(
        "🎨 Рангро нависед.\n"
        "Мисол: Black Titanium"
    )
    return PRODUCT_COLOR


async def product_color_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text("❌ Рангро нависед.")
        return PRODUCT_COLOR

    new_product(context)["color"] = value

    await update.message.reply_text(
        "🔐 IMEI дорад ё не?",
        reply_markup=imei_keyboard(),
    )
    return PRODUCT_IMEI


async def product_imei_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    value = query.data.removeprefix("admin_imei_")

    if value not in {"yes", "no"}:
        return PRODUCT_IMEI

    new_product(context)["has_imei"] = value == "yes"

    await query.edit_message_text(
        "🛡 Кафолатро нависед.\n\n"
        "Мисол: 1 моҳ, 6 моҳ, 12 моҳ\n"
        "Агар кафолат надошта бошад: -"
    )
    return PRODUCT_WARRANTY


async def product_warranty_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    new_product(context)["warranty"] = (
        None if value == "-" else value
    )

    await update.message.reply_text(
        "💰 Нархро бо сомонӣ нависед.\n"
        "Мисол: 9500"
    )
    return PRODUCT_PRICE


async def product_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip().replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Нарх бояд рақам бошад.")
        return PRODUCT_PRICE

    if price <= 0:
        await update.message.reply_text("❌ Нарх бояд аз 0 зиёд бошад.")
        return PRODUCT_PRICE

    new_product(context)["price"] = price
    await update.message.reply_text(
        "🖼 Аз 1 то 4 сурат фиристед.\n"
        "Баъди анҷом «✅ Суратҳо тамом»-ро пахш кунед.",
        reply_markup=finish_images_keyboard(),
    )
    return PRODUCT_IMAGES


async def product_image_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product = new_product(context)
    images = product.setdefault("images", [])

    if len(images) >= 4:
        await update.message.reply_text(
            "⚠️ Аллакай 4 сурат қабул шуд.",
            reply_markup=finish_images_keyboard(),
        )
        return PRODUCT_IMAGES

    images.append(update.message.photo[-1].file_id)
    await update.message.reply_text(
        f"✅ Сурати {len(images)} қабул шуд.",
        reply_markup=finish_images_keyboard(),
    )
    return PRODUCT_IMAGES


async def product_images_finished(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    product = new_product(context)
    images = product.get("images", [])

    if not images:
        await query.answer("Ҳадди ақал 1 сурат фиристед.", show_alert=True)
        return PRODUCT_IMAGES

    condition_text = "Нав" if product["condition"] == "new" else "Б/у"

    caption = (
        "📋 Маълумоти маҳсулоти нав:\n\n"
        f"📝 Ном: {product['title']}\n"
        f"📦 Ҳолат: {condition_text}\n"
        f"🧠 RAM: {product.get('ram') or '—'}\n"
        f"💾 Хотира: {product['storage']}\n"
        f"🎨 Ранг: {product['color']}\n"
        f"💰 Нарх: {product['price']:.2f} сомонӣ\n"
        f"🖼 Суратҳо: {len(images)}\n\n"
        f"📄 Тавсиф:\n{product['description']}\n\n"
        "Маҳсулотро нигоҳ дорем?"
    )

    await query.message.reply_photo(
        photo=images[0],
        caption=caption,
        reply_markup=confirm_product_keyboard(),
    )
    return PRODUCT_CONFIRM


async def product_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    product = context.user_data.get("new_product")
    if not product:
        await query.edit_message_caption(
            caption="❌ Маълумоти маҳсулот ёфт нашуд."
        )
        return ConversationHandler.END

    try:
        product_id = add_product(
            category_id=product["category_id"],
            brand_id=product["brand_id"],
            model_id=product["model_id"],
            title=product["title"],
            description=product["description"],
            condition=product["condition"],
            ram=product.get("ram"),
            storage=product["storage"],
            color=product["color"],
            has_imei=product.get("has_imei", False),
            warranty=product.get("warranty"),
            price=product["price"],
            stock=1,
        )

        for position, file_id in enumerate(product["images"], start=1):
            add_product_image(
                product_id=product_id,
                telegram_file_id=file_id,
                position=position,
            )

    except Exception as error:
        await query.edit_message_caption(
            caption=f"❌ Маҳсулот сабт нашуд:\n{error}"
        )
        return ConversationHandler.END

    title = product["title"]
    context.user_data.pop("new_product", None)

    await query.edit_message_caption(
        caption=(
            "✅ Маҳсулот бо муваффақият илова шуд!\n"
            f"ID: {product_id}\n"
            f"Ном: {title}"
        )
    )
    await query.message.reply_text(
        "👨‍💼 Панели администратор",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


# ===================== ORDERS / STATS =====================

async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orders = get_all_orders()

    if not orders:
        await update.message.reply_text("📦 Ҳоло ягон фармоиш нест.")
        return

    await update.message.reply_text(
        "📦 Ҳамаи фармоишҳо:",
        reply_markup=orders_admin_keyboard(orders),
    )


async def show_admin_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.removeprefix("admin_order_"))
    order = get_order_details(order_id)

    if not order:
        await query.edit_message_text("❌ Фармоиш ёфт нашуд.")
        return

    text = (
        f"📦 Фармоиш #{order['id']}\n"
        f"👤 {order.get('full_name') or 'Номаълум'}\n"
        f"📞 {order['phone']}\n"
        f"🏠 {order['address']}\n"
        f"💰 {float(order['total_price']):.2f} сомонӣ\n"
        f"📋 {order['status']}"
    )

    await query.edit_message_text(
        text,
        reply_markup=order_status_keyboard(order_id),
    )


async def change_order_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    _, _, status, order_id_text = query.data.split("_")
    order_id = int(order_id_text)

    update_order_status(order_id, status)

    await query.edit_message_text(
        f"✅ Статуси фармоиши #{order_id}: {status}",
        reply_markup=order_status_keyboard(order_id),
    )


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = get_all_users()
    products = get_products()
    orders = get_all_orders()
    categories = get_categories()
    brands = get_brands()

    total_income = sum(
        float(order["total_price"])
        for order in orders
        if order["status"] != "cancelled"
    )

    await update.message.reply_text(
        "📊 Статистика\n\n"
        f"👥 Корбарон: {len(users)}\n"
        f"📂 Категорияҳо: {len(categories)}\n"
        f"🏷 Брендҳо: {len(brands)}\n"
        f"🛍 Маҳсулот: {len(products)}\n"
        f"📦 Фармоишҳо: {len(orders)}\n"
        f"💰 Даромад: {total_income:.2f} сомонӣ"
    )


def register_handlers(app: Application) -> None:
    category_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^📂 Добавить категорию$"),
                add_category_start,
            )
        ],
        states={
            ADD_CATEGORY_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_category_name,
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    brand_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^🏷 Добавить бренд$"),
                add_brand_start,
            )
        ],
        states={
            ADD_BRAND_CATEGORY: [
                CallbackQueryHandler(
                    add_brand_category_selected,
                    pattern=r"^admin_brand_category_\d+$",
                )
            ],
            ADD_BRAND_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_brand_name,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(
                cancel,
                pattern=r"^admin_cancel$",
            ),
        ],
        allow_reentry=True,
    )

    model_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^📱 Добавить модель$"),
                add_model_start,
            )
        ],
        states={
            ADD_MODEL_CATEGORY: [
                CallbackQueryHandler(
                    add_model_category_selected,
                    pattern=r"^admin_model_category_\d+$",
                )
            ],
            ADD_MODEL_BRAND: [
                CallbackQueryHandler(
                    add_model_brand_selected,
                    pattern=r"^admin_model_brand_\d+$",
                )
            ],
            ADD_MODEL_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_model_name,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=r"^admin_cancel$"),
        ],
        allow_reentry=True,
    )

    product_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^➕ Добавить товар$"),
                add_product_start,
            )
        ],
        states={
            PRODUCT_CATEGORY: [
                CallbackQueryHandler(
                    product_category_selected,
                    pattern=r"^admin_category_\d+$",
                )
            ],
            PRODUCT_BRAND: [
                CallbackQueryHandler(
                    product_brand_selected,
                    pattern=r"^admin_product_brand_\d+$",
                )
            ],
            PRODUCT_MODEL: [
                CallbackQueryHandler(
                    product_model_selected,
                    pattern=r"^admin_product_model_\d+$",
                )
            ],
            PRODUCT_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_title_input,
                )
            ],
            PRODUCT_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_description_input,
                )
            ],
            PRODUCT_CONDITION: [
                CallbackQueryHandler(
                    product_condition_selected,
                    pattern=r"^admin_condition_(new|used)$",
                )
            ],
            PRODUCT_RAM: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_ram_input,
                )
            ],
            PRODUCT_STORAGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_storage_input,
                )
            ],
            PRODUCT_COLOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_color_input,
                )
            ],
            PRODUCT_IMEI: [
                CallbackQueryHandler(
                    product_imei_selected,
                    pattern=r"^admin_imei_(yes|no)$",
                )
            ],
            PRODUCT_WARRANTY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_warranty_input,
                )
            ],
            PRODUCT_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    product_price_input,
                )
            ],
            PRODUCT_IMAGES: [
                MessageHandler(filters.PHOTO, product_image_input),
                CallbackQueryHandler(
                    product_images_finished,
                    pattern=r"^admin_images_finished$",
                ),
            ],
            PRODUCT_CONFIRM: [
                CallbackQueryHandler(
                    product_save,
                    pattern=r"^admin_product_save$",
                ),
                CallbackQueryHandler(
                    cancel,
                    pattern=r"^admin_cancel$",
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=r"^admin_cancel$"),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(CommandHandler("admin", admin_command), group=-1)
    app.add_handler(product_conv, group=-1)
    app.add_handler(model_conv, group=-1)
    app.add_handler(category_conv, group=-1)
    app.add_handler(brand_conv, group=-1)

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 Все заказы$"),
            show_all_orders,
        ),
        group=-1,
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📊 Статистика$"),
            show_statistics,
        ),
        group=-1,
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^🔙 Главное меню$"),
            back_to_main,
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            show_admin_order,
            pattern=r"^admin_order_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            change_order_status,
            pattern=(
                r"^admin_status_"
                r"(confirmed|processing|shipped|delivered|cancelled)_\d+$"
            ),
        ),
        group=-1,
    )