"""Video generation handler - placeholder for future RunPod integration."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_user, spend_diamonds
from src.services.mercadopago_service import COST_PER_VIDEO_4S, COST_PER_VIDEO_8S


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)

    if not db_user or db_user.get("diamonds", 0) < COST_PER_VIDEO_4S:
        await update.message.reply_text(
            f"❌ Saldo insuficiente!\n\n"
            f"💎 Tu tens: {db_user.get('diamonds', 0) if db_user else 0} diamantes\n"
            f"💎 Necessário: {COST_PER_VIDEO_4S} diamante(s)\n\n"
            f"Usa /comprar pra adicionar diamantes."
        )
        return

    prompt = " ".join(context.args) if context.args else None

    if not prompt:
        await update.message.reply_text(
            "🎬 *Uso:* `/video <descrição>`\n\n"
            "Exemplo: `/video uma garota dançando na chuva`\n\n"
            "💡 Custo: 💎 1 diamante (4s) ou 💎 2 diamantes (8s)",
            parse_mode="Markdown",
        )
        return

    # TODO: Implementar com RunPod quando tiver GPU
    await update.message.reply_text(
        "🎬 *Geração de vídeo em breve!*\n\n"
        "Por enquanto, focamos em imagens.\n"
        "O sistema de vídeo será integrado quando tiver GPU.",
        parse_mode="Markdown",
    )
