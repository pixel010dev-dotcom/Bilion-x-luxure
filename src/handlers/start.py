"""Start handler - ToS, menu, and message routing for button-only flow."""
import base64
import io
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.services.database import create_user, get_user, accept_tos, spend_coins, save_generation, add_coins
from src.services.mercadopago_service import COST_PER_IMAGE, COST_PER_VIDEO_4S, COST_PER_VIDEO_8S
from src.services.replicate_service import generate_image
from src.services.runpod_service import generate_video
from src.services.image_utils import download_photo_to_data_url

logger = logging.getLogger(__name__)

TOS_TEXT = (
    "📋 *Termos de Uso — Bilion Luxure*\n\n"
    "Ao usar este bot, voce concorda que:\n\n"
    "1. 🔞 Conteudo gerado *para maiores de 18 anos*.\n"
    "2. ⚖️ Voce e responsavel pelo que gera.\n"
    "3. 👤 Pagamentos via PIX *exibem nome do recebedor* (exigencia BC).\n"
    "4. 💰 Coins comprados *nao sao reembolsaveis* apos uso.\n"
    "5. 🚫 Conteudo ilegal/abusivo resultara em banimento.\n\n"
    "Clique em *Aceitar* para continuar."
)


def menu_keyboard(coins=0):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Gerar Imagem", callback_data="menu_img")],
        [InlineKeyboardButton("🎬 Gerar Video", callback_data="menu_video")],
        [InlineKeyboardButton("💰 Comprar Coins", callback_data="menu_buy")],
        [InlineKeyboardButton("📊 Meu Saldo", callback_data="menu_balance")],
    ])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username, user.first_name)

    db_user = get_user(user.id)
    coins = db_user.get("coins", 0) if db_user else 0
    tos_accepted = db_user.get("tos_accepted", False) if db_user else False

    if not tos_accepted:
        keyboard = [[InlineKeyboardButton("✅ Aceitar Termos", callback_data="accept_tos")]]
        await update.message.reply_text(
            TOS_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"👋 *Bilion Luxure*\n\n🪙 {coins} coins\n\nEscolha uma opcao:",
        reply_markup=menu_keyboard(coins),
        parse_mode="Markdown",
    )


async def accept_tos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    accept_tos(user_id)

    db_user = get_user(user_id)
    coins = db_user.get("coins", 0) if db_user else 0

    await query.edit_message_text(
        f"✅ *Termos aceitos!*\n\n👋 *Bilion Luxure*\n\n🪙 {coins} coins\n\nEscolha uma opcao:",
        reply_markup=menu_keyboard(coins),
        parse_mode="Markdown",
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_img":
        context.user_data["state"] = "awaiting_img_prompt"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Cancelar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "🎨 *Gerar Imagem*\n\n"
            "Custo: 🪙 1 coin\n\n"
            "Mande o *contexto/historia* que quer gerar.\n"
            "Se quiser uma *foto de referencia*, envia ela junto com o texto.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif data == "menu_video":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("4s — 🪙 15 coins", callback_data="vid_4s")],
            [InlineKeyboardButton("8s — 🪙 30 coins", callback_data="vid_8s")],
            [InlineKeyboardButton("◀️ Voltar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "🎬 *Gerar Video*\n\nEscolha a duracao:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif data == "menu_buy":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Basico — R$15 (150 coins)", callback_data="buy_basico")],
            [InlineKeyboardButton("💎 Premium — R$30 (350 coins)", callback_data="buy_premium")],
            [InlineKeyboardButton("👑 Ultra — R$60 (800 coins)", callback_data="buy_ultra")],
            [InlineKeyboardButton("◀️ Voltar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "💰 *Escolha um Pack:*\n\n✅ Pagamento via PIX automatico.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif data == "menu_balance":
        db_user = get_user(query.from_user.id)
        coins = db_user.get("coins", 0) if db_user else 0
        plan = db_user.get("plan", "free") if db_user else "free"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Voltar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            f"📊 *Seu Saldo*\n\n"
            f"🪙 Coins: {coins}\n"
            f"📦 Plano: {plan}\n\n"
            f"*Custos:*\n"
            f"• Imagem: 🪙 {COST_PER_IMAGE} coin\n"
            f"• Video 4s: 🪙 {COST_PER_VIDEO_4S} coins\n"
            f"• Video 8s: 🪙 {COST_PER_VIDEO_8S} coins",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif data == "menu_back":
        context.user_data.pop("state", None)
        db_user = get_user(query.from_user.id)
        coins = db_user.get("coins", 0) if db_user else 0
        try:
            await query.edit_message_text(
                f"👋 *Bilion Luxure*\n\n🪙 {coins} coins\n\nEscolha uma opcao:",
                reply_markup=menu_keyboard(coins),
                parse_mode="Markdown",
            )
        except Exception:
            # Se for foto/video (nao da pra editar), deleta e manda nova
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"👋 *Bilion Luxure*\n\n🪙 {coins} coins\n\nEscolha uma opcao:",
                reply_markup=menu_keyboard(coins),
                parse_mode="Markdown",
            )

    elif data == "vid_4s":
        context.user_data["video_duration"] = "4s"
        context.user_data["state"] = "awaiting_video_prompt"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Cancelar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "🎬 *Gerar Video (4s)*\n\n"
            "Custo: 🪙 15 coins\n\n"
            "Mande o *contexto/historia* do video:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif data == "vid_8s":
        context.user_data["video_duration"] = "8s"
        context.user_data["state"] = "awaiting_video_prompt"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Cancelar", callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "🎬 *Gerar Video (8s)*\n\n"
            "Custo: 🪙 30 coins\n\n"
            "Mande o *contexto/historia* do video:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteia mensagens de texto baseado no estado do usuario."""
    user_id = update.effective_user.id
    state = context.user_data.get("state")
    text = update.message.text or ""

    # Se tem foto anexada, processa junto
    has_photo = bool(update.message.photo)
    if has_photo:
        await handle_photo_message(update, context)
        return

    if state == "awaiting_img_prompt":
        context.user_data.pop("state", None)
        await gerar_imagem(update, context, user_id, text)

    elif state == "awaiting_video_prompt":
        context.user_data.pop("state", None)
        duration = context.user_data.pop("video_duration", "4s")
        await gerar_video(update, context, user_id, text, duration)

    elif text.startswith("/img "):
        prompt = text[5:].strip()
        if prompt:
            await gerar_imagem(update, context, user_id, prompt)
        else:
            await update.message.reply_text("Manda: /img <contexto> ou usa o menu 😉")

    elif text.startswith("/video "):
        resto = text[7:].strip()
        dur = "4s"
        if resto.startswith("8s") or resto.startswith("8 "):
            dur = "8s"
            resto = resto[2:].strip() if resto.startswith("8s") else resto[3:].strip()
        elif resto.startswith("4s") or resto.startswith("4 "):
            resto = resto[2:].strip() if resto.startswith("4s") else resto[3:].strip()
        if resto:
            await gerar_video(update, context, user_id, resto, dur)
        else:
            await update.message.reply_text("Manda: /video 4s <contexto> ou usa o menu 😉")

    else:
        db_user = get_user(user_id)
        coins = db_user.get("coins", 0) if db_user else 0
        await update.message.reply_text(
            f"👋 *Bilion Luxure*\n\n🪙 {coins} coins\n\nEscolha uma opcao:",
            reply_markup=menu_keyboard(coins),
            parse_mode="Markdown",
        )


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa foto enviada com ou sem legenda."""
    user_id = update.effective_user.id
    state = context.user_data.get("state")
    caption = update.message.caption or ""

    photo = update.message.photo[-1]  # maior resolucao
    file = await photo.get_file()

    try:
        img_data_url = await download_photo_to_data_url(file)
    except Exception as e:
        logger.error(f"Erro ao baixar foto: {e}")
        await update.message.reply_text("❌ Nao consegui baixar sua foto. Tenta de novo.")
        return

    if state == "awaiting_img_prompt":
        context.user_data.pop("state", None)
        if caption.strip():
            await gerar_imagem(update, context, user_id, caption, image_url=img_data_url)
        else:
            # Foto sem legenda — pergunta o contexto
            context.user_data["state"] = "awaiting_img_prompt"
            context.user_data["pending_image_url"] = img_data_url
            await update.message.reply_text(
                "📸 Foto recebida! Agora manda o *contexto/historia* pra gerar junto:",
                parse_mode="Markdown",
            )
    else:
        # Foto fora de estado — mostra opcoes
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Usar como referencia", callback_data="menu_img")],
            [InlineKeyboardButton("◀️ Voltar", callback_data="menu_back")],
        ])
        await update.message.reply_text(
            "📸 Quer usar essa foto como referencia? Clica ai:",
            reply_markup=keyboard,
        )


async def gerar_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                       prompt: str, image_url: str = None):
    # Se tem imagem pendente do estado anterior, usa
    if not image_url:
        image_url = context.user_data.pop("pending_image_url", None)

    db_user = get_user(user_id)
    if not db_user or db_user.get("coins", 0) < COST_PER_IMAGE:
        await update.message.reply_text(
            f"❌ Saldo insuficiente!\n\n"
            f"🪙 Tens: {db_user.get('coins', 0) if db_user else 0} coins\n"
            f"🪙 Necessario: {COST_PER_IMAGE} coin\n\n"
            f"💰 Compra coins no menu!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Comprar Coins", callback_data="menu_buy")],
                [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_back")],
            ]),
        )
        return

    if not spend_coins(user_id, COST_PER_IMAGE):
        await update.message.reply_text("❌ Erro ao debitar coins. Tenta de novo.")
        return

    msg = await update.message.reply_text("🎨 Gerando imagem... ⏳")

    try:
        result = generate_image(prompt, image_url=image_url)
    except Exception as e:
        await msg.edit_text(f"❌ Erro: {e}")
        add_coins(user_id, COST_PER_IMAGE)
        return

    if result.get("success"):
        url = result["url"]
        save_generation(user_id, "image", prompt, COST_PER_IMAGE, url)
        db_user = get_user(user_id)
        coins = db_user.get("coins", 0)

        ref_text = " (com foto de referencia)" if image_url else ""
        await msg.delete()
        await update.message.reply_photo(
            photo=url,
            caption=(
                f"🎨 Imagem gerada{ref_text}!\n"
                f"🪙 Saldo: {coins} coins\n"
                f"📝 {prompt[:100]}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_back")],
            ]),
        )
    else:
        error_msg = result.get("error", "Erro desconhecido")
        if "credit" in error_msg.lower() or "402" in error_msg:
            error_msg = "API sem creditos. O dono precisa recarregar em replicate.com/account/billing"
        add_coins(user_id, COST_PER_IMAGE)
        await msg.edit_text(f"❌ {error_msg}")


async def gerar_video(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                      prompt: str, duration: str):
    cost = COST_PER_VIDEO_4S if duration == "4s" else COST_PER_VIDEO_8S

    db_user = get_user(user_id)
    if not db_user or db_user.get("coins", 0) < cost:
        await update.message.reply_text(
            f"❌ Saldo insuficiente!\n\n"
            f"🪙 Tens: {db_user.get('coins', 0) if db_user else 0} coins\n"
            f"🪙 Necessario: {cost} coins\n\n"
            f"💰 Compra coins no menu!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Comprar Coins", callback_data="menu_buy")],
                [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_back")],
            ]),
        )
        return

    if not spend_coins(user_id, cost):
        await update.message.reply_text("❌ Erro ao debitar coins. Tenta de novo.")
        return

    msg = await update.message.reply_text("🎬 Gerando video... ⏳ (ate 5 min)")

    try:
        result = generate_video(prompt, duration)
    except Exception as e:
        await msg.edit_text(f"❌ Erro: {e}")
        add_coins(user_id, cost)
        return

    if result.get("success"):
        url = result["url"]
        save_generation(user_id, "video", prompt, cost, url)
        db_user = get_user(user_id)
        coins = db_user.get("coins", 0)

        await msg.delete()
        await update.message.reply_video(
            video=url,
            caption=f"🎬 Video gerado!\n🪙 Saldo: {coins} coins",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_back")],
            ]),
        )
    else:
        error_msg = result.get("error", "Erro desconhecido")
        if "credit" in error_msg.lower() or "402" in error_msg:
            error_msg = "API sem creditos. O dono precisa configurar em replicate.com"
        if "configurado" in error_msg.lower():
            error_msg = "Geracao de video nao configurada ainda."
        add_coins(user_id, cost)
        await msg.edit_text(f"❌ {error_msg}")
