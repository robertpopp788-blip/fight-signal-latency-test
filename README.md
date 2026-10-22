# Fight Signal — Read-only Kalshi latency test

This is **not** the Fight Signal trading application. It contains no API credentials and cannot submit orders.

## Render setup
- Source repository: `robertpopp788-blip/fight-signal-latency-test`
- Branch: `main`
- Runtime: Python 3
- Region: Ohio (US East)
- Instance: Free
- Build command: `echo "No dependencies"`
- Start command: `python app.py`

Once deployed, visit `https://YOUR-RENDER-URL/benchmark` for 15 serialized, public read-only HTTPS response-time samples. It may take ~3–80 seconds depending on connectivity. The free tier may sleep and the first request may have a cold-start delay.

This **does not** determine end-to-end courtside latency. The test creates a fresh HTTPS connection for each sample; a trading client often reuses connections. Do not use these measurements to claim a fill-speed advantage.

Compare with a local benchmark against the same public endpoint, and later compare persistent connections and phone-to-server latency.
