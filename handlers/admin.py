from __future__ import annotations

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
    order_status_keyboard,
    orders_admin_keyboard,
)
from keyboards.menu import main_menu_keyboard

(
    ADD_CATEGORY_NAME,
    ADD_BRAND_NAME,
    ADD_MODEL_BRAND,
    ADD_MODEL_NAME,
    PRODUCT_CATEGORY,
    PRODUCT_BRAND,
    PRODUCT_MODEL,
    PRODUCT_TITLE,
    PRODUCT_CONDITION,
    PRODUCT_RAM,
    PRODUCT_STORAGE,
    PRODUCT_COLOR,
    PRODUCT_PRICE,
    PRODUCT_DISCOUNT,
    PRODUCT_STOCK,
    PRODUCT_CITY,
    PRODUCT_WARRANTY,
    PRODUCT_BATTERY,
    PRODUCT_SIM,
    PRODUCT_DESCRIPTION,
    PRODUCT_IMAGES,
    PRODUCT_CONFIRM,
) = range(22)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def deny_access(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer(
            "Шумо администратор нестед.", show_alert=True
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Шумо ҳуқуқи администратор надоред."
        )


def get_new_product(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("new_product", {})


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    context.user_data.pop("new_model", None)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            if query.message and query.message.photo:
                await query.edit_message_caption(caption="❌ Амалиёт бекор карда шуд.")
            else:
                await query.edit_message_text("❌ Амалиёт бекор карда шуд.")
        except Exception:
            pass
        if query.message:
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


async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END
    await update.message.reply_text(
        "📂 Номи категорияро нависед.\n\nМисол: 📱 Смартфоны\n\nБекор кардан: /cancel"
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


async def add_brand_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END
    await update.message.reply_text(
        "🏷 Номи брендро нависед.\n\nМисол: Samsung\n\nБекор кардан: /cancel"
    )
    return ADD_BRAND_NAME


async def add_brand_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Ном хеле кӯтоҳ аст.")
        return ADD_BRAND_NAME
    try:
        brand_id = add_brand(name=name)
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "❌ Ин бренд аллакай вуҷуд дорад.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END
    await update.message.reply_text(
        f"✅ Бренд илова шуд.\nID: {brand_id}\nНом: {name}",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def add_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END
    brands = get_brands()
    if not brands:
        await update.message.reply_text(
            "❌ Аввал бренд илова кунед.",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END
    context.user_data["new_model"] = {}
    await update.message.reply_text(
        "🏷 Барои модели нав брендро интихоб кунед:",
        reply_markup=admin_brands_keyboard(brands, prefix="admin_model_brand"),
    )
    return ADD_MODEL_BRAND


async def add_model_brand_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        brand_id = int(query.data.removeprefix("admin_model_brand_"))
    except ValueError:
        await query.edit_message_text("❌ ID-и бренд нодуруст аст.")
        return ConversationHandler.END
    context.user_data["new_model"] = {"brand_id": brand_id}
    await query.edit_message_text("📱 Номи моделро нависед.\n\nМисол: Galaxy S24 Ultra")
    return ADD_MODEL_NAME


async def add_model_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    model_data = context.user_data.get("new_model", {})
    if len(name) < 2:
        await update.message.reply_text("❌ Номи модел хеле кӯтоҳ аст.")
        return ADD_MODEL_NAME
    if "brand_id" not in model_data:
        await update.message.reply_text("❌ Бренд интихоб нашудааст.")
        return ConversationHandler.END
    try:
        model_id = add_model(model_data["brand_id"], name)
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


async def product_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        category_id = int(query.data.removeprefix("admin_category_"))
    except ValueError:
        await query.edit_message_text("❌ ID-и категория нодуруст аст.")
        return ConversationHandler.END
    get_new_product(context)["category_id"] = category_id
    brands = get_brands()
    if not brands:
        await query.edit_message_text("❌ Аввал бренд илова кунед.")
        return ConversationHandler.END
    await query.edit_message_text(
        "🏷 Брендро интихоб кунед:",
        reply_markup=admin_brands_keyboard(brands, prefix="admin_product_brand"),
    )
    return PRODUCT_BRAND


async def product_brand_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        brand_id = int(query.data.removeprefix("admin_product_brand_"))
    except ValueError:
        await query.edit_message_text("❌ ID-и бренд нодуруст аст.")
        return ConversationHandler.END
    get_new_product(context)["brand_id"] = brand_id
    models = get_models_by_brand(brand_id)
    if not models:
        await query.edit_message_text(
            "❌ Барои ин бренд ягон модел нест.\n"
            "Аввал «📱 Добавить модель»-ро истифода баред."
        )
        return ConversationHandler.END
    await query.edit_message_text(
        "📱 Моделро интихоб кунед:",
        reply_markup=admin_models_keyboard(models),
    )
    return PRODUCT_MODEL


async def product_model_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        model_id = int(query.data.removeprefix("admin_product_model_"))
    except ValueError:
        await query.edit_message_text("❌ ID-и модел нодуруст аст.")
        return ConversationHandler.END
    get_new_product(context)["model_id"] = model_id
    await query.edit_message_text(
        "📝 Номи эълонро нависед.\n\nМисол: Samsung Galaxy S24 Ultra 12/256GB"
    )
    return PRODUCT_TITLE


async def product_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if len(title) < 3:
        await update.message.reply_text("❌ Ном хеле кӯтоҳ аст.")
        return PRODUCT_TITLE
    get_new_product(context)["title"] = title
    await update.message.reply_text(
        "📦 Ҳолати маҳсулотро интихоб кунед:",
        reply_markup=condition_keyboard(),
    )
    return PRODUCT_CONDITION


async def product_condition_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = query.data.removeprefix("admin_condition_")
    if value not in {"new", "used"}:
        await query.edit_message_text("❌ Ҳолат нодуруст аст.")
        return PRODUCT_CONDITION
    get_new_product(context)["condition"] = value
    await query.edit_message_text("🧠 RAM-ро нависед. Мисол: 8 GB. Агар лозим набошад: -")
    return PRODUCT_RAM


async def product_ram_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["ram"] = None if value == "-" else value
    await update.message.reply_text("💾 Хотираро нависед. Мисол: 128 GB. Агар лозим набошад: -")
    return PRODUCT_STORAGE


async def product_storage_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["storage"] = None if value == "-" else value
    await update.message.reply_text("🎨 Рангро нависед. Мисол: Black Titanium. Агар лозим набошад: -")
    return PRODUCT_COLOR


async def product_color_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["color"] = None if value == "-" else value
    await update.message.reply_text("💰 Нархро бо сомонӣ нависед. Мисол: 9500")
    return PRODUCT_PRICE


async def product_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip().replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Нарх бояд рақам бошад.")
        return PRODUCT_PRICE
    if price < 0:
        await update.message.reply_text("❌ Нарх манфӣ шуда наметавонад.")
        return PRODUCT_PRICE
    get_new_product(context)["price"] = price
    await update.message.reply_text("📉 Тахфифро нависед. Агар набошад: 0")
    return PRODUCT_DISCOUNT


async def product_discount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        discount = float(update.message.text.strip().replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Тахфиф бояд рақам бошад.")
        return PRODUCT_DISCOUNT
    product = get_new_product(context)
    if discount < 0 or discount > product["price"]:
        await update.message.reply_text("❌ Тахфиф нодуруст аст.")
        return PRODUCT_DISCOUNT
    product["discount"] = discount
    await update.message.reply_text("📦 Миқдорро дар анбор нависед. Мисол: 10")
    return PRODUCT_STOCK


async def product_stock_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        stock = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Миқдор бояд адади бутун бошад.")
        return PRODUCT_STOCK
    if stock < 0:
        await update.message.reply_text("❌ Миқдор манфӣ шуда наметавонад.")
        return PRODUCT_STOCK
    get_new_product(context)["stock"] = stock
    await update.message.reply_text("📍 Шаҳрро нависед. Мисол: Душанбе")
    return PRODUCT_CITY


async def product_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_new_product(context)["city"] = update.message.text.strip()
    await update.message.reply_text("🛡 Кафолатро нависед. Мисол: 12 моҳ. Агар набошад: -")
    return PRODUCT_WARRANTY


async def product_warranty_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["warranty"] = None if value == "-" else value
    await update.message.reply_text("🔋 Battery health-ро нависед. Мисол: 100%. Агар лозим набошад: -")
    return PRODUCT_BATTERY


async def product_battery_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["battery_health"] = None if value == "-" else value
    await update.message.reply_text("📶 Навъи SIM-ро нависед. Мисол: Nano SIM + eSIM. Агар лозим набошад: -")
    return PRODUCT_SIM


async def product_sim_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    get_new_product(context)["sim_type"] = None if value == "-" else value
    await update.message.reply_text("📄 Тавсифи маҳсулотро нависед.")
    return PRODUCT_DESCRIPTION


async def product_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_new_product(context)["description"] = update.message.text.strip()
    await update.message.reply_text(
        "🖼 Аз 1 то 4 сурат фиристед. Суратҳоро як-як фиристед.\n"
        "Баъди анҷом «✅ Суратҳо тамом»-ро пахш кунед.",
        reply_markup=finish_images_keyboard(),
    )
    return PRODUCT_IMAGES


async def product_image_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.photo:
        await update.message.reply_text("❌ Суратро ҳамчун Photo фиристед.")
        return PRODUCT_IMAGES
    images = get_new_product(context).setdefault("images", [])
    if len(images) >= 4:
        await update.message.reply_text("⚠️ Аллакай 4 сурат қабул шуд.")
        return PRODUCT_IMAGES
    images.append(update.message.photo[-1].file_id)
    await update.message.reply_text(
        f"✅ Сурати {len(images)} қабул шуд.",
        reply_markup=finish_images_keyboard(),
    )
    return PRODUCT_IMAGES


async def product_images_finished(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    product = get_new_product(context)
    images = product.get("images", [])
    if not images:
        await query.answer("Ҳадди ақал 1 сурат фиристед.", show_alert=True)
        return PRODUCT_IMAGES
    condition_text = "Нав" if product["condition"] == "new" else "Б/у"
    final_price = product["price"] - product["discount"]
    caption = (
        "📋 Маълумоти эълони нав:\n\n"
        f"📝 Ном: {product['title']}\n"
        f"📦 Ҳолат: {condition_text}\n"
        f"🧠 RAM: {product.get('ram') or '—'}\n"
        f"💾 Хотира: {product.get('storage') or '—'}\n"
        f"🎨 Ранг: {product.get('color') or '—'}\n"
        f"💰 Нарх: {product['price']:.2f} сомонӣ\n"
        f"📉 Тахфиф: {product['discount']:.2f} сомонӣ\n"
        f"💳 Нархи ниҳоӣ: {final_price:.2f} сомонӣ\n"
        f"📦 Миқдор: {product['stock']}\n"
        f"📍 Шаҳр: {product['city']}\n"
        f"🛡 Кафолат: {product.get('warranty') or '—'}\n"
        f"🔋 Battery: {product.get('battery_health') or '—'}\n"
        f"📶 SIM: {product.get('sim_type') or '—'}\n"
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
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return ConversationHandler.END
    product = context.user_data.get("new_product")
    if not product:
        await query.edit_message_caption(caption="❌ Маълумоти маҳсулот ёфт нашуд.")
        return ConversationHandler.END
    try:
        product_id = add_product(
            category_id=product["category_id"],
            brand_id=product["brand_id"],
            model_id=product["model_id"],
            title=product["title"],
            description=product.get("description"),
            condition=product["condition"],
            ram=product.get("ram"),
            storage=product.get("storage"),
            color=product.get("color"),
            price=product["price"],
            discount=product["discount"],
            stock=product["stock"],
            city=product.get("city"),
            warranty=product.get("warranty"),
            battery_health=product.get("battery_health"),
            sim_type=product.get("sim_type"),
        )
        for position, file_id in enumerate(product.get("images", []), start=1):
            add_product_image(product_id, file_id, position)
    except Exception as error:
        await query.edit_message_caption(caption=f"❌ Маҳсулот сабт нашуд:\n{error}")
        return ConversationHandler.END
    title = product["title"]
    context.user_data.pop("new_product", None)
    await query.edit_message_caption(
        caption=f"✅ Маҳсулот илова шуд!\n\nID: {product_id}\nНом: {title}"
    )
    await query.message.reply_text(
        "👨‍💼 Панели администратор",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return
    orders = get_all_orders()
    if not orders:
        await update.message.reply_text("📦 Ҳоло ягон фармоиш нест.")
        return
    await update.message.reply_text(
        "📦 Ҳамаи фармоишҳо:",
        reply_markup=orders_admin_keyboard(orders),
    )


async def admin_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    orders = get_all_orders()
    if not orders:
        await query.edit_message_text("📦 Ҳоло ягон фармоиш нест.")
        return
    await query.edit_message_text(
        "📦 Ҳамаи фармоишҳо:",
        reply_markup=orders_admin_keyboard(orders),
    )


async def show_admin_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        order_id = int(query.data.removeprefix("admin_order_"))
    except ValueError:
        return
    order = get_order_details(order_id)
    if not order:
        await query.edit_message_text("❌ Фармоиш ёфт нашуд.")
        return
    lines = [
        f"📦 Фармоиш #{order['id']}",
        f"👤 Мизоҷ: {order.get('full_name') or 'Номаълум'}",
        f"🆔 Telegram ID: {order.get('telegram_id')}",
        f"📞 Телефон: {order['phone']}",
        f"🏠 Адрес: {order['address']}",
        f"💰 Маблағ: {float(order['total_price']):.2f} сомонӣ",
        f"📋 Статус: {order['status']}",
        f"📅 Сана: {order['created_at']}",
        "",
        "🛍 Маҳсулот:",
    ]
    for item in order["items"]:
        total = float(item["price"]) * item["quantity"]
        lines.append(f"• {item['product_name']} × {item['quantity']} = {total:.2f} сомонӣ")
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=order_status_keyboard(order_id),
    )


async def change_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    if len(parts) != 4:
        return
    status = parts[2]
    try:
        order_id = int(parts[3])
    except ValueError:
        return
    if not update_order_status(order_id, status):
        await query.answer("❌ Статус иваз нашуд.", show_alert=True)
        return
    await query.edit_message_text(
        f"✅ Статуси фармоиши #{order_id} иваз шуд.\nСтатуси нав: {status}",
        reply_markup=order_status_keyboard(order_id),
    )


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await deny_access(update)
        return
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
    delivered_orders = sum(1 for order in orders if order["status"] == "delivered")
    await update.message.reply_text(
        "📊 Статистика\n\n"
        f"👥 Корбарон: {len(users)}\n"
        f"📂 Категорияҳо: {len(categories)}\n"
        f"🏷 Брендҳо: {len(brands)}\n"
        f"🛍 Маҳсулот: {len(products)}\n"
        f"📦 Фармоишҳо: {len(orders)}\n"
        f"✅ Расонидашуда: {delivered_orders}\n"
        f"💰 Даромади умумӣ: {total_income:.2f} сомонӣ"
    )


def register_handlers(app: Application) -> None:
    category_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📂 Добавить категорию$"), add_category_start)],
        states={ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        allow_reentry=True,
    )
    brand_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^🏷 Добавить бренд$"), add_brand_start)],
        states={ADD_BRAND_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_brand_name)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        allow_reentry=True,
    )
    model_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📱 Добавить модель$"), add_model_start)],
        states={
            ADD_MODEL_BRAND: [CallbackQueryHandler(add_model_brand_selected, pattern=r"^admin_model_brand_\d+$")],
            ADD_MODEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_model_name)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern=r"^admin_cancel$"),
        ],
        allow_reentry=True,
    )
    product_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^➕ Добавить товар$"), add_product_start)],
        states={
            PRODUCT_CATEGORY: [CallbackQueryHandler(product_category_selected, pattern=r"^admin_category_\d+$")],
            PRODUCT_BRAND: [CallbackQueryHandler(product_brand_selected, pattern=r"^admin_product_brand_\d+$")],
            PRODUCT_MODEL: [CallbackQueryHandler(product_model_selected, pattern=r"^admin_product_model_\d+$")],
            PRODUCT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_title_input)],
            PRODUCT_CONDITION: [CallbackQueryHandler(product_condition_selected, pattern=r"^admin_condition_(new|used)$")],
            PRODUCT_RAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_ram_input)],
            PRODUCT_STORAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_storage_input)],
            PRODUCT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_color_input)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_price_input)],
            PRODUCT_DISCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_discount_input)],
            PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_stock_input)],
            PRODUCT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_city_input)],
            PRODUCT_WARRANTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_warranty_input)],
            PRODUCT_BATTERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_battery_input)],
            PRODUCT_SIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_sim_input)],
            PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_description_input)],
            PRODUCT_IMAGES: [
                MessageHandler(filters.PHOTO, product_image_input),
                CallbackQueryHandler(product_images_finished, pattern=r"^admin_images_finished$"),
            ],
            PRODUCT_CONFIRM: [
                CallbackQueryHandler(product_save, pattern=r"^admin_product_save$"),
                CallbackQueryHandler(cancel_conversation, pattern=r"^admin_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern=r"^admin_cancel$"),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(CommandHandler("admin", admin_command), group=-1)
    app.add_handler(product_conversation, group=-1)
    app.add_handler(model_conversation, group=-1)
    app.add_handler(category_conversation, group=-1)
    app.add_handler(brand_conversation, group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^📦 Все заказы$"), show_all_orders), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^📊 Статистика$"), show_statistics), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^🔙 Главное меню$"), back_to_main), group=-1)
    app.add_handler(CallbackQueryHandler(admin_orders_callback, pattern=r"^admin_orders$"), group=-1)
    app.add_handler(CallbackQueryHandler(show_admin_order, pattern=r"^admin_order_\d+$"), group=-1)
    app.add_handler(
        CallbackQueryHandler(
            change_order_status,
            pattern=r"^admin_status_(confirmed|processing|shipped|delivered|cancelled)_\d+$",
        ),
        group=-1,
    )