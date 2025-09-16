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
- **Research Notebooks**: Provides Jupyter notebooks (`PAIRS_TRADING_RESEARCH.ipynb`, `options_strategy.ipynb`) for backtesting and experimentation.  
- **Configurable Environment**: API keys, tokens, and parameters are easily managed through environment files (`.env`, `access_token.env`).  
- **Scalable Design**: Modular code structure (`data_fetching.py`, `execution.py`, `order.py`, etc.) allows easy extension and integration with other strategies.  
