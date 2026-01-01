import requests
import json

domains = ["www.shikharamschoolofarts.com"]

for d in domains:
    print(f"\n--- Testing {d} ---")
    
    # 1. Generic Gateway (What we currently use)
    print("1. rdap.org:")
    try:
        r = requests.get(f"https://rdap.org/domain/{d}", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Success")
        else:
            print(f"Fail: {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Authoritative (Verisign for .com)
    print("2. rdap.verisign.com:")
    try:
        r = requests.get(f"https://rdap.verisign.com/com/v1/domain/{d}", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Success")
            # Print events to verify date presence
            data = r.json()
            events = data.get('events', [])
            for e in events:
                print(f" - {e['eventAction']}: {e['eventDate']}")
        else:
            print(f"Fail: {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
