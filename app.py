import argparse

from src.app_manager import GEXIndicatorManager
from src.scripts.telegram_bot import IntegrateTelegramBot


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
        action="store_true",
        help="See the GEX results isolated (calls and puts separated). Ommit to see total GEX.",
    )
    parser.add_argument(
        "--zero_dte",
        action="store_true",
        help="Consider only Zero Days To Expiration options (0DTE). Ommit to calculate all expirations.",
    )
    parser.add_argument(
        "--flip_point",
        action="store_true",
        help="Consider only Zero Days To Expiration options (0DTE). Ommit to calculate all expirations.",
    )
    parser.add_argument(
        "--telegram_chat_id",
        type=str,
        help="Passed automatically by the Webhook when in Telegram Chat Mode.",
    )
    args = parser.parse_args()
    urls = args.urls.split(",") if args.urls else None
    expiration_type = args.expiration_type
    expiration_month = args.expiration_month
    split_visualization = args.split_visualization
    zero_dte = args.zero_dte
    calc_flip_point = args.flip_point
    telegram_chat_id = args.telegram_chat_id
    return {
        "urls": urls,
        "expiration_type": expiration_type,
        "expiration_month": expiration_month,
        "split_visualization": split_visualization,
        "zero_dte": zero_dte,
        "calc_flip_point": calc_flip_point,
        "telegram_chat_id": telegram_chat_id,
    }


if __name__ == "__main__":
    args = _args()

    app_manager = GEXIndicatorManager(
        urls=args.get("urls"),
        expiration_type=args.get("expiration_type"),
        expiration_month=args.get("expiration_month"),
        split_visualization=args.get("split_visualization"),
        parse_only_zero_dte=args.get("zero_dte"),
        calc_flip_point=args.get("calc_flip_point"),
    )
    gex_metrics = app_manager.run(headless=True, telegram_chat_id=args.get("telegram_chat_id"))

    # If in Telegram Mode...
    if chat_id := args.get("telegram_chat_id"):
        import asyncio

        telegram_bot = IntegrateTelegramBot()
        for asset, gex_data in gex_metrics.items():
            name_parts = asset.split("_")
            date_part = name_parts[-1]
            asset_title = f"{name_parts[1].upper()} {name_parts[2].upper()} {date_part}"
            asyncio.run(
                telegram_bot._send_telegram_message(message=f"Metricas para {asset_title}\nGráfico:\n", chat_id=chat_id)
            )
            with open(gex_data.get("chart_image_path"), "rb") as f:
                asyncio.run(telegram_bot._send_photo(chat_id=chat_id, binary_file=f))

            asyncio.run(
                telegram_bot._send_telegram_message(
                    message=(
                        "\n"
                        f"🔵 Call Wall: {gex_data.get('call_wall_strike')}\n"
                        f"🔴 Put Wall: {gex_data.get('put_wall_strike')}\n"
                        f"🟡 Flip Point: {gex_data.get('flip_point')}\n"
                        f"Top Calls: {gex_data.get('top_calls')}\n"
                        f"Top Puts: {gex_data.get('top_puts')}\n\n"
                        "📲 Pine Script para colar no Code Editor do TradingView:\n\n"
                        "==============================\n"
                        f"{gex_data.get('pine_script')}\n"
                        "==============================\n"
                    ),
                    chat_id=chat_id,
                )
            )
