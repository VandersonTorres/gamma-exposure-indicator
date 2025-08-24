import argparse

from src.analytics.gamma_exposure import calculate_gex_per_strikes
from src.downloader.cboe_downloader import CBOEDownloader
from src.parsers.cboe_parser import parse_cboe_csv
from src.vizualization.gex_charts import handle_metrics
from src.settings import REPORTS_DIR

CBOE_DEFAULT_URLS = [
    "https://www.cboe.com/delayed_quotes/spy/quote_table",  # ETF
    "https://www.cboe.com/delayed_quotes/spx/quote_table",  # SPOT
]


def _args() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--urls",
        type=str,
        help="Papers URLs to crawl. Comma separated (url1,url2,url3). The default are the ETF and SPOT urls.",
    )
    parser.add_argument(
        "--expiration_type",
        type=str,
        help=(
            "Type of the expiration. Supported values: 'all' (Default), 'standard', 'weekly', 'quarterly', 'monthly'"
        ),
    )
    parser.add_argument(
        "--expiration_month",
        type=str,
        help="Month of expiration. Supported values: 'all' (Default), 'agosto', 'setembro' (in portuguese).",
    )
    parser.add_argument(
        "--split_visualization",
        type=bool,
        help="See the GEX results isolated (calls and puts separated). Ommit to see total GEX.",
    )
    parser.add_argument(
        "--zero_days",
        type=bool,
        help="Consider only Zero Days To Expiration options (0DTE). Ommit to calculate all expirations.",
    )
    args = parser.parse_args()
    urls = args.urls.split(",") if args.urls else CBOE_DEFAULT_URLS
    expiration_type = args.expiration_type or "all"
    expiration_month = args.expiration_month or "all"
    split_visualization = args.split_visualization or False
    zero_days = args.zero_days or False
    return {
        "urls": urls,
        "expiration_type": expiration_type,
        "expiration_month": expiration_month,
        "split_visualization": split_visualization,
        "zero_days": zero_days,
    }


if __name__ == "__main__":
    cboe_downloader = CBOEDownloader()
    args = _args()
    urls = args.get("urls")
    expiration_type = args.get("expiration_type")
    expiration_month = args.get("expiration_month")
    split_visualization = args.get("split_visualization")
    parse_only_zero_days = args.get("zero_days")

    raw_csv_files_to_check = [
        # ("data/raw/cboe_spx_quotedata_all_22-08-25.csv", "6,466.91"), # Uncomment only for DEBUG
        # ("data/raw/cboe_spy_quotedata_all_22-08-25.csv", "650.0"),    # Uncomment only for DEBUG
    ]
    for url in urls:
        options_csv_file_path, last_price = cboe_downloader.get_csv_and_last_price(
            url=url,
            expiration_type=expiration_type,
            expiration_month=expiration_month,
            # headless=False  # Uncomment to show browser
        )
        raw_csv_files_to_check.append((options_csv_file_path, last_price))

    processed_files = [
        # "data/processed/processed_cboe_spx_quotedata_all_22-08-25.json",  # Uncomment only for DEBUG
        # "data/processed/processed_cboe_spy_quotedata_all_22-08-25.json",  # Uncomment only for DEBUG
    ]
    for file_path, last_price in raw_csv_files_to_check:
        processed_file = parse_cboe_csv(
            file_path=file_path, last_price=last_price, parse_only_zero_days=parse_only_zero_days
        )
        processed_files.append(processed_file)

    total_gex_per_asset = {}
    for processed_file in processed_files:
        calculated_gex = calculate_gex_per_strikes(processed_file_path=processed_file)
        total_gex_per_asset.update(calculated_gex)

    visualization_mode = "total"
    if split_visualization:
        visualization_mode = "split"

    gex_metrics = handle_metrics(total_gex_per_asset, path_to_store=REPORTS_DIR, mode=visualization_mode)

    pine_script = ""
    for asset, metrics in gex_metrics.items():
        if "spx" in asset:
            pine_script = (
                "// This Pine Script® code is subject to the terms of "
                "the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/\n"
                "// © Tenv66\n\n"
                "//@version=6\n"
                "indicator('GEX Levels', overlay=true)\n\n"
                f"call_wall = {metrics.get('call_wall_strike')}\n"
                f"put_wall  = {metrics.get('put_wall_strike')}\n"
                f"top_calls = array.from({metrics.get('top_calls')})\n"
                f"top_puts  = array.from({metrics.get('top_puts')})\n\n"
                "// Call Wall and Put Wall (static lines with hline)\n"
                "hline(call_wall, 'Call Wall', color=color.blue, linewidth=2, "
                "linestyle=hline.style_solid)\n"
                "hline(put_wall, 'Put Wall', color=color.red, linewidth=2, "
                "linestyle=hline.style_solid)\n\n"
                "// Function to draw horizontal dynamic lines\n"
                "f_draw_levels(levels_array, col) =>\n"
                "  for i = 0 to array.size(levels_array) - 1\n"
                "    level = array.get(levels_array, i)\n"
                "    line.new(bar_index[100], level, bar_index, level, extend=extend.both, "
                "style=line.style_dashed, color=col, width=1)\n\n"
                "// Draw top calls (dark blue)\n"
                "f_draw_levels(top_calls, color.rgb(62, 34, 186))\n\n"
                "// Draw top puts (blood red)\n"
                "f_draw_levels(top_puts, color.rgb(161, 17, 94))\n"
            )

    if pine_script:
        print(f"\n>>> Place the following Pine Script on the code editor of TradingView:\n{pine_script}")
