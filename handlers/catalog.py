from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import (
    get_brands_by_category,
    get_categories,
    get_models_by_category_and_brand,
    get_order_details,
    get_or_create_user,
    get_product,
    get_products_by_model,
    get_user_orders,
)
from keyboards.menu import (
    brands_keyboard,
    categories_keyboard,
    main_menu_keyboard,
    models_keyboard,
    order_detail_keyboard,
    product_detail_keyboard,
    products_keyboard,
)


ITEMS_PER_PAGE = 5


# =========================================================
# HELPERS
# =========================================================

def get_database_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    saved_user_id = context.user_data.get("user_id")

    if saved_user_id is not None:
        try:
            return int(saved_user_id)
        except (TypeError, ValueError):
            context.user_data.pop("user_id", None)

    telegram_user = update.effective_user

    if not telegram_user:
        return None

    db_user = get_or_create_user(
        telegram_id=telegram_user.id,
        full_name=telegram_user.full_name,
        username=telegram_user.username,
    )

    if not db_user:
        return None

    user_id = int(db_user["id"])
    context.user_data["user_id"] = user_id
    return user_id


def build_product_caption(product: dict) -> str:
    price = float(product["price"])
    condition = "Нав" if product["condition"] == "new" else "Б/у"
    imei = "✅ Дорад" if product.get("has_imei") else "❌ Надорад"

    return (
        f"📦 {product['title']}\n\n"
        f"📂 Категория: {product['category_name']}\n"
        f"🏷 Бренд: {product['brand_name']}\n"
        f"📲 Модел: {product['model_name']}\n"
        f"📦 Ҳолат: {condition}\n"
        f"🧠 RAM: {product.get('ram') or '—'}\n"
        f"💾 Хотира: {product.get('storage') or '—'}\n"
        f"🎨 Ранг: {product.get('color') or '—'}\n"
        f"🔐 IMEI: {imei}\n"
        f"🛡 Кафолат: {product.get('warranty') or 'Бе кафолат'}\n"
        f"💰 Нарх: {price:.2f} сомонӣ\n\n"
        f"📝 Тавсиф:\n"
        f"{product.get('description') or 'Тавсиф мавҷуд нест.'}"
    )


async def edit_or_send_text(
    query,
    text: str,
    reply_markup=None,
) -> None:
    try:
        if query.message.photo:
            chat = query.message.chat
            await query.delete_message()
            await chat.send_message(
                text=text,
                reply_markup=reply_markup,
            )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

    except BadRequest as error:
        if "Message is not modified" in str(error):
            return

        await query.message.chat.send_message(
            text=text,
            reply_markup=reply_markup,
        )

    except Exception:
        await query.message.chat.send_message(
            text=text,
            reply_markup=reply_markup,
        )


# =========================================================
# CATEGORIES
# =========================================================

async def show_categories(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message:
        return

    categories = get_categories()

    if not categories:
        await update.message.reply_text(
            "😔 Категорияҳо ҳоло илова нашудаанд."
        )
        return

    await update.message.reply_text(
        "📂 Категорияро интихоб кунед:",
        reply_markup=categories_keyboard(categories),
    )


async def show_categories_callback(query) -> None:
    categories = get_categories()

    if not categories:
        await edit_or_send_text(
            query,
            "😔 Категорияҳо ҳоло илова нашудаанд.",
        )
        return

    await edit_or_send_text(
        query,
        "📂 Категорияро интихоб кунед:",
        categories_keyboard(categories),
    )


# =========================================================
# BRANDS / MODELS
# =========================================================

async def show_brands_callback(query, category_id: int) -> None:
    brands = get_brands_by_category(category_id)

    if not brands:
        await edit_or_send_text(
            query,
            "😔 Дар ин категория ҳоло бренд ё маҳсулот нест.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Ба категорияҳо",
                        callback_data="back_to_categories",
                    )
                ]
            ]),
        )
        return

    await edit_or_send_text(
        query,
        "🏷 Брендро интихоб кунед:",
        brands_keyboard(brands),
    )


async def show_models_callback(
    query,
    category_id: int,
    brand_id: int,
) -> None:
    models = get_models_by_category_and_brand(
        category_id=category_id,
        brand_id=brand_id,
    )

    if not models:
        await edit_or_send_text(
            query,
            "😔 Барои ин бренд ҳоло модел ё эълон нест.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Ба брендҳо",
                        callback_data="back_to_brands",
                    )
                ]
            ]),
        )
        return

    await edit_or_send_text(
        query,
        "📱 Моделро интихоб кунед:",
        models_keyboard(models),
    )


# =========================================================
# PRODUCTS
# =========================================================

async def show_products_page(
    query,
    products: list,
    page: int,
) -> None:
    if not products:
        await edit_or_send_text(query, "😔 Эълонҳо ёфт нашуданд.")
        return

    total = len(products)
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total)

    text = (
        "📱 Эълонҳо\n\n"
        f"Нишон дода мешавад: {start + 1}–{end}\n"
        f"Ҳамагӣ: {total}\n"
        f"Саҳифа: {page + 1}/{total_pages}"
    )

    await edit_or_send_text(
        query,
        text,
        products_keyboard(
            products=products,
            page=page,
            items_per_page=ITEMS_PER_PAGE,
        ),
    )


async def show_product_card(
    query,
    product_id: int,
    image_index: int = 0,
) -> None:
    product = get_product(product_id)

    if not product:
        await edit_or_send_text(query, "😔 Маҳсулот ёфт нашуд.")
        return

    images = product.get("images", [])
    caption = build_product_caption(product)

    if not images:
        await edit_or_send_text(
            query,
            caption,
            product_detail_keyboard(product_id),
        )
        return

    image_index = max(0, min(image_index, len(images) - 1))
    image_file_id = images[image_index]["telegram_file_id"]

    keyboard = product_detail_keyboard(
        product_id=product_id,
        image_index=image_index,
        images_count=len(images),
    )

    try:
        if query.message.photo:
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=image_file_id,
                    caption=caption,
                ),
                reply_markup=keyboard,
            )
        else:
            chat = query.message.chat
            await query.delete_message()
            await chat.send_photo(
                photo=image_file_id,
                caption=caption,
                reply_markup=keyboard,
            )
    except Exception:
        await query.message.chat.send_photo(
            photo=image_file_id,
            caption=caption,
            reply_markup=keyboard,
        )


# =========================================================
# ORDERS
# =========================================================

async def show_orders(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message:
        return

    user_id = get_database_user_id(update, context)
    orders = get_user_orders(user_id) if user_id else []

    if not orders:
        await update.message.reply_text(
            "📦 Шумо ҳоло ягон фармоиш надоред.",
            reply_markup=main_menu_keyboard(),
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                f"Фармоиш №{order['id']} | {order['status']}",
                callback_data=f"order_status_{order['id']}",
            )
        ]
        for order in orders
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Менюи асосӣ",
            callback_data="back_to_main",
        )
    ])

    await update.message.reply_text(
        "📦 Фармоишҳои шумо:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_orders_callback(query, user_id: int | None) -> None:
    orders = get_user_orders(user_id) if user_id else []

    if not orders:
        await edit_or_send_text(
            query,
            "📦 Шумо ҳоло ягон фармоиш надоред.",
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                f"Фармоиш №{order['id']} | {order['status']}",
                callback_data=f"order_status_{order['id']}",
            )
        ]
        for order in orders
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Менюи асосӣ",
            callback_data="back_to_main",
        )
    ])

    await edit_or_send_text(
        query,
        "📦 Фармоишҳои шумо:",
        InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# CALLBACKS
# =========================================================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""
    user_id = get_database_user_id(update, context)

    if data == "back_to_main":
        try:
            await query.delete_message()
        except Exception:
            pass

        await query.message.chat.send_message(
            "🏠 Менюи асосӣ:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "back_to_categories":
        await show_categories_callback(query)
        return

    if data == "back_to_brands":
        category_id = context.user_data.get("last_category_id")

        if category_id:
            await show_brands_callback(query, int(category_id))
        else:
            await show_categories_callback(query)
        return

    if data == "back_to_models":
        category_id = context.user_data.get("last_category_id")
        brand_id = context.user_data.get("last_brand_id")

        if category_id and brand_id:
            await show_models_callback(
                query,
                int(category_id),
                int(brand_id),
            )
        else:
            await show_categories_callback(query)
        return

    if data == "back_to_products":
        products = context.user_data.get("products_list", [])
        page = int(context.user_data.get("last_page", 0))

        if products:
            await show_products_page(query, products, page)
        else:
            await show_categories_callback(query)
        return

    if data.startswith("category_"):
        try:
            category_id = int(data.removeprefix("category_"))
        except ValueError:
            return

        context.user_data["last_category_id"] = category_id
        await show_brands_callback(query, category_id)
        return

    if data.startswith("brand_"):
        try:
            brand_id = int(data.removeprefix("brand_"))
        except ValueError:
            return

        category_id = context.user_data.get("last_category_id")

        if not category_id:
            await show_categories_callback(query)
            return

        context.user_data["last_brand_id"] = brand_id

        await show_models_callback(
            query=query,
            category_id=int(category_id),
            brand_id=brand_id,
        )
        return

    if data.startswith("model_"):
        try:
            model_id = int(data.removeprefix("model_"))
        except ValueError:
            return

        products = get_products_by_model(model_id)

        context.user_data["last_model_id"] = model_id
        context.user_data["products_list"] = products
        context.user_data["last_page"] = 0

        await show_products_page(query, products, 0)
        return

    if data.startswith("products_page_"):
        try:
            page = int(data.removeprefix("products_page_"))
        except ValueError:
            page = 0

        products = context.user_data.get("products_list", [])
        context.user_data["last_page"] = page

        await show_products_page(query, products, page)
        return

    if data.startswith("product_image_"):
        parts = data.split("_")

        try:
            product_id = int(parts[2])
            image_index = int(parts[3])
        except (ValueError, IndexError):
            return

        await show_product_card(query, product_id, image_index)
        return

    if data.startswith("product_"):
        try:
            product_id = int(data.removeprefix("product_"))
        except ValueError:
            return

        await show_product_card(query, product_id, 0)
        return

    if data == "my_orders":
        await show_orders_callback(query, user_id)
        return

    if data.startswith("order_status_"):
        try:
            order_id = int(data.removeprefix("order_status_"))
        except ValueError:
            return

        order = get_order_details(order_id)

        if not order:
            await edit_or_send_text(query, "Фармоиш ёфт нашуд.")
            return

        lines = [
            f"📋 Фармоиш №{order['id']}",
            f"📅 {order['created_at']}",
            f"💰 {float(order['total_price']):.2f} сомонӣ",
            f"📦 {order['status']}",
            f"🏠 {order['address']}",
            f"📞 {order['phone']}",
            "",
            "🛍 Маҳсулот:",
        ]

        for item in order["items"]:
            total = float(item["price"]) * int(item["quantity"])
            lines.append(
                f"• {item['product_name']} × "
                f"{item['quantity']} = {total:.2f} сомонӣ"
            )

        await edit_or_send_text(
            query,
            "\n".join(lines),
            order_detail_keyboard(
                order_id,
                order.get("status"),
            ),
        )


# =========================================================
# REGISTER
# =========================================================

def register_handlers(app: Application) -> None:
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^🛍 Каталог$"),
            show_categories,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 Мои заказы$"),
            show_orders,
        )
    )

    # Фақат callback-ҳои каталог ва фармоишҳоро қабул мекунад.
    # Callback-ҳои корзина дар handlers/cart.py мемонанд.
    app.add_handler(
        CallbackQueryHandler(
            handle_callback,
            pattern=(
                r"^(?:"
                r"back_to_main|"
                r"back_to_categories|"
                r"back_to_brands|"
                r"back_to_models|"
                r"back_to_products|"
                r"category_\d+|"
                r"brand_\d+|"
                r"model_\d+|"
                r"products_page_\d+|"
                r"product_image_\d+_\d+|"
                r"product_\d+|"
                r"my_orders|"
                r"order_status_\d+"
                r")$"
            ),
        )
    )