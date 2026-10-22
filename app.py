"""Read-only Kalshi REST connection benchmark; no credentials or trading."""
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

PING_PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fight Signal Phone Latency</title><style>body{font:16px system-ui;background:#0b1424;color:#eaf2ff;max-width:550px;margin:40px auto;padding:16px}button{padding:14px 24px;background:#2776e8;color:white;border:0;border-radius:8px;font-size:17px}pre{white-space:pre-wrap;background:#16243a;padding:16px;border-radius:10px}</style></head><body><h2>Fight Signal — Phone to Ohio</h2><p>Switch off Wi-Fi to test cellular. Wait for the service to wake up before measuring.</p><button id="go">Run 30 pings</button><pre id="out">Ready</pre><script>document.getElementById("go").onclick=async()=>{let out=document.getElementById("out"),vals=[],fail=0;out.textContent="Testing...";for(let i=0;i<30;i++){let t=performance.now();try{let r=await fetch("/ping?i="+i+"&t="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error(r.status);await r.arrayBuffer();vals.push(performance.now()-t)}catch(e){fail++}out.textContent="Completed "+(i+1)+"/30";await new Promise(r=>setTimeout(r,150))}vals.sort((a,b)=>a-b);let p=q=>vals.length?vals[Math.ceil(q*vals.length)-1].toFixed(1):"n/a";out.textContent="Phone → Ohio → Phone (HTTPS)\\nSamples: "+vals.length+" | Failures: "+fail+"\\nMedian: "+p(.5)+" ms\\nP95: "+p(.95)+" ms\\nMin: "+p(1/vals.length)+" ms\\nMax: "+p(1)+" ms\\n\\nNote: browser HTTP timing, not ICMP ping or trading order latency. Free Render cold starts can skew results."};</script></body></html>"""

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
        path = urlsplit(self.path).path
        if path not in ("/", "/health", "/benchmark", "/ping", "/phone-test"):
            self.send_error(404)
            return
        if path == "/phone-test":
            raw = PING_PAGE.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/ping":
            raw = b"ok"
            content_type = "text/plain"
        elif path == "/benchmark":
            data = benchmark()
            raw = json.dumps(data).encode("utf-8")
            content_type = "application/json"
        else:
            data = {"service": "Fight Signal Ohio latency test", "read_only": True, "ready": True,
                    "benchmark_path": "/benchmark", "phone_test_path": "/phone-test"}
            raw = json.dumps(data).encode("utf-8")
            content_type = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
