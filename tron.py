import requests
import time
from datetime import datetime
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

TRON_API_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=TRX'
IFTTT_WEBHOOKS_URL = #ENTER YOUR IFTTT WEBOOK LINK HERE
DATA_FIXER_URL = 'http://data.fixer.io/api/latest?access_key=e27e604e4721351e0992c09933660458&symbols=USD,NGN&format=1' #FOR CONVERTING USD TO NGN

TRON_UPPER_THRESHOLD = 0.028 
TRON_LOWER_THRESHOLD = 0.024

def get_latest_tron_price():
    parameters = {'convert':'USD'}

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'ENTER KEY HERE',
    }

    response = requests.get(TRON_API_URL, headers=headers, params=parameters)
    response = json.loads(response.text)
    usd_price = round(float(response['data']['TRX']['quote']['USD']['price']), 5) # Get the quote price of Tron in USD and rounds off to 5dp

    response = requests.get(DATA_FIXER_URL)
    response = json.loads(response.text)
    rate = float(response['rates']['NGN']/response['rates']['USD']) #Get the conversion rate of USD to NGN

    ngn_price =  round(usd_price * rate, 2)
    info = ({'USD_PRICE':usd_price, 'NGN_PRICE':ngn_price, 'RATE': 'NGN' + str(round(rate, 2)) + '/USD' })
    return info # e.g 'USD_PRICE':0.23, 'NGN_PRICE':225, 'RATE': '978' 

def post_ifttt_webhook(event, value, last_price):
    # The payload that will be sent to IFTTT service

    if last_price: #Get run on subsequent requests
        change = (((value['USD_PRICE'] - last_price['USD_PRICE']) / value['USD_PRICE']) * 100)
        change = round(change, 5)
        data = {'value1': value['USD_PRICE'], 'value2': value['NGN_PRICE'], 'value3': change}
        ifttt_event_url = IFTTT_WEBHOOKS_URL.format(event)
        requests.post(ifttt_event_url, json=data)
    
    else: #Runs once during the first
        data = {'value1': value['USD_PRICE'], 'value2': value['NGN_PRICE']}
        # inserts our desired event
        ifttt_event_url = IFTTT_WEBHOOKS_URL.format(event)
        # Sends a HTTP POST request to the webhook URL
        requests.post(ifttt_event_url, json=data)


def main(): #main function that runs the app

    last_price = 0 #initiaizing the last price at 0 for a fresh start

    while True: 
        try:
            current_price = get_latest_tron_price()
            
            # Send an emergency notification
            if current_price['USD_PRICE'] >= TRON_UPPER_THRESHOLD or current_price['USD_PRICE'] <= TRON_LOWER_THRESHOLD:
                post_ifttt_webhook(event='tron_price_emergency', value=current_price, last_price=last_price)

            else:
                # Send a Telegram notification
                post_ifttt_webhook(event='tron_price_update', value=current_price, last_price=last_price)
            
            last_price = current_price
            
            print('Done, now waiting for 1 hour!')
            # Sleep for 60 minutes 
            # (For testing purposes you can set it to a lower number)
            time.sleep(60 * 60)

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


if __name__ == '__main__':
    main()