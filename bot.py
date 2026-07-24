"""Bilion Luxure Bot - Main entry point."""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.services.database import init_db
from src.handlers.start import start_handler, menu_callback, accept_tos_callback, handle_text_message
from src.handlers.payment import buy_callback, check_payment_callback
from src.handlers.finance import financial_handler


def main():
    init_db()
    logger.info("Database initialized")

    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN not set!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Registrar admin IDs no bot_data
    admin_ids = os.environ.get("ADMIN_IDS", "")
    if admin_ids:
        app.bot_data["admin_ids"] = admin_ids

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("finance", financial_handler))

    # Text messages (button flow - prompts / comandos)
    app.add_handler(MessageHandler(filters.TEXT, handle_text_message))

    # Photos (com ou sem legenda)
    app.add_handler(MessageHandler(filters.PHOTO, handle_text_message))

    # Callbacks
    app.add_handler(CallbackQueryHandler(accept_tos_callback, pattern="^accept_tos$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^vid_"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_"))

    logger.info("Bilion Luxure bot started!")
    app.run_polling()


if __name__ == "__main__":
    main()
