import urllib.request
import json
import time

_cached_rate = 12800.0
_last_fetch = 0
CACHE_DURATION = 3600  # cache rate for 1 hour

def get_usd_to_uzs_rate():
    global _cached_rate, _last_fetch
    now = time.time()
    if now - _last_fetch < CACHE_DURATION:
        return _cached_rate
    
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            rate = data.get('rates', {}).get('UZS')
            if rate:
                _cached_rate = float(rate)
                _last_fetch = now
                print(f"Updated cached exchange rate: {rate}")
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        # Keep using the cached_rate (or fallback)
    return _cached_rate

def convert_currency(amount, from_curr, to_curr):
    if amount is None:
        return 0.0
    amount = float(amount)
    if from_curr == to_curr:
        return amount
    rate = get_usd_to_uzs_rate()
    if from_curr == 'USD' and to_curr == 'UZS':
        return amount * rate
    elif from_curr == 'UZS' and to_curr == 'USD':
        return amount / rate
    return amount
