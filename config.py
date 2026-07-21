import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in environment variables")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

# Admin Configuration
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
if ADMIN_TELEGRAM_ID:
    ADMIN_TELEGRAM_ID = int(ADMIN_TELEGRAM_ID)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

# Bot Configuration
BOT_USERNAME = "auto_otclick_bot"
LOG_FILE = "bot.log"
