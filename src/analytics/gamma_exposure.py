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
        call_gex = sum([option.get("gex_at_call") for option in options])
        put_gex = sum([option.get("gex_at_put") for option in options])
        total_gex = sum([option.get("gamma_exposure_result") for option in options])
        total_gex_per_strike[asset_name][strike] = {
            "call": call_gex,
            "put": put_gex,
            "total": total_gex,
        }

    logger.info(f"Calculated Total Gamma Exposure per strike for '{asset_name}'.")
    total_gex_per_strike[asset_name]["last_price"] = last_price

    return total_gex_per_strike


# TODO: IMPLEMENTS THIS FUNCTION
# def calculate_gamma_flips(total_gex_per_strike: dict) -> dict:
#     """
#     Calculate all Gamma Flip Points based on aggregated Gamma Exposure.

#     Args:
#         total_gex_per_strike (dict): JSON structure with processed strikes
#     Returns:
#         dict: {
#             "gamma_flips": [float, ...],
#             "historical_exposure_values": [float, ...],
#         }
#     """
#     gex_by_strike = [(strike, gex) for strike, gex in total_gex_per_strike.items()]

#     gamma_flips = []
#     historical_exposure_values = []
#     for i in range(1, len(gex_by_strike)):
#         _, prev_gex = gex_by_strike[i - 1]
#         curr_strike, curr_gex = gex_by_strike[i]

#         result = prev_gex + curr_gex
#         historical_exposure_values.append((float(curr_strike), result))
#         if (prev_gex <= 0 and result > 0) or (prev_gex >= 0 and result < 0):
#             gamma_flips.append(float(curr_strike))

#     return {"gamma_flips": gamma_flips, "historical_exposure_values": historical_exposure_values}
