from flask import Flask, Response
import requests
import time
import threading
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

metrics = []
UPDATE_INTERVAL = 5

ADGUARD_STATS_URL = os.getenv("ADGUARD_STATS_URL", "http://localhost/control/stats")
ADGUARD_STATUS_URL = os.getenv("ADGUARD_STATUS_URL", "http://localhost/control/status")
ADGUARD_USER = os.getenv("ADGUARD_USER")
ADGUARD_PASS = os.getenv("ADGUARD_PASS")

if not ADGUARD_USER or not ADGUARD_PASS:
    raise Exception("❌ ENV belum lengkap. Pastikan ADGUARD_USER dan ADGUARD_PASS ada di file .env")

def fetch_metrics():
    global metrics
    while True:
        try:
            response_stats = requests.get(ADGUARD_STATS_URL, auth=(ADGUARD_USER, ADGUARD_PASS))
            stats = response_stats.json()

            response_status = requests.get(ADGUARD_STATUS_URL, auth=(ADGUARD_USER, ADGUARD_PASS))
            status = response_status.json()

            new_metrics = []

            # top_queried_domains
            for item in stats.get("top_queried_domains", []):
                if isinstance(item, dict):
                    for domain, count in item.items():
                        new_metrics.append(f'adguard_top_queried_domains{{domain="{domain}"}} {count}')

            # top_blocked_domains
            for item in stats.get("top_blocked_domains", []):
                if isinstance(item, dict):
                    for domain, count in item.items():
                        new_metrics.append(f'adguard_top_blocked_domains{{domain="{domain}"}} {count}')

            # top_clients
            for item in stats.get("top_clients", []):
                if isinstance(item, dict):
                    for client, count in item.items():
                        new_metrics.append(f'adguard_top_clients{{client="{client}"}} {count}')

            # top_upstreams_responses
            for item in stats.get("top_upstreams_responses", []):
                if isinstance(item, dict):
                    for upstream, count in item.items():
                        new_metrics.append(f'adguard_top_upstreams_responses{{upstream="{upstream}"}} {count}')

            # top_upstreams_avg_time
            for item in stats.get("top_upstreams_avg_time", []):
                if isinstance(item, dict):
                    for upstream, avg_time in item.items():
                        new_metrics.append(f'adguard_top_upstreams_avg_time{{upstream="{upstream}"}} {avg_time}')

            # query_types
            for item in stats.get("query_types", []):
                if isinstance(item, dict):
                    for qtype, count in item.items():
                        new_metrics.append(f'adguard_query_types{{type="{qtype}"}} {count}')

            # time series data (pakai nilai terakhir)
            dns_queries = stats.get("dns_queries", [])
            if dns_queries:
                new_metrics.append(f"adguard_dns_queries_total {dns_queries[-1]}")

            blocked_filtering = stats.get("blocked_filtering", [])
            if blocked_filtering:
                new_metrics.append(f"adguard_blocked_filtering_total {blocked_filtering[-1]}")

            replaced_safebrowsing = stats.get("replaced_safebrowsing", [])
            if replaced_safebrowsing:
                new_metrics.append(f"adguard_replaced_safebrowsing_total {replaced_safebrowsing[-1]}")

            replaced_parental = stats.get("replaced_parental", [])
            if replaced_parental:
                new_metrics.append(f"adguard_replaced_parental_total {replaced_parental[-1]}")

            # numeric values
            new_metrics.append(f"adguard_num_dns_queries {stats.get('num_dns_queries', 0)}")
            new_metrics.append(f"adguard_num_blocked_filtering {stats.get('num_blocked_filtering', 0)}")
            new_metrics.append(f"adguard_num_replaced_safebrowsing {stats.get('num_replaced_safebrowsing', 0)}")
            new_metrics.append(f"adguard_num_replaced_safesearch {stats.get('num_replaced_safesearch', 0)}")
            new_metrics.append(f"adguard_num_replaced_parental {stats.get('num_replaced_parental', 0)}")
            new_metrics.append(f"adguard_avg_processing_time {stats.get('avg_processing_time', 0.0)}")

            # status
            new_metrics.append(f"adguard_protection_enabled {int(status.get('protection_enabled', False))}")
            new_metrics.append(f"adguard_protection_disabled_duration {status.get('protection_disabled_duration', 0)}")
            new_metrics.append(f"adguard_dhcp_available {int(status.get('dhcp_available', False))}")
            new_metrics.append(f"adguard_running {int(status.get('running', False))}")
            new_metrics.append(f"adguard_dns_port {status.get('dns_port', 0)}")
            new_metrics.append(f"adguard_http_port {status.get('http_port', 0)}")

            metrics = new_metrics
        except Exception as e:
            print(f"Error fetching metrics: {e}")

        time.sleep(UPDATE_INTERVAL)

@app.route("/metrics")
def metrics_endpoint():
    return Response("\n".join(metrics), mimetype="text/plain")

if __name__ == "__main__":
    threading.Thread(target=fetch_metrics, daemon=True).start()
    app.run(host="0.0.0.0", port=9617)
