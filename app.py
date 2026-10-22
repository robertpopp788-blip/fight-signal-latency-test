"""Read-only Kalshi REST connection benchmark; no credentials or trading."""
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = "https://external-api.kalshi.com/trade-api/v2/exchange/status"
MAX_SAMPLES = 15

def benchmark():
    measurements = []
    errors = []
    for _ in range(MAX_SAMPLES):
        start = time.perf_counter()
        req = urllib.request.Request(TARGET, headers={"User-Agent": "FightSignal-ReadOnly-Latency-Test/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read(4096)
                if resp.status != 200:
                    raise RuntimeError("Unexpected HTTP status " + str(resp.status))
            measurements.append(round((time.perf_counter() - start) * 1000, 2))
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError) as exc:
            errors.append(type(exc).__name__)
        time.sleep(0.2)
    values = sorted(measurements)
    return {
        "target": TARGET,
        "region": os.getenv("RENDER_REGION", "not supplied"),
        "sample_count": len(values),
        "failures": len(errors),
        "median_ms": round(statistics.median(values), 2) if values else None,
        "p95_ms": values[min(len(values)-1, int(0.95*(len(values)-1)+0.999))] if values else None,
        "min_ms": values[0] if values else None,
        "max_ms": values[-1] if values else None,
        "samples_ms": values,
        "notes": "Read-only public REST endpoint. New HTTPS connection per sample; not order latency or matching-engine location."
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health", "/benchmark"):
            self.send_error(404)
            return
        if self.path == "/benchmark":
            data = benchmark()
        else:
            data = {"service": "Fight Signal Ohio latency test", "read_only": True, "ready": True,
                    "benchmark_path": "/benchmark"}
        raw = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
