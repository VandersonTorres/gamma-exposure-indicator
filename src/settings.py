import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()  # Loads env vars from .env file if it exists

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)

DOWNLOADS_BASE_DIR = os.path.join(os.getcwd(), "data")
PROJECT_BASE_DIR = os.path.join(os.getcwd(), "src")

RAW_DIR = os.path.join(DOWNLOADS_BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(DOWNLOADS_BASE_DIR, "processed")
REPORTS_DIR = os.path.join(DOWNLOADS_BASE_DIR, "reports")
TEMP_DIR = os.path.join(DOWNLOADS_BASE_DIR, "temp_files")
WEBHOOK_BASE_DIR = os.path.join(PROJECT_BASE_DIR, "webhook_files")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(WEBHOOK_BASE_DIR, exist_ok=True)

WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
TELEGRAM_TOKEN = os.getenv("GEX_INDICATOR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS_FILE = os.path.join(WEBHOOK_BASE_DIR, "chat_ids.txt")
