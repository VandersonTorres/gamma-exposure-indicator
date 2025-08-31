import logging
import os

from src.analytics.gamma_exposure import calculate_gex_per_strikes
from src.downloader.cboe_downloader import CBOEDownloader
from src.parsers.cboe_parser import parse_cboe_csv
from src.vizualization.gex_charts import process_metrics
from src.settings import REPORTS_DIR, TEMP_DIR
from src.utils import extract_date

logger = logging.getLogger(__name__)


class GEXIndicatorManager:
    cboe_default_urls = [
        # "https://www.cboe.com/delayed_quotes/spy/quote_table",  # ETF
        "https://www.cboe.com/delayed_quotes/spx/quote_table",  # SPOT
    ]

    def __init__(
        self,
        urls: list,
        expiration_type: str,
        expiration_month: str,
        split_visualization: bool,
        parse_only_zero_dte: bool,
        calc_flip_point: bool,
    ) -> None:
        """
        Initialize the GEXIndicatorManager.

        Args:
            urls (list): List of CBOE URLs to fetch data from.
            expiration_type (str): Option expiration type filter (e.g., "monthly", "weekly", "all").
            expiration_month (str): Specific expiration month to filter (e.g., "Jan", "Feb", or "all").
            split_visualization (bool): Whether to generate separate visualizations for calls and puts.
            parse_only_zero_dte (bool): Whether to parse only zero-days-to-expiration options.
            calc_flip_point (bool): Whether to calculate the Gamma Flip point.
        """
        self.urls = urls or self.cboe_default_urls
        self.expiration_type = expiration_type or "all"
        self.expiration_month = expiration_month or "all"
        self.split_visualization = split_visualization or False
        self.parse_only_zero_dte = parse_only_zero_dte or False
        self.calc_flip_point = calc_flip_point or False

    def get_data(self, headless: bool) -> list[tuple]:
        """
        Download CBOE option chain CSV files and extract last prices.

        Args:
            headless (bool): Whether to run the browser in headless mode.

        Returns:
            list[tuple]: A list of tuples containing (csv_file_path, last_price).
        """
        cboe_downloader = CBOEDownloader()
        csv_files_and_last_price = []
        for url in self.urls:
            options_csv_file_path, last_price = cboe_downloader.get_csv_and_last_price(
                url=url,
                expiration_type=self.expiration_type,
                expiration_month=self.expiration_month,
                headless=headless,
            )
            csv_files_and_last_price.append((options_csv_file_path, last_price))

        return csv_files_and_last_price

    def process_data(self, csv_files_and_last_price: list[tuple]) -> list:
        """
        Parse CBOE CSV files and extract structured option data.

        Args:
            csv_files_and_last_price (list[tuple]): List of tuples containing
                (csv_file_path, last_price).

        Returns:
            list: A list of processed file paths containing parsed option data.
        """
        processed_files = []
        for file_path, last_price in csv_files_and_last_price:
            processed_file = parse_cboe_csv(
                file_path=file_path,
                last_price=last_price,
                parse_only_zero_dte=self.parse_only_zero_dte,
                calc_flip_point=self.calc_flip_point,
            )
            processed_files.append(processed_file)

        return processed_files

    def process_gex_metrics(self, processed_files: list[str]) -> dict:
        """
        Calculate Gamma Exposure (GEX) metrics from processed files.

        Args:
            processed_files (list[str]): List of processed file paths containing option data.

        Returns:
            dict: Dictionary mapping assets to their calculated GEX metrics.
        """
        gex_metrics_per_asset = {}
        for processed_file in processed_files:
            calculated_gex = calculate_gex_per_strikes(processed_file_path=processed_file)
            gex_metrics_per_asset.update(calculated_gex)

        self.set_gamma_flip(gex_metrics_per_asset)
        return gex_metrics_per_asset

    def set_gamma_flip(self, gex_metrics_per_asset: dict) -> None:
        """
        Attach Gamma Flip values (if available) to the GEX metrics.

        Args:
            gex_metrics_per_asset (dict): Dictionary containing GEX metrics per asset.
        """
        files = os.listdir(TEMP_DIR)

        # Dynamic Mapping
        flip_map = {}
        for asset in gex_metrics_per_asset.keys():
            asset_ticket = asset.split("_quotedata")[0].replace("processed_cboe_", "")
            flip_file = max(
                (f for f in files if asset_ticket.lower() in f.lower()),
                key=extract_date,
                default=None,
            )
            if flip_file:
                with open(os.path.join(TEMP_DIR, flip_file), "r") as f:
                    flip_map[asset] = f.read()

        for asset, _ in gex_metrics_per_asset.items():
            gex_metrics_per_asset[asset]["flip"] = flip_map.get(asset, "")

    def generate_pine_script(self, gex_metrics: dict) -> None:
        """
        Generate a Pine Script® code snippet for TradingView visualization.

        Args:
            gex_metrics (dict): Dictionary containing GEX metrics per asset.

        Side Effects:
            Log the generated Pine Script to the console and add it to the asset.
        """
        pine_script = ""
        for asset, metrics in gex_metrics.items():
            asset_ticket = asset.split("_quotedata")[0].replace("processed_cboe_", "")
            pine_script = (
                "// This Pine Script® code is subject to the terms of "
                "the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/\n"
                "// © Tenv66\n\n"
                "//@version=6\n"
                "indicator('GEX Levels', overlay=true)\n\n"
                f"call_wall = {metrics.get('call_wall_strike')}\n"
                f"put_wall  = {metrics.get('put_wall_strike')}\n"
                f"flip_point = {metrics.get('flip_point')}\n"
                f"top_calls = array.from({metrics.get('top_calls')})\n"
                f"top_puts  = array.from({metrics.get('top_puts')})\n\n"
                "// Call Wall and Put Wall (static lines with hline)\n"
                "hline(call_wall, 'Call Wall', color=color.blue, linewidth=2, "
                "linestyle=hline.style_solid)\n"
                "hline(put_wall, 'Put Wall', color=color.red, linewidth=2, "
                "linestyle=hline.style_solid)\n"
                "hline(flip_point, 'Flip Point', color=color.rgb(251, 218, 0), "
                "linewidth=2, linestyle=hline.style_solid)\n\n"
                "// Function to draw horizontal dynamic lines\n"
                "f_draw_levels(levels_array, col) =>\n"
                "  for i = 0 to array.size(levels_array) - 1\n"
                "    level = array.get(levels_array, i)\n"
                "    line.new(bar_index[100], level, bar_index, level, extend=extend.both, "
                "style=line.style_dashed, color=col, width=1)\n"
                "    label.new(bar_index, level, str.tostring(i + 1), "
                "style=label.style_label_left, textcolor=color.white, color=col)\n\n"
                "// Draw top calls (dark blue)\n"
                "f_draw_levels(top_calls, color.rgb(62, 34, 186))\n\n"
                "// Draw top puts (blood red)\n"
                "f_draw_levels(top_puts, color.rgb(161, 17, 94))\n"
            )
            gex_metrics[asset]["pine_script"] = pine_script
            logger.info(
                "\n"
                f"{'=' * 80}"
                f"\n🚨  PINE SCRIPT GENERATED for {asset_ticket.upper()}  🚨\n"
                f"{'-' * 80}"
                f"\n📌 Asset Ticket: {asset_ticket.upper()}\n"
                "\n>>> Copy the following Pine Script into TradingView's Pine Editor:\n\n"
                f"{pine_script}\n"
                f"{'=' * 80}\n"
            )

    def run(self, headless: bool = True) -> None:
        """
        Execute the full GEX indicator workflow.

        This includes:
        - Downloading and parsing option chain data
        - Calculating Gamma Exposure (GEX) metrics
        - Generating visualizations
        - Printing Pine Script® code for TradingView

        Args:
            headless (bool, optional): Whether to run the downloader in headless mode.
                Defaults to True.
        """
        csv_files_and_last_price = self.get_data(headless)
        processed_files = self.process_data(csv_files_and_last_price)
        gex_metrics_per_asset = self.process_gex_metrics(processed_files)
        visualization_mode = "total"
        if self.split_visualization:
            visualization_mode = "split"
        final_gex_metrics = process_metrics(gex_metrics_per_asset, REPORTS_DIR, visualization_mode)
        self.generate_pine_script(final_gex_metrics)
        return final_gex_metrics
