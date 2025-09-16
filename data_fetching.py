import os
from dotenv import load_dotenv
import pandas as pd
import upstox_client
from upstox_client.rest import ApiException
from shared_queue import tick_queue
from datetime import datetime, time as dtime
import time

path = os.path.abspath("acess_token.env")
load_dotenv(path)


access_token = os.getenv("ACCESS_TOKEN")
if not access_token:
    raise ValueError("ACCESS_TOKEN environment variable is not set.")


def hist_data(instrument_key , interval , interval_unit , end , start ):
  apiInstance = upstox_client.HistoryV3Api()
  try:
    response = apiInstance.get_historical_candle_data1(instrument_key, interval, interval_unit,end,start)
  except Exception as e:
    print("Exception when calling HistoryV3Api->get_historical_candle_data1: %s\n" % e)
    
  data = response.data.candles
  data = pd.DataFrame(data , columns=["TimeStamp" , "Open" , "High" , "Low" , "Close" , "Volume" , "OpenIntrest"])
  data["TimeStamp"] = pd.to_datetime(data["TimeStamp"])
  data.set_index("TimeStamp" , inplace=True)
  data.sort_index(inplace= True)
  return data  

def intraday_data(instrument_key , interval , interval_unit):
  apiInstance = upstox_client.HistoryV3Api()
  try:
    response = apiInstance.get_intra_day_candle_data(instrument_key, interval, interval_unit)
  except Exception as e:
    print("Exception when calling HistoryV3Api->get_intra_day_candle_data: %s\n" % e)
  data = response.data.candles
  data = pd.DataFrame(data , columns=["TimeStamp" , "Open" , "High" , "Low" , "Close" , "Volume" , "OpenIntrest"])
  data["TimeStamp"] = pd.to_datetime(data["TimeStamp"])
  data.set_index("TimeStamp" , inplace=True)
  data.sort_index(inplace= True)
  return data  


def get_instrument_key(ticker , segment):
  df = pd.read_json(r"https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz")
  if segment == "equity":
    ticker_df = df[df["trading_symbol"] == ticker]
    instrument_key = ticker_df["instrument_key"].values[0]
  else:
     today = datetime.now()
     day_of_month = today.day
     ticker_df = df[df["asset_symbol"] == ticker]
     ticker_df = ticker_df[ticker_df["instrument_type"] == "FUT"]
     if day_of_month < 15:
      instrument_key = ticker_df["instrument_key"].values[0]
     else:
      instrument_key = ticker_df["instrument_key"].values[1]
  return instrument_key   

def get_lot_size(ticker):
  df = pd.read_json(r"https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz")
  today = datetime.now()
  ticker_df = df[df["asset_symbol"] == ticker]
  ticker_df = ticker_df[ticker_df["instrument_type"] == "FUT"]
  lot_size = ticker_df["lot_size"].values[0]

  return lot_size
  
   
    

def market_quote_ltp(access_token , ticker):
  configuration = upstox_client.Configuration()
  configuration.access_token = access_token

  apiInstance = upstox_client.MarketQuoteV3Api(upstox_client.ApiClient(configuration))
  try:
      # For a single instrument
      response = apiInstance.get_ltp(instrument_key=get_instrument_key(ticker , "equity"))
  except ApiException as e:
      print("Exception when calling MarketQuoteV3Api->get_ltp: %s\n" % e)

  name = list(response.data.keys())[0]  
  return response.data[name].last_price


def order_book_price(access_token , ticker , order_type):

  configuration = upstox_client.Configuration()
  configuration.access_token = access_token
  api_version = '2.0'

  symbol = get_instrument_key(ticker , "equity")
  api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))


  try:
      api_response = api_instance.get_full_market_quote(symbol, api_version)
  except ApiException as e:
      print("Exception when calling MarketQuoteApi->get_full_market_quote: %s\n" % e)

  symbol_key = list(api_response.data.keys())[0]
  buy_price = api_response.data[f"{symbol_key}"].depth.sell[0].price
  sell_price =  api_response.data[f"{symbol_key}"].depth.buy[0].price 
  if order_type == "buy":
     return buy_price
  return sell_price   




def live_data( ticker1 , ticker2 , hedge_ratio):

  path = os.path.abspath("acess_token.env")
  load_dotenv(path)
  access_token = os.getenv("ACCESS_TOKEN")
  if not access_token:
    raise ValueError("ACCESS_TOKEN environment variable is not set.")
  
  configuration = upstox_client.Configuration()
  configuration.access_token = access_token

  streamer = upstox_client.MarketDataStreamerV3(
      upstox_client.ApiClient(configuration)
  )

  instrument_key1 = get_instrument_key(ticker1 , "equity")
  instrument_key2 = get_instrument_key(ticker2 , "equity")

  df_new = pd.DataFrame(columns=["timestamp", "ticker1_y", "ticker2_x"])
  df_new.to_csv("live_data.csv", index=False)  # Create CSV with headers


  # store latest prices
  latest_prices = {instrument_key1: None, instrument_key2: None}

  def on_open():
      streamer.subscribe([instrument_key1, instrument_key2], "ltpc")

  def on_message(message):
      data = message.get("feeds", {})
      for key, val in data.items():
          ltp = val.get("ltpc", {}).get("ltp")
          latest_prices[key] = ltp

      # Only print when both are available
      if latest_prices[instrument_key1] is not None and latest_prices[instrument_key2] is not None:
          

          rows = []

          rows.append({
              "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "ticker1_y": latest_prices[instrument_key1],
              "ticker2_x": latest_prices[instrument_key2],
              
          })

          # Append new rows to CSV
          if rows:
              df_new = pd.DataFrame(rows)
              df_new.to_csv("live_data.csv", mode="a", header=False, index=False)

          time.sleep(5)    

  streamer.on("open", on_open)
  streamer.on("message", on_message)
  streamer.connect()



def live_data_queue(ticker1 , ticker2 , hedge_ratio):
    
    path = os.path.abspath("acess_token.env")
    load_dotenv(path)
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise ValueError("ACCESS_TOKEN environment variable is not set.")
    
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token

    streamer = upstox_client.MarketDataStreamerV3(
        upstox_client.ApiClient(configuration)
    )

    instrument_key1 = get_instrument_key(ticker1 , "equity")
    instrument_key2 = get_instrument_key(ticker2 , "equity")

    latest_prices = {instrument_key1: None, instrument_key2: None}

    def on_open():
        streamer.subscribe([instrument_key1, instrument_key2], "ltpc")

    def on_message(message):
        # Exit condition -> 15:16
        if datetime.now().time() >= dtime(15, 15):
            print("Market close. Disconnecting stream...")
            streamer.disconnect()
            return

        data = message.get("feeds", {})
        for key, val in data.items():
            ltp = val.get("ltpc", {}).get("ltp")
            latest_prices[key] = ltp

        if latest_prices[instrument_key1] and latest_prices[instrument_key2]:
            tick = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker1_y": latest_prices[instrument_key1],
                "ticker2_x": latest_prices[instrument_key2],
            }
            tick_queue.put(tick)
            time.sleep(5)    

    streamer.on("open", on_open)
    streamer.on("message", on_message)
    streamer.connect()




