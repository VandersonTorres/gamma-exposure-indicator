import json
import logging
import os
import pandas as pd

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


def calculate_leads(df: pd.DataFrame, last_price: str) -> dict:
    """
    Calculate the leads for each strike.
    Args:
        df (pd.DataFrame): A dataframe to be processed.
        last_price (str): Last price of the asset.
    Returns:
        dict:
    {
        "strike1": [ {exp1}, {exp2}, ... ],
        "strike2": [ {exp1}, {exp2}, ... ],
    }
    """
    processed_strikes = {}
    for _, row in df.iterrows():
        call_gamma_value = row["Gamma"]
        call_open_interest = row["Open Interest"]
        put_open_interest = row["Open Interest"]
        put_gamma_value = row["Gamma.1"]
        strike = str(row["Strike"])
        call_result = (call_gamma_value * call_open_interest) * 100
        put_result = (put_gamma_value * put_open_interest) * -100
        gamma_exposure = call_result + put_result

        if strike not in processed_strikes:
            processed_strikes[strike] = []

        processed_strikes[strike].append(
            {
                "expiration_date": row["Expiration Date"],
                "gex_at_call": call_result,
                "gex_at_put": put_result,
                "call_open_interest": call_open_interest,
                "put_open_interest": put_open_interest,
                "gamma_exposure_result": gamma_exposure,
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
    name, _ = os.path.splitext(raw_file_path.split("/")[-1])
    filename = f"processed_{name}.json"
    output_path = os.path.join(PROCESSED_DIR, filename)

    with open(output_path, "w") as f:
        json.dump(processed_strikes, f, indent=2)

    logger.info(f"Serialized data stored at {output_path}")
    return output_path


def parse_cboe_csv(file_path: str, last_price: str) -> str:
    """
    Manage processing of Raw CSV File from CBOE.
    Args:
        file_path (str): Path to the CSV file from CBOE.
        last_price (str): Last price of the asset.
    Returns:
        str: Processed file path.
    """
    df = load_cboe_csv(file_path)
    logger.info(f"Calculating the leads for '{len(df)}' Strikes at '{file_path}'...")
    processed_strikes = calculate_leads(df, last_price)
    return save_processed_strikes(processed_strikes, file_path)
