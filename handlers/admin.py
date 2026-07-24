import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest

from config import ADMIN_IDS
from database import (
    add_brand,
    add_category,
    add_model,
    add_payment_bank,
    add_payment_method,
    add_product,
    add_product_image,
    delete_payment_bank,
    delete_payment_method,
    get_all_orders,
    get_all_users,
    get_brands,
    get_brands_by_category,
    get_categories,
    get_models_by_brand,
    get_order_details,
    get_orders_waiting_payment_review,
    get_payment_bank,
    get_payment_banks,
    get_payment_method,
    get_payment_methods,
    get_products,
    is_phone_category,
    mask_card_number,
    set_payment_bank_active,
    set_payment_method_active,
    update_order_status,
    update_payment_bank,
    update_payment_method,
    update_payment_status,
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
    payment_receipt_actions_keyboard,
    payment_receipts_keyboard,
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
    PAYMENT_BANK_NAME,
    PAYMENT_BANK_HOLDER,
    PAYMENT_BANK_LOGO,
    PAYMENT_METHOD_TITLE,
    PAYMENT_METHOD_VALUE,
    PAYMENT_METHOD_QR,
    PAYMENT_EDIT_BANK_NAME,
    PAYMENT_EDIT_BANK_HOLDER,
    PAYMENT_EDIT_BANK_LOGO,
    PAYMENT_EDIT_METHOD_TITLE,
    PAYMENT_EDIT_METHOD_VALUE,
    PAYMENT_EDIT_METHOD_QR,
) = range(32)


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


async def safe_edit_message_text(
    query,
    text: str,
    reply_markup=None,
) -> None:
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )
    except BadRequest as error:
        if "Message is not modified" in str(error):
            return
        raise


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
    context.user_data.pop("new_payment_bank", None)
    context.user_data.pop("new_payment_method", None)
    context.user_data.pop("edit_payment_bank_id", None)
    context.user_data.pop("edit_payment_method_id", None)

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
    context.user_data.pop("new_payment_bank", None)
    context.user_data.pop("new_payment_method", None)
    context.user_data.pop("edit_payment_bank_id", None)
    context.user_data.pop("edit_payment_method_id", None)

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

    product = new_product(context)
    product["description"] = description

    category_id = product.get("category_id")

    if category_id and is_phone_category(category_id):
        await update.message.reply_text(
            "📦 Ҳолати телефонро интихоб кунед:",
            reply_markup=condition_keyboard(),
        )
        return PRODUCT_CONDITION

    # Барои дигар категорияҳо майдонҳои телефонӣ истифода намешаванд.
    product["condition"] = "new"
    product["ram"] = None
    product["storage"] = None
    product["color"] = None
    product["has_imei"] = False
    product["warranty"] = None

    await update.message.reply_text(
        "💰 Нархро бо сомонӣ нависед.\n"
        "Мисол: 250"
    )
    return PRODUCT_PRICE


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
        await query.answer(
            "Ҳадди ақал 1 сурат фиристед.",
            show_alert=True,
        )
        return PRODUCT_IMAGES

    category_id = product.get("category_id")
    phone_product = bool(
        category_id and is_phone_category(category_id)
    )

    caption_lines = [
        "📋 Маълумоти маҳсулоти нав:",
        "",
        f"📝 Ном: {product['title']}",
    ]

    if phone_product:
        condition_text = (
            "Нав"
            if product.get("condition") == "new"
            else "Б/у"
        )

        caption_lines.extend([
            f"📦 Ҳолат: {condition_text}",
            f"🧠 RAM: {product.get('ram') or '—'}",
            f"💾 Хотира: {product.get('storage') or '—'}",
            f"🎨 Ранг: {product.get('color') or '—'}",
            (
                "🔐 IMEI: Дорад"
                if product.get("has_imei")
                else "🔐 IMEI: Надорад"
            ),
            f"🛡 Кафолат: {product.get('warranty') or '—'}",
        ])

    caption_lines.extend([
        f"💰 Нарх: {product['price']:.2f} сомонӣ",
        f"🖼 Суратҳо: {len(images)}",
        "",
        f"📄 Тавсиф:\n{product['description']}",
        "",
        "Маҳсулотро нигоҳ дорем?",
    ])

    await query.message.reply_photo(
        photo=images[0],
        caption="\n".join(caption_lines),
        reply_markup=confirm_product_keyboard(),
    )
    return PRODUCT_CONFIRM


async def product_save(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    product = context.user_data.get("new_product")

    if not product:
        await query.edit_message_caption(
            caption="❌ Маълумоти маҳсулот ёфт нашуд."
        )
        return ConversationHandler.END

    category_id = product["category_id"]
    phone_product = is_phone_category(category_id)

    if phone_product:
        condition = product.get("condition", "new")
        ram = product.get("ram")
        storage = product.get("storage")
        color = product.get("color")
        has_imei = product.get("has_imei", False)
        warranty = product.get("warranty")
    else:
        condition = "new"
        ram = None
        storage = None
        color = None
        has_imei = False
        warranty = None

    try:
        product_id = add_product(
            category_id=category_id,
            brand_id=product["brand_id"],
            model_id=product["model_id"],
            title=product["title"],
            description=product["description"],
            condition=condition,
            ram=ram,
            storage=storage,
            color=color,
            has_imei=has_imei,
            warranty=warranty,
            price=product["price"],
            stock=1,
        )

        for position, file_id in enumerate(
            product["images"],
            start=1,
        ):
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

    keyboard = (
        None
        if order["status"] == "delivered"
        else order_status_keyboard(order_id)
    )

    await safe_edit_message_text(
        query=query,
        text=text,
        reply_markup=keyboard,
    )


async def change_order_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    data = query.data or ""

    # Формати callback:
    # admin_status_confirmed_15
    try:
        payload = data.removeprefix("admin_status_")
        new_status, order_id_text = payload.rsplit("_", 1)
        order_id = int(order_id_text)
    except (ValueError, AttributeError):
        await query.answer(
            "❌ Маълумоти статус нодуруст аст.",
            show_alert=True,
        )
        return

    allowed_statuses = {
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
    }

    if new_status not in allowed_statuses:
        await query.answer(
            "❌ Статуси нодуруст.",
            show_alert=True,
        )
        return

    order = get_order_details(order_id)

    if not order:
        await query.answer(
            "❌ Фармоиш ёфт нашуд.",
            show_alert=True,
        )
        return

    if order["status"] == "delivered":
        await query.answer(
            "✅ Ин фармоиш аллакай расонида шудааст.",
            show_alert=True,
        )
        return

    if order["status"] == new_status:
        await query.answer(
            "ℹ️ Ин статус аллакай интихоб шудааст.",
            show_alert=True,
        )
        return

    success = update_order_status(
        order_id=order_id,
        status=new_status,
    )

    if not success:
        await query.answer(
            "❌ Статус иваз нашуд.",
            show_alert=True,
        )
        return

    updated_order = get_order_details(order_id)

    if not updated_order:
        await query.answer(
            "❌ Маълумоти навшудаи фармоиш ёфт нашуд.",
            show_alert=True,
        )
        return

    await query.answer("✅ Статус иваз шуд.")

    text = (
        f"📦 Фармоиш #{updated_order['id']}\n"
        f"👤 {updated_order.get('full_name') or 'Номаълум'}\n"
        f"📞 {updated_order.get('phone') or '—'}\n"
        f"🏠 {updated_order.get('address') or '—'}\n"
        f"💰 {float(updated_order['total_price']):.2f} сомонӣ\n"
        f"📋 {updated_order['status']}"
    )

    keyboard = (
        None
        if updated_order["status"] == "delivered"
        else order_status_keyboard(order_id)
    )

    await safe_edit_message_text(
        query=query,
        text=text,
        reply_markup=keyboard,
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



# ===================== PAYMENT BANKS / METHODS =====================

METHOD_LABELS = {
    "card": "💳 Корт",
    "phone": "📱 Телефон",
    "qr": "🖼 QR-код",
}


def payment_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Илова кардани бонк", callback_data="admin_pay_bank_add")],
        [InlineKeyboardButton("🏦 Рӯйхати бонкҳо", callback_data="admin_pay_banks")],
        [InlineKeyboardButton("🧾 Чекҳои интизор", callback_data="admin_receipts_refresh")],
        [InlineKeyboardButton("❌ Пӯшидан", callback_data="admin_pay_close")],
    ])


def payment_banks_keyboard(banks: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for bank in banks:
        status = "✅" if bank.get("is_active") else "⛔"
        rows.append([
            InlineKeyboardButton(
                f"{status} {bank['name']} ({bank.get('methods_count', 0)})",
                callback_data=f"admin_pay_bank_{bank['id']}",
            )
        ])
    rows.extend([
        [InlineKeyboardButton("➕ Илова кардани бонк", callback_data="admin_pay_bank_add")],
        [InlineKeyboardButton("🔙 Қафо", callback_data="admin_pay_home")],
    ])
    return InlineKeyboardMarkup(rows)


def payment_bank_keyboard(bank: dict) -> InlineKeyboardMarkup:
    bank_id = bank["id"]
    active_text = "⛔ Ғайрифаъол кардан" if bank.get("is_active") else "✅ Фаъол кардан"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Усули пардохт", callback_data=f"admin_pay_method_add_{bank_id}")],
        [InlineKeyboardButton("📋 Усулҳои пардохт", callback_data=f"admin_pay_methods_{bank_id}")],
        [InlineKeyboardButton("✏️ Номи бонк", callback_data=f"admin_pay_bank_name_{bank_id}")],
        [InlineKeyboardButton("👤 Соҳиби ҳисоб", callback_data=f"admin_pay_bank_holder_{bank_id}")],
        [InlineKeyboardButton("🖼 Логотип", callback_data=f"admin_pay_bank_logo_{bank_id}")],
        [InlineKeyboardButton(active_text, callback_data=f"admin_pay_bank_toggle_{bank_id}")],
        [InlineKeyboardButton("🗑 Нест кардани бонк", callback_data=f"admin_pay_bank_delete_{bank_id}")],
        [InlineKeyboardButton("🔙 Бонкҳо", callback_data="admin_pay_banks")],
    ])


def payment_method_types_keyboard(bank_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Корт", callback_data=f"admin_pay_type_card_{bank_id}")],
        [InlineKeyboardButton("📱 Телефон", callback_data=f"admin_pay_type_phone_{bank_id}")],
        [InlineKeyboardButton("🖼 QR-код", callback_data=f"admin_pay_type_qr_{bank_id}")],
        [InlineKeyboardButton("🔙 Қафо", callback_data=f"admin_pay_bank_{bank_id}")],
    ])


def payment_methods_keyboard(bank_id: int, methods: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for method in methods:
        status = "✅" if method.get("is_active") else "⛔"
        label = METHOD_LABELS.get(method.get("method_type"), "💳 Пардохт")
        rows.append([
            InlineKeyboardButton(
                f"{status} {label}: {method['title']}",
                callback_data=f"admin_pay_method_{method['id']}",
            )
        ])
    rows.extend([
        [InlineKeyboardButton("➕ Усули нав", callback_data=f"admin_pay_method_add_{bank_id}")],
        [InlineKeyboardButton("🔙 Қафо", callback_data=f"admin_pay_bank_{bank_id}")],
    ])
    return InlineKeyboardMarkup(rows)


def payment_method_keyboard(method: dict) -> InlineKeyboardMarkup:
    method_id = method["id"]
    bank_id = method["bank_id"]
    active_text = "⛔ Ғайрифаъол кардан" if method.get("is_active") else "✅ Фаъол кардан"
    value_label = "🖼 QR-код" if method.get("method_type") == "qr" else "🔢 Маълумот"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Ном", callback_data=f"admin_pay_method_title_{method_id}")],
        [InlineKeyboardButton(value_label, callback_data=f"admin_pay_method_value_{method_id}")],
        [InlineKeyboardButton(active_text, callback_data=f"admin_pay_method_toggle_{method_id}")],
        [InlineKeyboardButton("🗑 Нест кардан", callback_data=f"admin_pay_method_delete_{method_id}")],
        [InlineKeyboardButton("🔙 Усулҳо", callback_data=f"admin_pay_methods_{bank_id}")],
    ])


def skip_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Гузаштан", callback_data=callback_data)],
        [InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_cancel")],
    ])


def bank_text(bank: dict) -> str:
    status = "Фаъол" if bank.get("is_active") else "Ғайрифаъол"
    return (
        f"🏦 Бонк #{bank['id']}\n\n"
        f"Ном: {bank['name']}\n"
        f"👤 Соҳиби ҳисоб: {bank.get('card_holder') or '—'}\n"
        f"🖼 Логотип: {'✅ Ҳаст' if bank.get('logo_file_id') else '❌ Нест'}\n"
        f"💳 Усулҳо: {bank.get('methods_count', 0)}\n"
        f"📌 Ҳолат: {status}"
    )


def method_text(method: dict) -> str:
    label = METHOD_LABELS.get(method.get("method_type"), "Пардохт")
    status = "Фаъол" if method.get("is_active") else "Ғайрифаъол"
    value = "QR-код нигоҳ дошта шудааст" if method.get("method_type") == "qr" else method.get("value") or "—"
    if method.get("method_type") == "card":
        value = mask_card_number(method.get("value"))
    return (
        f"{label}\n\n"
        f"🏦 Бонк: {method.get('bank_name') or '—'}\n"
        f"📝 Ном: {method['title']}\n"
        f"🔢 Маълумот: {value}\n"
        f"📌 Ҳолат: {status}"
    )


async def payment_settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END

    await update.message.reply_text(
        "💳 Идоракунии пардохт\n\nДар ин ҷо бонкҳо ва усулҳои пардохтро идора кунед.",
        reply_markup=payment_main_keyboard(),
    )
    return ConversationHandler.END


async def payment_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await safe_edit_message_text(
        query,
        "💳 Идоракунии пардохт\n\nДар ин ҷо бонкҳо ва усулҳои пардохтро идора кунед.",
        payment_main_keyboard(),
    )
    return ConversationHandler.END


async def payment_banks_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    banks = get_payment_banks()
    text = "🏦 Бонкҳои пардохт:" if banks else "🏦 Ҳоло ягон бонк илова нашудааст."
    await safe_edit_message_text(query, text, payment_banks_keyboard(banks))
    return ConversationHandler.END


async def payment_bank_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_bank_"))
    bank = get_payment_bank(bank_id)
    if not bank:
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    await safe_edit_message_text(query, bank_text(bank), payment_bank_keyboard(bank))
    return ConversationHandler.END


async def payment_bank_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["new_payment_bank"] = {}
    await query.message.reply_text("🏦 Номи бонкро нависед.\nМисол: Alif Bank")
    return PAYMENT_BANK_NAME


async def payment_bank_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if len(value) < 2:
        await update.message.reply_text("❌ Номи бонк хеле кӯтоҳ аст.")
        return PAYMENT_BANK_NAME
    context.user_data.setdefault("new_payment_bank", {})["name"] = value
    await update.message.reply_text(
        "👤 Номи соҳиби ҳисоб ё кортро нависед.\nАгар лозим набошад «-» нависед."
    )
    return PAYMENT_BANK_HOLDER


async def payment_bank_holder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    context.user_data.setdefault("new_payment_bank", {})["card_holder"] = None if value == "-" else value
    await update.message.reply_text(
        "🖼 Логотипи бонкро ҳамчун сурат фиристед ё гузаред.",
        reply_markup=skip_keyboard("admin_pay_bank_logo_skip"),
    )
    return PAYMENT_BANK_LOGO


async def _finish_payment_bank(update: Update, context: ContextTypes.DEFAULT_TYPE, logo_file_id: str | None) -> int:
    data = context.user_data.get("new_payment_bank", {})
    try:
        bank_id = add_payment_bank(
            name=data["name"],
            card_holder=data.get("card_holder"),
            logo_file_id=logo_file_id,
        )
    except (KeyError, ValueError, sqlite3.IntegrityError) as error:
        message = update.effective_message
        await message.reply_text(f"❌ Бонк илова нашуд: {error}", reply_markup=admin_menu_keyboard())
        return ConversationHandler.END

    context.user_data.pop("new_payment_bank", None)
    bank = get_payment_bank(bank_id)
    await update.effective_message.reply_text(
        "✅ Бонк илова шуд.\n\n" + bank_text(bank),
        reply_markup=payment_bank_keyboard(bank),
    )
    return ConversationHandler.END


async def payment_bank_logo_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_payment_bank(update, context, update.message.photo[-1].file_id)


async def payment_bank_logo_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _finish_payment_bank(update, context, None)


async def payment_bank_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payload = query.data.removeprefix("admin_pay_bank_")
    field, bank_id_text = payload.rsplit("_", 1)
    bank_id = int(bank_id_text)
    if not get_payment_bank(bank_id):
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    context.user_data["edit_payment_bank_id"] = bank_id
    prompts = {
        "name": ("✏️ Номи нави бонкро нависед:", PAYMENT_EDIT_BANK_NAME),
        "holder": ("👤 Номи нави соҳиби ҳисобро нависед. Барои холӣ кардан «-»:", PAYMENT_EDIT_BANK_HOLDER),
        "logo": ("🖼 Логотипи нави бонкро фиристед:", PAYMENT_EDIT_BANK_LOGO),
    }
    prompt, state = prompts[field]
    await query.message.reply_text(prompt)
    return state


async def payment_edit_bank_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    bank_id = context.user_data.get("edit_payment_bank_id")
    if not bank_id or len(value) < 2:
        await update.message.reply_text("❌ Номи дуруст ворид кунед.")
        return PAYMENT_EDIT_BANK_NAME
    update_payment_bank(bank_id, name=value)
    return await _show_updated_bank(update, context, bank_id)


async def payment_edit_bank_holder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    bank_id = context.user_data.get("edit_payment_bank_id")
    if not bank_id:
        return ConversationHandler.END
    update_payment_bank(bank_id, card_holder="" if value == "-" else value)
    return await _show_updated_bank(update, context, bank_id)


async def payment_edit_bank_logo_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bank_id = context.user_data.get("edit_payment_bank_id")
    if not bank_id:
        return ConversationHandler.END
    update_payment_bank(bank_id, logo_file_id=update.message.photo[-1].file_id)
    return await _show_updated_bank(update, context, bank_id)


async def _show_updated_bank(update: Update, context: ContextTypes.DEFAULT_TYPE, bank_id: int) -> int:
    context.user_data.pop("edit_payment_bank_id", None)
    bank = get_payment_bank(bank_id)
    await update.effective_message.reply_text(
        "✅ Маълумоти бонк нав шуд.\n\n" + bank_text(bank),
        reply_markup=payment_bank_keyboard(bank),
    )
    return ConversationHandler.END


async def payment_bank_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_bank_toggle_"))
    bank = get_payment_bank(bank_id)
    if not bank:
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    set_payment_bank_active(bank_id, not bool(bank["is_active"]))
    bank = get_payment_bank(bank_id)
    await safe_edit_message_text(query, bank_text(bank), payment_bank_keyboard(bank))
    return ConversationHandler.END


async def payment_bank_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_bank_delete_"))
    bank = get_payment_bank(bank_id)
    if not bank:
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ҳа, нест кун", callback_data=f"admin_pay_bank_delete_yes_{bank_id}")],
        [InlineKeyboardButton("❌ Не", callback_data=f"admin_pay_bank_{bank_id}")],
    ])
    await safe_edit_message_text(
        query,
        f"⚠️ Бонк «{bank['name']}» ва ҳамаи усулҳои он нест карда мешаванд. Давом диҳем?",
        keyboard,
    )
    return ConversationHandler.END


async def payment_bank_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_bank_delete_yes_"))
    deleted = delete_payment_bank(bank_id)
    banks = get_payment_banks()
    text = "✅ Бонк нест карда шуд." if deleted else "❌ Бонк нест карда нашуд."
    await safe_edit_message_text(query, text, payment_banks_keyboard(banks))
    return ConversationHandler.END


async def payment_methods_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_methods_"))
    bank = get_payment_bank(bank_id)
    if not bank:
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    methods = get_payment_methods(bank_id)
    text = f"💳 Усулҳои пардохти {bank['name']}:" if methods else f"💳 Барои {bank['name']} ҳоло усул нест."
    await safe_edit_message_text(query, text, payment_methods_keyboard(bank_id, methods))
    return ConversationHandler.END


async def payment_method_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bank_id = int(query.data.removeprefix("admin_pay_method_add_"))
    if not get_payment_bank(bank_id):
        await query.answer("Бонк ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    context.user_data["new_payment_method"] = {"bank_id": bank_id}
    await safe_edit_message_text(query, "Навъи усули пардохтро интихоб кунед:", payment_method_types_keyboard(bank_id))
    return ConversationHandler.END


async def payment_method_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payload = query.data.removeprefix("admin_pay_type_")
    method_type, bank_id_text = payload.rsplit("_", 1)
    if method_type not in METHOD_LABELS:
        return ConversationHandler.END
    context.user_data["new_payment_method"] = {"bank_id": int(bank_id_text), "method_type": method_type}
    await query.message.reply_text("📝 Номи усулро нависед.\nМисол: Корти асосӣ, Рақами Душанбе Сити")
    return PAYMENT_METHOD_TITLE


async def payment_method_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    data = context.user_data.get("new_payment_method", {})
    if len(value) < 2 or not data:
        await update.message.reply_text("❌ Номи дуруст ворид кунед.")
        return PAYMENT_METHOD_TITLE
    data["title"] = value
    if data["method_type"] == "qr":
        await update.message.reply_text("🖼 QR-кодро ҳамчун сурат фиристед.")
        return PAYMENT_METHOD_QR
    example = "9860 1234 5678 9012" if data["method_type"] == "card" else "+992 00 000 00 00"
    await update.message.reply_text(f"🔢 Маълумоти пардохтро нависед.\nМисол: {example}")
    return PAYMENT_METHOD_VALUE


async def payment_method_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    data = context.user_data.get("new_payment_method", {})
    if not value or not data:
        await update.message.reply_text("❌ Маълумот холӣ буда наметавонад.")
        return PAYMENT_METHOD_VALUE
    if data.get("method_type") == "card":
        clean = value.replace(" ", "").replace("-", "")
        if not clean.isdigit() or len(clean) < 12:
            await update.message.reply_text("❌ Рақами корт нодуруст аст.")
            return PAYMENT_METHOD_VALUE
    return await _finish_payment_method(update, context, value=value)


async def payment_method_qr_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_payment_method(update, context, qr_file_id=update.message.photo[-1].file_id)


async def _finish_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE, value: str | None = None, qr_file_id: str | None = None) -> int:
    data = context.user_data.get("new_payment_method", {})
    try:
        method_id = add_payment_method(
            bank_id=data["bank_id"],
            method_type=data["method_type"],
            title=data["title"],
            value=value,
            qr_file_id=qr_file_id,
        )
    except (KeyError, ValueError, sqlite3.IntegrityError) as error:
        await update.effective_message.reply_text(f"❌ Усул илова нашуд: {error}")
        return ConversationHandler.END
    context.user_data.pop("new_payment_method", None)
    method = get_payment_method(method_id)
    await update.effective_message.reply_text(
        "✅ Усули пардохт илова шуд.\n\n" + method_text(method),
        reply_markup=payment_method_keyboard(method),
    )
    return ConversationHandler.END


async def payment_method_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method_id = int(query.data.removeprefix("admin_pay_method_"))
    method = get_payment_method(method_id)
    if not method:
        await query.answer("Усул ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    if method.get("method_type") == "qr" and method.get("qr_file_id"):
        await query.message.reply_photo(
            photo=method["qr_file_id"],
            caption=method_text(method),
            reply_markup=payment_method_keyboard(method),
        )
    else:
        await safe_edit_message_text(query, method_text(method), payment_method_keyboard(method))
    return ConversationHandler.END


async def payment_method_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payload = query.data.removeprefix("admin_pay_method_")
    field, method_id_text = payload.rsplit("_", 1)
    method_id = int(method_id_text)
    method = get_payment_method(method_id)
    if not method:
        await query.answer("Усул ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    context.user_data["edit_payment_method_id"] = method_id
    if field == "title":
        await query.message.reply_text("✏️ Номи нави усулро нависед:")
        return PAYMENT_EDIT_METHOD_TITLE
    if method["method_type"] == "qr":
        await query.message.reply_text("🖼 QR-коди навро фиристед:")
        return PAYMENT_EDIT_METHOD_QR
    await query.message.reply_text("🔢 Маълумоти нави пардохтро нависед:")
    return PAYMENT_EDIT_METHOD_VALUE


async def payment_edit_method_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    method_id = context.user_data.get("edit_payment_method_id")
    if not method_id or len(value) < 2:
        await update.message.reply_text("❌ Номи дуруст ворид кунед.")
        return PAYMENT_EDIT_METHOD_TITLE
    update_payment_method(method_id, title=value)
    return await _show_updated_method(update, context, method_id)


async def payment_edit_method_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    method_id = context.user_data.get("edit_payment_method_id")
    method = get_payment_method(method_id) if method_id else None
    if not method or not value:
        await update.message.reply_text("❌ Маълумоти дуруст ворид кунед.")
        return PAYMENT_EDIT_METHOD_VALUE
    if method["method_type"] == "card":
        clean = value.replace(" ", "").replace("-", "")
        if not clean.isdigit() or len(clean) < 12:
            await update.message.reply_text("❌ Рақами корт нодуруст аст.")
            return PAYMENT_EDIT_METHOD_VALUE
    update_payment_method(method_id, value=value)
    return await _show_updated_method(update, context, method_id)


async def payment_edit_method_qr_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    method_id = context.user_data.get("edit_payment_method_id")
    if not method_id:
        return ConversationHandler.END
    update_payment_method(method_id, qr_file_id=update.message.photo[-1].file_id)
    return await _show_updated_method(update, context, method_id)


async def _show_updated_method(update: Update, context: ContextTypes.DEFAULT_TYPE, method_id: int) -> int:
    context.user_data.pop("edit_payment_method_id", None)
    method = get_payment_method(method_id)
    await update.effective_message.reply_text(
        "✅ Усули пардохт нав шуд.\n\n" + method_text(method),
        reply_markup=payment_method_keyboard(method),
    )
    return ConversationHandler.END


async def payment_method_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method_id = int(query.data.removeprefix("admin_pay_method_toggle_"))
    method = get_payment_method(method_id)
    if not method:
        await query.answer("Усул ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    set_payment_method_active(method_id, not bool(method["is_active"]))
    method = get_payment_method(method_id)
    await safe_edit_message_text(query, method_text(method), payment_method_keyboard(method))
    return ConversationHandler.END


async def payment_method_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method_id = int(query.data.removeprefix("admin_pay_method_delete_"))
    method = get_payment_method(method_id)
    if not method:
        await query.answer("Усул ёфт нашуд.", show_alert=True)
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ҳа, нест кун", callback_data=f"admin_pay_method_delete_yes_{method_id}")],
        [InlineKeyboardButton("❌ Не", callback_data=f"admin_pay_method_{method_id}")],
    ])
    await safe_edit_message_text(query, f"⚠️ Усули «{method['title']}» нест карда шавад?", keyboard)
    return ConversationHandler.END


async def payment_method_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method_id = int(query.data.removeprefix("admin_pay_method_delete_yes_"))
    method = get_payment_method(method_id)
    bank_id = method["bank_id"] if method else None
    deleted = delete_payment_method(method_id)
    if bank_id:
        methods = get_payment_methods(bank_id)
        await safe_edit_message_text(
            query,
            "✅ Усул нест карда шуд." if deleted else "❌ Усул нест карда нашуд.",
            payment_methods_keyboard(bank_id, methods),
        )
    else:
        await safe_edit_message_text(query, "❌ Усул ёфт нашуд.", payment_main_keyboard())
    return ConversationHandler.END


async def payment_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👨‍💼 Панели администратор", reply_markup=admin_menu_keyboard())
    return ConversationHandler.END


# ===================== PAYMENT RECEIPTS =====================

async def show_payment_receipts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    orders = get_orders_waiting_payment_review()

    if not orders:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "🧾 Ҳоло ягон чеки нав барои санҷиш нест."
            )
        else:
            await update.message.reply_text(
                "🧾 Ҳоло ягон чеки нав барои санҷиш нест."
            )
        return

    text = f"🧾 Чекҳои интизори санҷиш: {len(orders)}"
    keyboard = payment_receipts_keyboard(orders)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def show_payment_receipt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    await query.answer()
    order_id = int(query.data.removeprefix("admin_receipt_"))
    order = get_order_details(order_id)

    if not order:
        await query.edit_message_text("❌ Фармоиш ёфт нашуд.")
        return

    receipt_file_id = order.get("receipt_file_id")

    if not receipt_file_id:
        await query.edit_message_text("❌ Чеки пардохт ёфт нашуд.")
        return

    username = order.get("username")
    username_text = f"@{username}" if username else "—"

    caption = (
        f"🧾 Чеки фармоиши #{order['id']}\n\n"
        f"👤 {order.get('full_name') or 'Номаълум'}\n"
        f"🔗 Telegram: {username_text}\n"
        f"📞 {order.get('phone') or '—'}\n"
        f"🏠 {order.get('address') or '—'}\n"
        f"💰 {float(order['total_price']):.2f} сомонӣ\n"
        f"🏦 Бонк: {order.get('payment_bank_name') or '—'}\n"
        f"💳 Усул: {order.get('payment_method_title') or '—'}\n"
        f"📌 Статус: {order.get('payment_status') or '—'}"
    )

    await query.message.reply_photo(
        photo=receipt_file_id,
        caption=caption,
        reply_markup=payment_receipt_actions_keyboard(order_id),
    )


async def approve_or_reject_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    user = update.effective_user

    if not user or not is_admin(user.id):
        await deny_access(update)
        return

    await query.answer()
    parts = query.data.rsplit("_", 1)
    order_id = int(parts[1])
    approved = query.data.startswith("admin_payment_approve_")
    payment_status = "confirmed" if approved else "rejected"

    order = get_order_details(order_id)

    if not order:
        await query.edit_message_caption(caption="❌ Фармоиш ёфт нашуд.")
        return

    updated = update_payment_status(order_id, payment_status)

    if not updated:
        await query.edit_message_caption(
            caption="❌ Статуси пардохт тағйир дода нашуд."
        )
        return

    result_text = (
        "✅ Пардохт тасдиқ шуд."
        if approved
        else "❌ Пардохт рад карда шуд."
    )
    await query.edit_message_caption(
        caption=f"{result_text}\nФармоиш #{order_id}"
    )

    telegram_id = order.get("telegram_id")

    if telegram_id:
        customer_text = (
            f"✅ Пардохти фармоиши #{order_id} тасдиқ шуд.\n"
            "Фармоиши шумо ба коркард гузашт."
            if approved
            else (
                f"❌ Пардохти фармоиши #{order_id} тасдиқ нашуд.\n"
                "Лутфан чеки дурустро аз нав фиристед ё бо админ "
                "тамос гиред."
            )
        )

        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=customer_text,
            )
        except Exception:
            pass

async def admin_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    error = context.error

    if isinstance(error, BadRequest):
        if "Message is not modified" in str(error):
            return

    raise error


def register_handlers(app: Application) -> None:
    app.add_error_handler(admin_error_handler)

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

    payment_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^💳 Танзимоти пардохт$"),
                payment_settings_start,
            ),
            CallbackQueryHandler(payment_home_callback, pattern=r"^admin_pay_home$"),
            CallbackQueryHandler(payment_banks_callback, pattern=r"^admin_pay_banks$"),
            CallbackQueryHandler(payment_bank_add_start, pattern=r"^admin_pay_bank_add$"),
            CallbackQueryHandler(payment_bank_logo_skip, pattern=r"^admin_pay_bank_logo_skip$"),
            CallbackQueryHandler(payment_bank_toggle, pattern=r"^admin_pay_bank_toggle_\d+$"),
            CallbackQueryHandler(payment_bank_delete_confirm, pattern=r"^admin_pay_bank_delete_\d+$"),
            CallbackQueryHandler(payment_bank_delete, pattern=r"^admin_pay_bank_delete_yes_\d+$"),
            CallbackQueryHandler(payment_bank_edit_start, pattern=r"^admin_pay_bank_(name|holder|logo)_\d+$"),
            CallbackQueryHandler(payment_method_add_start, pattern=r"^admin_pay_method_add_\d+$"),
            CallbackQueryHandler(payment_method_type_selected, pattern=r"^admin_pay_type_(card|phone|qr)_\d+$"),
            CallbackQueryHandler(payment_methods_callback, pattern=r"^admin_pay_methods_\d+$"),
            CallbackQueryHandler(payment_method_toggle, pattern=r"^admin_pay_method_toggle_\d+$"),
            CallbackQueryHandler(payment_method_delete_confirm, pattern=r"^admin_pay_method_delete_\d+$"),
            CallbackQueryHandler(payment_method_delete, pattern=r"^admin_pay_method_delete_yes_\d+$"),
            CallbackQueryHandler(payment_method_edit_start, pattern=r"^admin_pay_method_(title|value)_\d+$"),
            CallbackQueryHandler(payment_method_view, pattern=r"^admin_pay_method_\d+$"),
            CallbackQueryHandler(payment_bank_view, pattern=r"^admin_pay_bank_\d+$"),
            CallbackQueryHandler(payment_close, pattern=r"^admin_pay_close$"),
        ],
        states={
            PAYMENT_BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_bank_name_input)],
            PAYMENT_BANK_HOLDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_bank_holder_input)],
            PAYMENT_BANK_LOGO: [
                MessageHandler(filters.PHOTO, payment_bank_logo_input),
                CallbackQueryHandler(payment_bank_logo_skip, pattern=r"^admin_pay_bank_logo_skip$"),
            ],
            PAYMENT_METHOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method_title_input)],
            PAYMENT_METHOD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method_value_input)],
            PAYMENT_METHOD_QR: [MessageHandler(filters.PHOTO, payment_method_qr_input)],
            PAYMENT_EDIT_BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_edit_bank_name_input)],
            PAYMENT_EDIT_BANK_HOLDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_edit_bank_holder_input)],
            PAYMENT_EDIT_BANK_LOGO: [MessageHandler(filters.PHOTO, payment_edit_bank_logo_input)],
            PAYMENT_EDIT_METHOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_edit_method_title_input)],
            PAYMENT_EDIT_METHOD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_edit_method_value_input)],
            PAYMENT_EDIT_METHOD_QR: [MessageHandler(filters.PHOTO, payment_edit_method_qr_input)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern=r"^admin_cancel$"),
        ],
        allow_reentry=True,
        per_message=False,
    )
    app.add_handler(payment_conv, group=-1)
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
            filters.Regex(r"^🧾 Санҷиши чекҳо$"),
            show_payment_receipts,
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            show_payment_receipts,
            pattern=r"^admin_receipts_refresh$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            show_payment_receipt,
            pattern=r"^admin_receipt_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            approve_or_reject_payment,
            pattern=r"^admin_payment_(approve|reject)_\d+$",
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