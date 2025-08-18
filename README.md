# Gamma Exposure Indicator

**Gamma Exposure Indicator** is a Python tool with a modular and extendable architecture using Playwright that automates the download of S&P 500 options CSV files from CBOE and CME, calculates the dealer's Gamma Exposure (GEX) and build charts structured with the results from the data analysis. It supports crawling ETF (SPY), Spot (SPX) and Futures (ES) data.

---

## Features

- Crawl CBOE pages for SPX (Spot) and SPY (ETF) options.            ✅
- Download and save structured options CSV files.                   ✅
- Calculate the Dealers and Market Makers Gamma Exposure (GEX).
- Structure the analysis result's visualization into charts.

---

## Installation

1. Clone the repository:

```bash
$ git clone git@github.com:VandersonTorres/gamma-exposure-indicator.git
```

2. (Optional) Create a virtual environment:
```bash
$ python -m venv venv
$ source venv/bin/activate  # Linux/Mac
$ venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
$ pip install -r requirements.txt
```

4. Install Playwright browsers:

```bash
$ playwright install
```

5. Install pre-commit:

```bash
$ pre-commit install
```

---

## Usage
You can run the downloader using app.py passing (or not) the following arguments:

- URLs: Comma-separated URLs to crawl (url1,url2,url3). Default:
1. https://www.cboe.com/delayed_quotes/spy/quote_table
2. https://www.cboe.com/delayed_quotes/spx/quote_table


- Expiration Type: Type of expiration. Supported values:
1. all (default)
2. standard (0DTE)
3. weekly
4. quarterly
5. monthly

- Expiration Month: Expiration month (in Portuguese). Supported values:

1. all (default)
2. janeiro, fevereiro, etc...

### Usage Example

*Ensure you are inside `gamma-exposure-indicator` dir*
```bash
$ cd gamma-exposure-indicator
```

1. **Download all options for SPX and SPY:**
```bash
$ python app.py
```

2. **Download all 0DTE options for SPX and SPY:**
```bash
$ python app.py --expiration_type standard
```
*Note that if `expiration_type` is "standard" you shall ignore monthly expirations.*

3. **Download all options for SPX and SPY expiring at august:**
```bash
$ python app.py --expiration_type all --expiration_month agosto
```

- **Output**:

    CSV files will be saved in the directory specified in src/settings.py (default: data/raw/) with filenames like: `SPX_monthly_agosto_17-08-23.csv`

---

## Notes
The downloader is built with Playwright (sync API). Ensure browsers are installed via playwright install.

The tool handles cookie popups automatically.

Designed to be modular, so adding CME downloads or analytics features is straightforward.
