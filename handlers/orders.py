from __future__ import annotations

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
    get_order_details,
    get_or_create_user,
    get_user_orders,
    update_order_status,
)
from keyboards.menu import (
    main_menu_keyboard,
    order_detail_keyboard,
)


# =========================================================
# HELPERS
# =========================================================

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

    if not db_user:
        return None

    context.user_data["user_id"] = int(db_user["id"])
    return int(db_user["id"])


def status_text(status: str) -> str:
    statuses = {
        "pending": "⏳ Дар интизорӣ",
        "confirmed": "✅ Тасдиқ шуд",
        "processing": "⚙️ Дар коркард",
        "shipped": "🚚 Фиристода шуд",
        "delivered": "📬 Расонида шуд",
        "cancelled": "❌ Бекор карда шуд",
    }

    return statuses.get(status, status)


def orders_keyboard(orders: list[dict]) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []

    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                (
                    f"Фармоиш №{order['id']} — "
                    f"{float(order['total_price']):.2f} сомонӣ — "
                    f"{status_text(order['status'])}"
                ),
                callback_data=f"order_status_{order['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Менюи асосӣ",
            callback_data="orders_back_to_main",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def build_order_text(order: dict) -> str:
    lines = [
        f"📦 Фармоиш №{order['id']}",
        "",
        f"📅 Сана: {order['created_at']}",
        f"📋 Статус: {status_text(order['status'])}",
        f"💰 Ҳамагӣ: {float(order['total_price']):.2f} сомонӣ",
        "",
        "🛍 Маҳсулот:",
    ]

    for item in order.get("items", []):
        quantity = int(item["quantity"])
        price = float(item["price"])
        total = price * quantity

        product_name = (
            item.get("product_name")
            or item.get("name")
            or "Маҳсулот"
        )

        lines.append(
            f"• {product_name}\n"
            f"  {quantity} × {price:.2f} = {total:.2f} сомонӣ"
        )

    return "\n".join(lines)


async def edit_or_send(
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
# SHOW ORDERS
# =========================================================

async def show_orders(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message:
        return

    user_id = get_database_user_id(update, context)

    if not user_id:
        await update.message.reply_text(
            "❌ Корбар ёфт нашуд. /start-ро пахш кунед.",
            reply_markup=main_menu_keyboard(),
        )
        return

    orders = get_user_orders(user_id)

    if not orders:
        await update.message.reply_text(
            "📦 Шумо ҳоло ягон фармоиш надоред.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        "📦 Фармоишҳои шумо:",
        reply_markup=orders_keyboard(orders),
    )


async def show_orders_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = get_database_user_id(update, context)

    if not user_id:
        await query.answer(
            "❌ Корбар ёфт нашуд.",
            show_alert=True,
        )
        return

    orders = get_user_orders(user_id)

    if not orders:
        await edit_or_send(
            query,
            "📦 Шумо ҳоло ягон фармоиш надоред.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Менюи асосӣ",
                        callback_data="orders_back_to_main",
                    )
                ]
            ]),
        )
        return

    await edit_or_send(
        query,
        "📦 Фармоишҳои шумо:",
        orders_keyboard(orders),
    )


# =========================================================
# ORDER DETAILS
# =========================================================

async def show_order_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    try:
        order_id = int(
            query.data.removeprefix("order_status_")
        )
    except (TypeError, ValueError):
        await query.answer(
            "❌ ID-и фармоиш нодуруст аст.",
            show_alert=True,
        )
        return

    user_id = get_database_user_id(update, context)
    order = get_order_details(order_id)

    if not order:
        await query.answer(
            "❌ Фармоиш ёфт нашуд.",
            show_alert=True,
        )
        return

    if not user_id or int(order["user_id"]) != int(user_id):
        await query.answer(
            "❌ Ин фармоиш ба шумо тааллуқ надорад.",
            show_alert=True,
        )
        return

    await edit_or_send(
        query,
        build_order_text(order),
        order_detail_keyboard(
            order_id=order_id,
            status=order["status"],
        ),
    )


# =========================================================
# CANCEL ORDER
# =========================================================

async def cancel_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    try:
        order_id = int(
            query.data.removeprefix("cancel_order_")
        )
    except (TypeError, ValueError):
        await query.answer(
            "❌ ID-и фармоиш нодуруст аст.",
            show_alert=True,
        )
        return

    user_id = get_database_user_id(update, context)
    order = get_order_details(order_id)

    if not order:
        await query.answer(
            "❌ Фармоиш ёфт нашуд.",
            show_alert=True,
        )
        return

    if not user_id or int(order["user_id"]) != int(user_id):
        await query.answer(
            "❌ Шумо ин фармоишро бекор карда наметавонед.",
            show_alert=True,
        )
        return

    if order["status"] == "cancelled":
        await query.answer(
            "ℹ️ Фармоиш аллакай бекор шудааст.",
            show_alert=True,
        )
        return

    if order["status"] in {"shipped", "delivered"}:
        await query.answer(
            "❌ Фармоиши фиристодашуда ё расонидашударо "
            "бекор кардан мумкин нест.",
            show_alert=True,
        )
        return

    success = update_order_status(
        order_id=order_id,
        status="cancelled",
    )

    if not success:
        await query.answer(
            "❌ Фармоиш бекор карда нашуд.",
            show_alert=True,
        )
        return

    updated_order = get_order_details(order_id)

    await edit_or_send(
        query,
        (
            build_order_text(updated_order)
            if updated_order
            else f"❌ Фармоиши №{order_id} бекор карда шуд."
        ),
        order_detail_keyboard(
            order_id=order_id,
            status="cancelled",
        ),
    )


# =========================================================
# BACK TO MAIN
# =========================================================

async def back_to_main(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    await query.answer()

    try:
        await query.delete_message()
    except Exception:
        pass

    await query.message.chat.send_message(
        "🏠 Менюи асосӣ:",
        reply_markup=main_menu_keyboard(),
    )


# =========================================================
# REGISTER
# =========================================================

def register_handlers(app: Application) -> None:
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 Мои заказы$"),
            show_orders,
        ),
        group=-1,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_orders_callback,
            pattern=r"^my_orders$",
        ),
        group=-1,
    )

    app.add_handler(
        CallbackQueryHandler(
            show_order_details,
            pattern=r"^order_status_\d+$",
        ),
        group=-1,
    )

    app.add_handler(
        CallbackQueryHandler(
            cancel_order,
            pattern=r"^cancel_order_\d+$",
        ),
        group=-1,
    )

    app.add_handler(
        CallbackQueryHandler(
            back_to_main,
            pattern=r"^orders_back_to_main$",
        ),
        group=-1,
    )