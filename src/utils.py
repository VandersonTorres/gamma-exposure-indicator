import numpy as np
from datetime import datetime
from scipy.stats import norm


# Black-Scholes European-Options Gamma
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    if T <= 0 or vol <= 0:
        return 0

    dp = (np.log(S / K) + (r - q + 0.5 * vol**2) * T) / (vol * np.sqrt(T))
    dm = dp - vol * np.sqrt(T)

    if optType == "call":
        gamma = np.exp(-q * T) * norm.pdf(dp) / (S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma
    else:  # Gamma is same for calls and puts. This is just to cross-check
        gamma = K * np.exp(-r * T) * norm.pdf(dm) / (S * S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma


def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21


def extract_date(file_name):
    """Extract date from filename in format DD-MM-YY."""
    try:
        date_part = file_name.split("_")[-1].replace(".txt", "")
        return datetime.strptime(date_part, "%d-%m-%y")
    except Exception:
        return datetime.min
