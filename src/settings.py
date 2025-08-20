import logging
import os


DOWNLOADS_BASE_DIR = os.path.join(os.getcwd(), "data")

RAW_DIR = os.path.join(DOWNLOADS_BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(DOWNLOADS_BASE_DIR, "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

LOG_FORMAT = "[%(asctime)s] [%(name)s] - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
