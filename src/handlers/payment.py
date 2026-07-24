"""Payment handler - PIX via MercadoPago com tracking financeiro."""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.services.database import create_user, create_payment, update_payment_status, get_user
from src.services.mercadopago_service import create_pix_payment, check_payment, PLANS, get_plan_cost_percentage

logger = logging.getLogger(__name__)


async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    create_user(user_id, update.effective_user.username, update.effective_user.first_name)

    keyboard = [
        [InlineKeyboardButton("⚡ Básico — R$15 (150 coins)", callback_data="buy_basico")],
        [InlineKeyboardButton("💎 Premium — R$30 (350 coins)", callback_data="buy_premium")],
        [InlineKeyboardButton("👑 Ultra — R$60 (800 coins)", callback_data="buy_ultra")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💰 *Escolha um Pack:*\n\n"
        "⚡ *Básico* — R$15\n"
        "🪙 150 coins\n\n"
        "💎 *Premium* — R$30\n"
        "🪙 350 coins\n\n"
        "👑 *Ultra* — R$60\n"
        "🪙 800 coins\n\n"
        "✅ Pagamento via PIX. Os coins caem na hora!",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan = query.data.replace("buy_", "")
    plan_data = PLANS.get(plan)

    if not plan_data:
        await query.edit_message_text("❌ Plano inválido.")
        return

    user_id = query.from_user.id
    await query.edit_message_text("⏳ Gerando PIX...")

    result = create_pix_payment(user_id, plan)

    if result.get("success"):
        import base64
        qr_b64 = result.get("qr_code", "")
        gross = result["amount_gross"]
        net = result["amount_net"]
        coins = plan_data["coins"]

        # Salva pagamento com tracking financeiro
        create_payment(user_id, gross, net, result["payment_id"], plan, coins)

        keyboard = [
            [InlineKeyboardButton("✅ Paguei", callback_data=f"check_{result['payment_id']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        plan_cost_pct = get_plan_cost_percentage(plan)

        if qr_b64:
            try:
                qr_bytes = base64.b64decode(qr_b64)
                pix_code = result.get("qr_code_text", "")
                caption = (
                    f"💰 *PIX gerado!*\n\n"
                    f"📦 Plano: {plan_data['label']}\n"
                    f"🪙 {coins} coins\n"
                    f"💵 Valor: R${gross:.2f}\n\n"
                )
                if pix_code:
                    caption += (
                        f"📋 *Código PIX* (copia e cola):\n"
                        f"`{pix_code}`\n\n"
                    )
                caption += (
                    f"Escaneia o QR ou copia o código acima.\n"
                    f"Clica em *'Paguei'* quando pagar.\n\n"
                    f"⏱ Expira em 30 minutos."
                )
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=qr_bytes,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
                return
            except Exception as e:
                logger.error(f"QR send error: {e}")

        # Fallback: link
        await query.edit_message_text(
            f"💰 *PIX gerado!*\n\n"
            f"📦 Plano: {plan_data['label']}\n"
            f"🪙 {coins} coins\n"
            f"💵 Valor: R${gross:.2f}\n\n"
            f"[Clique aqui pra ver o PIX]({result.get('qr_code_link', '')})\n\n"
            f"Clica em *'Paguei'* quando pagar.",
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    else:
        await query.edit_message_text(f"❌ Erro ao gerar PIX: {result.get('error', 'Desconhecido')}")


async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Verificando pagamento...")

    payment_id = query.data.replace("check_", "")
    status = check_payment(payment_id)

    if status == "approved":
        update_payment_status(payment_id, "approved")
        db_user = get_user(query.from_user.id)
        coins = db_user.get("coins", 0) if db_user else 0

        await query.message.delete()
        keyboard = [[InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_back")]]
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=(
                f"✅ *Pagamento confirmado!*\n\n"
                f"🪙 Saldo: {coins} coins\n\n"
                f"Pronto! Usa /img ou /video pra gerar conteúdo."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    elif status == "pending":
        await query.answer("⏳ Ainda não confirmou. Espera um pouco e clica de novo.", show_alert=True)
    else:
        await query.answer("❌ Pagamento não encontrado ou expirado.", show_alert=True)


# List of handlers to register
payment_handlers = [
    (lambda: buy_handler, "comprar"),
    (buy_callback, "buy_"),
    (check_payment_callback, "check_"),
]
