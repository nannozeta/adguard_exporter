from flask import Flask, Response
import requests
import json
import os
import time
import threading
from dotenv import load_dotenv
from prometheus_client import (
    CollectorRegistry, Gauge, Counter, Histogram,
    generate_latest, CONTENT_TYPE_LATEST
)

load_dotenv()

ADGUARD_HOST = os.getenv("ADGUARD_HOST", "http://localhost")
ADGUARD_USER = os.getenv("ADGUARD_USER", "")
ADGUARD_PASS = os.getenv("ADGUARD_PASS", "")
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 10))

app = Flask(__name__)
registry = CollectorRegistry()

# METRICS
# General stats
dns_queries_total = Counter("adguard_dns_queries_total", "Total DNS queries", registry=registry)
blocked_filtering_total = Counter("adguard_blocked_filtering_total", "Total blocked queries", registry=registry)
parental_filtered_total = Counter("adguard_parental_filtered_total", "Total parental filtered queries", registry=registry)
avg_processing_time = Gauge("adguard_avg_processing_time", "Average DNS processing time", registry=registry)

# Histogram per jam
dns_queries_hourly = Histogram("adguard_dns_queries_per_hour", "DNS Queries Per Hour", buckets=[1, 10, 100, 500, 1000, 2000], registry=registry)
blocked_queries_hourly = Histogram("adguard_blocked_queries_per_hour", "Blocked Queries Per Hour", buckets=[1, 10, 100, 500, 1000], registry=registry)

# Per-domain
top_domains = Gauge("adguard_top_queried_domain", "Top queried domain", ['domain'], registry=registry)
top_blocked_domains = Gauge("adguard_top_blocked_domain", "Top blocked domain", ['domain'], registry=registry)

# Per-client
top_clients = Gauge("adguard_top_clients", "Top DNS Clients", ['client'], registry=registry)

# Per-upstream
top_upstreams = Gauge("adguard_top_upstreams", "Top upstream DNS", ['upstream'], registry=registry)
top_upstream_avg = Gauge("adguard_upstream_avg_response_time", "Upstream average response time", ['upstream'], registry=registry)

# Status flags
protection_enabled = Gauge("adguard_protection_enabled", "AdGuard protection status", registry=registry)
adguard_running = Gauge("adguard_running", "AdGuard running status", registry=registry)

# Function to get AdGuard data
def fetch_data():
    try:
        # Auth
        auth = (ADGUARD_USER, ADGUARD_PASS) if ADGUARD_USER else None

        stats = requests.get(f"{ADGUARD_HOST}/control/stats", auth=auth).json()
        status = requests.get(f"{ADGUARD_HOST}/control/status", auth=auth).json()

        # Global stats
        dns_queries_total._value.set(stats['num_dns_queries'])
        blocked_filtering_total._value.set(stats['num_blocked_filtering'])
        parental_filtered_total._value.set(stats['num_replaced_parental'])
        avg_processing_time.set(stats['avg_processing_time'])

        # Histogram update
        for hour_count in stats['dns_queries']:
            dns_queries_hourly.observe(hour_count)
        for hour_count in stats['blocked_filtering']:
            blocked_queries_hourly.observe(hour_count)

        # Top domains
        top_domains.clear()
        for entry in stats['top_queried_domains']:
            for domain, count in entry.items():
                top_domains.labels(domain=domain).set(count)

        # Top blocked
        top_blocked_domains.clear()
        for entry in stats['top_blocked_domains']:
            for domain, count in entry.items():
                top_blocked_domains.labels(domain=domain).set(count)

        # Top clients
        top_clients.clear()
        for entry in stats['top_clients']:
            for client, count in entry.items():
                top_clients.labels(client=client).set(count)

        # Upstreams
        top_upstreams.clear()
        for entry in stats['top_upstreams_responses']:
            for upstream, count in entry.items():
                top_upstreams.labels(upstream=upstream).set(count)

        top_upstream_avg.clear()
        for entry in stats['top_upstreams_avg_time']:
            for upstream, time_val in entry.items():
                top_upstream_avg.labels(upstream=upstream).set(time_val)

        # Status
        protection_enabled.set(1 if status.get('protection_enabled') else 0)
        adguard_running.set(1 if status.get('running') else 0)

    except Exception as e:
        print(f"Error fetching AdGuard data: {e}")

# Background update loop
def update_loop():
    while True:
        fetch_data()
        time.sleep(UPDATE_INTERVAL)

# Start background update thread
threading.Thread(target=update_loop, daemon=True).start()

# Expose Prometheus metrics endpoint
@app.route("/metrics")
def metrics():
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

# Healthcheck
@app.route("/")
def home():
    return "AdGuard Exporter Aktif!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9617)
