import os
from datetime import datetime
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

SO_HOST = os.getenv("SO_HOST", "localhost")
SO_PORT = int(os.getenv("SO_PORT", "9200"))
SO_USER = os.getenv("SO_USER", "")
SO_PASS = os.getenv("SO_PASS", "")
SO_VERIFY_CERTS = os.getenv("SO_VERIFY_CERTS", "false").lower() == "true"
SO_INDEX_PATTERN = os.getenv("SO_INDEX_PATTERN", "so-alert*")


def make_es_client():
    return Elasticsearch(
        [f"https://{SO_HOST}:{SO_PORT}"],
        basic_auth=(SO_USER, SO_PASS),
        verify_certs=SO_VERIFY_CERTS,
        ssl_show_warn=False,
        request_timeout=20,
        retry_on_timeout=True,
        max_retries=2,
    )


def normalize_severity(value):
    if value is None:
        return 1
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        mapping = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
            "informational": 1,
        }
        return mapping.get(text, 1)


def severity_label(sev):
    if sev >= 5:
        return "CRITICAL"
    if sev == 4:
        return "HIGH"
    if sev == 3:
        return "MEDIUM"
    if sev == 2:
        return "LOW"
    return "INFO"


def discover_index_pattern(es):
    try:
        indices_info = es.indices.get(index="*", expand_wildcards="open,hidden")
        names = list(indices_info.keys())

        if any(name.startswith("so-alert") for name in names):
            return "so-alert*"

        alert_like = [n for n in names if "alert" in n.lower()]
        if alert_like:
            return ",".join(sorted(alert_like)[:50])

        return "*"
    except Exception:
        return SO_INDEX_PATTERN


def get_dashboard_data():
    es = make_es_client()

    info = es.info()
    version = info.get("version", {}).get("number", "-")

    try:
        all_indices = es.cat.indices(format="json")
        index_count = len(all_indices)
    except Exception:
        index_count = 0

    active_pattern = discover_index_pattern(es)

    base_query = {
        "bool": {
            "filter": [
                {"range": {"@timestamp": {"gte": "now-24h"}}}
            ]
        }
    }

    count_res = es.count(index=active_pattern, query=base_query)
    total_alerts = count_res.get("count", 0)

    agg_res = es.search(
        index=active_pattern,
        size=0,
        query=base_query,
        aggs={
            "by_sev": {"terms": {"field": "event.severity", "size": 10}},
            "by_hour": {
                "date_histogram": {
                    "field": "@timestamp",
                    "calendar_interval": "hour",
                    "min_doc_count": 0,
                }
            },
            "top_ips": {"terms": {"field": "source.ip", "size": 8}},
        },
    )

    aggs = agg_res.get("aggregations", {}) or {}

    critical = high = medium = 0

    for bucket in aggs.get("by_sev", {}).get("buckets", []):
        sev = normalize_severity(bucket.get("key"))
        cnt = int(bucket.get("doc_count", 0))
        if sev >= 5:
            critical += cnt
        elif sev == 4:
            high += cnt
        elif sev == 3:
            medium += cnt

    timeline = []
    for bucket in aggs.get("by_hour", {}).get("buckets", []):
        key_as_string = bucket.get("key_as_string")
        label = key_as_string[11:16] if key_as_string and len(key_as_string) >= 16 else "-"
        timeline.append({
            "time": label,
            "count": int(bucket.get("doc_count", 0))
        })

    top_ips = []
    for bucket in aggs.get("top_ips", {}).get("buckets", []):
        top_ips.append({
            "ip": str(bucket.get("key", "—")),
            "count": int(bucket.get("doc_count", 0)),
        })

    recent_res = es.search(
        index=active_pattern,
        size=10,
        sort=[{"@timestamp": {"order": "desc"}}],
        query=base_query,
        source=[
            "@timestamp",
            "rule.name",
            "event.severity",
            "source.ip",
            "destination.port",
            "message",
        ],
    )

    recent_alerts = []
    for hit in recent_res.get("hits", {}).get("hits", []):
        src = hit.get("_source", {})
        event = src.get("event", {}) or {}
        rule = src.get("rule", {}) or {}
        source = src.get("source", {}) or {}
        dest = src.get("destination", {}) or {}

        sev = normalize_severity(event.get("severity"))

        recent_alerts.append({
            "timestamp": src.get("@timestamp", ""),
            "severity": sev,
            "severity_label": severity_label(sev),
            "rule_name": rule.get("name") or src.get("message") or "—",
            "source_ip": source.get("ip", "—"),
            "destination_port": dest.get("port", "—"),
        })

    return {
        "connected": True,
        "status": f"Connected to Elasticsearch v{version}",
        "total_alerts": total_alerts,
        "critical": critical,
        "high": high,
        "medium": medium,
        "timeline": timeline,
        "top_ips": top_ips,
        "recent_alerts": recent_alerts,
        "last_update": datetime.now().strftime("%H:%M:%S"),
        "es_version": version,
        "index_count": index_count,
        "active_index_pattern": active_pattern,
    }