import os
import logging
from typing_extensions import Buffer
import requests

from telegram import Bot
from jmespath import search as jsearch

from src.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS_FILE

logger = logging.getLogger(__name__)


class IntegrateTelegramBot:
    def __init__(self, telegram_bot_token: str = "") -> None:
        """Initialize the Telegram bot integration.

        Args:
            telegram_bot_token (str, optional): Telegram bot token.
                If not provided, it will be loaded from TELEGRAM_TOKEN in settings.

        Raises:
            ValueError: If no Telegram bot token is provided.
        """
        if not telegram_bot_token:
            telegram_bot_token = TELEGRAM_TOKEN
        self.telegram_bot_token = telegram_bot_token

        if not self.telegram_bot_token:
            raise ValueError("Missing Telegram Bot Token")

    async def _send_telegram_message(self, message: str, chat_id: str) -> None:
        """Send a text message to a specific Telegram chat.

        Args:
            message (str): The message text to send.
            chat_id (str): The target chat ID.
        """
        bot = Bot(token=self.telegram_bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    async def _send_photo(self, binary_file: Buffer, chat_id: str) -> None:
        """Send a photo to a specific Telegram chat.

        Args:
            binary_file (Buffer): Binary file buffer representing the photo.
            chat_id (str): The target chat ID.
        """
        bot = Bot(token=self.telegram_bot_token)
        await bot.send_photo(chat_id=chat_id, photo=binary_file)

    @staticmethod
    def load_chat_ids():
        """Load Telegram chat IDs from a local file.

        Returns:
            set[str]: A set of chat IDs loaded from the file.
        """
        if not os.path.exists(TELEGRAM_CHAT_IDS_FILE):
            logger.warning(f"File {TELEGRAM_CHAT_IDS_FILE} not found. Creating...")
            with open(TELEGRAM_CHAT_IDS_FILE, "w") as f:
                f.write("")

            return set()
        with open(TELEGRAM_CHAT_IDS_FILE, "r") as file:
            return set(line.strip() for line in file)

    def get_telegram_chat_ids(self):
        """Retrieve chat IDs by querying Telegram updates or falling back to local storage.

        Returns:
            set[str]: A set of unique Telegram chat IDs.
        """
        response = requests.get(url=f"https://api.telegram.org/bot{self.telegram_bot_token}/getUpdates")
        if response.status_code == 200:
            data = response.json()
            if data["ok"]:
                chat_ids = set()
                for result in data.get("result", []):
                    chat_id = jsearch("message.chat.id", result)
                    if chat_id:
                        chat_ids.add(chat_id)
                return chat_ids
        elif chat_ids := self.load_chat_ids():
            return chat_ids

        logger.error(f"Failed to get chat_ids: {response.text}")
        return set()

    async def send_all(self, message: str):
        """Send a message to all known chat IDs.

        Args:
            message (str): The message text to send to all chats.
        """
        for chat_id in self.get_telegram_chat_ids():
            await self._send_telegram_message(message=message, chat_id=chat_id)
