"""Image generation handler - custo 1 coin."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_user, spend_coins, save_generation
from src.services.replicate_service import generate_image
from src.services.mercadopago_service import COST_PER_IMAGE


async def img_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)

    if not db_user or db_user.get("coins", 0) < COST_PER_IMAGE:
        await update.message.reply_text(
            f"❌ Saldo insuficiente!\n\n"
            f"🪙 Tu tens: {db_user.get('coins', 0) if db_user else 0} coins\n"
            f"🪙 Necessário: {COST_PER_IMAGE} coin\n\n"
            f"Usa /comprar pra adicionar coins."
        )
        return

    prompt = " ".join(context.args) if context.args else None

    if not prompt:
        await update.message.reply_text(
            "🎨 *Uso:* `/img <descrição>`\n\n"
            "Exemplo: `/img uma garota loira sorrindo na praia`",
            parse_mode="Markdown",
        )
        return

    # Debita coins
    if not spend_coins(user_id, COST_PER_IMAGE):
        await update.message.reply_text("❌ Erro ao debitar coins. Tenta novamente.")
        return

    # Mensagem de "gerando"
    msg = await update.message.reply_text("🎨 Gerando imagem... ⏳")

    # Gera
    result = generate_image(prompt)

    if result.get("success"):
        url = result["url"]
        save_generation(user_id, "image", prompt, COST_PER_IMAGE, url)

        # Saldo atualizado
        db_user = get_user(user_id)
        coins = db_user.get("coins", 0)

        await msg.delete()
        await update.message.reply_photo(
            photo=url,
            caption=(
                f"🎨 Imagem gerada!\n\n"
                f"🪙 Saldo: {coins} coins\n"
                f"📝 Prompt: {prompt[:100]}"
            ),
        )
    else:
        # Reembolsa
        from src.services.database import add_coins
        add_coins(user_id, COST_PER_IMAGE)
        await msg.edit_text(f"❌ Erro ao gerar imagem: {result.get('error', 'Desconhecido')}")
