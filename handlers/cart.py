from telegram import (
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
    get_cart,
    get_or_create_user,
    get_product,
    remove_from_cart,
    update_cart_quantity,
)
from keyboards.menu import cart_keyboard


def get_database_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    saved_user_id = context.user_data.get("user_id")

    if saved_user_id:
        return int(saved_user_id)

    telegram_user = update.effective_user

    if not telegram_user:
        return None

    db_user = get_or_create_user(
        telegram_id=telegram_user.id,
        full_name=telegram_user.full_name,
        username=telegram_user.username,
    )

    context.user_data["user_id"] = int(db_user["id"])
    return int(db_user["id"])


def build_cart_text(items: list[dict]) -> str:
    lines = ["🛒 Корзинаи шумо:\n"]
    total = 0.0

    for item in items:
        item_total = float(item["total"])
        total += item_total

        lines.append(
            f"📦 {item['name']}\n"
            f"{item['quantity']} × "
            f"{float(item['final_price']):.2f} = "
            f"{item_total:.2f} сомонӣ\n"
        )

    lines.append(f"💰 Ҳамагӣ: {total:.2f} сомонӣ")
    return "\n".join(lines)


async def render_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user_id = get_database_user_id(update, context)
    items = get_cart(user_id) if user_id else []

    if items:
        text = build_cart_text(items)
        keyboard = cart_keyboard(items)
    else:
        text = "🛒 Корзинаи шумо холӣ аст."
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛍 Ба каталог",
                    callback_data="back_to_categories",
                )
            ]
        ])

    if update.callback_query:
        query = update.callback_query

        try:
            if query.message.photo:
                await query.delete_message()
                await query.message.chat.send_message(
                    text,
                    reply_markup=keyboard,
                )
            else:
                await query.edit_message_text(
                    text,
                    reply_markup=keyboard,
                )
        except Exception:
            await query.message.chat.send_message(
                text,
                reply_markup=keyboard,
            )

    elif update.message:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
        )


async def show_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await render_cart(update, context)


async def add_product_to_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(
        query.data.removeprefix("add_to_cart_")
    )
    user_id = get_database_user_id(update, context)
    product = get_product(product_id)

    if not user_id or not product:
        await query.answer(
            "❌ Корбар ё маҳсулот ёфт нашуд.",
            show_alert=True,
        )
        return

    if int(product["stock"]) <= 0:
        await query.answer(
            "❌ Маҳсулот дастрас нест.",
            show_alert=True,
        )
        return

    success = add_to_cart(
        user_id=user_id,
        product_id=product_id,
        quantity=1,
    )

    await query.answer(
        "✅ Ба корзина илова шуд!"
        if success
        else "❌ Миқдори кофӣ нест.",
        show_alert=True,
    )


async def show_cart_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)
    product_id = int(
        query.data.removeprefix("cart_item_")
    )
    items = get_cart(user_id)

    item = next(
        (
            row
            for row in items
            if int(row["product_id"]) == product_id
        ),
        None,
    )

    if not item:
        await render_cart(update, context)
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➖",
                callback_data=f"cart_dec_{product_id}",
            ),
            InlineKeyboardButton(
                f"{item['quantity']} дона",
                callback_data="cart_noop",
            ),
            InlineKeyboardButton(
                "➕",
                callback_data=f"cart_inc_{product_id}",
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
    ])

    await query.edit_message_text(
        (
            f"📦 {item['name']}\n\n"
            f"Миқдор: {item['quantity']}\n"
            f"Ҳамагӣ: {float(item['total']):.2f} сомонӣ"
        ),
        reply_markup=keyboard,
    )


async def increase_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)
    product_id = int(
        query.data.removeprefix("cart_inc_")
    )
    items = get_cart(user_id)
    product = get_product(product_id)

    item = next(
        (
            row
            for row in items
            if int(row["product_id"]) == product_id
        ),
        None,
    )

    if item and product:
        new_quantity = int(item["quantity"]) + 1

        if new_quantity > int(product["stock"]):
            await query.answer(
                "❌ Миқдори кофӣ нест.",
                show_alert=True,
            )
            return

        update_cart_quantity(
            user_id,
            product_id,
            new_quantity,
        )

    await render_cart(update, context)


async def decrease_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)
    product_id = int(
        query.data.removeprefix("cart_dec_")
    )
    items = get_cart(user_id)

    item = next(
        (
            row
            for row in items
            if int(row["product_id"]) == product_id
        ),
        None,
    )

    if item:
        if int(item["quantity"]) <= 1:
            remove_from_cart(user_id, product_id)
        else:
            update_cart_quantity(
                user_id,
                product_id,
                int(item["quantity"]) - 1,
            )

    await render_cart(update, context)


async def remove_product(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)
    product_id = int(
        query.data.removeprefix("cart_remove_")
    )

    remove_from_cart(user_id, product_id)
    await render_cart(update, context)


async def clear_user_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)
    clear_cart(user_id)

    await render_cart(update, context)


async def checkout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)

    if not user_id or not get_cart(user_id):
        await query.answer(
            "🛒 Корзина холӣ аст.",
            show_alert=True,
        )
        return

    order_id = create_order(user_id=user_id)

    if not order_id:
        await query.answer(
            "❌ Фармоиш сохта нашуд.",
            show_alert=True,
        )
        return

    await query.edit_message_text(
        (
            f"✅ Фармоиши №{order_id} қабул шуд!\n\n"
            "Барои дидани он «📦 Мои заказы»-ро пахш кунед."
        ),
        reply_markup=InlineKeyboardMarkup([
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
        ]),
    )


async def noop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await update.callback_query.answer()


def register_handlers(app: Application) -> None:
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^🛒 Корзина$"),
            show_cart,
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            add_product_to_cart,
            pattern=r"^add_to_cart_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            show_cart,
            pattern=r"^show_cart$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            show_cart_item,
            pattern=r"^cart_item_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            increase_quantity,
            pattern=r"^cart_inc_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            decrease_quantity,
            pattern=r"^cart_dec_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            remove_product,
            pattern=r"^cart_remove_\d+$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            clear_user_cart,
            pattern=r"^clear_cart$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            checkout,
            pattern=r"^checkout$",
        ),
        group=-1,
    )
    app.add_handler(
        CallbackQueryHandler(
            noop,
            pattern=r"^cart_noop$",
        ),
        group=-1,
    )
    