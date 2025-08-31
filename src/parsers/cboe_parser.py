import dateparser
import json
import logging
import numpy as np
import os
import pandas as pd
from datetime import datetime, date
from decimal import Decimal

from src.settings import PROCESSED_DIR, TEMP_DIR
from src.utils import calcGammaEx, isThirdFriday

logger = logging.getLogger(__name__)


def load_cboe_csv(file_path: str) -> tuple[pd.DataFrame, list]:
    """
    Load a CSV from CBOE.
    Args:
        file_path (str): Path of the (raw) file to be readed (csv)
    Returns:
        DataFrame
    """
    df = pd.read_csv(file_path, skiprows=3)
    df = df.rename(columns=lambda x: x.strip())

    with open(file_path, "r") as f:
        metadata = [next(f).strip() for _ in range(3)]

    return df, metadata


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


def calculate_gamma_flip(
    df: pd.DataFrame, _metadata: list, last_price: float, parse_only_zero_dte: bool, file_path: str
) -> int:
    """
    Calculate the Gamma Flip point for a given options DataFrame and save the result to a file.

    This function computes the gamma exposure for multiple spot levels based on the
    options data provided, identifies the zero-crossing point of the total gamma
    (the Gamma Flip), rounds it to the nearest multiple of 5, and writes the result
    to a file named 'gamma_flip_result.txt' in the current directory.

    Args:
        df (pd.DataFrame): DataFrame containing options data. Must include columns
            'Expiration Date', 'Strike', 'IV', 'IV.1', 'Open Interest', 'Open Interest.1'.
        _metadata (list): Metadata list containing the file's date at index 2.
        last_price (float): Current spot price of the underlying asset.
        parse_only_zero_dte (bool): Consider only zero days to expiration.
        file_path (str): Path of the (raw) file to be readed (csv)

    Returns:
        float: The rounded Gamma Flip value.
    """
    fromStrike = 0.8 * last_price
    toStrike = 1.2 * last_price
    levels = np.linspace(fromStrike, toStrike, 60)

    # Get Today's Date
    date_line = _metadata[2]
    today_date_str = date_line.split("Date: ")[1].split(",")[0]
    parsed_date = dateparser.parse(today_date_str)
    today_date = datetime(year=parsed_date.year, month=parsed_date.month, day=parsed_date.day)

    df["Expiration Date"] = pd.to_datetime(df["Expiration Date"])
    if parse_only_zero_dte:
        df = df[df["Expiration Date"].dt.date == today_date.date()]

    df["IsThirdFriday"] = [isThirdFriday(x) for x in df["Expiration Date"]]
    df["daysTillExp"] = [
        (
            1 / 262
            if (np.busday_count(today_date.date(), x.date())) == 0
            else np.busday_count(today_date.date(), x.date()) / 262
        )
        for x in df["Expiration Date"]
    ]

    nextExpiry = df["Expiration Date"].min()
    thirdFridays = df.loc[df["IsThirdFriday"]]
    nextMonthlyExp = thirdFridays["Expiration Date"].min()

    total_gamma = []
    total_gex_next = []
    total_gex_fri = []

    # For each spot level, calc gamma exposure at that point
    logger.info("Calculating Gamma Flip...")
    for level in levels:
        df["callGammaEx"] = df.apply(
            lambda row: calcGammaEx(
                level, row["Strike"], row["IV"], row["daysTillExp"], 0, 0, "call", row["Open Interest"]
            ),
            axis=1,
        )

        df["putGammaEx"] = df.apply(
            lambda row: calcGammaEx(
                level, row["Strike"], row["IV.1"], row["daysTillExp"], 0, 0, "put", row["Open Interest.1"]
            ),
            axis=1,
        )
        total_gamma.append(df["callGammaEx"].sum() - df["putGammaEx"].sum())
        exNxt = df.loc[df["Expiration Date"] != nextExpiry]
        total_gex_next.append(exNxt["callGammaEx"].sum() - exNxt["putGammaEx"].sum())

        exFri = df.loc[df["Expiration Date"] != nextMonthlyExp]
        total_gex_fri.append(exFri["callGammaEx"].sum() - exFri["putGammaEx"].sum())

    total_gamma = np.array(total_gamma) / 10**9
    total_gex_next = np.array(total_gex_next) / 10**9
    total_gex_fri = np.array(total_gex_fri) / 10**9

    # Find Gamma Flip Point
    zero_cross_idx = np.where(np.diff(np.sign(total_gamma)))[0]
    neg_gamma = total_gamma[zero_cross_idx]
    pos_gamma = total_gamma[zero_cross_idx + 1]
    neg_strike = levels[zero_cross_idx]
    pos_strike = levels[zero_cross_idx + 1]
    zero_gamma = pos_strike - ((pos_strike - neg_strike) * pos_gamma / (pos_gamma - neg_gamma))
    zero_gamma = zero_gamma[0]
    flip_point = round(float(zero_gamma) / 5) * 5
    logger.info(f"Calculated flip point {flip_point}")

    name = os.path.splitext(os.path.basename(file_path))[0]
    filename = f"flip_point_{name}.txt"
    filepath = f"{TEMP_DIR}/{filename}"
    with open(filepath, "w") as f:
        f.write(str(flip_point))
    logger.info(f"Stored flip point result at {filepath}")

    return flip_point


def generate_leads(
    df: pd.DataFrame,
    _metadata: list,
    last_price: str,
    parse_only_zero_dte: bool,
    calc_flip_point: bool,
    file_path: str,
) -> dict:
    """
    Calculate the leads for each strike.
    Args:
        df (pd.DataFrame): A dataframe to be processed.
        last_price (str): Last price of the asset.
        parse_only_zero_dte (bool): If we will consider only 0DTE options
        calc_flip_point (bool): If we will calculate Flip Gamma Point
        file_path (str): Path of the (raw) file to be readed (csv)
    Returns:
        dict:
    {
        "strike1": [ {exp1}, {exp2}, ... ],
        "strike2": [ {exp1}, {exp2}, ... ],
    }
    """
    last_price = float(Decimal(last_price.replace(",", "")))
    processed_strikes = {}
    for idx, row in df.iterrows():
        if idx < 3:  # Skip initial 3 lines
            continue

        expiration_date = row["Expiration Date"]
        if parse_only_zero_dte:
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

    if calc_flip_point:
        calculate_gamma_flip(df, _metadata, last_price, parse_only_zero_dte, file_path)

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


def parse_cboe_csv(file_path: str, last_price: str, parse_only_zero_dte: bool, calc_flip_point: bool) -> str:
    """
    Manage processing of Raw CSV File from CBOE.
    Args:
        file_path (str): Path to the CSV file from CBOE.
        last_price (str): Last price of the asset.
        parse_only_zero_dte (bool): If we will consider only 0DTE options
        calc_flip_point (bool): If we will calculate Flip Gamma Point
    Returns:
        str: Processed file path.
    """
    df, _metadata = load_cboe_csv(file_path)
    logger.info(f"Calculating the leads for '{len(df)}' Strikes at '{file_path}'...")
    processed_strikes = generate_leads(df, _metadata, last_price, parse_only_zero_dte, calc_flip_point, file_path)
    return save_processed_strikes(processed_strikes, file_path)
