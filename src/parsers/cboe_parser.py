import json
import logging
import os
import pandas as pd
from datetime import datetime, date
from decimal import Decimal

from src.settings import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_cboe_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV from CBOE.
    Args:
        file_path (str): Path of the (raw) file to be readed (csv)
    Returns:
        DataFrame
    """
    df = pd.read_csv(file_path, skiprows=3)
    return df.rename(columns=lambda x: x.strip())


def calculate_gamma_exposure(gamma_value: float, open_interest: float, option_type: str, last_price: float) -> float:
    """
    Calculate Gamma Exposure Result.
    Args:
        gamma_value (float): Value of the Gamma
        open_interest (float): Value of the Open Interest
        option_type (str): Type of Option ("call" or "put")
        last_price (float): Value of Last Price
    Returns:
        float: GEX Result
    """
    if option_type.lower() == "call":
        multiplier = 100
    elif option_type.lower() == "put":
        multiplier = -100
    gex_value = gamma_value * open_interest * multiplier * last_price
    return gex_value


def generate_leads(df: pd.DataFrame, last_price: str, parse_only_zero_days: bool) -> dict:
    """
    Calculate the leads for each strike.
    Args:
        df (pd.DataFrame): A dataframe to be processed.
        last_price (str): Last price of the asset.
        parse_only_zero_days (bool): If we will consider only 0DTE options
    Returns:
        dict:
    {
        "strike1": [ {exp1}, {exp2}, ... ],
        "strike2": [ {exp1}, {exp2}, ... ],
    }
    """
    last_price = float(Decimal(last_price.replace(",", "")))
    processed_strikes = {}
    for _, row in df.iterrows():
        expiration_date = row["Expiration Date"]
        if parse_only_zero_days:
            parsed_expiration = datetime.strptime(expiration_date, "%a %b %d %Y").date()
            if date.today() != parsed_expiration:
                continue

        call_gamma_value = row["Gamma"]
        call_open_interest = row["Open Interest"]
        put_gamma_value = row["Gamma.1"]
        put_open_interest = row["Open Interest.1"]
        strike = str(row["Strike"])
        call_result = calculate_gamma_exposure(
            gamma_value=call_gamma_value,
            open_interest=call_open_interest,
            option_type="call",
            last_price=last_price,
        )
        put_result = calculate_gamma_exposure(
            gamma_value=put_gamma_value,
            open_interest=put_open_interest,
            option_type="put",
            last_price=last_price,
        )
        gamma_exposure_result = call_result + put_result

        if not processed_strikes.get(strike):
            processed_strikes[strike] = []

        processed_strikes[strike].append(
            {
                "expiration_date": expiration_date,
                "gex_at_call": call_result,
                "gex_at_put": put_result,
                "call_open_interest": call_open_interest,
                "put_open_interest": put_open_interest,
                "gamma_exposure_result": gamma_exposure_result,
                "call_gamma_value": call_gamma_value,
                "put_gamma_value": put_gamma_value,
            }
        )
    processed_strikes["last_price"] = last_price
    return processed_strikes


def save_processed_strikes(processed_strikes: dict, raw_file_path: str) -> str:
    """
    Store the processed data into a JSON file.
    Args:
        processed_strikes (dict): Strikes with calculated gex for calls and puts
        raw_file_path (str): Initial CSV file path
    """
    name = os.path.splitext(os.path.basename(raw_file_path))[0]
    filename = f"processed_{name}.json"
    output_path = os.path.join(PROCESSED_DIR, filename)

    with open(output_path, "w") as f:
        json.dump(processed_strikes, f, indent=2)

    logger.info(f"Serialized data stored at {output_path}")
    return output_path


def parse_cboe_csv(file_path: str, last_price: str, parse_only_zero_days: bool) -> str:
    """
    Manage processing of Raw CSV File from CBOE.
    Args:
        file_path (str): Path to the CSV file from CBOE.
        last_price (str): Last price of the asset.
        parse_only_zero_days (bool): If we will consider only 0DTE options
    Returns:
        str: Processed file path.
    """
    df = load_cboe_csv(file_path)
    logger.info(f"Calculating the leads for '{len(df)}' Strikes at '{file_path}'...")
    processed_strikes = generate_leads(df, last_price, parse_only_zero_days)
    return save_processed_strikes(processed_strikes, file_path)
