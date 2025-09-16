from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os
import pyotp
import upstox_client
from upstox_client.rest import ApiException



def set_access_token():
    # LOADING VARIABLES
    path = os.path.abspath("a.env")
    load_dotenv(path)

    api = os.getenv("API_KEY")
    secret = os.getenv("SECRET_KEY")
    redirected_url = os.getenv("REDIRECTED_URL")
    state = "Rohit"
    mobile_number = os.getenv("MY_MOBILE_NUMBER")
    pin = os.getenv("MY_PIN")
    totp_secret = os.getenv("TOTP_KEY")
    totp = pyotp.TOTP(totp_secret)
    otp = totp.now()
    # check if variables are loaded correctly
    if not all([api, secret, redirected_url , mobile_number , pin , otp]):
        raise ValueError("One or more environment variables are missing or not loaded correctly.")
    else:
        print("Environment variables loaded successfully.")

    #################################################################################################################################################### 
    url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api}&redirect_uri={redirected_url}&state={state}"
    driver = webdriver.Chrome()
    driver.get(url)

    # 1. Enter mobile number
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "mobileNum"))).send_keys(mobile_number)
    # 2. Click "Get OTP"
    driver.find_element(By.ID, "getOtp").click()
    # 3. Wait for OTP input and then enter OTP (OTP managed manually or via TOTP)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "otpNum"))).send_keys(otp)
    # 4. Click continue after OTP
    driver.find_element(By.ID, "continueBtn").click()
    # 5. Wait for PIN input (if required), enter it
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "pinCode"))).send_keys(pin)
    # 6. Click the final continue to complete login
    driver.find_element(By.ID, "pinContinueBtn").click()
    # Now you're logged in and can proceed.
    WebDriverWait(driver, 30).until(lambda d: redirected_url in d.current_url)
    # 8. Get the full redirected URL as string
    final_url = driver.current_url
    
    if "code=" not in final_url:
            driver.quit()
            raise ValueError("Login failed or redirected URL does not contain authorization code.")
    auth_code = final_url[final_url.index("code=") + 5:final_url.index("&state=")]
    driver.quit()

    env_file="a.env"

    # Read existing env file
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add AUTH_CODE
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("AUTH_CODE="):
            lines[i] = f"AUTH_CODE={auth_code}\n"
            updated = True
            break
    if not updated:
        lines.append(f"\nAUTH_CODE={auth_code}\n")

    # Write back to file
    with open(env_file, "w") as f:
        f.writelines(lines)

    print(f"AUTH_CODE updated in {env_file}")

    api_instance = upstox_client.LoginApi()
    api_version = '2.0'
    code = auth_code
    client_id = api
    client_secret = secret
    redirect_uri = redirected_url
    grant_type = 'authorization_code'

    fetched_access_token = False
    try:
        # Get token API
        api_response = api_instance.token(api_version, code=code, client_id=client_id, client_secret=client_secret,
                                            redirect_uri=redirect_uri, grant_type=grant_type)
        access_token = api_response.access_token
        fetched_access_token = True

    except ApiException as e:
        print("Exception when calling LoginApi->token: %s\n" % e)

    with open("acess_token.env", "w") as f:
        f.write(f"ACCESS_TOKEN={access_token}\n") 

    if fetched_access_token:
        print("ACCESS KEY SAVED SUCCESSFULLY")       

    return


set_access_token()