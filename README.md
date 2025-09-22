## 🔹 Overview  

This project implements a **Pairs Trading Strategy** on Indian markets using the Upstox API for live deployment.  

Pairs trading is a **market-neutral strategy** that takes advantage of the relative price movement between two highly correlated or cointegrated stocks. The idea is to long one stock and short the other when their price spread deviates from the historical mean, and then close the position when the spread reverts.  

In this project:  
1. I have identified **pairs from each sector in the Indian markets** using **correlation and cointegration tests** to ensure the chosen pairs have strong statistical relationships.  
2. Since **short-selling and holding positions overnight is restricted in Indian markets**, this strategy is designed as an **Intraday Strategy**. However, if conditions permit, the trading signal may be **carried forward to the next trading day**.  

The project includes modules for **data fetching, strategy execution, order placement, and risk management**, making it suitable for **real-time deployment**. It can also be extended for research, backtesting, and integration with other trading strategies.  
## 🔹 Features  

- **Pairs Selection**: Identifies statistically significant stock pairs from each sector using correlation and cointegration tests.  
- **Intraday Strategy**: Designed specifically for Indian markets where short-selling and overnight holding are restricted.  
- **Signal Carry Forward**: Option to carry forward signals to the next trading day if conditions remain valid.  
- **Live Data Fetching**: Pulls real-time market data using the Upstox API.  
- **Automated Execution**: Places and manages orders automatically based on strategy signals.  
- **Risk Management**: Includes brokerage and transaction charge calculation to ensure realistic performance tracking.  
- **Research Notebooks**: Provides Jupyter notebooks (`PAIRS_TRADING_RESEARCH.ipynb`) for backtesting and experimentation.  
- **Configurable Environment**: API keys, tokens, and parameters are easily managed through environment files (`.env`, `access_token.env`).  
- **Scalable Design**: Modular code structure (`data_fetching.py`, `execution.py`, `order.py`, etc.) allows easy extension and integration with other strategies.  

## 🔹 Project Structure  

The project is organized into multiple scripts and notebooks, each serving a specific purpose.  

- **`PAIRS_TRADING_RESEARCH.ipynb`** – Research notebook for identifying cointegrated and correlated pairs.  
  - Functions:  
    1. Backtest any pair on historical data.  
    2. Fetch and compare the best pairs from each sector, along with spread plots, to identify the most suitable pairs.  

- **`data_fetching.py`** – Fetches live and historical market data from Upstox.  
  - Functions:  
    1. `hist_data` – Fetch historical data with convenient timeframe and tick sizes.  
    2. `get_instrument_key` – Fetch instrument keys for the stock you want to work on.  
    3. `market_quote_ltp` – Fetch the last traded price for realistic execution price tracking.  
    4. `order_book_price` – Fetch the actual buy/sell price available in the order book.  
    5. `live_data` – Pipeline to fetch live data via Upstox websocket and store in a CSV file (computationally expensive, slower).  
    6. `live_data_queue` – Pipeline to fetch live data via Upstox websocket and append to a shared queue (faster and efficient for real-time).  

- **`order.py`** – Defines order placement functions and order flow handling.  
  - Functions:  
    1. `placing_order` – Place market orders for the given ticker and quantity.  
    2. `exit_all_positions` – Exit all currently open positions in the portfolio.  
    3. `get_positions` – Retrieve current open positions.  
    4. `BUY/SELL_portfolio_pairtrading` – Customized buy/sell functions tailored for the pair trading strategy.  

- **`charges.py`** – Calculates brokerage and transaction costs for realistic PnL tracking.  
  - Functions:  
    1. `charges_delivery` – Calculate charges incurred while buying delivery holdings.  
    2. `margins` – Get the margin required for a futures contract.  
    3. `margins_intraday` – Get the margin required to enter an intraday trade for a given ticker and quantity.  

- **`profile.py`** – Stores user-specific and strategy-related configurations.  
  - Functions:  
    1. `get_funds_available` – Fetch current available funds to enter a trade.  

- **`shared_queue.py`** – Creates a shared queue to store live data and share it across different threads.  

- **`fetch_access_key.py`** – Function to fetch the Upstox access key, essential for performing account activities through API functions.  

- **`pair_trading.py`** – Core pairs trading logic and signal generation.  
  - Functions:  
    1. `prepare_historical_data` – Fetch historical data for the pair and store in a CSV for computing z-scores.  
    2. `update_pairs_data` – Compute z-score at the start of the current day and update the CSV file.  
    3. `trading_day / trading_day_queue` – Core trading loop; CSV method uses file-sharing while queue method is more efficient for real-time execution.  

- **`execution.py`** – Manages all modules and runs them in the correct sequence to execute the strategy.  

- **`a.env` / `acess_token.env`** – Environment files for securely storing API keys, secrets, and access tokens.  

- **`requirmnts.txt`** – List of required Python libraries and dependencies.  

## 🔹 INSTALLATION  

Follow these steps to set up the project on your local machine:  

### 1. Clone the Repository  
```bash
git clone https://github.com/your-username/pairs-trading-upstox.git
cd pairs-trading-upstox
pip install -r requirmnts.txt
```

## 🔹 USAGE  

### Pre-requisites  
- You must have an **Upstox Pro/Plus account** with API access enabled.

### Steps to Follow  

1. **Create an App** on your Upstox account, filling in the required details and activating it.  
   - Make sure to use the same `redirected_url` in the `a.env` file.  

2. **Enable TOTP** (Two-Factor Authentication) on your Upstox account and copy the `TOTP_KEY`.  

3. **Fill in your details** in the `a.env` file as per the provided template.  
   - Keep this file secure and do not share it.  

4. (Optional) **Adjust key parameters** in the config:  
   - Factor of available funds to use (default = `0.5`).  
   - Thresholds for `z_score` based on your strategy.  
   - Entry and exit timings to suit your trading needs.
5. Use the PAIR_TRADING_RESEARCH notebook and functions to come up with a pair who has done well
   in backtesting and you think will be an opt pair to run strategy with ( most crucial step).
   - enter the pairs keeping in mind the ticker1 -> y and ticker2 -> x and their hedge ratio in the execution.py file
   - set the schedule timing accordinglly. Remember to keep a 1 min gap in fetching live data and running strategy to have a buffer data to act upon 

5. **Run the strategy** by executing the following command in your terminal:  
```bash
python execution.py
```
## ⚠️ DISCLAIMER  

This project is provided **for educational and research purposes only**.  
Trading in financial markets involves significant risk, including the possible loss of capital.  

- The author is **not responsible for any financial losses** incurred from the use of this project.  
- Use this tool at your own risk and responsibility.  
- Always backtest thoroughly and consult with a financial advisor before using in live markets.  

