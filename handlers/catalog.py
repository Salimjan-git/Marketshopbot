from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import (
    add_to_cart,
    clear_cart,
    create_order,
    get_brands_by_category,
    get_cart,
    get_models_by_category_and_brand,
    get_order_details,
    get_or_create_user,
    get_product,
    get_products_by_model,
    get_user_orders,
    remove_from_cart,
    update_cart_quantity,
    update_order_status
)
from keyboards.menu import (
    brands_keyboard,
    cart_keyboard,
    categories_keyboard,
    main_menu_keyboard,
    models_keyboard,
    order_detail_keyboard,
    product_detail_keyboard,
    products_keyboard,
)
from database import get_categories


ITEMS_PER_PAGE = 5


# =========================================================
# HELPERS
# =========================================================

def get_database_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    saved_user_id = context.user_data.get("user_id")

    if saved_user_id:
        return saved_user_id

    telegram_user = update.effective_user

    if not telegram_user:
        return None

    db_user = get_or_create_user(
        telegram_id=telegram_user.id,
        full_name=telegram_user.full_name,
        username=telegram_user.username,
    )

    context.user_data["user_id"] = db_user["id"]
    return db_user["id"]


def build_product_caption(product: dict) -> str:
    price = float(product["price"])
    discount = float(product["discount"] or 0)
    final_price = max(0, price - discount)

    condition = "Нав" if product["condition"] == "new" else "Б/у"

    return (
        f"📱 {product['title']}\n\n"
        f"🏷 Бренд: {product['brand_name']}\n"
        f"📲 Модел: {product['model_name']}\n"
        f"📂 Категория: {product['category_name']}\n"
        f"📦 Ҳолат: {condition}\n"
        f"🧠 RAM: {product.get('ram') or '—'}\n"
        f"💾 Хотира: {product.get('storage') or '—'}\n"
        f"🎨 Ранг: {product.get('color') or '—'}\n"
        f"💰 Нарх: {price:.2f} сомонӣ\n"
        f"📉 Тахфиф: {discount:.2f} сомонӣ\n"
        f"💳 Нархи ниҳоӣ: {final_price:.2f} сомонӣ\n"
        f"📦 Дар анбор: {product['stock']} дона\n"
        f"📍 Шаҳр: {product.get('city') or '—'}\n"
        f"🛡 Кафолат: {product.get('warranty') or '—'}\n"
        f"🔋 Battery health: {product.get('battery_health') or '—'}\n"
        f"📶 SIM: {product.get('sim_type') or '—'}\n\n"
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
            await query.delete_message()
            await query.message.chat.send_message(
                text=text,
                reply_markup=reply_markup,
            )
        else:
            await query.edit_message_text(
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
# BRANDS
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


# =========================================================
# MODELS
# =========================================================

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
            await query.delete_message()
            await query.message.chat.send_photo(
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
# CART
# =========================================================

def build_cart_text(cart: list) -> str:
    lines = ["🛒 Корзинаи шумо:\n"]
    total_price = 0.0

    for item in cart:
        item_total = float(item["total"])
        total_price += item_total

        lines.append(
            f"• {item['name']}\n"
            f"  {item['quantity']} дона × "
            f"{float(item['final_price']):.2f} сомонӣ = "
            f"{item_total:.2f} сомонӣ\n"
        )

    lines.append(f"💰 Ҳамагӣ: {total_price:.2f} сомонӣ")
    return "\n".join(lines)


async def show_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message:
        return

    user_id = get_database_user_id(update, context)

    if not user_id:
        await update.message.reply_text(
            "❌ Корбар ёфт нашуд. /start-ро пахш кунед."
        )
        return

    cart = get_cart(user_id)

    if not cart:
        await update.message.reply_text(
            "🛒 Корзинаи шумо холӣ аст.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        build_cart_text(cart),
        reply_markup=cart_keyboard(cart),
    )


async def show_cart_callback(query, user_id: int | None) -> None:
    if not user_id:
        await edit_or_send_text(
            query,
            "❌ Корбар ёфт нашуд. /start-ро пахш кунед.",
        )
        return

    cart = get_cart(user_id)

    if not cart:
        await edit_or_send_text(
            query,
            "🛒 Корзинаи шумо холӣ аст.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛍 Ба каталог",
                        callback_data="back_to_categories",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Менюи асосӣ",
                        callback_data="back_to_main",
                    )
                ],
            ]),
        )
        return

    await edit_or_send_text(
        query,
        build_cart_text(cart),
        cart_keyboard(cart),
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

    lines = ["📦 Фармоишҳои шумо:\n"]

    for order in orders:
        lines.append(
            f"№{order['id']} | "
            f"{float(order['total_price']):.2f} сомонӣ | "
            f"{order['status']}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(),
    )


async def show_orders_callback(query, user_id: int | None) -> None:
    orders = get_user_orders(user_id) if user_id else []

    if not orders:
        await edit_or_send_text(
            query,
            "📦 Шумо ҳоло ягон фармоиш надоред.",
        )
        return

    keyboard = []

    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"Фармоиш №{order['id']}",
                callback_data=f"order_status_{order['id']}",
            )
        ])

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
            await show_brands_callback(query, category_id)
        else:
            await show_categories_callback(query)
        return

    if data == "back_to_models":
        category_id = context.user_data.get("last_category_id")
        brand_id = context.user_data.get("last_brand_id")

        if category_id and brand_id:
            await show_models_callback(query, category_id, brand_id)
        else:
            await show_categories_callback(query)
        return

    if data == "back_to_products":
        products = context.user_data.get("products_list", [])
        page = context.user_data.get("last_page", 0)

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
            category_id=category_id,
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

    if data.startswith("add_to_cart_"):
        try:
            product_id = int(data.removeprefix("add_to_cart_"))
        except ValueError:
            return

        if not user_id:
            await query.answer("Корбар ёфт нашуд.", show_alert=True)
            return

        success = add_to_cart(user_id, product_id, 1)

        await query.answer(
            "✅ Ба корзина илова шуд!"
            if success
            else "❌ Дар анбор миқдори кофӣ нест.",
            show_alert=True,
        )
        return

    if data == "show_cart":
        await show_cart_callback(query, user_id)
        return

    if data.startswith("cart_item_"):
        try:
            product_id = int(data.removeprefix("cart_item_"))
        except ValueError:
            return

        cart = get_cart(user_id) if user_id else []
        item = next(
            (
                row
                for row in cart
                if row["product_id"] == product_id
            ),
            None,
        )

        if not item:
            await edit_or_send_text(query, "Товар дар корзина нест.")
            return

        await edit_or_send_text(
            query,
            (
                f"📦 {item['name']}\n\n"
                f"Миқдор: {item['quantity']}\n"
                f"Маблағ: {float(item['total']):.2f} сомонӣ"
            ),
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕",
                        callback_data=f"cart_inc_{product_id}",
                    ),
                    InlineKeyboardButton(
                        "➖",
                        callback_data=f"cart_dec_{product_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🗑 Нест кардан",
                        callback_data=f"cart_remove_{product_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Ба корзина",
                        callback_data="show_cart",
                    )
                ],
            ]),
        )
        return

    if data.startswith("cart_inc_"):
        product_id = int(data.removeprefix("cart_inc_"))
        cart = get_cart(user_id) if user_id else []
        item = next(
            (row for row in cart if row["product_id"] == product_id),
            None,
        )

        if item:
            update_cart_quantity(
                user_id,
                product_id,
                item["quantity"] + 1,
            )

        await show_cart_callback(query, user_id)
        return

    if data.startswith("cart_dec_"):
        product_id = int(data.removeprefix("cart_dec_"))
        cart = get_cart(user_id) if user_id else []
        item = next(
            (row for row in cart if row["product_id"] == product_id),
            None,
        )

        if item:
            if item["quantity"] > 1:
                update_cart_quantity(
                    user_id,
                    product_id,
                    item["quantity"] - 1,
                )
            else:
                remove_from_cart(user_id, product_id)

        await show_cart_callback(query, user_id)
        return

    if data.startswith("cart_remove_"):
        product_id = int(data.removeprefix("cart_remove_"))

        if user_id:
            remove_from_cart(user_id, product_id)

        await show_cart_callback(query, user_id)
        return

    if data == "clear_cart":
        if user_id:
            clear_cart(user_id)

        await show_cart_callback(query, user_id)
        return

    if data == "checkout":
        cart = get_cart(user_id) if user_id else []

        if not cart:
            await edit_or_send_text(query, "🛒 Корзина холӣ аст.")
            return

        context.user_data["awaiting_order_data"] = True

        await edit_or_send_text(
            query,
            (
                "Адрес ва телефонро дар як паём фиристед.\n\n"
                "Мисол:\n"
                "Душанбе, Рӯдакӣ 10 | +992900001122"
            ),
        )
        return

    if data == "my_orders":
        await show_orders_callback(query, user_id)
        return
    if data.startswith("cancel_order_"):
        try:
            order_id = int(
                data.removeprefix("cancel_order_")
            )
        except ValueError:
            await query.answer(
                "ID-и заказ нодуруст аст.",
                show_alert=True,
            )
            return

        if not user_id:
            await query.answer(
                "Корбар ёфт нашуд.",
                show_alert=True,
            )
            return

        order = get_order_details(order_id)

        if not order:
            await query.answer(
                "Заказ ёфт нашуд.",
                show_alert=True,
            )
            return

        # Корбар танҳо закази худашро бекор карда метавонад
        if order["user_id"] != user_id:
            await query.answer(
                "Шумо ин заказро бекор карда наметавонед.",
                show_alert=True,
            )
            return

        if order["status"] == "cancelled":
            await query.answer(
                "Ин заказ аллакай бекор шудааст.",
                show_alert=True,
            )
            return

        if order["status"] == "delivered":
            await query.answer(
                "Закази расонидашударо бекор кардан мумкин нест.",
                show_alert=True,
            )
            return

        success = update_order_status(
            order_id=order_id,
            status="cancelled",
        )

        if not success:
            await query.answer(
                "Заказ бекор карда нашуд.",
                show_alert=True,
            )
            return

        await query.edit_message_text(
            text=(
                f"❌ Закази №{order_id} бекор карда шуд.\n\n"
                "Статус: cancelled"
            ),
            reply_markup=order_detail_keyboard(
                order_id=order_id,
                status=order["status"],
            ),
        )


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
            total = float(item["price"]) * item["quantity"]
            lines.append(
                f"• {item['product_name']} × "
                f"{item['quantity']} = {total:.2f} сомонӣ"
            )

        await edit_or_send_text(
            query,
            "\n".join(lines),
            order_detail_keyboard(order_id),
        )
        return
    return


# =========================================================
# ORDER INPUT
# =========================================================

async def handle_order_data(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message or not update.message.text:
        return

    if not context.user_data.get("awaiting_order_data"):
        return

    text = update.message.text.strip()

    if "|" not in text:
        await update.message.reply_text(
            "❌ Формат нодуруст аст.\n"
            "Мисол: Душанбе, Рӯдакӣ 10 | +992900001122"
        )
        return

    address, phone = [part.strip() for part in text.split("|", 1)]

    if len(address) < 5 or len(phone) < 7:
        await update.message.reply_text(
            "❌ Адрес ё телефон нодуруст аст."
        )
        return

    user_id = get_database_user_id(update, context)

    order_id = create_order(
        user_id=user_id,
        address=address,
        phone=phone,
    )

    context.user_data["awaiting_order_data"] = False

    if not order_id:
        await update.message.reply_text(
            "❌ Фармоиш сохта нашуд.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        (
            f"✅ Фармоиши №{order_id} қабул шуд!\n"
            f"🏠 {address}\n"
            f"📞 {phone}"
        ),
        reply_markup=main_menu_keyboard(),
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
            filters.Regex(r"^🛒 Корзина$"),
            show_cart,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 Мои заказы$"),
            show_orders,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_callback,
            pattern=r"^(?!admin_).+",
        )
    )

