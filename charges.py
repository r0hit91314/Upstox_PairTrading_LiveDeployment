import os
from dotenv import load_dotenv
import pandas as pd
import upstox_client
from upstox_client.rest import ApiException
from data_fetching import market_quote_ltp
from data_fetching import get_instrument_key
from data_fetching import get_lot_size

# path = os.path.abspath("acess_token.env")
# load_dotenv(path)


# access_token = os.getenv("ACCESS_TOKEN")
# if not access_token:
#     raise ValueError("ACCESS_TOKEN environment variable is not set.")



def charges_delivery(access_token , ticker , quantity , price_):
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_version = '2.0'

    api_instance = upstox_client.ChargeApi(upstox_client.ApiClient(configuration))
    instrument_token = get_instrument_key(ticker , "equity")
    quantity = quantity          # quantity to buy or sell
    product = 'D'                 # 'D'- delivery
    transaction_type  = "BUY"     # enter "SELL" , if you want to sell
    price = price_                # price at which you want the trade


    try:
        # Brokerage details
        api_response = api_instance.get_brokerage(instrument_token, quantity, product, transaction_type, price, api_version)
        print(api_response)
    except ApiException as e:
        print("Exception when calling ChargeApi->get_brokerage: %s\n" % e)
        return (quantity*price_*0.0015) # if api call fails assume the charge to be 0.15% of the total value

    return api_response.data.charges.total

def margins(access_token , ticker , quantity_):          # ONLY FOR COMPUTING MARGINS FOR  FUTURES
    lot_size = get_lot_size(ticker)
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_instance = upstox_client.ChargeApi(upstox_client.ApiClient(configuration))
    instruments = [upstox_client.Instrument(instrument_key= get_instrument_key(ticker , "futures"),quantity=(quantity_*lot_size),product="D",transaction_type="BUY")]
    margin_body = upstox_client.MarginRequest(instruments)
    try:
        api_response = api_instance.post_margin(margin_body)
    except ApiException as e:
        print("Exception when calling Margin API: %s\n" % e.body)

    margin = api_response.data.final_margin
    return margin    

def margins_intraday(access_token , ticker , quantity_):           # ONLY FOR COMPUTING MARGINS FOR INTRADAY
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_instance = upstox_client.ChargeApi(upstox_client.ApiClient(configuration))
    instruments = [upstox_client.Instrument(instrument_key= get_instrument_key(ticker , "equity"),quantity=quantity_,product="I",transaction_type="BUY")]
    margin_body = upstox_client.MarginRequest(instruments)
    try:
        api_response = api_instance.post_margin(margin_body)
    except ApiException as e:
        print("Exception when calling Margin API: %s\n" % e.body)

    margin = api_response.data.final_margin
    return margin    


