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
- SSH
```bash
$ git clone git@github.com:VandersonTorres/gamma-exposure-indicator.git
```
- HTTPS
```bash
$ git clone https://github.com/VandersonTorres/gamma-exposure-indicator.git
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
2. standard
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

*NOTE: You can combine multiple args*

0. **HELP MODE:**
```bash
$ python app.py -h
```

1. **Download all options for SPX and SPY for all expirations:**
```bash
$ python app.py
```

2. **Download only 0DTE options (Zero Days to Expiration):**
```bash
$ python app.py --zero_days True
```

3. **Download all standard expiration options for SPX and SPY:**
```bash
$ python app.py --expiration_type standard
```

4. **Download all options for SPX and SPY expiring at august:**
```bash
$ python app.py --expiration_month agosto
```

5. **Isolate the view of GEX results for both, call and puts separatedly, on the charts:**
```bash
$ python app.py --split_visualization True
```

- **Output**:

    CSV files will be saved in the directory specified in src/settings.py (default: data/raw/) with filenames like: `SPX_monthly_agosto_17-08-23.csv`

---

## Notes
The downloader is built with Playwright (sync API). Ensure browsers are installed via playwright install.

The tool handles cookie popups automatically.

Designed to be modular, so adding CME downloads or analytics features is straightforward.

---

# ESTUDO

## CENÁRIOS MARKET MAKERS (Comportamento dos MM)

### Compressão de Volatilidade
*(Market Maker está comprado em opções, tende a estabilizar o mercado.)*

1. Compra de Calls:

    D + | G +

    - Se o mercado sobe  ->  Venda do Ativo
    - Se o mercado cai   ->  Compra do Ativo
    (compra fundo | vende topo)

    Explicação:
    - Se o preço sobe, o DELTA (+) aumenta, então ele zera o delta vendendo o ativo.
    - Se o preço cai, o DELTA (+) diminui, e ele zera comprando o ativo.

2. Compra de Puts:

    D - | G +

    - Se o mercado sobe  ->  Venda do Ativo
    - Se o mercado cai   ->  Compra do Ativo
    (compra fundo | vende topo)

    Explicação:
    - Se o preço sobe, o DELTA (-) diminui (fica menos negativo), então ele zera vendendo o ativo
    - Se o preço cai, o DELTA (-) aumenta (fica mais negativo), então ele zera comprando o ativo

### Expansão de Volatilidade
*(Market Maker está vendido em opções, tende a amplificar o movimento do mercado.)*

1. Venda de Calls:

    D + | G -

    - Se o mercado sobe ->  Compra do Ativo
    - Se o mercado cai  ->  Venda do Ativo
    (compra topo | vende fundo)

    Explicação:
    - Se o preço sobe, o DELTA (+) aumenta, mas como o MM está vendido em calls, seu risco aumenta, então ele precisa comprar o ativo para cobrir.
    - Se o preço cai, o DELTA (+) diminui, então MM precisa vender o ativo.

2. Venda de Puts

    D - | G -

    - Se o mercado sobe ->   Compra do Ativo
    - Se o mercado cai  ->   Venda do Ativo
    (compra topo | vende fundo)

    Explicação:

    - Se o preço sobe, o DELTA (-) diminui (fica menos negativo), então ele precisa comprar o ativo.
    - Se o preço cai, o DELTA (-) aumenta (fica mais negativo), então ele precisa vender ativo.
