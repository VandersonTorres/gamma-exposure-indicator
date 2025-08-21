import logging
import json
import os

logger = logging.getLogger(__name__)


def calculate_gex_per_strikes(processed_file_path: str) -> dict:
    """
    Calculate Total Gamma Exposure per Strike.
    Args:
        processed_file_path (str): Path of the processed data file
    Returns:
        dict: A structured dict containing the total gamma exposure for each strike
        {
            "strike1": GEX VALUE,
            "strike2": GEX VALUE,
        }
    """
    asset_name, _ = os.path.splitext(processed_file_path.split("/")[-1])

    with open(processed_file_path, "r") as f:
        processed_data = json.loads(f.read())

    last_price = processed_data.pop("last_price")
    total_gex_per_strike = {asset_name: {}}
    for strike, options in processed_data.items():
        gex_result_at_strike = sum([option.get("gamma_exposure_result") for option in options])
        total_gex_per_strike[asset_name][strike] = gex_result_at_strike

    logger.info(f"Calculated Total Gamma Exposure per strike for '{asset_name}'.")
    flip_and_walls = calculate_flip_and_walls(processed_data=processed_data)
    total_gex_per_strike[asset_name]["last_price"] = last_price
    total_gex_per_strike[asset_name].update(flip_and_walls)

    return total_gex_per_strike


def calculate_flip_and_walls(processed_data: str) -> dict:
    """
    Calculate Gamma Flip Point based on aggregated Gamma Exposure.

    Args:
        processed_data (str): JSON file with processed strikes
    Returns:
        dict: {
            "gamma_flip_price": float,
            "call_wall": float,  # Optional: max positive GEX
            "put_wall": float    # Optional: max negative GEX
        }
    """
    # GEX agregado por strike
    aggregated_gex = {}
    for strike, options in processed_data.items():
        aggregated_gex[float(strike)] = sum(opt["gamma_exposure_result"] for opt in options)

    # TODO: Calculate Gamma Flip

    call_wall = max(aggregated_gex.values())
    put_wall = min(aggregated_gex.values())

    return {
        "call_wall": call_wall,
        "put_wall": put_wall,
    }
