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
)
from src.services.database import init_db
from src.handlers.start import start_handler, menu_callback
from src.handlers.img import img_handler
from src.handlers.video import video_handler
from src.handlers.payment import buy_handler, buy_callback, check_payment_callback
from src.handlers.balance import balance_handler


def main():
    init_db()
    logger.info("Database initialized")

    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN not set!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("img", img_handler))
    app.add_handler(CommandHandler("video", video_handler))
    app.add_handler(CommandHandler("comprar", buy_handler))
    app.add_handler(CommandHandler("saldo", balance_handler))

    # Callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_"))

    logger.info("Bilion Luxure bot started!")
    app.run_polling()


if __name__ == "__main__":
    main()
