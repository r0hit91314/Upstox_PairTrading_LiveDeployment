import os
from dotenv import load_dotenv
import pandas as pd
from upstox_client.rest import ApiException
import upstox_client
from data_fetching import get_instrument_key
from data_fetching import market_quote_ltp
from data_fetching import get_lot_size
import time
from datetime import datetime

# path = os.path.abspath("acess_token.env")
# load_dotenv(path)

# access_token_ = os.getenv("ACCESS_TOKEN")
# if not access_token_:
#     raise ValueError("ACCESS_TOKEN environment variable is not set.")

def placing_order(access_token_ , quantity_  , ticker , trans_type="BUY"):
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token_
    api_instance = upstox_client.OrderApiV3(upstox_client.ApiClient(configuration))
    body = upstox_client.PlaceOrderV3Request(quantity= quantity_, product="I", validity="DAY", 
        price= 0, tag="string", instrument_token= get_instrument_key(ticker , "equity"), 
        order_type="MARKET", transaction_type= trans_type, disclosed_quantity=0, 
        trigger_price=0.0, is_amo=False, slice=True)

    try:
        api_response = api_instance.place_order(body)
    except ApiException as e:
        print("Exception when calling OrderApiV3->place_order: %s\n" % e)

    return api_response.status

def exit_all_positions(access_token_):
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token_
    api_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))

    try:
        api_response = api_instance.exit_positions()
        print(api_response)
    except ApiException as e:
        print("Exception when calling OrderApi->exit all positions: %s\n" % e.body)

    return

def get_positions(access_token_):

    configuration = upstox_client.Configuration()
    configuration.access_token = access_token_
    api_version = '2.0'

    api_instance = upstox_client.PortfolioApi(upstox_client.ApiClient(configuration))

    try:
        api_response = api_instance.get_positions(api_version)
    except ApiException as e:
        print("Exception when calling ChargeApi->get_brokerage: %s\n" % e)

    return api_response.data


def buy_portfolio_pairtrading(access_token_ , shares_y , shares_x , ticker1 , ticker2):
    
    status_y = placing_order(access_token_ , shares_y , ticker1)
    time.sleep(2)
    status_x = placing_order(access_token_ , shares_x , ticker2 , trans_type= "SELL")
    # TO CONFIRM ALL POSITIONS ARE PLACED
    if status_y == "success" and status_x == "success":
        print("portfolio bought successfuly")
    else:
        print("one or more than one order failed.")
    return

def sell_portfolio_pairtrading(access_token_ , shares_y , shares_x , ticker1 , ticker2):
    
    status_y = placing_order(access_token_ , shares_y , ticker1 ,  trans_type= "SELL")
    time.sleep(2)
    status_x = placing_order(access_token_ , shares_x , ticker2)
    # TO CONFIRM ALL POSITIONS ARE PLACED
    if status_y == "success" and status_x == "success":
        print("portfolio bought successfuly")
    else:
        print("one or more than one order failed.")
    return


