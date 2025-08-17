import os


DOWNLOADS_DIR = os.path.join(os.getcwd(), "data", "raw")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
