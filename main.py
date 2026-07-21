#!/usr/bin/env python3
"""
Telegram Bot with GPT-5.5 Integration
Production-ready bot for request analysis and response generation
"""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from config import TELEGRAM_BOT_TOKEN
from database import init_db
from handlers import (
    start, help_command, prompt_command, process_prompt,
    profile_command, settings_command, test_command, button_handler,
    WAITING_FOR_PROMPT
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler for prompt workflow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("prompt", prompt_command)],
        states={
            WAITING_FOR_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_prompt)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start the Bot
    logger.info("Bot started successfully")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()
