import os
from dotenv import load_dotenv
import pandas as pd
from upstox_client.rest import ApiException
import upstox_client
import time
from datetime import datetime

path = os.path.abspath("acess_token.env")
load_dotenv(path)

access_token_ = os.getenv("ACCESS_TOKEN")
if not access_token_:
    raise ValueError("ACCESS_TOKEN environment variable is not set.")

def get_funds_available(access_token_):
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token_
    api_version = '2.0'

    api_instance = upstox_client.UserApi(upstox_client.ApiClient(configuration))
    try:
        # Get User Fund And Margin
        api_response = api_instance.get_user_fund_margin(api_version)
        # print(api_response.data)
    except ApiException as e:
        print("Exception when calling UserApi->get_user_fund_margin: %s\n" % e)

    return api_response.data["equity"].available_margin

