import requests
import json
import time
from decimal import Decimal
from datetime import datetime

# Replace with your own API key and secret
api_key = 'your_api_key'
api_secret = 'your_api_secret'

# Set base URL for Futures API
base_url = 'https://fapi.binance.com'

# Initialize headers for API request
headers = {
    'X-MBX-APIKEY': api_key
}

# Get all USDT pairs on the Futures API
def fetch_usdt_pairs():
    try:
        response = requests.get(f'{base_url}/fapi/v1/ticker/24hr', headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        tickers = response.json()
        return tickers
    except requests.exceptions.RequestException as e:
        print(f"Error fetching USDT pairs: {e}")
        return []

# Fetch open interest data with retries
def fetch_open_interest_with_retry(symbol, retries=1, period='4h'):
    for _ in range(retries):
        try:      
            response = requests.get(f'{base_url}/futures/data/openInterestHist?symbol={symbol}&period={period}', headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = json.loads(response.text)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching open interest data for {symbol}: {e}")
            time.sleep(2)  # Sleep for 2 seconds before retrying
    return None

usdt_pairs = fetch_usdt_pairs()
usdt_pairs_with_marketcap = [{'symbol': ticker['symbol'], 'marketCap': Decimal(ticker['quoteVolume']) * Decimal(ticker['weightedAvgPrice'])} for ticker in usdt_pairs if ticker['symbol'].endswith('USDT')]

# Get top 10 USDT pairs based on market capitalization
sorted_pairs = sorted(usdt_pairs_with_marketcap, key=lambda x: x['marketCap'], reverse=True)
pairs = [pair['symbol'] for pair in sorted_pairs[:500]]

# Define number of candles to compare
num_candles = 2

# Fetch open interest data for each symbol in the top 10 USDT pairs with retries and a specific period
for symbol in pairs:
    data = fetch_open_interest_with_retry(symbol, period='4h')
    if data is not None and len(data) >= num_candles:
        prev_sum = Decimal(data[-num_candles]['sumOpenInterestValue']) / Decimal('1000000')
        prev_timestamp = datetime.fromtimestamp(data[-num_candles]['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        curr_sum = Decimal(data[-1]['sumOpenInterestValue']) / Decimal('1000000')
        curr_timestamp = datetime.fromtimestamp(data[-1]['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        percent_change = (curr_sum - prev_sum) / prev_sum * 100
        if percent_change > 20:
            print(f'{symbol} has increased by {percent_change}% from {prev_sum} at {prev_timestamp} to {curr_sum} at {curr_timestamp}')
        elif percent_change < -20:
            print(f'{symbol} has decreased by {abs(percent_change)}% from {prev_sum} at {prev_timestamp} to {curr_sum} at {curr_timestamp}')
