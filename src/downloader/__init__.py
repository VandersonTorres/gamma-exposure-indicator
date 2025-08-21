import logging
import time

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Page


class BaseDownloader:

    def __init__(self) -> None:
        # Set logger
        self.logger = logging.getLogger(self.__class__.__name__)

    def _sleep_between_actions(self, seconds: int = 2) -> None:
        """
        Apply a delay between actions to avoid being detected.

        Args:
            seconds (int): Number of seconds to sleep.
        """
        time.sleep(seconds)

    def resolve_cookies_popup(self, page: Page, resolve_cookies_selector: str) -> None:
        """
        Check for the initial cookies popup and resolve it.

        Args:
            page (Page): The Playwright page object.
            resolve_cookies_selector (str): The selector for the cookies acceptance or close button.
        """
        try:
            page.locator(resolve_cookies_selector)
            page.click(resolve_cookies_selector)
            self.logger.info(f"Cookies resolved for {page.url}.")
        except TimeoutError:
            self.logger.warning(f"No cookies found for {page.url}. Continuing...")

        self._sleep_between_actions()

    def start_navigation(self, url: str, headless: bool = True) -> object:
        """
        Context manager to start a Playwright Page.
        Args:
            url (str): URL to be started.
            headless (bool): Do not show the browser.
        Returns:
            object: Playwright context.
        """

        class PageContext:
            def __enter__(inner_self):
                self._pw = sync_playwright().start()
                self._browser = self._pw.chromium.launch(headless=headless)
                self._context = self._browser.new_context()
                self._page = self._context.new_page()
                self._page.goto(url, wait_until="load")
                return self._page

            def __exit__(inner_self, exc_type, exc_val, exc_tb):
                self.logger.warning("Closing playwright context.")
                self._browser.close()
                self._pw.stop()

        return PageContext()
