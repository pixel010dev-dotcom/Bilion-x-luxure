"""Video generation handler - usa coins, integrado com RunPod Wan 2.1 + fallback Replicate."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_user, spend_coins, save_generation
from src.services.runpod_service import generate_video_with_fallback
from src.services.mercadopago_service import COST_PER_VIDEO_4S, COST_PER_VIDEO_8S


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)

    if not context.args:
        await update.message.reply_text(
            "🎬 *Uso:* `/video <duração> <descrição>`\n\n"
            "Exemplo:\n"
            f"`/video 4s uma garota dançando na chuva` (🪙 {COST_PER_VIDEO_4S} coins)\n"
            f"`/video 8s uma garota dançando na chuva` (🪙 {COST_PER_VIDEO_8S} coins)\n\n"
            "💡 Duração: `4s` ou `8s`",
            parse_mode="Markdown",
        )
        return

    args = context.args
    duration = args[0].lower()

    if duration not in ("4s", "8s"):
        await update.message.reply_text(
            "❌ Usa `4s` ou `8s` pro tempo.\n"
            "Exemplo: `/video 4s uma garota dançando`",
            parse_mode="Markdown",
        )
        return

    prompt = " ".join(args[1:])
    if not prompt:
        await update.message.reply_text(
            "❌ Escreve a descrição depois do tempo.\n"
            "Exemplo: `/video 4s uma garota dançando`",
            parse_mode="Markdown",
        )
        return

    cost = COST_PER_VIDEO_4S if duration == "4s" else COST_PER_VIDEO_8S

    # Verifica saldo
    if not db_user or db_user.get("coins", 0) < cost:
        await update.message.reply_text(
            f"❌ Saldo insuficiente!\n\n"
            f"🪙 Tu tens: {db_user.get('coins', 0) if db_user else 0} coins\n"
            f"🪙 Necessário: {cost} coins\n\n"
            f"Usa /comprar pra adicionar coins."
        )
        return

    # Debita coins
    if not spend_coins(user_id, cost):
        await update.message.reply_text("❌ Erro ao debitar coins. Tenta novamente.")
        return

    # Mensagem de progresso
    dur_label = "4 segundos" if duration == "4s" else "8 segundos"
    msg = await update.message.reply_text(
        f"🎬 Gerando vídeo de {dur_label}... ⏳\n"
        f"(pode levar até 2 minutos)"
    )

    # Gera vídeo (RunPod → fallback Replicate)
    result = generate_video_with_fallback(prompt, duration)

    if result.get("success"):
        url = result["url"]
        save_generation(user_id, "video", f"{duration}: {prompt}", cost, url)

        db_user = get_user(user_id)
        coins = db_user.get("coins", 0)
        fallback_tag = " ⚠️ fallback" if result.get("fallback") else ""

        await msg.delete()
        await update.message.reply_video(
            video=url,
            caption=(
                f"🎬 Vídeo gerado!{fallback_tag}\n\n"
                f"🪙 Saldo: {coins} coins\n"
                f"📝 {prompt[:100]}"
            ),
        )
    else:
        # Reembolsa em caso de erro
        from src.services.database import add_coins
        add_coins(user_id, cost)
        await msg.edit_text(f"❌ Erro ao gerar vídeo: {result.get('error', 'Desconhecido')}")
