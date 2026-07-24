from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest, Forbidden
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
    add_to_cart,
    clear_cart,
    create_order,
    get_cart,
    get_or_create_user,
    get_order_details,
    get_payment_bank,
    get_payment_banks,
    get_payment_method,
    get_payment_methods,
    get_product,
    remove_from_cart,
    save_order_receipt,
    update_cart_quantity,
)
from keyboards.admin import payment_receipt_actions_keyboard
from keyboards.menu import (
    cart_keyboard,
    cash_order_created_keyboard,
    checkout_payment_keyboard,
    main_menu_keyboard,
    online_order_created_keyboard,
    payment_banks_keyboard,
    payment_methods_keyboard,
)


(
    CHECKOUT_ADDRESS,
    CHECKOUT_PHONE,
    CHECKOUT_PAYMENT,
    CHECKOUT_BANK,
    CHECKOUT_METHOD,
    RECEIPT_PHOTO,
) = range(6)


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


def build_cart_text(items: list[dict]) -> str:
    lines = ["🛒 Корзинаи шумо:\n"]
    total = 0.0

    for item in items:
        item_total = float(item["total"])
        total += item_total
        lines.append(
            f"📦 {item['name']}\n"
            f"{int(item['quantity'])} × "
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
    items = get_cart(user_id) if user_id is not None else []

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

    query = update.callback_query

    if query and query.message:
        try:
            if query.message.photo:
                chat_id = query.message.chat_id
                await query.delete_message()
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                )
                context.user_data["cart_message_id"] = sent_message.message_id
            else:
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                )
                context.user_data["cart_message_id"] = query.message.message_id
        except Exception:
            sent_message = await query.message.chat.send_message(
                text=text,
                reply_markup=keyboard,
            )
            context.user_data["cart_message_id"] = sent_message.message_id
        return

    if update.message:
        chat_id = update.message.chat_id
        old_message_id = context.user_data.get("cart_message_id")

        if old_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=int(old_message_id),
                )
            except Exception:
                pass

        sent_message = await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
        )
        context.user_data["cart_message_id"] = sent_message.message_id


async def show_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user_id = get_database_user_id(update, context)

    if not user_id:
        if update.message:
            await update.message.reply_text(
                "❌ Корбар ёфт нашуд. /start-ро пахш кунед."
            )
        return

    if update.callback_query:
        await update.callback_query.answer()
        await render_cart(update, context)
        return

    if not update.message:
        return

    cart = get_cart(user_id)
    if not cart:
        sent_message = await update.message.reply_text(
            "🛒 Корзинаи шумо холӣ аст.",
            reply_markup=main_menu_keyboard(),
        )
        context.user_data["cart_message_id"] = sent_message.message_id
        return

    sent_message = await update.message.reply_text(
        build_cart_text(cart),
        reply_markup=cart_keyboard(cart),
    )
    context.user_data["cart_message_id"] = sent_message.message_id


async def add_product_to_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        product_id = int(query.data.removeprefix("add_to_cart_"))
    except ValueError:
        await query.answer("❌ ID-и маҳсулот нодуруст аст.", show_alert=True)
        return

    user_id = get_database_user_id(update, context)
    product = get_product(product_id)

    if user_id is None or not product:
        await query.answer("❌ Маҳсулот ё корбар ёфт нашуд.", show_alert=True)
        return

    success = add_to_cart(user_id, product_id, 1)
    await query.answer(
        "✅ Ба корзина илова шуд!" if success else "❌ Илова нашуд.",
        show_alert=True,
    )


async def show_cart_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    user_id = get_database_user_id(update, context)

    try:
        product_id = int(query.data.removeprefix("cart_item_"))
    except ValueError:
        return

    items = get_cart(user_id) if user_id is not None else []
    item = next(
        (row for row in items if int(row["product_id"]) == product_id),
        None,
    )

    if not item:
        await render_cart(update, context)
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data=f"cart_dec_{product_id}"),
            InlineKeyboardButton(
                f"{int(item['quantity'])} дона",
                callback_data="cart_noop",
            ),
            InlineKeyboardButton("➕", callback_data=f"cart_inc_{product_id}"),
        ],
        [
            InlineKeyboardButton(
                "🗑 Нест кардан",
                callback_data=f"cart_remove_{product_id}",
            )
        ],
        [
            InlineKeyboardButton("🔙 Ба корзина", callback_data="show_cart")
        ],
    ])

    text = (
        f"📦 {item['name']}\n\n"
        f"Миқдор: {int(item['quantity'])}\n"
        f"Ҳамагӣ: {float(item['total']):.2f} сомонӣ"
    )

    try:
        await query.edit_message_text(text=text, reply_markup=keyboard)
    except BadRequest:
        await query.message.reply_text(text=text, reply_markup=keyboard)


async def increase_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    user_id = get_database_user_id(update, context)
    try:
        product_id = int(query.data.removeprefix("cart_inc_"))
    except ValueError:
        return

    items = get_cart(user_id) if user_id is not None else []
    item = next(
        (row for row in items if int(row["product_id"]) == product_id),
        None,
    )

    if not item or user_id is None:
        await query.answer("❌ Маҳсулот ёфт нашуд.", show_alert=True)
        return

    update_cart_quantity(
        user_id,
        product_id,
        int(item["quantity"]) + 1,
    )
    await query.answer("✅ Миқдор зиёд шуд.")
    await render_cart(update, context)


async def decrease_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    user_id = get_database_user_id(update, context)
    try:
        product_id = int(query.data.removeprefix("cart_dec_"))
    except ValueError:
        return

    if user_id is not None:
        items = get_cart(user_id)
        item = next(
            (row for row in items if int(row["product_id"]) == product_id),
            None,
        )
        if item:
            quantity = int(item["quantity"])
            if quantity <= 1:
                remove_from_cart(user_id, product_id)
            else:
                update_cart_quantity(user_id, product_id, quantity - 1)

    await query.answer()
    await render_cart(update, context)


async def remove_product(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    user_id = get_database_user_id(update, context)
    try:
        product_id = int(query.data.removeprefix("cart_remove_"))
    except ValueError:
        return

    if user_id is not None:
        remove_from_cart(user_id, product_id)

    await query.answer()
    await render_cart(update, context)


async def clear_user_cart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query:
        return

    user_id = get_database_user_id(update, context)
    if user_id is not None:
        clear_cart(user_id)

    await query.answer()
    await render_cart(update, context)


# =========================================================
# CHECKOUT
# =========================================================

async def checkout_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    user_id = get_database_user_id(update, context)
    if user_id is None or not get_cart(user_id):
        await query.answer("🛒 Корзина холӣ аст.", show_alert=True)
        return ConversationHandler.END

    context.user_data["checkout"] = {}
    await query.answer()
    await query.edit_message_text(
        "🏠 Суроғаи расониданро нависед.\n\n"
        "Мисол: Душанбе, кӯчаи Рӯдакӣ 10\n"
        "Бекор кардан: /cancel"
    )
    return CHECKOUT_ADDRESS


async def checkout_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    address = (update.message.text or "").strip()

    if len(address) < 5:
        await update.message.reply_text("❌ Суроға хеле кӯтоҳ аст.")
        return CHECKOUT_ADDRESS

    context.user_data.setdefault("checkout", {})["address"] = address
    await update.message.reply_text(
        "📞 Рақами телефонро нависед.\n"
        "Мисол: +992928302409"
    )
    return CHECKOUT_PHONE


async def checkout_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    phone = (update.message.text or "").strip()
    clean_phone = (
        phone.replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if not clean_phone.isdigit() or len(clean_phone) < 9:
        await update.message.reply_text("❌ Рақами телефон нодуруст аст.")
        return CHECKOUT_PHONE

    context.user_data.setdefault("checkout", {})["phone"] = phone
    await update.message.reply_text(
        "💳 Тарзи пардохтро интихоб кунед:",
        reply_markup=checkout_payment_keyboard(),
    )
    return CHECKOUT_PAYMENT


async def checkout_payment_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    method = query.data.removeprefix("checkout_payment_")
    checkout = context.user_data.setdefault("checkout", {})

    if method == "cash":
        await query.answer()
        return await create_cash_order(update, context)

    if method != "online":
        await query.answer("❌ Тарзи пардохт нодуруст аст.", show_alert=True)
        return CHECKOUT_PAYMENT

    banks = get_payment_banks(active_only=True)
    banks = [bank for bank in banks if int(bank.get("methods_count") or 0) > 0]

    if not banks:
        await query.answer(
            "❌ Ҳоло ягон бонки фаъол вуҷуд надорад.",
            show_alert=True,
        )
        return CHECKOUT_PAYMENT

    checkout["payment_method"] = "online"
    await query.answer()
    await query.edit_message_text(
        "🏦 Бонкро интихоб кунед:",
        reply_markup=payment_banks_keyboard(banks),
    )
    return CHECKOUT_BANK


async def checkout_bank_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    try:
        bank_id = int(query.data.removeprefix("checkout_bank_"))
    except ValueError:
        await query.answer("❌ Бонк нодуруст аст.", show_alert=True)
        return CHECKOUT_BANK

    bank = get_payment_bank(bank_id)
    methods = get_payment_methods(bank_id, active_only=True)

    if not bank or not int(bank.get("is_active") or 0):
        await query.answer("❌ Ин бонк ғайрифаъол аст.", show_alert=True)
        return CHECKOUT_BANK

    if not methods:
        await query.answer("❌ Барои ин бонк усули пардохт нест.", show_alert=True)
        return CHECKOUT_BANK

    checkout = context.user_data.setdefault("checkout", {})
    checkout["payment_bank_id"] = bank_id

    await query.answer()
    await query.edit_message_text(
        f"🏦 {bank['name']}\n\nУсули пардохтро интихоб кунед:",
        reply_markup=payment_methods_keyboard(methods),
    )
    return CHECKOUT_METHOD


async def checkout_method_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    try:
        method_id = int(query.data.removeprefix("checkout_method_"))
    except ValueError:
        await query.answer("❌ Усул нодуруст аст.", show_alert=True)
        return CHECKOUT_METHOD

    checkout = context.user_data.get("checkout", {})
    bank_id = checkout.get("payment_bank_id")
    method = get_payment_method(method_id)

    if (
        not method
        or not bank_id
        or int(method["bank_id"]) != int(bank_id)
        or not int(method.get("is_active") or 0)
        or not int(method.get("bank_is_active") or 0)
    ):
        await query.answer(
            "❌ Ин усули пардохт дастрас нест.",
            show_alert=True,
        )
        return CHECKOUT_METHOD

    checkout["payment_method_id"] = method_id
    await query.answer()

    order_id = _create_checkout_order(
        update=update,
        context=context,
        payment_method="online",
        payment_bank_id=int(bank_id),
        payment_method_id=method_id,
    )

    if not order_id:
        await query.edit_message_text(
            "❌ Фармоиш сохта нашуд. Корзина ё маълумотро санҷед."
        )
        return ConversationHandler.END

    context.user_data.pop("checkout", None)
    await _send_online_payment_details(
        update=update,
        context=context,
        order_id=order_id,
        method=method,
    )
    return ConversationHandler.END


def _create_checkout_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payment_method: str,
    payment_bank_id: int | None = None,
    payment_method_id: int | None = None,
) -> int | None:
    user_id = get_database_user_id(update, context)
    checkout = context.user_data.get("checkout", {})

    if user_id is None:
        return None

    address = str(checkout.get("address") or "").strip()
    phone = str(checkout.get("phone") or "").strip()

    if not address or not phone:
        return None

    return create_order(
        user_id=user_id,
        address=address,
        phone=phone,
        payment_method=payment_method,
        payment_bank_id=payment_bank_id,
        payment_method_id=payment_method_id,
    )


async def create_cash_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    order_id = _create_checkout_order(
        update=update,
        context=context,
        payment_method="cash",
    )

    if not order_id:
        await query.edit_message_text(
            "❌ Фармоиш сохта нашуд. Маълумотро санҷед."
        )
        return ConversationHandler.END

    context.user_data.pop("checkout", None)
    await query.edit_message_text(
        f"✅ Фармоиши №{order_id} қабул шуд!\n\n"
        "💵 Пардохт ҳангоми гирифтани маҳсулот.",
        reply_markup=cash_order_created_keyboard(),
    )
    return ConversationHandler.END


async def _send_online_payment_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    order_id: int,
    method: dict,
) -> None:
    query = update.callback_query
    method_type = method["method_type"]

    labels = {
        "card": "💳 Рақами корт",
        "phone": "📱 Рақами телефон",
        "qr": "🔳 QR-код",
    }

    text = (
        f"✅ Фармоиши №{order_id} қабул шуд!\n\n"
        f"🏦 Бонк: {method['bank_name']}\n"
        f"👤 Қабулкунанда: {method.get('card_holder') or '—'}\n"
        f"💰 Усул: {method['title']}\n"
    )

    if method_type in {"card", "phone"}:
        text += f"{labels[method_type]}: {method.get('value') or '—'}\n"

    text += (
        "\nПас аз пардохт тугмаи «🧾 Чекро фиристодан»-ро "
        "пахш карда, сурати чекро фиристед."
    )

    keyboard = online_order_created_keyboard(order_id)

    if method_type == "qr" and method.get("qr_file_id"):
        try:
            await query.delete_message()
        except Exception:
            pass
        await query.message.chat.send_photo(
            photo=method["qr_file_id"],
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await query.edit_message_text(text=text, reply_markup=keyboard)


async def checkout_back_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 Тарзи пардохтро интихоб кунед:",
        reply_markup=checkout_payment_keyboard(),
    )
    return CHECKOUT_PAYMENT


async def checkout_back_banks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    banks = get_payment_banks(active_only=True)
    banks = [bank for bank in banks if int(bank.get("methods_count") or 0) > 0]
    await query.answer()
    await query.edit_message_text(
        "🏦 Бонкро интихоб кунед:",
        reply_markup=payment_banks_keyboard(banks),
    )
    return CHECKOUT_BANK


async def checkout_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data.pop("checkout", None)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Оформкунии фармоиш бекор карда шуд."
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Оформкунии фармоиш бекор карда шуд.",
            reply_markup=main_menu_keyboard(),
        )

    return ConversationHandler.END


# =========================================================
# RECEIPT UPLOAD
# =========================================================

async def receipt_upload_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    try:
        order_id = int(query.data.removeprefix("upload_receipt_"))
    except ValueError:
        await query.answer("❌ Фармоиш нодуруст аст.", show_alert=True)
        return ConversationHandler.END

    user_id = get_database_user_id(update, context)
    order = get_order_details(order_id)

    if (
        not order
        or user_id is None
        or int(order.get("user_id") or 0) != user_id
        or order.get("payment_method") != "online"
        or order.get("status") == "cancelled"
    ):
        await query.answer(
            "❌ Барои ин фармоиш чек фиристода намешавад.",
            show_alert=True,
        )
        return ConversationHandler.END

    context.user_data["receipt_order_id"] = order_id
    await query.answer()
    await query.message.reply_text(
        f"🧾 Сурати чеки фармоиши №{order_id}-ро фиристед.\n\n"
        "Бекор кардан: /cancel"
    )
    return RECEIPT_PHOTO


async def receipt_photo_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    order_id = context.user_data.get("receipt_order_id")

    if not order_id or not update.message or not update.message.photo:
        await update.message.reply_text("❌ Лутфан чекро ҳамчун сурат фиристед.")
        return RECEIPT_PHOTO

    user_id = get_database_user_id(update, context)
    order = get_order_details(int(order_id))

    if (
        not order
        or user_id is None
        or int(order.get("user_id") or 0) != user_id
    ):
        context.user_data.pop("receipt_order_id", None)
        await update.message.reply_text("❌ Фармоиш ёфт нашуд.")
        return ConversationHandler.END

    file_id = update.message.photo[-1].file_id

    if not save_order_receipt(int(order_id), file_id):
        await update.message.reply_text("❌ Чек нигоҳ дошта нашуд.")
        return RECEIPT_PHOTO

    context.user_data.pop("receipt_order_id", None)
    updated_order = get_order_details(int(order_id))

    await update.message.reply_text(
        f"✅ Чеки фармоиши №{order_id} қабул шуд.\n"
        "Администратор онро санҷида, ба шумо хабар медиҳад.",
        reply_markup=main_menu_keyboard(),
    )

    if updated_order:
        await _forward_receipt_to_admins(
            context=context,
            order=updated_order,
            receipt_file_id=file_id,
        )

    return ConversationHandler.END


async def _forward_receipt_to_admins(
    context: ContextTypes.DEFAULT_TYPE,
    order: dict,
    receipt_file_id: str,
) -> None:
    username = order.get("username")
    username_text = f"@{username}" if username else "—"
    method_type_labels = {
        "card": "Корт",
        "phone": "Телефон",
        "qr": "QR",
    }

    caption = (
        f"🧾 Чеки нави фармоиши #{order['id']}\n\n"
        f"👤 Муштарӣ: {order.get('full_name') or 'Номаълум'}\n"
        f"🔗 Username: {username_text}\n"
        f"🆔 Telegram ID: {order.get('telegram_id') or '—'}\n"
        f"📞 Телефон: {order.get('phone') or '—'}\n"
        f"🏠 Суроға: {order.get('address') or '—'}\n"
        f"🏦 Бонк: {order.get('payment_bank_name') or '—'}\n"
        f"💳 Усул: "
        f"{method_type_labels.get(order.get('payment_method_type'), '—')} — "
        f"{order.get('payment_method_title') or '—'}\n"
        f"💰 Ҳамагӣ: {float(order['total_price']):.2f} сомонӣ"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=receipt_file_id,
                caption=caption,
                reply_markup=payment_receipt_actions_keyboard(
                    int(order["id"])
                ),
            )
        except (BadRequest, Forbidden):
            continue
        except Exception:
            continue


async def receipt_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data.pop("receipt_order_id", None)
    await update.message.reply_text(
        "❌ Фиристодани чек бекор карда шуд.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def noop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.callback_query:
        await update.callback_query.answer()


def register_handlers(app: Application) -> None:
    checkout_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(checkout_start, pattern=r"^checkout$")
        ],
        states={
            CHECKOUT_ADDRESS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    checkout_address,
                )
            ],
            CHECKOUT_PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    checkout_phone,
                )
            ],
            CHECKOUT_PAYMENT: [
                CallbackQueryHandler(
                    checkout_payment_selected,
                    pattern=r"^checkout_payment_(cash|online)$",
                ),
                CallbackQueryHandler(
                    checkout_back_payment,
                    pattern=r"^checkout_back_payment$",
                ),
            ],
            CHECKOUT_BANK: [
                CallbackQueryHandler(
                    checkout_bank_selected,
                    pattern=r"^checkout_bank_\d+$",
                ),
                CallbackQueryHandler(
                    checkout_back_payment,
                    pattern=r"^checkout_back_payment$",
                ),
            ],
            CHECKOUT_METHOD: [
                CallbackQueryHandler(
                    checkout_method_selected,
                    pattern=r"^checkout_method_\d+$",
                ),
                CallbackQueryHandler(
                    checkout_back_banks,
                    pattern=r"^checkout_back_banks$",
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", checkout_cancel),
            CallbackQueryHandler(
                checkout_cancel,
                pattern=r"^checkout_cancel$",
            ),
        ],
        allow_reentry=True,
    )

    receipt_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                receipt_upload_start,
                pattern=r"^upload_receipt_\d+$",
            )
        ],
        states={
            RECEIPT_PHOTO: [
                MessageHandler(filters.PHOTO, receipt_photo_input)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", receipt_cancel)
        ],
        allow_reentry=True,
    )

    app.add_handler(
        MessageHandler(filters.Regex(r"^🛒 Корзина$"), show_cart),
        group=-1,
    )
    app.add_handler(checkout_conversation, group=-1)
    app.add_handler(receipt_conversation, group=-1)

    handlers = [
        (r"^add_to_cart_\d+$", add_product_to_cart),
        (r"^show_cart$", show_cart),
        (r"^cart_item_\d+$", show_cart_item),
        (r"^cart_inc_\d+$", increase_quantity),
        (r"^cart_dec_\d+$", decrease_quantity),
        (r"^cart_remove_\d+$", remove_product),
        (r"^clear_cart$", clear_user_cart),
        (r"^cart_noop$", noop),
    ]

    for pattern, callback in handlers:
        app.add_handler(
            CallbackQueryHandler(callback, pattern=pattern),
            group=-1,
        )