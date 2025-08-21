import os
from datetime import datetime

from playwright.sync_api._generated import Page

from src.settings import RAW_DIR
from . import BaseDownloader


class CBOEDownloader(BaseDownloader):
    def select_options_from_dropdown(self, page: Page, dropdown_selector: str, option_selector: str) -> None:
        """
        Expand a dropdown and select an option

        Args:
            page (Page): The Playwright page object.
            dropdown_selector (str): The selector of the wanted dropdown
            option_selector (str): The selector of the wanted option
        """
        # Expand the dropdown
        _dropdown = page.locator(dropdown_selector)
        _dropdown.wait_for(state="visible", timeout=5000)
        _dropdown.click()

        # Select the option
        option_locator = page.locator(option_selector).first
        option_locator.wait_for(state="visible", timeout=5000)
        option_locator.click()

    def setup_expiration(self, page: Page, _type: str, _month: str) -> None:
        """
        Sets up the expiration configs.
        Args:
            page (Page): The Playwright page object.
            _type (str): Type of expiration.
            _month (str): Expiration month for current year (portuguese).
        """
        if _type.lower() != "standard":
            # Type "standard" == 0DTE
            _month = "all"

        # Sets Expiration Type
        self.select_options_from_dropdown(
            page=page,
            dropdown_selector=(
                "//div[contains(text(), 'Expiration Type:')]/following::div[contains(@class, 'Box-cui__')][1]"
            ),
            option_selector=f"div.ReactSelect__option:has-text('{_type}')",
        )
        self.logger.info(f"Expiration type '{_type}' successfully selected.")
        self._sleep_between_actions()

        # Sets expiration Month
        self.select_options_from_dropdown(
            page=page,
            dropdown_selector=(
                "//div[contains(text(), 'Expiration:')]/following::div[contains(@class, 'Box-cui__')][1]"
            ),
            option_selector=f"div.ReactSelect__option:has-text('{_month}')",
        )
        self.logger.info(f"Expiration month '{_month}' successfully selected.")
        self._sleep_between_actions()

        # Sets Options Range
        self.select_options_from_dropdown(
            page=page,
            dropdown_selector=(
                "//div[contains(text(), 'Options Range:')]/following::div[contains(@class, 'Box-cui__')][1]"
            ),
            option_selector="div.ReactSelect__option:has-text('all')",
        )
        self.logger.info("Options Range 'all' successfully selected.")
        self._sleep_between_actions()

        set_params = page.locator("//button[contains(., 'View Chain')]")
        set_params.click()
        self._sleep_between_actions()

    def get_csv_and_last_price(
        self, url: str, expiration_type: str, expiration_month: str, headless: bool = True
    ) -> tuple[str]:
        """
        Download a CSV file from CBOE web page.
        Args:
            url (url): URL to be requested
            expiration_type (str): Type of expiration. Supported values:
                - "all" (Default)
                - "standard" (0DTE)
                - "weekly"
                - "quarterly"
                - "monthly"
            expiration_month (str): Expiration month for current year (portuguese). Ex:
                "agosto"
            headless (bool): Do not show the browser.
        Returns:
            File Path (str)
        """
        with self.start_navigation(url=url, headless=headless) as page:
            self.resolve_cookies_popup(page=page, resolve_cookies_selector="#onetrust-accept-btn-handler")
            self._sleep_between_actions(seconds=3)
            last_price = page.query_selector(
                "//div[contains(., 'Last:')]/div[contains(@class, 'Box-cui_') and contains(@class, 'Text-cui__')]"
            ).text_content()

            self.setup_expiration(page=page, _type=expiration_type, _month=expiration_month)
            with page.expect_download() as download_info:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                csv_link = page.locator("//a[contains(., 'Download CSV')]")
                csv_link.wait_for(state="visible", timeout=3000)
                csv_link.click()

            download = download_info.value
            expiration_type = "0dte" if expiration_type.lower() == "standard" else expiration_type
            name, _ = os.path.splitext(download.suggested_filename)
            filename = f"{name}_{expiration_type}"
            filename = f"{filename}_{expiration_month}" if expiration_month.lower() != "all" else filename
            file_path = os.path.join(RAW_DIR, f"cboe_{filename}_{datetime.now().strftime('%d-%m-%y')}.csv")
            download.save_as(file_path)
            self.logger.info(f"CSV successfully stored at {file_path}")
            return file_path, last_price
