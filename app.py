import argparse

from src.analytics.gamma_exposure import calculate_gex_per_strikes
from src.downloader.cboe_downloader import CBOEDownloader
from src.parsers.cboe_parser import parse_cboe_csv
from src.vizualization.gex_charts import plot_gex

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
            "Type of the expiration. Supported values: 'all' (Default), "
            "'standard' (0DTE), 'weekly', 'quarterly', 'monthly'"
        ),
    )
    parser.add_argument(
        "--expiration_month",
        type=str,
        help="Month of expiration. Supported values: 'all' (Default), 'agosto', 'setembro' (in portuguese)",
    )
    args = parser.parse_args()
    urls = args.urls.split(",") if args.urls else CBOE_DEFAULT_URLS
    expiration_type = args.expiration_type or "all"
    expiration_month = args.expiration_month or "all"
    return {
        "urls": urls,
        "expiration_type": expiration_type,
        "expiration_month": expiration_month,
    }


if __name__ == "__main__":
    cboe_downloader = CBOEDownloader()
    args = _args()
    urls = args.get("urls")
    expiration_type = args.get("expiration_type")
    expiration_month = args.get("expiration_month")

    raw_csv_files_to_check = []
    for url in urls:
        options_csv_file_path, last_price = cboe_downloader.get_csv_and_last_price(
            url=url,
            expiration_type=expiration_type,
            expiration_month=expiration_month,
            # headless=False  # Uncomment to show browser
        )
        raw_csv_files_to_check.append((options_csv_file_path, last_price))

    processed_files = [
        # "data/processed/processed_cboe_spx_quotedata_all_20-08-25.json",
        # "data/processed/processed_cboe_spy_quotedata_all_20-08-25.json",
    ]
    for file_path, last_price in raw_csv_files_to_check:
        processed_file = parse_cboe_csv(file_path=file_path, last_price=last_price)
        processed_files.append(processed_file)

    total_gex_per_asset = {}
    for processed_file in processed_files:
        calculated_gex = calculate_gex_per_strikes(processed_file_path=processed_file)
        total_gex_per_asset.update(calculated_gex)

    plot_gex(total_gex_per_asset)
