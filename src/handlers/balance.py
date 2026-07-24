"""Balance handler."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_user


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)

    if not db_user:
        await update.message.reply_text("❌ Tu não tem conta. Manda /start primeiro.")
        return

    coins = db_user.get("coins", 0)
    diamonds = db_user.get("diamonds", 0)
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
        f"💎 Diamantes: {diamonds}\n"
        f"📦 Plano: {plan_names.get(plan, plan)}\n\n"
        f"*Custos:*\n"
        f"• Imagem: 🪙 2 coins\n"
        f"• Vídeo 4s: 💎 1 diamante\n"
        f"• Vídeo 8s: 💎 2 diamantes",
        parse_mode="Markdown",
    )
