"""Start handler - welcome and menu."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.services.database import create_user, get_user


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username, user.first_name)

    db_user = get_user(user.id)
    coins = db_user.get("coins", 0) if db_user else 0
    diamonds = db_user.get("diamonds", 0) if db_user else 0

    keyboard = [
        [InlineKeyboardButton("🎨 Gerar Imagem", callback_data="menu_img")],
        [InlineKeyboardButton("🎬 Gerar Vídeo", callback_data="menu_video")],
        [InlineKeyboardButton("💰 Comprar Pack", callback_data="menu_buy")],
        [InlineKeyboardButton("📊 Meu Saldo", callback_data="menu_balance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"👋 Bem-vindo ao *Bilion Luxure*!\n\n"
        f"💎 {diamonds} diamantes | 🪙 {coins} coins\n\n"
        f"Escolha uma opção:"
    )

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_img":
        await query.edit_message_text(
            "🎨 *Gerar Imagem*\n\n"
            "Mande o comando:\n`/img <descrição>`\n\n"
            "Exemplo: `/img uma garota loira sorrindo na praia`\n\n"
            "💡 Custo: 🪙 2 coins por imagem",
            parse_mode="Markdown",
        )

    elif data == "menu_video":
        await query.edit_message_text(
            "🎬 *Gerar Vídeo*\n\n"
            "Mande o comando:\n`/video <descrição>`\n\n"
            "Exemplo: `/video uma garota dançando na chuva`\n\n"
            "💡 Custo:\n• 4 segundos: 💎 1 diamante\n• 8 segundos: 💎 2 diamantes",
            parse_mode="Markdown",
        )

    elif data == "menu_buy":
        keyboard = [
            [InlineKeyboardButton("⚡ Básico — R$15 (150 coins)", callback_data="buy_basico")],
            [InlineKeyboardButton("💎 Premium — R$30 (300 coins + 5 💎)", callback_data="buy_premium")],
            [InlineKeyboardButton("👑 Ultra — R$60 (700 coins + 10 💎)", callback_data="buy_ultra")],
            [InlineKeyboardButton("◀️ Voltar", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💰 *Escolha um Pack:*\n\nTodos pagam via PIX automático.",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif data == "menu_balance":
        db_user = get_user(query.from_user.id)
        coins = db_user.get("coins", 0) if db_user else 0
        diamonds = db_user.get("diamonds", 0) if db_user else 0
        plan = db_user.get("plan", "free") if db_user else "free"

        await query.edit_message_text(
            f"📊 *Seu Saldo*\n\n"
            f"🪙 Coins: {coins}\n"
            f"💎 Diamantes: {diamonds}\n"
            f"📦 Plano: {plan}",
            parse_mode="Markdown",
        )

    elif data == "menu_back":
        db_user = get_user(query.from_user.id)
        coins = db_user.get("coins", 0) if db_user else 0
        diamonds = db_user.get("diamonds", 0) if db_user else 0

        keyboard = [
            [InlineKeyboardButton("🎨 Gerar Imagem", callback_data="menu_img")],
            [InlineKeyboardButton("🎬 Gerar Vídeo", callback_data="menu_video")],
            [InlineKeyboardButton("💰 Comprar Pack", callback_data="menu_buy")],
            [InlineKeyboardButton("📊 Meu Saldo", callback_data="menu_balance")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"👋 *Bilion Luxure*\n\n"
            f"💎 {diamonds} diamantes | 🪙 {coins} coins\n\n"
            f"Escolha uma opção:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
