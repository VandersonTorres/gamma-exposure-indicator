import argparse

from src.app_manager import GEXIndicatorManager


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
    parser.add_argument(
        "--flip_point",
        type=bool,
        help="Consider only Zero Days To Expiration options (0DTE). Ommit to calculate all expirations.",
    )
    args = parser.parse_args()
    urls = args.urls.split(",") if args.urls else None
    expiration_type = args.expiration_type
    expiration_month = args.expiration_month
    split_visualization = args.split_visualization
    zero_days = args.zero_days
    calc_flip_point = args.flip_point
    return {
        "urls": urls,
        "expiration_type": expiration_type,
        "expiration_month": expiration_month,
        "split_visualization": split_visualization,
        "zero_days": zero_days,
        "calc_flip_point": calc_flip_point,
    }


if __name__ == "__main__":
    args = _args()

    app_manager = GEXIndicatorManager(
        urls=args.get("urls"),
        expiration_type=args.get("expiration_type"),
        expiration_month=args.get("expiration_month"),
        split_visualization=args.get("split_visualization"),
        parse_only_zero_days=args.get("zero_days"),
        calc_flip_point=args.get("calc_flip_point"),
    )
    app_manager.run(
        # headless=False  # Uncomment to see navigation
    )
