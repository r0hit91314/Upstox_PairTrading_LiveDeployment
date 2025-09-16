import os
import time
import math
import pyotp
import schedule
import logging
import threading
import pandas as pd
import numpy as np
from datetime import datetime, time as dtime
from dotenv import load_dotenv
# upstox libraries
from upstox_client.rest import ApiException 
import upstox_client 
# to fetch access key
from fetch_access_key import set_access_token
# functions to fetch data
from data_fetching import get_instrument_key
from data_fetching import live_data
from data_fetching import market_quote_ltp
from data_fetching import hist_data
from data_fetching import order_book_price
from data_fetching import live_data_queue
# functions to execute order placement
from order import exit_all_positions
from order import buy_portfolio_pairtrading
from order import sell_portfolio_pairtrading
from order import get_positions
# functions to run pair_trading
from pair_trading import trading_day_queue
from pair_trading import prepare_historical_data
# functions to know about user profile
from profile import get_funds_available
from shared_queue import tick_queue




def schedule_token_refresh():
    schedule1 = schedule.Scheduler()
    schedule1.every().day.at("15:35").do(set_access_token)   # 1 min before your 08:35 jobs
    while True:
        schedule1.run_pending()
        time.sleep(1)


def schedule_live_data(ticker1, ticker2, hedge_ratio):
    """Schedules live_data_queue to run everyday at 09:05"""

    schedule2 = schedule.Scheduler()
    # Schedule job for all days
    schedule2.every().day.at("13:52").do(live_data_queue, ticker1, ticker2, hedge_ratio)

    print("Scheduler started... Waiting for next run at 09:05 everyday.")

    # Run loop forever
    while True:
        schedule2.run_pending()
        time.sleep(1)

def run_algotrading(ticker1 , ticker2 , hedge_ratio , window):

    state = {"position": 0}
    schedule3 = schedule.Scheduler()
    schedule3.every().day.at("13:53").do(trading_day_queue
     , ticker1 , ticker2 , hedge_ratio , window , state)

    while True:
        schedule3.run_pending()
        time.sleep(1)
    


# EXECUTION OF THE ALGORITHM
if __name__ == "__main__":
    # set_access_token(api , secret , redirected_url , state_access , mobile_number , pin , otp)
    logging.basicConfig(
    level=logging.DEBUG,  # change to DEBUG if you want more detail
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pairs_trading.log"),
        logging.StreamHandler()
    ]
    )
    # Run both functions asynchronously
    ticker1 = "NHPC"
    ticker2 = "PFC"
    hedge_ratio  = 0.202760
    prepare_historical_data(ticker1 , ticker2 , hedge_ratio)
    t0 = threading.Thread(target=schedule_token_refresh, daemon=True)
    t1 = threading.Thread(target=schedule_live_data , args=(ticker1 , ticker2 , hedge_ratio), daemon=True)
    t2 = threading.Thread(target=run_algotrading, args=(ticker1, ticker2, hedge_ratio, 5), daemon=True)

    t0.start()
    t1.start()
    t2.start()

    # Keep main thread alive
    t1.join()
    t2.join()    

