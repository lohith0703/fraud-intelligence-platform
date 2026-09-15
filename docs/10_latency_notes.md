# Latency Measurement Notes — Phase 4

## Method
200 sequential POST requests to the running FastAPI /score endpoint,
using Python's `requests` library and `time.perf_counter()` for
wall-clock timing per request.

## Results
Mean:   1.87 ms
P50:    1.75 ms
P95:    2.17 ms
P99:    2.61 ms
Max:    13.94 ms

## Honest scope of this measurement
Measured locally: single machine, single client, sequential (not
concurrent) requests, over loopback (127.0.0.1) -- no real network hop,
no concurrent load, no container network boundary. This measures raw
model + SHAP inference latency inside the FastAPI process, not realistic
production traffic conditions.

## What this number does and doesn't demonstrate
Does demonstrate: the model + explainability computation itself is fast
enough for real-time use (well under typical <100ms production targets
for fraud scoring).
Does NOT demonstrate: latency under concurrent load, real network
conditions, or once deployed behind a real load balancer/container
network. A more complete latency benchmark (concurrent load testing,
e.g. with a tool like locust or k6) is noted as a possible future
improvement if time permits, rather than claimed as already measured.
