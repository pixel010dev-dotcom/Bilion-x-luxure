"""Balance handler."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_user
from src.services.mercadopago_service import (
    COST_PER_IMAGE,
    COST_PER_VIDEO_4S,
    COST_PER_VIDEO_8S,
)


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)

    if not db_user:
        await update.message.reply_text("❌ Tu não tem conta. Manda /start primeiro.")
        return

    coins = db_user.get("coins", 0)
    plan = db_user.get("plan", "free")

    plan_names = {
        "free": "🆓 Gratuito",
        "basico": "⚡ Básico",
        "premium": "💎 Premium",
        "ultra": "👑 Ultra",
    }

    await update.message.reply_text(
        f"📊 *Seu Saldo*\n\n"
        f"🪙 Coins: {coins}\n"
        f"📦 Plano: {plan_names.get(plan, plan)}\n\n"
        f"*Custos:*\n"
        f"• Imagem: 🪙 {COST_PER_IMAGE} coin\n"
        f"• Vídeo 4s: 🪙 {COST_PER_VIDEO_4S} coins\n"
        f"• Vídeo 8s: 🪙 {COST_PER_VIDEO_8S} coins",
        parse_mode="Markdown",
    )
