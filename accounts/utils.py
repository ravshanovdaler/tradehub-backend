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
    
    # Try primary exchange rate API
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            rate = data.get('rates', {}).get('UZS')
            if rate:
                _cached_rate = float(rate)
                _last_fetch = now
                return _cached_rate
    except Exception as e:
        print(f"Primary exchange rate API failed: {e}")

    # Fallback to secondary API
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            rate = data.get('rates', {}).get('UZS')
            if rate:
                _cached_rate = float(rate)
                _last_fetch = now
                return _cached_rate
    except Exception as e:
        print(f"Fallback exchange rate API failed: {e}")

    # Set retry cooldown (retry in 5 minutes instead of blocking on every hit)
    _last_fetch = now - CACHE_DURATION + 300
    return _cached_rate

def convert_currency(amount, from_curr, to_curr):
    if amount is None:
        return 0.0
    amount = float(amount)
    from_curr = str(from_curr).upper()
    to_curr = str(to_curr).upper()
    if from_curr == to_curr:
        return amount
    rate = get_usd_to_uzs_rate()
    if from_curr == 'USD' and to_curr == 'UZS':
        return amount * rate
    elif from_curr == 'UZS' and to_curr == 'USD':
        return amount / rate
    return amount
