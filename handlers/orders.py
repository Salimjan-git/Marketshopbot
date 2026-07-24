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
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS
from database import (
    get_order_details,
    get_or_create_user,
    get_user_orders,
    save_order_receipt,
)
from keyboards.menu import main_menu_keyboard


WAITING_RECEIPT = 1


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


def payment_method_text(method: str | None) -> str:
    methods = {
        "cash": "💵 Нақдӣ",
        "card": "💳 Бо корт",
    }
    return methods.get(method or "", method or "—")


def payment_status_text(status: str | None) -> str:
    statuses = {
        "unpaid": "❌ Пардохт нашудааст",
        "pending_receipt": "🧾 Чек интизор аст",
        "receipt_sent": "⏳ Чек барои санҷиш фиристода шуд",
        "confirmed": "✅ Пардохт тасдиқ шуд",
        "rejected": "❌ Чек рад карда шуд",
    }
    return statuses.get(status or "", status or "—")


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


def order_detail_keyboard(order: dict) -> InlineKeyboardMarkup:
    order_id = int(order["id"])
    status = order["status"]
    payment_method = order.get("payment_method")
    payment_status = order.get("payment_status")

    keyboard: list[list[InlineKeyboardButton]] = []

    if (
        payment_method == "card"
        and payment_status in {
            "pending_receipt",
            "rejected",
        }
        and status != "cancelled"
    ):
        keyboard.append([
            InlineKeyboardButton(
                "🧾 Фиристодани чек",
                callback_data=f"send_receipt_{order_id}",
            )
        ])

    if status in {"pending", "confirmed"}:
        keyboard.append([
            InlineKeyboardButton(
                "❌ Бекор кардани фармоиш",
                callback_data=f"cancel_order_{order_id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Ба фармоишҳо",
            callback_data="my_orders",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def build_order_text(order: dict) -> str:
    lines = [
        f"📦 Фармоиш №{order['id']}",
        "",
        f"📅 Сана: {order['created_at']}",
        f"📋 Статус: {status_text(order['status'])}",
        f"💳 Тарзи пардохт: "
        f"{payment_method_text(order.get('payment_method'))}",
        f"🧾 Ҳолати пардохт: "
        f"{payment_status_text(order.get('payment_status'))}",
        f"📞 Телефон: {order.get('phone') or '—'}",
        f"🏠 Суроға: {order.get('address') or '—'}",
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
        order_id = int(query.data.removeprefix("order_status_"))
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
        order_detail_keyboard(order),
    )


# =========================================================
# RECEIPT
# =========================================================

async def receipt_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()

    try:
        order_id = int(query.data.removeprefix("send_receipt_"))
    except (TypeError, ValueError):
        await query.answer("❌ ID нодуруст аст.", show_alert=True)
        return ConversationHandler.END

    user_id = get_database_user_id(update, context)
    order = get_order_details(order_id)

    if (
        not order
        or not user_id
        or int(order["user_id"]) != int(user_id)
    ):
        await query.answer(
            "❌ Фармоиш ёфт нашуд.",
            show_alert=True,
        )
        return ConversationHandler.END

    if order.get("payment_method") != "card":
        await query.answer(
            "❌ Барои ин фармоиш чек лозим нест.",
            show_alert=True,
        )
        return ConversationHandler.END

    context.user_data["receipt_order_id"] = order_id

    await edit_or_send(
        query,
        (
            f"🧾 Чеки пардохти фармоиши №{order_id}-ро "
            "ҳамчун сурат фиристед.\n\n"
            "Бекор кардан: /cancel"
        ),
    )
    return WAITING_RECEIPT


async def receipt_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    if not update.message or not update.message.photo:
        return WAITING_RECEIPT

    order_id = context.user_data.get("receipt_order_id")

    if not order_id:
        await update.message.reply_text(
            "❌ Маълумоти фармоиш ёфт нашуд."
        )
        return ConversationHandler.END

    user_id = get_database_user_id(update, context)
    order = get_order_details(int(order_id))

    if (
        not order
        or not user_id
        or int(order["user_id"]) != int(user_id)
    ):
        await update.message.reply_text("❌ Фармоиш ёфт нашуд.")
        return ConversationHandler.END

    receipt_file_id = update.message.photo[-1].file_id

    success = save_order_receipt(
        order_id=int(order_id),
        receipt_file_id=receipt_file_id,
    )

    if not success:
        await update.message.reply_text(
            "❌ Чек сабт нашуд. Боз кӯшиш кунед."
        )
        return WAITING_RECEIPT

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Тасдиқ",
                callback_data=f"admin_payment_approve_{order_id}",
            ),
            InlineKeyboardButton(
                "❌ Рад",
                callback_data=f"admin_payment_reject_{order_id}",
            ),
        ]
    ])

    admin_caption = (
        f"🧾 Чеки нави пардохт\n\n"
        f"📦 Фармоиш №{order_id}\n"
        f"👤 {order.get('full_name') or 'Номаълум'}\n"
        f"📞 {order.get('phone') or '—'}\n"
        f"💰 {float(order['total_price']):.2f} сомонӣ"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=receipt_file_id,
                caption=admin_caption,
                reply_markup=admin_keyboard,
            )
        except Exception:
            pass

    context.user_data.pop("receipt_order_id", None)

    await update.message.reply_text(
        (
            "✅ Чек қабул шуд ва барои санҷиш ба админ "
            "фиристода шуд."
        ),
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def receipt_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data.pop("receipt_order_id", None)

    if update.message:
        await update.message.reply_text(
            "❌ Фиристодани чек бекор карда шуд.",
            reply_markup=main_menu_keyboard(),
        )

    return ConversationHandler.END


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
    receipt_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                receipt_start,
                pattern=r"^send_receipt_\d+$",
            )
        ],
        states={
            WAITING_RECEIPT: [
                MessageHandler(
                    filters.PHOTO,
                    receipt_photo,
                )
            ]
        },
        fallbacks=[
            MessageHandler(
                filters.Regex(r"^/cancel$"),
                receipt_cancel,
            )
        ],
        allow_reentry=True,
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 Мои заказы$"),
            show_orders,
        ),
        group=-1,
    )

    app.add_handler(receipt_conversation, group=-1)

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
            back_to_main,
            pattern=r"^orders_back_to_main$",
        ),
        group=-1,
    )