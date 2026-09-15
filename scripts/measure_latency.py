import time
import requests
import numpy as np

URL = "http://127.0.0.1:8000/score"

payload = {
    "transaction_id": 5115795,
    "type": "TRANSFER",
    "amount": 7360.15,
    "account_velocity": 1,
    "amount_deviation": 0.0,
    "balance_mismatch": False,
    "is_new_destination": True,
    "dest_velocity": 1
}

N_REQUESTS = 200
latencies_ms = []

print(f"Sending {N_REQUESTS} requests to {URL}...")

for i in range(N_REQUESTS):
    start = time.perf_counter()
    response = requests.post(URL, json=payload)
    end = time.perf_counter()
    if response.status_code != 200:
        print(f"Request {i} failed: {response.status_code}")
        continue
    latencies_ms.append((end - start) * 1000)

latencies_ms = np.array(latencies_ms)

print(f"\nCompleted {len(latencies_ms)} successful requests")
print(f"Mean latency:   {latencies_ms.mean():.2f} ms")
print(f"P50 (median):   {np.percentile(latencies_ms, 50):.2f} ms")
print(f"P95 latency:    {np.percentile(latencies_ms, 95):.2f} ms")
print(f"P99 latency:    {np.percentile(latencies_ms, 99):.2f} ms")
print(f"Max latency:    {latencies_ms.max():.2f} ms")