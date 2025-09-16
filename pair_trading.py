import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from upstox_client.rest import ApiException 
import upstox_client 
from data_fetching import get_instrument_key
from data_fetching import live_data
from data_fetching import market_quote_ltp
from data_fetching import hist_data
from data_fetching import order_book_price
from order import exit_all_positions
from order import buy_portfolio_pairtrading
from order import sell_portfolio_pairtrading
from profile import get_funds_available
from order import get_positions
from charges import margins_intraday
from shared_queue import tick_queue
from data_fetching import live_data_queue
from datetime import datetime
import time
import threading
import math
import schedule
import logging


path = os.path.abspath("acess_token.env")
load_dotenv(path)


access_token = os.getenv("ACCESS_TOKEN")
if not access_token:
    raise ValueError("ACCESS_TOKEN environment variable is not set.")

# TO FETCH AND PREPARE HISTORICAL DATA AND MAKE EXECUTION ON THE FIRST DAY
def prepare_historical_data(ticker1 , ticker2 , hedge_ratio):
    tickers = [ticker1 , ticker2]
    ticker_data = {}
    for ticker in tickers:
        today = pd.Timestamp.today().strftime("%Y-%m-%d")
        dt = pd.to_datetime(today)
        ten_days_before = (dt - pd.Timedelta(days=20)).strftime("%Y-%m-%d")
        ticker_data[ticker] = hist_data(get_instrument_key(ticker, "equity"),"days","1" , today, ten_days_before)

    daily_data = pd.DataFrame()
    for ticker in tickers:
        daily_data[f"{ticker}"] = ticker_data[ticker].Open

    daily_data.index = daily_data[ticker1].index
    daily_data.index = pd.to_datetime(daily_data.index , format="%Y-%m-%d")
    daily_data.sort_index(inplace=True)
    daily_data["spread"] = daily_data[ticker1] - hedge_ratio * daily_data[ticker2]

    window = 5
    daily_data["mean_spread"] = daily_data["spread"].rolling(window).mean()
    daily_data["std_spread"] = daily_data["spread"].rolling(window).std()
    daily_data["z_score"] = (daily_data["spread"] - daily_data["mean_spread"]) / daily_data["std_spread"]
    daily_data.dropna(inplace=True)

    daily_data.to_csv("final_pairs_data.csv")

    return

# TO UPDATE EVERY DAY'S OPENING DATA OF PAIRS AND COMPUTING METRICES 
def update_pairs_data(access_token , ticker1 , ticker2 , hedge_ratio , window):
    daily_data = pd.read_csv("final_pairs_data.csv")
    price_ticker1 = market_quote_ltp(access_token, ticker1)
    price_ticker2 = market_quote_ltp(access_token, ticker2)
    current_spread = price_ticker1 - (hedge_ratio * price_ticker2)
    spread_array = np.array(daily_data["spread"][-(window-1):])
    spread_array = np.append(spread_array, current_spread)
    mean = spread_array.mean()
    std = spread_array.std(ddof=1)
    z_score_entry = (current_spread - mean) / std
    new_row = pd.DataFrame([{
        "TimeStamp": pd.Timestamp.now(),  
        f"{ticker1}": price_ticker1,
        f"{ticker2}": price_ticker2,
        "spread": current_spread,
        "mean_spread": mean,
        "std_spread": std,
        "z_score": z_score_entry
    }])
    new_row = pd.DataFrame(new_row)
    new_row.to_csv("final_pairs_data.csv", mode="a", header=False, index=False)

    return mean , std , z_score_entry


def trading_day(access_token , ticker1, ticker2, hedge_ratio, window, state):
    logging.info("Starting a new trading day")

    try:
        mean, std, z_score_entry = update_pairs_data(ticker1, ticker2, hedge_ratio, window)
    except Exception as e:
        logging.error(f"Failed to update pairs data: {e}")
        return

    # Entry signal check
    if state["position"] == 0:
        if z_score_entry > 1:
            logging.info(f"Initial Position: Short Spread at Z-Score {z_score_entry:.2f}")
            state["position"] = -1
        elif z_score_entry < -1:
            logging.info(f"Initial Position: Long Spread at Z-Score {z_score_entry:.2f}")
            state["position"] = 1

    if state["position"] != 0:
        logging.info(f"Entering position: {'Short' if state['position'] == -1 else 'Long'} "
                     f"Spread at Z-Score {z_score_entry:.2f}")
        try:
            amount = get_funds_available(access_token)
            entry_price_y = order_book_price(access_token, ticker1,
                                             f"{'buy' if state['position'] == -1 else 'sell'}")
            entry_price_x = order_book_price(access_token, ticker2,
                                             f"{'buy' if state['position'] == 1 else 'sell'}")
        except Exception as e:
            logging.error(f"Order book fetch failed: {e}")

        amount = 100000     # JUST FOR DRY RUNNING NEED TO REMOVE IN REAL CODE 
        n = math.floor((amount * 0.8) / (entry_price_y + hedge_ratio * entry_price_x))
        shares_y = n
        shares_x = math.floor(hedge_ratio * n)
        logging.info(f"Calculated position size: {shares_y} shares of {ticker1}, {shares_x} shares of {ticker2}")

        if state["position"] == 1:
            logging.info(f"Executing Long Spread: Buying {ticker1}, Selling {ticker2}")
            try:
                buy_portfolio_pairtrading(access_token, shares_y, shares_x, ticker1, ticker2)
            except Exception as e:
                logging.error(f"Error while executing Long Spread for {ticker1}-{ticker2}: {e}")

        elif state["position"] == -1:
            logging.info(f"Executing Short Spread: Selling {ticker1}, Buying {ticker2}")
            try:
                sell_portfolio_pairtrading(access_token, shares_y, shares_x, ticker1, ticker2)
            except Exception as e:
                logging.error(f"Error while executing Short Spread for {ticker1}-{ticker2}: {e}")

    else:
        logging.info("No entry signal today.")

    # Intraday monitoring loop
    while True:
        current_time = datetime.now().time()
        if current_time >= datetime.strptime("15:13:00", "%H:%M:%S").time():
            logging.info("Exiting all positions before market close")
            try:
                exit_all_positions(access_token)
            except Exception as e:
                logging.error(f"Error while exiting positions: {e}")
            break

        try:
            df = pd.read_csv("live_data.csv")
            y_price = df["ticker1_y"].iloc[-1]
            x_price = df["ticker2_x"].iloc[-1]
            current_spread = y_price - (hedge_ratio * x_price)
            z_score = (current_spread - mean) / std
            logging.debug(f"y_price={y_price:.2f}, x_price={x_price:.2f}, "
                          f"spread={current_spread:.2f}, z_score={z_score:.2f}")
        except Exception as e:
            logging.error(f"Failed to fetch live prices: {e}")
            time.sleep(10)
            continue

        if (state["position"] == 1 and z_score >= 0) or (state["position"] == -1 and z_score <= 0):
            logging.info(f"Exiting {'Long' if state['position'] == 1 else 'Short'} "
                         f"Spread Position at Z-Score {z_score:.2f}")
            try:
                exit_all_positions(access_token)
            except Exception as e:
                logging.error(f"Error while exiting position: {e}")
            state["position"] = 0
            break

        time.sleep(10)

    return    


def trading_day_queue(ticker1, ticker2, hedge_ratio, window, state):

    path = os.path.abspath("acess_token.env")
    load_dotenv(path)
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise ValueError("ACCESS_TOKEN environment variable is not set.")
    logging.info("Starting a new trading day")

    try:
        mean, std, z_score_entry = update_pairs_data(access_token , ticker1, ticker2, hedge_ratio, window)
    except Exception as e:
        logging.error(f"Failed to update pairs data: {e}")
        return

    # Entry signal check
    if state["position"] == 0:
        if z_score_entry > 1:
            logging.info(f"Initial Position: Short Spread at Z-Score {z_score_entry:.2f}")
            state["position"] = -1
        elif z_score_entry < -1:
            logging.info(f"Initial Position: Long Spread at Z-Score {z_score_entry:.2f}")
            state["position"] = 1

    if state["position"] != 0:
        logging.info(f"Entering position: {'Short' if state['position'] == -1 else 'Long'} "
                     f"Spread at Z-Score {z_score_entry:.2f}")
        try:
            amount = get_funds_available(access_token)
            entry_price_y = margins_intraday(access_token , ticker1 , 1 )
            entry_price_x = margins_intraday(access_token , ticker2 , 1)
        except Exception as e:
            logging.error(f"Order book fetch failed: {e}")

        # amount = 20000     # JUST FOR DRY RUNNING NEED TO REMOVE IN REAL CODE 
        n = math.floor((amount * 0.5) / (entry_price_y + hedge_ratio * entry_price_x))
        shares_y = n
        shares_x = math.floor(hedge_ratio * n)
        logging.info(f"Calculated position size: {shares_y} shares of {ticker1}, {shares_x} shares of {ticker2}")

        if state["position"] == 1:
            logging.info(f"Executing Long Spread: Buying {ticker1}, Selling {ticker2}")
            try:
                buy_portfolio_pairtrading(access_token, shares_y, shares_x, ticker1, ticker2)
            except Exception as e:
                logging.error(f"Error while executing Long Spread for {ticker1}-{ticker2}: {e}")

        elif state["position"] == -1:
            logging.info(f"Executing Short Spread: Selling {ticker1}, Buying {ticker2}")
            try:
                sell_portfolio_pairtrading(access_token, shares_y, shares_x, ticker1, ticker2)
            except Exception as e:
                logging.error(f"Error while executing Short Spread for {ticker1}-{ticker2}: {e}")

    else:
        logging.info("No entry signal today.")

    # Intraday monitoring loop
    while True:
        current_time = datetime.now().time()
        if current_time >= datetime.strptime("15:00:00", "%H:%M:%S").time():
            logging.info("Exiting all positions before market close")
            try:
                if state["position"] == 1:
                    sell_portfolio_pairtrading(access_token , shares_y , shares_x , ticker1 , ticker2)
                elif state["position"] == -1:
                    buy_portfolio_pairtrading(access_token , shares_y , shares_x , ticker1 , ticker2)
                else:
                    print("No current position to exit.")
            except Exception as e:
                logging.error(f"Error while exiting positions: {e}")
            break

        try:
            
            tick = tick_queue.get(timeout=6)   # blocking read with timeout
            y_price = tick["ticker1_y"]
            x_price = tick["ticker2_x"]
            current_spread = y_price - (hedge_ratio * x_price)
            z_score = (current_spread - mean) / std
            logging.debug(f"y_price={y_price:.2f}, x_price={x_price:.2f}, "
                          f"spread={current_spread:.2f}, z_score={z_score:.2f}")
        except Exception as e:
            logging.error(f"Failed to fetch live prices: {e}")
            time.sleep(10)
            continue

        if (state["position"] == 1 and z_score >= 0) or (state["position"] == -1 and z_score <= 0):
            logging.info(f"Exiting {'Long' if state['position'] == 1 else 'Short'} "
                         f"Spread Position at Z-Score {z_score:.2f}")
            try:
                if state["position"] == 1:
                    sell_portfolio_pairtrading(access_token , shares_y , shares_x , ticker1 , ticker2)
                else:
                    buy_portfolio_pairtrading(access_token , shares_y , shares_x , ticker1 , ticker2)
            except Exception as e:
                logging.error(f"Error while exiting position: {e}")
            state["position"] = 0
            break

        time.sleep(10)

    return    
