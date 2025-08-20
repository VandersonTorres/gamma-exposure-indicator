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


def calculate_gamma_exposure(df: pd.DataFrame) -> dict:
    """
    Calculate Gamma Exposure (GEX) for each strike.
    Args:
        df (pd.DataFrame): A dataframe to be processed.
    Returns:
        dict:
    {
        "strike1": [ {exp1}, {exp2}, ... ],
        "strike2": [ {exp1}, {exp2}, ... ],
    }
    """
    processed_strikes = {}
    for _, row in df.iterrows():
        strike = str(row["Strike"])
        call_result = (row["Gamma"] * row["Open Interest"]) * 100
        put_result = (row["Gamma.1"] * row["Open Interest.1"]) * -100
        gamma_exposure = call_result + put_result

        if strike not in processed_strikes:
            processed_strikes[strike] = []

        processed_strikes[strike].append(
            {
                "expiration_date": row["Expiration Date"],
                "gex_at_call": call_result,
                "gex_at_put": put_result,
                "gamma_exposure_result": gamma_exposure,
            }
        )
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

    logger.info(f"Processed data stored at {output_path}")
    return output_path


def parse_cboe_csv(file_path: str) -> str:
    """
    Manage processing of Raw CSV File from CBOE.
    Args:
        file_path (str): Path to the CSV file from CBOE.
    Returns:
        str: Processed file path.
    """
    df = load_cboe_csv(file_path)
    logger.info(f"Calculating Gamma Exposure for '{len(df)}' Strikes at '{file_path}'...")
    processed_strikes = calculate_gamma_exposure(df)
    return save_processed_strikes(processed_strikes, file_path)
