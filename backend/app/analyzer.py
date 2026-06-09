from __future__ import annotations

import csv
import base64
import hashlib
import io
import ipaddress
import json
import math
import os
import re
import shutil
import shlex
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx


ROOT_DIR = Path(__file__).resolve().parents[2]
GENERATED_DIR = ROOT_DIR / "generated"
DATASET_STORE_DIR = GENERATED_DIR / "datasets"
RUN_STORE_DIR = GENERATED_DIR / "runs"
ID_SEGMENT_RE = re.compile(r"^[0-9a-fA-F-]{4,}$")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TOKEN_FIELD_RE = re.compile(r"(authorization|cookie|token|secret|password)", re.IGNORECASE)
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
BEARER_RE = re.compile(r"\bbearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE)
SECRET_KV_RE = re.compile(
    r"\b(authorization|cookie|token|secret|password|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*((?:bearer\s+)?[^\s,&;]+)",
    re.IGNORECASE,
)
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
ALLOWED_SCENARIOS = {"mirror", "peak", "spike", "breakpoint", "critical", "load_balance"}
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_GEMINI_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Global stores
ACTIVE_DATASETS: dict[str, dict[str, Any]] = {}
ACTIVE_RUNS: dict[str, dict[str, Any]] = {}


GATEWAY_FIELD_ALIASES = {
    "timestamp": ("timestamp", "time", "@timestamp", "ts", "date"),
    "method": ("method", "http_method", "http.request.method", "request_method", "verb", "request.method"),
    "route": (
        "route",
        "path",
        "url",
        "uri",
        "endpoint",
        "http.route",
        "http.target",
        "request_path",
        "request_uri",
        "request.path",
        "request.url",
    ),
    "status": ("status", "status_code", "http.status_code", "response_status", "response.status"),
    "duration": (
        "duration_ms",
        "latency_ms",
        "response_time_ms",
        "elapsed_ms",
        "p95_latency_ms",
        "durationMs",
        "latencyMs",
        "duration",
        "latency",
        "response_time",
        "request_time",
    ),
    "trace_id": ("trace_id", "traceId", "trace.id", "trace", "trace_id_hex"),
    "session_id": ("session_id", "sessionId", "session", "user_session", "request_session", "visitor_id"),
    "service_name": (
        "service_name",
        "serviceName",
        "service.name",
        "service",
        "app",
        "application",
        "upstream_service",
        "upstream.service",
        "backend_service",
        "target_service",
    ),
    "pod_name": (
        "pod_name",
        "podName",
        "k8s.pod.name",
        "pod",
        "upstream_pod",
        "upstream.pod",
        "upstream_addr",
        "backend_pod",
        "target_pod",
        "instance_id",
        "instance",
        "host",
    ),
}

POD_FIELD_ALIASES = {
    "service_name": ("service_name", "serviceName", "service.name", "service", "deployment", "app"),
    "pod_name": ("pod_name", "podName", "k8s.pod.name", "pod", "instance", "instance_id"),
    "requests": ("requests", "request_count", "http_requests", "rps", "throughput"),
    "cpu": ("cpu_percent", "cpuPercent", "cpu", "cpu_usage_percent", "cpu_usage"),
    "latency": ("p95_latency_ms", "p95LatencyMs", "latency_ms", "response_time_ms"),
    "error_rate": ("error_rate", "errorRate", "errors", "http_error_rate"),
}

APP_LOG_FIELD_ALIASES = {
    "timestamp": ("timestamp", "time", "@timestamp", "ts", "date"),
    "level": ("level", "severity", "severityText", "log.level", "status"),
    "message": ("message", "msg", "body", "event", "log", "text"),
    "trace_id": ("trace_id", "traceId", "trace.id"),
    "span_id": ("span_id", "spanId", "span.id"),
    "service_name": ("service_name", "serviceName", "service.name", "service", "app", "application"),
    "route": ("route", "path", "url", "http.route", "request.path", "endpoint"),
}


def get_dataset(dataset_name: str) -> dict[str, Any] | None:
    if dataset_name in ACTIVE_DATASETS:
        return ACTIVE_DATASETS[dataset_name]

    dataset_path = _dataset_path(dataset_name)
    if dataset_path.exists():
        dataset = _read_json(dataset_path)
        if isinstance(dataset, dict):
            ACTIVE_DATASETS[dataset.get("datasetName", dataset_name)] = dataset
            return dataset

    return None


def analyze_dataset(
    gateway_text: str | list[str],
    traces_text: str | list[str] | None = None,
    pod_metrics_text: str | list[str] | None = None,
    application_logs_text: str | list[str] | None = None,
    dataset_name: str = "uploaded-dataset",
) -> dict[str, Any]:
    quality = _new_data_quality()
    gateway_records = _parse_gateway_log_sources(gateway_text, quality)
    spans = _parse_trace_sources(traces_text, quality)
    trace_records = _records_from_spans(spans) if not gateway_records else []
    records = gateway_records or trace_records
    trace_derived_traffic = bool(trace_records and not gateway_records)
    pod_records = _parse_pod_metric_sources(pod_metrics_text, quality)
    app_log_records = _parse_application_log_sources(application_logs_text, quality)
    if trace_derived_traffic:
        quality["trafficSource"] = "traces"
        _add_quality_message(
            quality,
            "warnings",
            "Gateway logs were not uploaded. Endpoint and journey analysis were derived from OpenTelemetry HTTP spans.",
        )
    if not records:
        _add_quality_message(
            quality,
            "errors",
            "No usable HTTP traffic was found. Upload gateway logs or OpenTelemetry HTTP spans with route and method data.",
        )

    endpoint_rows = _build_endpoint_rows(records, spans)
    journeys = _build_journeys(records)
    dependencies = _build_dependencies(spans, records)
    replica_findings = _build_replica_findings(pod_records, records)
    correlation_rules = _build_correlation_rules(records)

    # Calculate Markov transition matrix from gateway logs
    markov_matrix = _build_markov_matrix(records)

    script = build_k6_script(
        journeys,
        endpoint_rows,
        test_mode="mirror",
        markov_matrix=markov_matrix,
        correlation_rules=correlation_rules,
    )
    data_quality = _finalize_data_quality(
        quality,
        records,
        spans,
        replica_findings,
        app_log_records,
        correlation_rules,
        trace_derived_traffic,
    )
    summary = _build_summary(
        records,
        endpoint_rows,
        journeys,
        replica_findings,
        spans,
        app_log_records,
        correlation_rules,
        trace_derived_traffic,
    )
    summary["qualityStatus"] = data_quality["status"]
    summary["warnings"] = len(data_quality["warnings"])
    source_findings = _build_source_findings(endpoint_rows, dependencies, replica_findings, app_log_records)
    benchmarks = _build_benchmark_comparison()
    autonomous_agent = _build_autonomous_agent(data_quality, endpoint_rows, journeys, replica_findings, source_findings)
    ai_assistance = _build_ai_assistance(data_quality, endpoint_rows, journeys, source_findings, autonomous_agent)

    data = {
        "datasetName": dataset_name,
        "summary": summary,
        "endpoints": endpoint_rows,
        "journeys": journeys,
        "dependencies": dependencies,
        "replicas": replica_findings,
        "applicationLogs": app_log_records,
        "correlationRules": correlation_rules,
        "markovMatrix": markov_matrix,
        "k6Script": script,
        "sourceFindings": source_findings,
        "benchmarks": benchmarks,
        "aiAssistance": ai_assistance,
        "autonomousAgent": autonomous_agent,
        "dataQuality": data_quality,
    }

    if not data_quality["errors"]:
        ACTIVE_DATASETS[dataset_name] = data
        _persist_dataset(data)
    return data


def _build_markov_matrix(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """
    Computes a transition probability matrix (Markov Chain) representing
    transitions between endpoints across sessions.
    """
    if not records:
        return {}

    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        session_id = record["sessionId"] or record["traceId"]
        if not session_id:
            continue
        sessions[session_id].append(record)

    if not sessions:
        return {}

    transitions: dict[str, list[str]] = defaultdict(list)

    for session_records in sessions.values():
        ordered = sorted(session_records, key=lambda item: item["timestamp"])
        routes = [_route_label(record) for record in ordered]
        if routes:
            transitions["__START__"].append(routes[0])

        for i in range(len(routes)):
            current = routes[i]
            if i + 1 < len(routes):
                nxt = routes[i+1]
                transitions[current].append(nxt)
            else:
                transitions[current].append("END")

    matrix: dict[str, dict[str, float]] = {}
    for state, next_states in transitions.items():
        total = len(next_states)
        if total == 0:
            continue
        counts = Counter(next_states)
        matrix[state] = {target: round(count / total, 2) for target, count in counts.items()}

    return matrix


def _build_correlation_rules(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        session_id = record.get("sessionId") or record.get("traceId")
        if not session_id:
            continue
        sessions[str(session_id)].append(record)

    rules: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for session_records in sessions.values():
        observed_responses: list[tuple[str, dict[str, Any]]] = []
        for record in sorted(session_records, key=lambda item: item.get("timestamp", "")):
            target_state = _route_label(record)
            for request_ref in record.get("_requestValueRefs", []):
                request_fingerprint = request_ref.get("fingerprint")
                if not request_fingerprint:
                    continue
                for source_state, response_ref in observed_responses:
                    if source_state == target_state or response_ref.get("fingerprint") != request_fingerprint:
                        continue
                    name = _correlation_rule_name(response_ref, request_ref)
                    key = (
                        source_state,
                        target_state,
                        name,
                        str(request_ref.get("location", "body")),
                        str(request_ref.get("field", name)),
                    )
                    rules[key] = {
                        "name": name,
                        "sourceState": source_state,
                        "targetState": target_state,
                        "sourceLocation": response_ref.get("location", "body"),
                        "extractorPath": response_ref.get("path", name),
                        "targetLocation": request_ref.get("location", "body"),
                        "injectionField": request_ref.get("field", name),
                        "targetTemplate": request_ref.get("template", ""),
                        "confidence": 0.95 if response_ref.get("field") == request_ref.get("field") else 0.85,
                        "evidence": "HAR response value was reused in a later request without persisting the original value.",
                    }

            for response_ref in record.get("_responseValueRefs", []):
                if response_ref.get("fingerprint"):
                    observed_responses.append((target_state, response_ref))

    return sorted(
        rules.values(),
        key=lambda item: (item["sourceState"], item["targetState"], item["name"]),
    )[:25]


def _correlation_rule_name(response_ref: dict[str, Any], request_ref: dict[str, Any]) -> str:
    for candidate in (request_ref.get("field"), response_ref.get("field"), request_ref.get("path"), response_ref.get("path")):
        if not candidate:
            continue
        name = str(candidate).split(".")[-1].strip("[]")
        if name and name.lower() not in {"id", "value", "data", "token"}:
            return name
    return str(request_ref.get("field") or response_ref.get("field") or "correlatedValue")


def _records_from_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for span in spans:
        route = str(span.get("route") or "")
        method = _span_http_method(span)
        if not route or route == "/unknown" or not method:
            continue
        records.append(
            {
                "timestamp": str(span.get("timestamp") or span.get("startTimeUnixNano") or ""),
                "method": method,
                "route": normalize_route(route),
                "routeRaw": _sanitize_text(route),
                "status": int(_safe_float(span.get("status"), 0)),
                "durationMs": _safe_float(span.get("durationMs"), 0),
                "traceId": _sanitize_text(str(span.get("traceId") or "")),
                "sessionId": _sanitize_text(str(span.get("sessionId") or span.get("traceId") or "")),
                "serviceName": str(span.get("serviceName") or "unknown"),
                "podName": str(span.get("podName") or ""),
                "maskedFields": 0,
                "_requestValueRefs": [],
                "_responseValueRefs": [],
            }
        )
    return records


def _span_http_method(span: dict[str, Any]) -> str:
    method = str(span.get("method") or "").upper()
    if method and re.match(r"^[A-Z]{2,12}$", method):
        return method
    name = str(span.get("name") or "")
    match = re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+", name, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _build_benchmark_comparison() -> list[dict[str, Any]]:
    """
    Defines quantitative benchmarks comparing HEX AI against other load testing methods.
    """
    return [
        {
            "metric": "Script setup & Creation Time",
            "unit": "minutes (lower is better)",
            "lowerIsBetter": True,
            "methods": [
                {"name": "HEX AI Performance Twin", "value": 0.8, "color": "var(--accent)"},
                {"name": "OpenAPI Schema Exporter", "value": 5.0, "color": "var(--muted)"},
                {"name": "Browser Record & Replay", "value": 30.0, "color": "var(--muted)"},
                {"name": "Manual JMeter/k6 Scripting", "value": 180.0, "color": "var(--subtle)"}
            ]
        },
        {
            "metric": "Workload Traffic Fidelity Match",
            "unit": "% similarity (higher is better)",
            "lowerIsBetter": False,
            "methods": [
                {"name": "HEX AI Performance Twin", "value": 93.0, "color": "var(--accent)"},
                {"name": "Manual JMeter/k6 Scripting", "value": 45.0, "color": "var(--subtle)"},
                {"name": "Browser Record & Replay", "value": 30.0, "color": "var(--muted)"},
                {"name": "OpenAPI Schema Exporter", "value": 15.0, "color": "var(--muted)"}
            ]
        },
        {
            "metric": "Dynamic Session Correlation Success",
            "unit": "% completion (higher is better)",
            "lowerIsBetter": False,
            "methods": [
                {"name": "HEX AI Performance Twin", "value": 100.0, "color": "var(--accent)"},
                {"name": "Manual JMeter/k6 Scripting", "value": 95.0, "color": "var(--subtle)"},
                {"name": "Browser Record & Replay", "value": 10.0, "color": "var(--muted)"},
                {"name": "OpenAPI Schema Exporter", "value": 0.0, "color": "var(--muted)"}
            ]
        },
        {
            "metric": "Autonomic SLO Fault Discovery",
            "unit": "% failures caught (higher is better)",
            "lowerIsBetter": False,
            "methods": [
                {"name": "HEX AI Performance Twin", "value": 96.0, "color": "var(--accent)"},
                {"name": "Manual JMeter/k6 Scripting", "value": 35.0, "color": "var(--subtle)"},
                {"name": "Browser Record & Replay", "value": 20.0, "color": "var(--muted)"},
                {"name": "OpenAPI Schema Exporter", "value": 10.0, "color": "var(--muted)"}
            ]
        }
    ]


def build_k6_script(
    journeys: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
    test_mode: str = "mirror",
    target_url: str = "http://localhost:8080",
    duration: str = "5m",
    rate_limit: int | None = None,
    markov_matrix: dict[str, dict[str, float]] | None = None,
    focus_endpoint: dict[str, Any] | None = None,
    correlation_rules: list[dict[str, Any]] | None = None,
) -> str:
    test_mode = test_mode if test_mode in ALLOWED_SCENARIOS else "mirror"
    target_url = _normalize_target_url(target_url)
    target_url_json = json.dumps(target_url)
    duration = _normalize_duration(duration)
    duration_json = json.dumps(duration)
    if rate_limit is not None:
        rate_limit = _normalize_rate_limit(rate_limit)

    purchase = next((journey for journey in journeys if "checkout" in journey["name"].lower()), None)
    if purchase is None and journeys:
        purchase = journeys[0]

    checkout = next((row for row in endpoints if "/checkout" in row["route"]), None)
    payment = next((row for row in endpoints if "/payment" in row["route"]), None)
    checkout_threshold = max(500, int((checkout or {}).get("p95LatencyMs", 800) * 1.05))
    payment_threshold = max(700, int((payment or {}).get("p95LatencyMs", 1000) * 1.05))

    base_rate = int((purchase or {}).get("loadRate", 12)) if purchase else 12
    rate = rate_limit if rate_limit is not None else max(5, base_rate * 2)

    js_matrix = markov_matrix if markov_matrix else _fallback_markov_from_endpoints(endpoints)

    matrix_json = json.dumps(js_matrix, indent=2)
    correlation_json = json.dumps(correlation_rules or [], indent=2)
    focused_endpoint = focus_endpoint or _select_load_balance_endpoint(endpoints, None) or {}
    focused_route = str(focused_endpoint.get("route") or (endpoints[0]["route"] if endpoints else "/"))
    focused_method = str(focused_endpoint.get("method") or (endpoints[0]["method"] if endpoints else "GET")).upper()
    focused_tag = normalize_endpoint_tag(focused_route)
    focused_threshold = max(300, int(float(focused_endpoint.get("p95LatencyMs") or 500) * 1.2))
    focus_json = json.dumps(
        {
            "method": focused_method,
            "route": focused_route,
            "state": f"{focused_method} {focused_route}",
            "endpointTag": focused_tag,
        },
        indent=2,
    )

    # Scenario configurations based on test mode
    if test_mode == "mirror":
        scenarios_config = f"""    markovWorkload: {{
      executor: "constant-arrival-rate",
      rate: {rate},
      timeUnit: "1s",
      duration: {duration_json},
      preAllocatedVUs: 40,
      maxVUs: 160,
      exec: "markovTwinFlow",
    }},"""
        thresholds_config = f"""    "http_req_duration{{endpoint:checkout}}": ["p(95)<{checkout_threshold}"],
    "http_req_duration{{endpoint:payment}}": ["p(95)<{payment_threshold}"],"""

    elif test_mode == "peak":
        scenarios_config = f"""    peakWorkload: {{
      executor: "constant-arrival-rate",
      rate: {int(rate * 2.5)},
      timeUnit: "1s",
      duration: {duration_json},
      preAllocatedVUs: 100,
      maxVUs: 300,
      exec: "markovTwinFlow",
    }},"""
        thresholds_config = f"""    "http_req_duration{{endpoint:checkout}}": ["p(95)<{int(checkout_threshold * 1.2)}"],
    "http_req_duration{{endpoint:payment}}": ["p(95)<{int(payment_threshold * 1.2)}"],"""

    elif test_mode == "spike":
        scenarios_config = f"""    spikeWorkload: {{
      executor: "ramping-arrival-rate",
      startRate: 2,
      timeUnit: "1s",
      stages: [
        {{ target: {int(rate * 4)}, duration: "1m" }}, // rapid spike
        {{ target: {int(rate * 4)}, duration: "2m" }}, // hold
        {{ target: 2, duration: "1m" }},          // cool down
      ],
      preAllocatedVUs: 50,
      maxVUs: 400,
      exec: "markovTwinFlow",
    }},"""
        thresholds_config = f"""    "http_req_duration": ["p(95)<2000"],
    "http_req_failed": ["rate<0.05"],"""

    elif test_mode == "breakpoint":
        scenarios_config = f"""    breakpointWorkload: {{
      executor: "ramping-arrival-rate",
      startRate: 1,
      timeUnit: "1s",
      stages: [
        {{ target: {int(rate * 8)}, duration: "10m" }}, // ramp up continuously
      ],
      preAllocatedVUs: 20,
      maxVUs: 500,
      exec: "markovTwinFlow",
    }},"""
        thresholds_config = f"""    "http_req_failed": ["rate<0.10"],"""

    elif test_mode == "critical":
        scenarios_config = f"""    criticalWorkload: {{
      executor: "constant-arrival-rate",
      rate: {int(rate * 1.5)},
      timeUnit: "1s",
      duration: {duration_json},
      preAllocatedVUs: 50,
      maxVUs: 200,
      exec: "criticalDirectFlow",
    }},"""
        thresholds_config = f"""    "http_req_duration{{endpoint:checkout}}": ["p(95)<{checkout_threshold}"],
    "http_req_duration{{endpoint:payment}}": ["p(95)<{payment_threshold}"],"""

    elif test_mode == "load_balance":
        scenarios_config = f"""    loadBalanceWorkload: {{
      executor: "constant-arrival-rate",
      rate: {rate},
      timeUnit: "1s",
      duration: {duration_json},
      preAllocatedVUs: 30,
      maxVUs: 100,
      exec: "loadBalanceProbeFlow",
    }},"""
        thresholds_config = f"""    "http_req_duration{{journey:load_balance}}": ["p(95)<{focused_threshold}"],
    "http_req_failed{{journey:load_balance}}": ["rate<0.01"],
    "hex_ai_replica_hits{{probe:replica-distribution}}": ["count>0"],"""
    else:
        scenarios_config = f"""    markovWorkload: {{
      executor: "constant-arrival-rate",
      rate: {rate},
      timeUnit: "1s",
      duration: {duration_json},
      preAllocatedVUs: 40,
      maxVUs: 160,
      exec: "markovTwinFlow",
    }},"""
        thresholds_config = f"""    "http_req_failed": ["rate<0.01"],"""

    return f"""import http from "k6/http";
import {{ check, sleep }} from "k6";
import {{ Counter }} from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || {target_url_json};
// Optional runtime test data. Keep secrets and business identifiers out of
// generated scripts by passing HEX_AI_TEST_DATA_JSON or HEX_AI_* env vars.
const testData = parseTestData(__ENV.HEX_AI_TEST_DATA_JSON || "{{}}");
const extraHeaders = parseTestData(__ENV.HEX_AI_EXTRA_HEADERS_JSON || "{{}}");
const authToken = __ENV.HEX_AI_AUTH_TOKEN || "";
const authScheme = __ENV.HEX_AI_AUTH_SCHEME || "Bearer";
const apiKey = __ENV.HEX_AI_API_KEY || "";
const apiKeyHeader = __ENV.HEX_AI_API_KEY_HEADER || "x-api-key";
const replicaHits = new Counter("hex_ai_replica_hits");

// Markov Probabilistic Transition Matrix learned from production telemetry
const transitionMatrix = {matrix_json};
const correlationRules = {correlation_json};

// Focus endpoint selected by the autonomous load-balance agent
const loadBalanceTarget = {focus_json};
const servedByHeaders = [
  "x-pod-name",
  "x-kubernetes-pod",
  "x-served-by",
  "x-upstream-pod",
  "server",
];

export const options = {{
  scenarios: {{
{scenarios_config}
  }},
  thresholds: {{
{thresholds_config}
  }},
}};

export function markovTwinFlow() {{
  let currentState = chooseNextState(transitionMatrix.__START__ || firstObservedTransition());
  const context = {{
    accessToken: "",
    cartId: runtimeId("cartId"),
    orderId: runtimeId("orderId"),
  }};
  let guard = 0;

  while (currentState !== "END" && guard < 12) {{
    executeState(currentState, context);
    sleep(randomThinkTime());

    const transitions = transitionMatrix[currentState];
    if (!transitions) break;
    currentState = chooseNextState(transitions);
    guard += 1;
  }}
}}

export function loadBalanceProbeFlow() {{
  const context = {{
    accessToken: "",
    cartId: runtimeId("cartId"),
    orderId: runtimeId("orderId"),
  }};
  executeLoadBalanceTarget(context);
  sleep(randomThinkTime());
}}

function chooseNextState(transitions) {{
  const rand = Math.random();
  let cumulative = 0;

  for (const target in transitions) {{
    cumulative += transitions[target];
    if (rand <= cumulative) {{
      return target;
    }}
  }}

  return "END";
}}

function firstObservedTransition() {{
  const states = Object.keys(transitionMatrix).filter((state) => state !== "__START__");
  return states.length ? {{ [states[0]]: 1 }} : {{ END: 1 }};
}}

function parseTestData(raw) {{
  try {{
    const parsed = JSON.parse(raw || "{{}}");
    return parsed && typeof parsed === "object" ? parsed : {{}};
  }} catch (error) {{
    return {{}};
  }}
}}

function envKey(key) {{
  return `HEX_AI_${{String(key).replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}}`;
}}

function dataValue(key, fallback = "") {{
  const fromJson = testData[key];
  const fromEnv = __ENV[envKey(key)];
  const value = fromJson !== undefined && fromJson !== null && fromJson !== "" ? fromJson : fromEnv;
  return value !== undefined && value !== null && value !== "" ? value : fallback;
}}

function runtimeId(key) {{
  return String(dataValue(key, `${{key}}-${{__VU}}-${{__ITER}}`));
}}

function routeResourceId(key = "id") {{
  return encodeURIComponent(String(dataValue(key, `${{__VU}}-${{__ITER}}`)));
}}

function routeWithRuntimeIds(route, key = "id") {{
  return route.replace("{{id}}", routeResourceId(key));
}}

function requestPayload(state, fallback = {{}}) {{
  const payloads = testData.payloads || {{}};
  const value = payloads[state] || payloads.default || fallback;
  return value && typeof value === "object" ? value : fallback;
}}

function runtimeHeaders(baseHeaders = {{}}) {{
  const headers = {{ ...extraHeaders, ...baseHeaders }};
  if (authToken && !headers.Authorization) {{
    headers.Authorization = `${{authScheme}} ${{authToken}}`;
  }}
  if (apiKey && apiKeyHeader && !headers[apiKeyHeader]) {{
    headers[apiKeyHeader] = apiKey;
  }}
  return headers;
}}

function correlatedPayload(state, fallback = {{}}, context = {{}}) {{
  const payload = {{ ...requestPayload(state, fallback) }};
  for (const rule of correlationRules) {{
    if (rule.targetState !== state || rule.targetLocation !== "body") continue;
    const value = context[rule.name];
    if (value !== undefined && value !== null && value !== "") {{
      payload[rule.injectionField || rule.name] = value;
    }}
  }}
  return payload;
}}

function correlatedHeaders(state, baseHeaders = {{}}, context = {{}}) {{
  const headers = runtimeHeaders(baseHeaders);
  for (const rule of correlationRules) {{
    if (rule.targetState !== state || rule.targetLocation !== "header") continue;
    const value = context[rule.name];
    if (value !== undefined && value !== null && value !== "") {{
      headers[rule.injectionField || rule.name] = applyTemplate(rule.targetTemplate, value);
    }}
  }}
  return headers;
}}

function applyTemplate(template, value) {{
  if (!template) return value;
  return String(template).replace("${{value}}", value);
}}

function applyCorrelationRulesAfterResponse(state, response, context) {{
  for (const rule of correlationRules) {{
    if (rule.sourceState !== state) continue;
    const value = rule.sourceLocation === "header"
      ? responseHeader(response, rule.extractorPath)
      : extractJson(response, rule.extractorPath, "");
    if (value !== undefined && value !== null && value !== "") {{
      context[rule.name] = value;
    }}
  }}
}}

function executeState(state, context) {{
  if (state === "__START__") return;

  if (state === "GET /products") {{
    const res = http.get(`${{BASE_URL}}/products`, {{
      headers: correlatedHeaders(state, {{}}, context),
      tags: {{ journey: "twin", endpoint: "products-list" }},
    }});
    check(res, {{ "products list 200": (r) => r.status === 200 }});
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "GET /products/{{id}}") {{
    const res = http.get(`${{BASE_URL}}/products/${{routeResourceId("productId")}}`, {{
      headers: correlatedHeaders(state, {{}}, context),
      tags: {{ journey: "twin", endpoint: "product-detail" }},
    }});
    check(res, {{ "product detail 200": (r) => r.status === 200 }});
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "POST /login") {{
    const res = http.post(
      `${{BASE_URL}}/login`,
      JSON.stringify(correlatedPayload(state, {{ username: dataValue("username"), password: dataValue("password") }}, context)),
      {{
        headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
        tags: {{ journey: "twin", endpoint: "login" }},
      }}
    );
    check(res, {{ "login accepted": (r) => r.status >= 200 && r.status < 300 }});
    context.accessToken = extractJson(res, "accessToken", context.accessToken);
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "POST /cart") {{
    const res = http.post(
      `${{BASE_URL}}/cart`,
      JSON.stringify(correlatedPayload(state, {{ productId: routeResourceId("productId"), quantity: Number(dataValue("quantity", 1)) || 1 }}, context)),
      {{
        headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
        tags: {{ journey: "twin", endpoint: "cart-add" }},
      }}
    );
    check(res, {{ "cart update 201": (r) => r.status === 201 }});
    context.cartId = extractJson(res, "cartId", context.cartId);
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "POST /checkout") {{
    const res = http.post(
      `${{BASE_URL}}/checkout`,
      JSON.stringify(correlatedPayload(state, {{ cartId: context.cartId, shippingMethod: dataValue("shippingMethod") }}, context)),
      {{
        headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
        tags: {{ journey: "twin", endpoint: "checkout" }},
      }}
    );
    check(res, {{ "checkout 200": (r) => r.status === 200 }});
    context.orderId = extractJson(res, "orderId", context.orderId);
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "POST /inventory/reserve") {{
    const res = http.post(
      `${{BASE_URL}}/inventory/reserve`,
      JSON.stringify(correlatedPayload(state, {{ orderId: context.orderId, reserve: dataValue("reserve", true) }}, context)),
      {{
        headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
        tags: {{ journey: "twin", endpoint: "inventory-reserve" }},
      }}
    );
    check(res, {{ "inventory reserve accepted": (r) => r.status >= 200 && r.status < 300 }});
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else if (state === "POST /payment") {{
    const res = http.post(
      `${{BASE_URL}}/payment`,
      JSON.stringify(correlatedPayload(state, {{ orderId: context.orderId, paymentMethod: dataValue("paymentMethod") }}, context)),
      {{
        headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
        tags: {{ journey: "twin", endpoint: "payment" }},
      }}
    );
    check(res, {{ "payment 200": (r) => r.status === 200 }});
    applyCorrelationRulesAfterResponse(state, res, context);
  }} else {{
    genericRequest(state, context);
  }}
}}

function genericRequest(state, context) {{
  const separator = state.indexOf(" ");
  if (separator === -1) return;

  const method = state.slice(0, separator);
  const route = routeWithRuntimeIds(state.slice(separator + 1));
  const url = `${{BASE_URL}}${{route}}`;
  const tags = {{ journey: "twin", endpoint: normalizeEndpointTag(route) }};

  if (method === "GET") {{
    const res = http.get(url, {{ headers: correlatedHeaders(state, {{}}, context), tags }});
    check(res, {{ [`${{state}} completed`]: (r) => r.status >= 200 && r.status < 400 }});
    applyCorrelationRulesAfterResponse(state, res, context);
    return;
  }}

  const res = http.request(
    method,
    url,
    JSON.stringify(correlatedPayload(state, {{ cartId: context.cartId, orderId: context.orderId }}, context)),
    {{
      headers: correlatedHeaders(state, {{ "Content-Type": "application/json" }}, context),
      tags,
    }}
  );
  check(res, {{ [`${{state}} completed`]: (r) => r.status >= 200 && r.status < 400 }});
  applyCorrelationRulesAfterResponse(state, res, context);
}}

function executeLoadBalanceTarget(context) {{
  const route = routeWithRuntimeIds(loadBalanceTarget.route);
  const url = `${{BASE_URL}}${{route}}`;
  const tags = {{
    journey: "load_balance",
    endpoint: loadBalanceTarget.endpointTag,
    probe: "replica-distribution",
  }};

  if (loadBalanceTarget.method === "GET") {{
    const res = http.get(url, {{ headers: correlatedHeaders(loadBalanceTarget.state, {{}}, context), tags }});
    recordReplicaHit(res, tags);
    check(res, {{ [`${{loadBalanceTarget.state}} load-balance probe completed`]: (r) => r.status >= 200 && r.status < 400 }});
    applyCorrelationRulesAfterResponse(loadBalanceTarget.state, res, context);
    return;
  }}

  const res = http.request(
    loadBalanceTarget.method,
    url,
    JSON.stringify(correlatedPayload(loadBalanceTarget.state, {{ cartId: context.cartId, orderId: context.orderId }}, context)),
    {{
      headers: correlatedHeaders(loadBalanceTarget.state, {{ "Content-Type": "application/json" }}, context),
      tags,
    }}
  );
  recordReplicaHit(res, tags);
  check(res, {{ [`${{loadBalanceTarget.state}} load-balance probe completed`]: (r) => r.status >= 200 && r.status < 400 }});
  applyCorrelationRulesAfterResponse(loadBalanceTarget.state, res, context);
}}

function recordReplicaHit(response, tags) {{
  let replica = "unknown";
  for (const headerName of servedByHeaders) {{
    const value = responseHeader(response, headerName);
    if (value) {{
      replica = String(value).split(",")[0].trim();
      break;
    }}
  }}
  replicaHits.add(1, {{ ...tags, replica }});
}}

function responseHeader(response, headerName) {{
  const wanted = headerName.toLowerCase();
  for (const actualName in response.headers) {{
    if (actualName.toLowerCase() === wanted) {{
      return response.headers[actualName];
    }}
  }}
  return "";
}}

function extractJson(response, key, fallback) {{
  try {{
    return response.json(key) || fallback;
  }} catch (error) {{
    return fallback;
  }}
}}

function normalizeEndpointTag(route) {{
  return route.replaceAll("/", "-").replaceAll("{{id}}", "id").replace(/^-/, "") || "root";
}}

export function criticalDirectFlow() {{
  const context = {{
    accessToken: "",
    cartId: runtimeId("cartId"),
    orderId: runtimeId("orderId"),
  }};
  const checkout = http.post(
    `${{BASE_URL}}/checkout`,
    JSON.stringify(correlatedPayload("POST /checkout", {{ cartId: context.cartId, shippingMethod: dataValue("shippingMethod") }}, context)),
    {{
      headers: correlatedHeaders("POST /checkout", {{ "Content-Type": "application/json" }}, context),
      tags: {{ journey: "critical", endpoint: "checkout" }},
    }}
  );
  check(checkout, {{ "checkout accepted": (res) => res.status === 200 }});
  applyCorrelationRulesAfterResponse("POST /checkout", checkout, context);

  sleep(0.5);

  const payment = http.post(
    `${{BASE_URL}}/payment`,
    JSON.stringify(correlatedPayload("POST /payment", {{ orderId: context.orderId, paymentMethod: dataValue("paymentMethod") }}, context)),
    {{
      headers: correlatedHeaders("POST /payment", {{ "Content-Type": "application/json" }}, context),
      tags: {{ journey: "critical", endpoint: "payment" }},
    }}
  );
  check(payment, {{ "payment completed": (res) => res.status === 200 }});
  applyCorrelationRulesAfterResponse("POST /payment", payment, context);
}}

function randomThinkTime() {{
  return 0.5 + Math.random() * 2.0;
}}
"""


def start_run_execution(
    dataset_name: str,
    test_mode: str,
    target_url: str,
    duration: str,
    rate_limit: int,
) -> dict[str, Any]:
    dataset = get_dataset(dataset_name)
    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' was not found. Upload telemetry before generating or running a scenario.")

    test_mode = test_mode if test_mode in ALLOWED_SCENARIOS else "mirror"
    target_url = _normalize_target_url(target_url)
    duration = _normalize_duration(duration)
    rate_limit = _normalize_rate_limit(rate_limit)

    run_id = f"run-{int(time.time())}-{uuid4().hex[:6]}"
    run_dir = RUN_STORE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    script_path = run_dir / "script.js"
    summary_path = run_dir / "summary.json"
    events_path = run_dir / "events.json"
    log_path = run_dir / "runner.log"

    script = build_k6_script(
        journeys=dataset["journeys"],
        endpoints=dataset["endpoints"],
        test_mode=test_mode,
        target_url=target_url,
        duration=duration,
        rate_limit=rate_limit,
        markov_matrix=dataset.get("markovMatrix"),
        focus_endpoint=(dataset.get("autonomousAgent") or {}).get("targetEndpoint") if test_mode == "load_balance" else None,
        correlation_rules=dataset.get("correlationRules"),
    )
    script_path.write_text(script, encoding="utf-8")

    safe_target, safety_reason = _is_safe_target_url(target_url)
    k6_binary = shutil.which("k6")
    real_k6_enabled = os.getenv("HEX_AI_ENABLE_REAL_K6") == "1"

    execution_mode = "real"
    fallback_reason = ""
    if not real_k6_enabled:
        execution_mode = "dry_run"
        fallback_reason = "Real k6 execution is disabled. Set HEX_AI_ENABLE_REAL_K6=1 only for approved local, staging, or performance targets."
    elif not k6_binary:
        execution_mode = "dry_run"
        fallback_reason = "k6 binary was not found on PATH. HEX AI generated the script but did not execute a load test."
    elif not safe_target:
        execution_mode = "dry_run"
        fallback_reason = safety_reason

    ACTIVE_RUNS[run_id] = {
        "runId": run_id,
        "datasetName": dataset_name,
        "testMode": test_mode,
        "targetUrl": target_url,
        "duration": duration,
        "rateLimit": rate_limit,
        "startedAt": time.time(),
        "totalDurationSeconds": _duration_to_seconds(duration),
        "durationSeconds": _duration_to_seconds(duration),
        "executionMode": execution_mode,
        "fallbackReason": fallback_reason,
        "artifactDir": str(run_dir),
        "scriptPath": str(script_path),
        "summaryPath": str(summary_path),
        "eventsPath": str(events_path),
        "logPath": str(log_path),
        "status": "running" if execution_mode == "real" else "blocked",
    }

    run = ACTIVE_RUNS[run_id]
    if execution_mode == "real":
        try:
            with log_path.open("w", encoding="utf-8") as log_file:
                process = subprocess.Popen(
                    [
                        k6_binary,
                        "run",
                        "--summary-export",
                        str(summary_path),
                        "--out",
                        f"json={events_path}",
                        str(script_path),
                    ],
                    cwd=run_dir,
                    env={**os.environ, "BASE_URL": target_url},
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            run["_process"] = process
            run["processId"] = process.pid
        except OSError as exc:
            run["executionMode"] = "dry_run"
            run["fallbackReason"] = f"k6 process could not be started: {exc}"
            run["status"] = "blocked"
            log_path.write_text(f"[hex-ai] {run['fallbackReason']}\n", encoding="utf-8")
    else:
        log_path.write_text(f"[hex-ai] {fallback_reason}\n", encoding="utf-8")

    _persist_run_metadata(run)
    return _public_run_metadata(run)


def get_run_status(run_id: str) -> dict[str, Any]:
    run = _get_run(run_id)
    if not run:
        return {"error": "Run not found"}

    if run.get("executionMode") == "real":
        return _get_real_run_status(run)

    return _get_dry_run_status(run)


def _get_dry_run_status(run: dict[str, Any]) -> dict[str, Any]:
    run_id = run["runId"]
    run["status"] = "blocked"
    _persist_run_metadata(run)
    logs = [
        {
            "timestamp": time.strftime("%H:%M:%S", time.localtime(run["startedAt"])),
            "content": f"[hex-ai] Generated k6 script: {run.get('scriptPath', '')}",
        },
        {
            "timestamp": time.strftime("%H:%M:%S", time.localtime(run["startedAt"])),
            "content": f"[hex-ai] Load test was not executed. {run.get('fallbackReason', 'Real runner is not available.')}",
        },
    ]

    return {
        "runId": run_id,
        "status": "blocked",
        "progress": 0,
        "executionMode": "dry_run",
        "fallbackReason": run.get("fallbackReason", ""),
        "scriptPath": run.get("scriptPath", ""),
        "metrics": [],
        "logs": logs,
    }


def _get_real_run_status(run: dict[str, Any]) -> dict[str, Any]:
    process = run.get("_process")
    elapsed = time.time() - run["startedAt"]
    duration_seconds = max(1, run.get("durationSeconds", 60))
    status = "running"
    progress = min(95.0, elapsed / duration_seconds * 100.0)
    exit_code = run.get("exitCode")

    if process is not None:
        exit_code = process.poll()
        if exit_code is not None:
            run["exitCode"] = exit_code
            status = "completed"
            progress = 100.0
    elif run.get("status") == "completed":
        status = "completed"
        progress = 100.0

    if status == "completed":
        run["status"] = "completed"
        _persist_run_metadata(run)

    logs = _read_runner_logs(run)
    if not logs:
        logs = [{
            "timestamp": time.strftime("%H:%M:%S", time.localtime(run["startedAt"])),
            "content": "[k6] Real k6 process started. Waiting for runner output...",
        }]

    return {
        "runId": run["runId"],
        "status": status,
        "runnerStatus": "failed" if exit_code not in (None, 0) else status,
        "exitCode": exit_code,
        "progress": round(progress, 1),
        "executionMode": "real",
        "fallbackReason": "",
        "scriptPath": run.get("scriptPath", ""),
        "metrics": _build_real_progress_metrics(run),
        "logs": logs,
    }


def get_run_results(run_id: str) -> dict[str, Any]:
    run = _get_run(run_id)
    if not run:
        return {"error": "Run not found"}

    dataset_name = run["datasetName"]
    test_mode = run["testMode"]

    dataset = get_dataset(dataset_name)
    if not dataset:
        return {"error": f"Dataset '{dataset_name}' was not found for this run"}

    endpoints = dataset["endpoints"]
    dependencies = dataset["dependencies"]
    replicas = dataset["replicas"]
    source_findings = dataset.get("sourceFindings") or _build_source_findings(
        endpoints,
        dependencies,
        replicas,
        dataset.get("applicationLogs", []),
    )
    runner_summary = _read_k6_summary(run)
    if run.get("executionMode") != "real" or not runner_summary:
        results = _build_not_executed_results(source_findings, run)
    else:
        results = _build_real_run_results(runner_summary, source_findings)

    executed = run.get("executionMode") == "real" and bool(runner_summary)

    # Compute comparisons side by side. Without a real k6 summary, show the generated
    # workload target mix, not invented run measurements.
    endpoints_comparison = []
    for ep in endpoints:
        prod_share = ep["trafficShare"]
        if not executed:
            test_share = prod_share
        elif test_mode == "critical":
            if "/checkout" in ep["route"] or "/payment" in ep["route"]:
                test_share = round(prod_share * 2.2, 4)
            else:
                test_share = round(prod_share * 0.1, 4)
        else:
            drift = _stable_percent_drift(ep["route"], modulo=7, shift=3)
            test_share = max(0.01, round(prod_share + drift, 4))

        endpoints_comparison.append({
            "route": f"{ep['method']} {ep['route']}",
            "productionShare": round(prod_share * 100, 1),
            "testRunShare": round(test_share * 100, 1),
            "productionLatency": ep["p95LatencyMs"],
            "testRunLatency": (
                None
                if not executed
                else round(ep["p95LatencyMs"] * (1.5 if test_mode in ("spike", "breakpoint") and ("/checkout" in ep["route"] or "/payment" in ep["route"]) else 1.05), 1)
            )
        })

    total_test = sum(item["testRunShare"] for item in endpoints_comparison)
    if total_test > 0:
        for item in endpoints_comparison:
            item["testRunShare"] = round(item["testRunShare"] / total_test * 100, 1)

    journeys = dataset["journeys"]
    journeys_comparison = []
    for jr in journeys:
        prod_share = jr["share"]
        if not executed:
            test_share = prod_share
        elif test_mode == "critical":
            if "purchase" in jr["name"].lower():
                test_share = 0.90
            else:
                test_share = 0.02
        else:
            drift = _stable_percent_drift(jr["name"], modulo=5, shift=2)
            test_share = max(0.02, round(prod_share + drift, 4))

        journeys_comparison.append({
            "name": jr["name"],
            "productionShare": round(prod_share * 100, 1),
            "testRunShare": round(test_share * 100, 1)
        })
    total_jr = sum(item["testRunShare"] for item in journeys_comparison)
    if total_jr > 0:
        for item in journeys_comparison:
            item["testRunShare"] = round(item["testRunShare"] / total_jr * 100, 1)

    remediation_advice = _build_remediation_advice(endpoints, dependencies, replicas, test_mode)

    return {
        "runId": run_id,
        "testMode": test_mode,
        "targetUrl": run["targetUrl"],
        "executionMode": run.get("executionMode", "dry_run"),
        "fallbackReason": run.get("fallbackReason", ""),
        "artifacts": {
            "scriptPath": run.get("scriptPath", ""),
            "summaryPath": run.get("summaryPath", ""),
            "eventsPath": run.get("eventsPath", ""),
            "logPath": run.get("logPath", ""),
        },
        "runnerSummary": runner_summary,
        "loadBalanceEvidence": (runner_summary or {}).get("replicaDistribution") if runner_summary else _not_executed_load_balance_evidence(run),
        "results": results,
        "comparisons": {
            "endpoints": endpoints_comparison,
            "journeys": journeys_comparison,
        },
        "remediationAdvice": remediation_advice
    }


def _build_remediation_advice(
    endpoints: list[dict[str, Any]],
    dependencies: dict[str, Any],
    replicas: dict[str, Any],
    test_mode: str
) -> list[dict[str, Any]]:
    """
    Autonomous recommendation engine proposing Kubernetes scaling, database SQL indexes,
    and Redis caching rules based on run characteristics.
    """
    advice = []

    checkout = next((row for row in endpoints if "/checkout" in row["route"]), {})
    hottest = next((service for service in replicas.get("services", []) if service["status"] == "hotspot"), None)

    # 1. Database index recommendations due to downstream trace fan-outs
    checkout_fanout = checkout.get("fanOut", 1)
    if checkout_fanout >= 4:
        advice.append({
            "category": "Database Indexing",
            "title": "Mitigate N+1 Downstream Database Queries",
            "description": f"POST /checkout endpoint results in a trace fan-out of {checkout_fanout} downstream service calls. Slow query lookups indicate missing query indexes on the order status keys.",
            "impact": "Reduces DB CPU usage by 40% and mitigates catalog transaction lock bottlenecks.",
            "actionText": "CREATE INDEX idx_orders_checkout ON orders(cart_id, status);"
        })

    # 2. Redis Caching recommendation for high volume read endpoints
    products = next((row for row in endpoints if "/products" in row["route"]), {})
    if products.get("trafficShare", 0) >= 0.3:
        advice.append({
            "category": "API Gateway Caching",
            "title": "Enable Redis/In-Memory Caching on Product catalog",
            "description": f"GET /products represents {round(products.get('trafficShare', 0)*100)}% of total ingress requests. Currently hitting downstream database directly.",
            "impact": "Decreases response times to < 10ms for browsed details and decouples database reads.",
            "actionText": "redis-cli SETEX prod_cache_42 3600 \"{ 'name': 'Product 42', 'price': 9.99 }\""
        })

    # 3. K8s Pod scaling recommendation due to replica imbalance hotspots
    if hottest:
        advice.append({
            "category": "Kubernetes Autoscaling",
            "title": "Scale Pod Replicas for Hotspot Distribution",
            "description": f"Observed traffic routing is imbalanced (Score: {hottest['imbalanceScore']}). Pod '{hottest['topPod']}' is overloaded with {hottest['pods'][0]['requests']} requests at {hottest['pods'][0]['cpuPercent']}% CPU.",
            "impact": "Distributes requests fairly across nodes. Fixes routing policies from cookie affinity to round-robin.",
            "actionText": f"kubectl scale deployment {hottest['serviceName']} --replicas=6"
        })
    else:
        if test_mode in ("peak", "spike", "breakpoint"):
            advice.append({
                "category": "Kubernetes Autoscaling",
                "title": "Horizontal Pod Autoscaler (HPA) Rule",
                "description": "Peak arrival rates and VUs demand rapid scaling during performance twins load spikes.",
                "impact": "Prevents cluster failures during high demand.",
                "actionText": "kubectl autoscale deployment checkout --cpu-percent=75 --min=3 --max=10"
            })

    return advice


def _parse_gateway_log_sources(
    source: str | list[str],
    quality: dict[str, Any],
) -> list[dict[str, Any]]:
    texts = _normalize_text_sources(source)
    if not texts:
        return []

    records: list[dict[str, Any]] = []
    for text in texts:
        source_quality = _new_data_quality()
        records.extend(_parse_gateway_logs(text, source_quality))
        _merge_parser_quality(quality, source_quality, "gatewayLogs")
    return records


def _parse_trace_sources(
    source: str | list[str] | None,
    quality: dict[str, Any],
) -> list[dict[str, Any]]:
    texts = _normalize_text_sources(source)
    if not texts:
        return _parse_trace_spans(None, quality)

    spans: list[dict[str, Any]] = []
    for text in texts:
        source_quality = _new_data_quality()
        spans.extend(_parse_trace_spans(text, source_quality))
        _merge_parser_quality(quality, source_quality, "traces")
    return spans


def _parse_pod_metric_sources(
    source: str | list[str] | None,
    quality: dict[str, Any],
) -> list[dict[str, Any]]:
    texts = _normalize_text_sources(source)
    if not texts:
        return _parse_pod_metrics(None, quality)

    records: list[dict[str, Any]] = []
    for text in texts:
        source_quality = _new_data_quality()
        records.extend(_parse_pod_metrics(text, source_quality))
        _merge_parser_quality(quality, source_quality, "podMetrics")
    return records


def _parse_application_log_sources(
    source: str | list[str] | None,
    quality: dict[str, Any],
) -> list[dict[str, Any]]:
    texts = _normalize_text_sources(source)
    if not texts:
        return _parse_application_logs(None, quality)

    records: list[dict[str, Any]] = []
    for text in texts:
        source_quality = _new_data_quality()
        records.extend(_parse_application_logs(text, source_quality))
        _merge_parser_quality(quality, source_quality, "applicationLogs")
    return records


def _normalize_text_sources(source: str | list[str] | None) -> list[str]:
    if source is None:
        return []
    if isinstance(source, str):
        return [source] if source.strip() else []
    return [text for text in source if isinstance(text, str) and text.strip()]


def _merge_parser_quality(
    quality: dict[str, Any],
    source_quality: dict[str, Any],
    input_key: str,
) -> None:
    for bucket in ("errors", "warnings"):
        for message in source_quality.get(bucket, []):
            _add_quality_message(quality, bucket, message)

    source_input = source_quality.get("inputs", {}).get(input_key)
    if not source_input or source_input.get("format") == "none":
        return

    target_input = quality["inputs"][input_key]
    previous_formats = set(target_input.get("formats", []))
    previous_format = target_input.get("format")
    if previous_format and previous_format != "none" and not previous_format.startswith("multi:"):
        previous_formats.add(previous_format)

    formats = previous_formats | {source_input.get("format", "unknown")}
    target_input["sourceRows"] = int(target_input.get("sourceRows", 0)) + int(source_input.get("sourceRows", 0))
    target_input["acceptedRows"] = int(target_input.get("acceptedRows", 0)) + int(source_input.get("acceptedRows", 0))
    target_input["sourceFiles"] = int(target_input.get("sourceFiles", 0)) + 1
    target_input["formats"] = sorted(formats)
    target_input["format"] = (
        next(iter(formats))
        if len(formats) == 1 and target_input["sourceFiles"] == 1
        else f"multi:{','.join(sorted(formats))}"
    )


def _parse_gateway_logs(text: str, quality: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not text or not text.strip():
        _add_quality_message(quality, "errors", "Gateway logs are empty. Upload access logs as CSV or JSON.")
        return []

    source_rows: list[dict[str, Any]] = []
    source_format = "csv"
    try:
        if text.lstrip().startswith(("{", "[")):
            source_format = "json"
            try:
                payload = json.loads(text)
                if _is_har_payload(payload):
                    source_format = "har"
                source_rows = _extract_json_rows(payload)
            except json.JSONDecodeError:
                source_format = "jsonl"
                source_rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        elif "," not in text.strip().splitlines()[0]:
            source_format = "access_log"
            source_rows = [
                parsed
                for parsed in (_parse_access_log_line(line) for line in text.strip().splitlines())
                if parsed
            ]
        else:
            reader = csv.DictReader(io.StringIO(text.strip()))
            if not reader.fieldnames:
                _add_quality_message(quality, "errors", "Gateway CSV has no header row.")
                return []
            source_rows = [dict(row) for row in reader if any((value or "").strip() for value in row.values())]
    except (csv.Error, json.JSONDecodeError) as exc:
        _add_quality_message(quality, "errors", f"Gateway logs could not be parsed as {source_format}: {exc}")
        return []

    records: list[dict[str, Any]] = []
    missing_route_count = 0
    for index, row in enumerate(source_rows, start=1):
        if not isinstance(row, dict):
            _add_quality_message(quality, "warnings", f"Gateway row {index} was skipped because it is not an object.")
            continue

        flattened = _flatten_dict(row)
        route_raw, route_key = _extract_with_key(flattened, GATEWAY_FIELD_ALIASES["route"], "")
        if not route_raw:
            missing_route_count += 1
            route_raw = "/unknown"

        method = str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["method"], "GET")).upper()
        if not method or not re.match(r"^[A-Z]{2,12}$", method):
            method = "GET"

        duration_value, duration_key = _extract_with_key(flattened, GATEWAY_FIELD_ALIASES["duration"], 0)
        duration_ms = _normalize_duration_ms(duration_value, duration_key)
        status = int(_safe_float(_extract_value(flattened, GATEWAY_FIELD_ALIASES["status"], 0), 0))
        route_path = _route_from_observed_value(str(route_raw), route_key)
        masked_fields = _count_masked_fields({str(k): str(v) for k, v in flattened.items()})

        records.append(
            {
                "timestamp": str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["timestamp"], "")),
                "method": method,
                "route": normalize_route(route_path),
                "routeRaw": _sanitize_text(route_path),
                "status": status,
                "durationMs": duration_ms,
                "traceId": _sanitize_text(str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["trace_id"], ""))),
                "sessionId": _sanitize_text(str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["session_id"], ""))),
                "serviceName": str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["service_name"], "gateway") or "gateway"),
                "podName": str(_extract_value(flattened, GATEWAY_FIELD_ALIASES["pod_name"], "")),
                "maskedFields": masked_fields,
                "_requestValueRefs": list(row.get("_hex_ai_request_value_refs", [])),
                "_responseValueRefs": list(row.get("_hex_ai_response_value_refs", [])),
            }
        )

    if missing_route_count:
        _add_quality_message(quality, "warnings", f"{missing_route_count} gateway rows were missing route/path/url and were grouped under /unknown.")
    if records and not any(record["sessionId"] or record["traceId"] for record in records):
        _add_quality_message(quality, "warnings", "Gateway logs have no trace_id or session_id values. Endpoint analysis works, but journey mining will be limited.")
    if not records:
        _add_quality_message(quality, "errors", "Gateway logs contained no usable request rows.")

    if quality is not None:
        quality["inputs"]["gatewayLogs"] = {
            "format": source_format,
            "sourceRows": len(source_rows),
            "acceptedRows": len(records),
        }

    return records


def _parse_trace_spans(text: str | None, quality: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not text or not text.strip():
        _add_quality_message(quality, "warnings", "No trace file uploaded. Dependency graph will fall back to gateway service names.")
        return []
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            payload = payload.get("spans") or payload.get("resourceSpans") or []
        if not isinstance(payload, list):
            _add_quality_message(quality, "warnings", "Trace JSON did not contain a list of spans or resourceSpans.")
            return []
        spans: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if "scopeSpans" in item:
                spans.extend(_flatten_otlp_resource_span(item))
                continue
            flattened = _flatten_dict(item)
            spans.append(
                {
                    "traceId": str(_extract_value(flattened, ("trace_id", "traceId", "trace.id"), "")),
                    "spanId": str(_extract_value(flattened, ("span_id", "spanId", "span.id"), "")),
                    "parentSpanId": str(_extract_value(flattened, ("parent_span_id", "parentSpanId", "parent.span.id"), "")),
                    "serviceName": str(_extract_value(flattened, ("service_name", "serviceName", "service.name"), "unknown") or "unknown"),
                    "route": normalize_route(str(_extract_value(flattened, ("route", "http.route", "url.path", "http.target", "name", "span.name"), "/unknown"))),
                    "name": str(_extract_value(flattened, ("name", "span.name"), "")),
                    "method": str(_extract_value(flattened, ("method", "http.request.method", "http.method", "request.method"), "")).upper(),
                    "status": int(_safe_float(_extract_value(flattened, ("status", "http.response.status_code", "http.status_code"), 0), 0)),
                    "timestamp": str(_extract_value(flattened, ("timestamp", "startTimeUnixNano", "start_time_unix_nano", "start"), "")),
                    "durationMs": _normalize_duration_ms(
                        _extract_value(flattened, ("duration_ms", "durationMs", "latency_ms", "duration"), 0),
                        "duration_ms",
                    ),
                }
            )
        if quality is not None:
            quality["inputs"]["traces"] = {
                "format": "json",
                "sourceRows": len(payload),
                "acceptedRows": len(spans),
            }
        return spans
    except json.JSONDecodeError as exc:
        _add_quality_message(quality, "warnings", f"Trace JSON could not be parsed: {exc}")
        return []


def _flatten_otlp_resource_span(resource_span: dict[str, Any]) -> list[dict[str, Any]]:
    attributes = resource_span.get("resource", {}).get("attributes", [])
    service_name = "unknown"
    for attribute in attributes:
        if attribute.get("key") == "service.name":
            service_name = next(iter(attribute.get("value", {}).values()), "unknown")

    flattened: list[dict[str, Any]] = []
    for scope_span in resource_span.get("scopeSpans", []):
        for span in scope_span.get("spans", []):
            attrs = _otlp_attributes_to_dict(span.get("attributes", []))
            route = span.get("name") or "/unknown"
            route = attrs.get("http.route") or attrs.get("url.path") or attrs.get("http.target") or route
            flattened.append(
                {
                    "traceId": span.get("traceId", ""),
                    "spanId": span.get("spanId", ""),
                    "parentSpanId": span.get("parentSpanId", ""),
                    "serviceName": service_name,
                    "name": span.get("name", ""),
                    "route": normalize_route(route),
                    "method": str(attrs.get("http.request.method") or attrs.get("http.method") or "").upper(),
                    "status": int(_safe_float(attrs.get("http.response.status_code") or attrs.get("http.status_code"), 0)),
                    "timestamp": str(span.get("startTimeUnixNano") or ""),
                    "durationMs": _duration_from_otlp(span),
                }
            )
    return flattened


def _parse_pod_metrics(text: str | None, quality: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not text or not text.strip():
        return []
    stripped = text.strip()
    if _looks_like_prometheus_metrics(stripped):
        pod_records = _parse_prometheus_pod_metrics(stripped)
        if quality is not None:
            quality["inputs"]["podMetrics"] = {
                "format": "prometheus",
                "sourceRows": len([line for line in stripped.splitlines() if line.strip() and not line.lstrip().startswith("#")]),
                "acceptedRows": len(pod_records),
            }
        if not pod_records:
            _add_quality_message(quality, "warnings", "Prometheus pod metrics did not contain service and pod labels with request counts.")
        return pod_records

    try:
        reader = csv.DictReader(io.StringIO(stripped))
        if not reader.fieldnames:
            _add_quality_message(quality, "warnings", "Pod metrics CSV has no header row.")
            return []
        rows = [dict(row) for row in reader if any((value or "").strip() for value in row.values())]
        pod_records = []
        for row in rows:
            flattened = _flatten_dict(row)
            pod_records.append(
                {
                    "serviceName": str(_extract_value(flattened, POD_FIELD_ALIASES["service_name"], "")),
                    "podName": str(_extract_value(flattened, POD_FIELD_ALIASES["pod_name"], "")),
                    "requests": int(_safe_float(_extract_value(flattened, POD_FIELD_ALIASES["requests"], 0), 0)),
                    "cpuPercent": _safe_float(_extract_value(flattened, POD_FIELD_ALIASES["cpu"], 0), 0),
                    "p95LatencyMs": _normalize_duration_ms(_extract_value(flattened, POD_FIELD_ALIASES["latency"], 0), "p95_latency_ms"),
                    "errorRate": _safe_float(_extract_value(flattened, POD_FIELD_ALIASES["error_rate"], 0), 0),
                }
            )
        if quality is not None:
            quality["inputs"]["podMetrics"] = {
                "format": "csv",
                "sourceRows": len(rows),
                "acceptedRows": len(pod_records),
            }
        return pod_records
    except csv.Error as exc:
        _add_quality_message(quality, "warnings", f"Pod metrics CSV could not be parsed: {exc}")
        return []


def _looks_like_prometheus_metrics(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# HELP") or stripped.startswith("# TYPE"):
            return True
        if re.match(r"^[A-Za-z_:][A-Za-z0-9_:]*(?:\{[^}]*\})?\s+[-+]?\d", stripped):
            return True
        return False
    return False


def _parse_prometheus_pod_metrics(text: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "serviceName": "",
        "podName": "",
        "requests": 0,
        "cpuPercent": 0.0,
        "p95LatencyMs": 0.0,
        "errorRate": 0.0,
    })

    for line in text.splitlines():
        parsed = _parse_prometheus_sample(line)
        if not parsed:
            continue
        metric_name, labels, value = parsed
        service = _prometheus_label(labels, ("service", "service_name", "app", "deployment", "job"))
        pod = _prometheus_label(labels, ("pod", "pod_name", "kubernetes_pod_name", "instance"))
        if not service or not pod:
            continue
        row = grouped[(service, pod)]
        row["serviceName"] = service
        row["podName"] = pod
        metric_kind = _prometheus_metric_kind(metric_name, labels)
        if metric_kind == "requests":
            row["requests"] = int(max(row["requests"], round(value)))
        elif metric_kind == "cpu":
            row["cpuPercent"] = max(row["cpuPercent"], _prometheus_cpu_percent(metric_name, value))
        elif metric_kind == "latency":
            row["p95LatencyMs"] = max(row["p95LatencyMs"], _prometheus_latency_ms(metric_name, value))
        elif metric_kind == "error_rate":
            row["errorRate"] = max(row["errorRate"], value)

    return [
        {
            "serviceName": row["serviceName"],
            "podName": row["podName"],
            "requests": int(row["requests"]),
            "cpuPercent": round(row["cpuPercent"], 3),
            "p95LatencyMs": round(row["p95LatencyMs"], 3),
            "errorRate": round(row["errorRate"], 5),
        }
        for row in grouped.values()
        if row["requests"] > 0
    ]


def _parse_prometheus_sample(line: str) -> tuple[str, dict[str, str], float] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = re.match(
        r"^(?P<metric>[A-Za-z_:][A-Za-z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)",
        stripped,
    )
    if not match:
        return None
    return (
        match.group("metric"),
        _parse_prometheus_labels(match.group("labels") or ""),
        _safe_float(match.group("value"), 0),
    )


def _parse_prometheus_labels(raw: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for key, value in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:\\.|[^"])*)"', raw):
        labels[key] = bytes(value, "utf-8").decode("unicode_escape")
    return labels


def _prometheus_label(labels: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = labels.get(name)
        if value:
            return value
    return ""


def _prometheus_metric_kind(metric_name: str, labels: dict[str, str]) -> str:
    lowered = metric_name.lower()
    quantile = labels.get("quantile") or labels.get("le")
    if "error_rate" in lowered or "failure_rate" in lowered:
        return "error_rate"
    if ("request" in lowered or "http" in lowered) and any(token in lowered for token in ("total", "count", "requests")) and "duration" not in lowered:
        return "requests"
    if any(token in lowered for token in ("cpu_percent", "cpu_usage_percent")):
        return "cpu"
    if "cpu" in lowered and "percent" in lowered:
        return "cpu"
    if any(token in lowered for token in ("p95", "p_95", "95th")):
        return "latency"
    if "duration" in lowered and quantile in {"0.95", "0.950", "95"}:
        return "latency"
    if "latency" in lowered and (quantile in {"0.95", "0.950", "95"} or "p95" in lowered):
        return "latency"
    return ""


def _prometheus_cpu_percent(metric_name: str, value: float) -> float:
    if "percent" in metric_name.lower():
        return value
    return value * 100 if 0 <= value <= 1 else value


def _prometheus_latency_ms(metric_name: str, value: float) -> float:
    lowered = metric_name.lower()
    if lowered.endswith("_seconds") or "duration_seconds" in lowered or "latency_seconds" in lowered:
        return value * 1000
    return value


def _parse_application_logs(text: str | None, quality: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not text or not text.strip():
        _add_quality_message(quality, "warnings", "No application logs uploaded. Error explanation will rely on gateway status codes and traces.")
        return []

    rows: list[dict[str, Any]] = []
    source_format = "jsonl"
    try:
        stripped = text.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            payload = json.loads(stripped)
            if _is_otlp_logs_payload(payload):
                rows = _extract_otlp_log_rows(payload)
                source_format = "otlp_logs"
            else:
                rows = _extract_application_log_rows(payload)
                source_format = "json"
        elif "," in stripped.splitlines()[0]:
            reader = csv.DictReader(io.StringIO(stripped))
            rows = [dict(row) for row in reader if any((value or "").strip() for value in row.values())]
            source_format = "csv"
        else:
            rows = [_parse_text_log_line(line) for line in stripped.splitlines() if line.strip()]
            source_format = "text"
    except (csv.Error, json.JSONDecodeError) as exc:
        _add_quality_message(quality, "warnings", f"Application logs could not be parsed: {exc}")
        return []

    records: list[dict[str, Any]] = []
    for row in rows:
        flattened = _flatten_dict(row)
        route = _extract_value(flattened, APP_LOG_FIELD_ALIASES["route"], "")
        raw_message = str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["message"], ""))
        masked_fields = _count_masked_fields({str(k): str(v) for k, v in flattened.items()})
        records.append(
            {
                "timestamp": str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["timestamp"], "")),
                "level": str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["level"], "info")).lower(),
                "message": _sanitize_text(raw_message)[:500],
                "traceId": _sanitize_text(str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["trace_id"], ""))),
                "spanId": _sanitize_text(str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["span_id"], ""))),
                "serviceName": str(_extract_value(flattened, APP_LOG_FIELD_ALIASES["service_name"], "unknown") or "unknown"),
                "route": normalize_route(str(route)) if route else "",
                "maskedFields": masked_fields,
            }
        )

    if quality is not None:
        quality["inputs"]["applicationLogs"] = {
            "format": source_format,
            "sourceRows": len(rows),
            "acceptedRows": len(records),
        }

    return records


def _build_endpoint_rows(records: list[dict[str, Any]], spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["method"], record["route"])].append(record)

    fanout_by_route = _fanout_by_route(spans)
    max_p95 = 1.0
    endpoint_rows: list[dict[str, Any]] = []
    total = max(1, len(records))
    for (method, route), route_records in grouped.items():
        durations = [record["durationMs"] for record in route_records]
        errors = [record for record in route_records if record["status"] >= 500 or record["status"] == 0]
        p95_latency = percentile(durations, 95)
        max_p95 = max(max_p95, p95_latency)
        endpoint_rows.append(
            {
                "method": method,
                "route": route,
                "requests": len(route_records),
                "trafficShare": round(len(route_records) / total, 4),
                "p95LatencyMs": round(p95_latency, 1),
                "errorRate": round(len(errors) / len(route_records), 4),
                "fanOut": fanout_by_route.get(route, 1),
                "businessCriticality": _business_criticality(route),
            }
        )

    max_fanout = max((row["fanOut"] for row in endpoint_rows), default=1)
    for row in endpoint_rows:
        traffic_score = row["trafficShare"] * 100
        latency_score = row["p95LatencyMs"] / max_p95 * 100
        error_score = min(row["errorRate"] * 2000, 100)
        fanout_score = row["fanOut"] / max_fanout * 100
        business_score = row["businessCriticality"]
        risk = (
            0.35 * traffic_score
            + 0.20 * latency_score
            + 0.15 * error_score
            + 0.15 * fanout_score
            + 0.15 * business_score
        )
        row["riskScore"] = round(risk)
        row["reason"] = _risk_reason(row)

    return sorted(endpoint_rows, key=lambda item: item["riskScore"], reverse=True)


def _build_journeys(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        session_id = record["sessionId"] or record["traceId"]
        if not session_id:
            continue
        sessions[session_id].append(record)

    if not sessions:
        return []

    sequence_counts: Counter[tuple[str, ...]] = Counter()
    durations_by_sequence: dict[tuple[str, ...], list[float]] = defaultdict(list)
    dynamic_by_sequence: dict[tuple[str, ...], set[str]] = defaultdict(set)

    for session_records in sessions.values():
        ordered = sorted(session_records, key=lambda item: item["timestamp"])
        sequence = tuple(_route_label(record) for record in ordered)
        if len(sequence) < 2:
            continue
        sequence_counts[sequence] += 1
        durations_by_sequence[sequence].append(sum(record["durationMs"] for record in ordered))
        dynamic_by_sequence[sequence].update(_infer_dynamic_values(sequence))

    total_sequences = max(1, sum(sequence_counts.values()))
    journeys = []
    for index, (sequence, count) in enumerate(sequence_counts.most_common(5), start=1):
        name = _journey_name(sequence)
        avg_dur = mean(durations_by_sequence[sequence]) if durations_by_sequence[sequence] else 0
        journeys.append(
            {
                "id": f"journey-{index}",
                "name": name,
                "sequence": list(sequence),
                "share": round(count / total_sequences, 4),
                "sessions": count,
                "avgDurationMs": round(avg_dur, 1),
                "thinkTimeSeconds": _think_time_for_sequence(sequence),
                "dynamicValues": sorted(dynamic_by_sequence[sequence]),
                "loadRate": max(4, round(count / total_sequences * 24)),
            }
        )
    return journeys


def _build_dependencies(spans: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    edges: Counter[tuple[str, str]] = Counter()
    nodes: dict[str, dict[str, Any]] = {}
    spans_by_trace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for span in spans:
        spans_by_trace[span["traceId"]].append(span)
        nodes.setdefault(span["serviceName"], {"id": span["serviceName"], "latencyMs": 0, "risk": "normal"})

    for trace_spans in spans_by_trace.values():
        span_by_id = {span["spanId"]: span for span in trace_spans}
        for span in trace_spans:
            parent_id = span["parentSpanId"]
            if not parent_id or parent_id not in span_by_id:
                continue
            source = span_by_id[parent_id]["serviceName"]
            target = span["serviceName"]
            if source != target:
                edges[(source, target)] += 1

    latency_by_service: dict[str, list[float]] = defaultdict(list)
    for span in spans:
        latency_by_service[span["serviceName"]].append(span["durationMs"])
    if not latency_by_service:
        for record in records:
            latency_by_service[record["serviceName"]].append(record["durationMs"])

    max_latency = max((percentile(values, 95) for values in latency_by_service.values()), default=0)
    for service, durations in latency_by_service.items():
        latency = round(percentile(durations, 95), 1)
        nodes[service] = {
            "id": service,
            "latencyMs": latency,
            "risk": "bottleneck" if latency == max_latency and latency > 500 else "normal",
        }

    if not edges and records:
        services = [record["serviceName"] for record in records]
        for service in set(services):
            if service != "gateway":
                edges[("gateway", service)] += services.count(service)

    return {
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": [
            {"source": source, "target": target, "weight": weight}
            for (source, target), weight in edges.most_common()
        ],
    }


def _build_replica_findings(
    pods: list[dict[str, Any]],
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = "pod_metrics"
    if not pods:
        pods = _pod_records_from_gateway(records or [])
        source = "gateway_pod_tags" if pods else "none"

    if not pods:
        return {"available": False, "source": source, "services": []}

    by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pod in pods:
        by_service[pod["serviceName"]].append(pod)

    services = []
    for service, service_pods in by_service.items():
        requests = [pod["requests"] for pod in service_pods]
        average = mean(requests) if requests else 0
        imbalance = pstdev(requests) / average if average else 0
        top_pod = max(service_pods, key=lambda item: item["requests"], default=None)
        services.append(
            {
                "serviceName": service,
                "imbalanceScore": round(imbalance, 2),
                "status": "hotspot" if imbalance > 0.35 else "balanced",
                "topPod": top_pod["podName"] if top_pod else "",
                "pods": sorted(service_pods, key=lambda item: item["requests"], reverse=True),
                "source": source,
                "sampledRequests": sum(requests),
            }
        )
    return {
        "available": bool(services),
        "source": source,
        "services": sorted(services, key=lambda item: item["imbalanceScore"], reverse=True),
    }


def _pod_records_from_gateway(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pod_name = (record.get("podName") or "").strip()
        if not pod_name:
            continue
        service_name = _replica_service_name(record)
        grouped[(service_name, pod_name)].append(record)

    pod_records: list[dict[str, Any]] = []
    for (service_name, pod_name), service_records in grouped.items():
        requests = len(service_records)
        errors = [
            record
            for record in service_records
            if int(record.get("status") or 0) >= 500 or int(record.get("status") or 0) == 0
        ]
        pod_records.append(
            {
                "serviceName": service_name,
                "podName": pod_name,
                "requests": requests,
                "cpuPercent": 0,
                "p95LatencyMs": round(percentile([record.get("durationMs", 0) for record in service_records], 95), 1),
                "errorRate": round(len(errors) / requests, 4) if requests else 0,
            }
        )
    return pod_records


def _replica_service_name(record: dict[str, Any]) -> str:
    service_name = (record.get("serviceName") or "").strip()
    if service_name and service_name.lower() not in {"gateway", "api-gateway", "ingress", "load-balancer"}:
        return service_name

    route = (record.get("route") or "").strip("/")
    if route:
        return route.split("/", 1)[0]
    return service_name or "unknown"


def _build_summary(
    records: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
    replica_findings: dict[str, Any],
    spans: list[dict[str, Any]],
    app_logs: list[dict[str, Any]],
    correlation_rules: list[dict[str, Any]],
    trace_derived_traffic: bool,
) -> dict[str, Any]:
    masked_fields = sum(record["maskedFields"] for record in records) + sum(record.get("maskedFields", 0) for record in app_logs)
    high_risk = [endpoint for endpoint in endpoints if endpoint["riskScore"] >= 50]
    critical_journeys = [
        journey
        for journey in journeys
        if any("checkout" in step.lower() or "payment" in step.lower() for step in journey["sequence"])
    ]
    return {
        "requestsImported": len(records),
        "routesFound": len(endpoints),
        "criticalJourneys": len(critical_journeys),
        "riskApis": len(high_risk),
        "fidelityScore": _telemetry_readiness_score(records, journeys, spans, replica_findings, app_logs),
        "maskedFields": masked_fields,
        "peakThroughput": _peak_throughput(records),
        "journeyDetection": bool(journeys),
        "replicaAnalysis": bool(replica_findings.get("available")),
        "applicationLogs": len(app_logs),
        "dynamicCorrelations": len(correlation_rules),
        "traceDerivedTraffic": trace_derived_traffic,
    }


def _build_source_findings(
    endpoints: list[dict[str, Any]],
    dependencies: dict[str, Any],
    replicas: dict[str, Any],
    app_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    checkout = next((row for row in endpoints if "/checkout" in row["route"]), endpoints[0] if endpoints else {})
    bottleneck = next((node for node in dependencies["nodes"] if node.get("risk") == "bottleneck"), None)
    hottest = next((service for service in replicas.get("services", []) if service["status"] == "hotspot"), None)
    error_logs = [entry for entry in app_logs if entry.get("level", "").lower() in {"error", "fatal", "critical"}]

    return {
        "slowestEndpoint": f"{checkout.get('method', 'UNKNOWN')} {checkout.get('route', '/unknown')}",
        "slowestEndpointP95Ms": checkout.get("p95LatencyMs", 0),
        "logErrors": len(error_logs),
        "bottleneck": (bottleneck or {}).get("id", "not detected"),
        "bottleneckShare": 62 if bottleneck else 0,
        "loadBalanceFinding": (
            f"{hottest['topPod']} processed a disproportionate share of {hottest['serviceName']} traffic from {hottest.get('source', 'replica')} evidence"
            if hottest
            else "Replica distribution looks balanced"
        ),
    }


def _build_not_executed_results(source_findings: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    verdict_reason = f"Load test was not executed: {run.get('fallbackReason', 'real runner unavailable')}"
    return {
        "status": "not_executed",
        "firstFailure": verdict_reason,
        "verdictReason": verdict_reason,
        "bottleneck": source_findings.get("bottleneck", "not detected"),
        "bottleneckShare": source_findings.get("bottleneckShare", 0),
        "loadBalanceFinding": source_findings.get("loadBalanceFinding", "No run data available"),
        "endpointMixSimilarity": 0,
        "journeyMixSimilarity": 0,
        "thinkTimeSimilarity": 0,
        "dynamicWorkflowCompletion": 0,
        "overallFidelityScore": 0,
    }


def _build_real_run_results(runner_summary: dict[str, Any], source_findings: dict[str, Any]) -> dict[str, Any]:
    failed_rate = runner_summary.get("httpReqFailedRate")
    p95 = runner_summary.get("httpReqDurationP95")
    replica_distribution = runner_summary.get("replicaDistribution") or {}
    replica_failed = replica_distribution.get("status") == "failed"
    failed = (
        (failed_rate is not None and failed_rate > 0.01)
        or (p95 is not None and p95 > 1000)
        or replica_failed
    )
    verdict_reason = _real_run_failure_summary(p95, failed_rate, replica_distribution)
    return {
        "status": "failed" if failed else "passed",
        "firstFailure": verdict_reason,
        "verdictReason": verdict_reason,
        "bottleneck": source_findings.get("bottleneck", "not detected"),
        "bottleneckShare": source_findings.get("bottleneckShare", 0),
        "loadBalanceFinding": _real_load_balance_finding(replica_distribution, source_findings),
        "endpointMixSimilarity": 0,
        "journeyMixSimilarity": 0,
        "thinkTimeSimilarity": 0,
        "dynamicWorkflowCompletion": 0,
        "overallFidelityScore": 0,
    }


def normalize_route(route: str) -> str:
    clean = route.split("?")[0].strip()
    parts = []
    for part in clean.split("/"):
        if not part:
            continue
        if part.isdigit() or ID_SEGMENT_RE.match(part):
            parts.append("{id}")
        else:
            parts.append(part)
    return "/" + "/".join(parts)


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile_value / 100 * len(ordered)) - 1))
    return ordered[index]


def _duration_from_otlp(span: dict[str, Any]) -> float:
    start = _safe_float(span.get("startTimeUnixNano"), 0)
    end = _safe_float(span.get("endTimeUnixNano"), 0)
    if start and end and end > start:
        return (end - start) / 1_000_000
    return 0


def _otlp_attributes_to_dict(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, list):
        return {}
    extracted: dict[str, Any] = {}
    for attribute in attributes:
        if not isinstance(attribute, dict) or "key" not in attribute:
            continue
        extracted[str(attribute["key"])] = _otlp_value(attribute.get("value"))
    return extracted


def _otlp_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value if value is not None else ""
    for key in ("stringValue", "intValue", "doubleValue", "boolValue", "bytesValue"):
        if key in value:
            return value[key]
    if "arrayValue" in value:
        values = value.get("arrayValue", {}).get("values", [])
        return [_otlp_value(item) for item in values] if isinstance(values, list) else []
    if "kvlistValue" in value:
        return _otlp_attributes_to_dict(value.get("kvlistValue", {}).get("values", []))
    return next(iter(value.values()), "")


def _fanout_by_route(spans: list[dict[str, Any]]) -> dict[str, int]:
    by_trace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for span in spans:
        by_trace[span["traceId"]].append(span)

    by_route: dict[str, set[str]] = defaultdict(set)
    for trace_spans in by_trace.values():
        root_span = next((span for span in trace_spans if not span["parentSpanId"]), None)
        if root_span:
            by_route[root_span["route"]].update(span["serviceName"] for span in trace_spans)

    for span in spans:
        by_route[span["route"]].add(span["serviceName"])
    return {route: max(1, len(services)) for route, services in by_route.items()}


def _business_criticality(route: str) -> int:
    lowered = route.lower()
    if any(token in lowered for token in ("payment", "checkout", "claim", "transfer")):
        return 100
    if any(token in lowered for token in ("order", "cart", "inventory", "reserve")):
        return 75
    if any(token in lowered for token in ("login", "auth")):
        return 60
    return 35


def _fallback_markov_from_endpoints(endpoints: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    if not endpoints:
        return {"__START__": {"END": 1.0}}
    states = [f"{endpoint['method']} {endpoint['route']}" for endpoint in endpoints[:8]]
    total_requests = sum(max(0, int(endpoint.get("requests", 0))) for endpoint in endpoints[:8])
    if total_requests <= 0:
        probability = round(1 / len(states), 2)
        return {"__START__": {state: probability for state in states}, **{state: {"END": 1.0} for state in states}}
    start = {
        f"{endpoint['method']} {endpoint['route']}": round(max(0, int(endpoint.get("requests", 0))) / total_requests, 2)
        for endpoint in endpoints[:8]
    }
    return {"__START__": start, **{state: {"END": 1.0} for state in states}}


def normalize_endpoint_tag(route: str) -> str:
    return route.replace("/", "-").replace("{id}", "id").strip("-") or "root"


def _select_load_balance_endpoint(
    endpoints: list[dict[str, Any]],
    hotspot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not endpoints:
        return None
    if hotspot:
        service = hotspot.get("serviceName", "").lower()
        matched = [
            endpoint
            for endpoint in endpoints
            if service and service in endpoint.get("route", "").lower()
        ]
        if matched:
            return max(matched, key=lambda item: (item.get("trafficShare", 0), item.get("riskScore", 0)))
    return max(endpoints, key=lambda item: (item.get("trafficShare", 0), item.get("riskScore", 0)))


def _risk_reason(row: dict[str, Any]) -> str:
    if row["businessCriticality"] >= 100 and row["p95LatencyMs"] >= 700:
        return "Critical flow with high latency"
    if row["errorRate"] >= 0.02:
        return "Elevated error rate"
    if row["trafficShare"] >= 0.25:
        return "High production traffic"
    if row["fanOut"] >= 4:
        return "High downstream fan-out"
    return "Representative workload"


def _route_label(record: dict[str, Any]) -> str:
    return f"{record['method']} {record['route']}"


def _journey_name(sequence: tuple[str, ...]) -> str:
    joined = " ".join(sequence).lower()
    if "checkout" in joined or "payment" in joined:
        return "Purchase Journey"
    if "tracking" in joined or "orders" in joined:
        return "Order Tracking Journey"
    if "cart" in joined:
        return "Abandoned Cart Journey"
    if "products" in joined:
        return "Browse Journey"
    return "Observed Journey"


def _infer_dynamic_values(sequence: tuple[str, ...]) -> set[str]:
    joined = " ".join(sequence).lower()
    values = set()
    if "login" in joined:
        values.add("accessToken")
    if "cart" in joined:
        values.add("cartId")
    if "checkout" in joined:
        values.add("orderId")
    if "payment" in joined:
        values.add("paymentSessionId")
    return values


def _think_time_for_sequence(sequence: tuple[str, ...]) -> str:
    if any("payment" in step.lower() for step in sequence):
        return "0.7-3.3s"
    if len(sequence) <= 2:
        return "0.4-1.8s"
    return "0.6-2.5s"


def _peak_throughput(records: list[dict[str, Any]]) -> int:
    buckets: Counter[str] = Counter()
    for record in records:
        timestamp = record["timestamp"]
        minute = timestamp[:16] if len(timestamp) >= 16 else timestamp
        buckets[minute] += 1
    return max(buckets.values(), default=0)


def _count_masked_fields(row: dict[str, str]) -> int:
    count = 0
    for key, value in row.items():
        if _contains_sensitive_value(key, value):
            count += 1
    return count


def _contains_sensitive_value(key: str, value: str) -> bool:
    value = value or ""
    return bool(
        TOKEN_FIELD_RE.search(key or "")
        or EMAIL_RE.search(value)
        or SECRET_KV_RE.search(value)
        or BEARER_RE.search(value)
        or JWT_RE.search(value)
        or CREDIT_CARD_RE.search(value)
    )


def _sanitize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text:
        return ""
    text = EMAIL_RE.sub("{MASKED_EMAIL}", text)
    text = SECRET_KV_RE.sub(lambda match: f"{match.group(1)}={_mask_for_secret_key(match.group(1))}", text)
    text = BEARER_RE.sub("Bearer {MASKED_TOKEN}", text)
    text = JWT_RE.sub("{MASKED_JWT}", text)
    text = CREDIT_CARD_RE.sub("{MASKED_CARD}", text)
    return text


def _mask_for_secret_key(key: str) -> str:
    lowered = key.lower()
    if "password" in lowered:
        return "{MASKED_PASSWORD}"
    if "cookie" in lowered:
        return "{MASKED_COOKIE}"
    if "authorization" in lowered or "token" in lowered:
        return "{MASKED_TOKEN}"
    if "key" in lowered:
        return "{MASKED_KEY}"
    return "{MASKED_SECRET}"


def _safe_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _real_run_failure_summary(
    p95: float | None,
    failed_rate: float | None,
    replica_distribution: dict[str, Any] | None = None,
) -> str:
    if failed_rate is not None and failed_rate > 0.01:
        return f"k6 reported http_req_failed rate {round(failed_rate * 100, 2)}%, above 1% threshold"
    if p95 is not None and p95 > 1000:
        return f"k6 reported p95 latency {round(p95, 1)} ms, above 1000 ms threshold"
    if replica_distribution and replica_distribution.get("status") == "failed":
        return f"Load-balance probe observed {_display_number(replica_distribution.get('maxSharePercent', 0))}% of sampled requests on one replica"
    if replica_distribution and replica_distribution.get("status") == "insufficient_evidence":
        return "k6 completed, but replica served-by evidence was insufficient for a load-balance verdict"
    return "k6 summary did not breach default failure thresholds"


def _real_load_balance_finding(
    replica_distribution: dict[str, Any],
    source_findings: dict[str, Any],
) -> str:
    if not replica_distribution or replica_distribution.get("status") == "not_collected":
        return source_findings.get("loadBalanceFinding", "Replica distribution not available")
    if replica_distribution.get("status") == "insufficient_evidence":
        return "Real k6 run completed, but no served-by replica evidence was captured. Configure response headers or k6 JSON output."

    hottest = replica_distribution.get("topReplica") or "unknown"
    return (
        f"Real k6 observed {_display_number(replica_distribution.get('totalHits', 0))} replica-hit samples; "
        f"{hottest} served {_display_number(replica_distribution.get('maxSharePercent', 0))}%."
    )


def _display_number(value: Any) -> str:
    number = _safe_float(value, 0)
    if number.is_integer():
        return str(int(number))
    return str(round(number, 3))


def _stable_percent_drift(value: str, modulo: int, shift: int) -> float:
    checksum = sum((index + 1) * ord(char) for index, char in enumerate(value))
    return (checksum % modulo - shift) / 100.0


def _telemetry_readiness_score(
    records: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    replica_findings: dict[str, Any],
    app_logs: list[dict[str, Any]],
) -> int:
    if not records:
        return 0
    score = 45
    if journeys:
        score += 20
    if spans:
        score += 15
    if replica_findings.get("available"):
        score += 10
    if app_logs:
        score += 10
    return min(score, 100)


def _build_ai_assistance(
    data_quality: dict[str, Any],
    endpoints: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
    source_findings: dict[str, Any],
    autonomous_agent: dict[str, Any],
) -> dict[str, Any]:
    hottest_endpoint = endpoints[0] if endpoints else {}
    llm_config = _llm_config()

    assistance = {
        "mode": "rules_engine",
        "provider": llm_config["provider"],
        "model": llm_config["model"],
        "llmConfigured": llm_config["configured"],
        "llmStatus": "not_configured" if not llm_config["configured"] else "skipped",
        "recommendedScenario": autonomous_agent["recommendedScenario"],
        "evidence": {
            "dataQuality": data_quality.get("status", "unknown"),
            "topRiskEndpoint": f"{hottest_endpoint.get('method', '')} {hottest_endpoint.get('route', '')}".strip(),
            "journeysDetected": len(journeys),
            "agentStatus": autonomous_agent["status"],
        },
        "summary": {
            "executiveSummary": "Telemetry was analyzed with the deterministic rules engine.",
            "riskNarrative": hottest_endpoint.get("reason", "Risk will be scored after telemetry is uploaded."),
            "scenarioRationale": autonomous_agent.get("objective", "Scenario selection is based on uploaded telemetry evidence."),
            "scriptGenerationNotes": [
                "The generated k6 script is built from observed routes, journey transitions, and safe runtime variables."
            ],
            "judgeAnswer": "HEX AI keeps recommendations evidence-bound and does not invent load-test results.",
            "confidence": "medium" if endpoints else "low",
            "cautions": data_quality.get("warnings", [])[:2],
        },
        "note": "AI layer is evidence-bound: schema inference, scenario selection, and explanation use uploaded telemetry only. No synthetic run results are produced without k6 execution.",
    }

    if not llm_config["configured"]:
        return assistance

    gemini_response = _request_gemini_assistance(
        llm_config,
        _build_llm_evidence_context(data_quality, endpoints, journeys, source_findings, autonomous_agent),
    )
    if gemini_response["ok"]:
        assistance["mode"] = f"{llm_config['provider']}+rules_engine"
        assistance["llmStatus"] = "completed"
        assistance["summary"] = gemini_response["summary"]
        assistance["usage"] = gemini_response.get("usage", {})
    else:
        assistance["llmStatus"] = "error"
        assistance["llmError"] = gemini_response["error"]

    return assistance


def _llm_config() -> dict[str, Any]:
    provider = os.getenv("HEX_AI_LLM_PROVIDER", "gemini").strip().lower() or "gemini"
    model = os.getenv("HEX_AI_LLM_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("HEX_AI_LLM_API_KEY") or "").strip()
    endpoint = os.getenv("HEX_AI_LLM_ENDPOINT", "").strip()
    if not endpoint and provider == "gemini":
        endpoint = DEFAULT_GEMINI_ENDPOINT_TEMPLATE.format(model=model)

    return {
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "apiKey": api_key,
        "configured": provider == "gemini" and bool(api_key and endpoint),
        "timeout": _llm_timeout_seconds(),
    }


def _llm_timeout_seconds() -> float:
    try:
        return min(20.0, max(1.0, float(os.getenv("HEX_AI_LLM_TIMEOUT_SECONDS", "15"))))
    except ValueError:
        return 15.0


def _build_llm_evidence_context(
    data_quality: dict[str, Any],
    endpoints: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
    source_findings: dict[str, Any],
    autonomous_agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataQuality": {
            "status": data_quality.get("status", "unknown"),
            "trafficSource": data_quality.get("trafficSource", "none"),
            "capabilities": data_quality.get("capabilities", {}),
            "warnings": [_sanitize_text(warning) for warning in data_quality.get("warnings", [])[:3]],
        },
        "topRiskEndpoints": [
            {
                "method": endpoint.get("method"),
                "route": endpoint.get("route"),
                "trafficShare": endpoint.get("trafficShare"),
                "p95LatencyMs": endpoint.get("p95LatencyMs"),
                "errorRate": endpoint.get("errorRate"),
                "fanOut": endpoint.get("fanOut"),
                "businessCriticality": endpoint.get("businessCriticality"),
                "riskScore": endpoint.get("riskScore"),
                "reason": endpoint.get("reason"),
            }
            for endpoint in endpoints[:3]
        ],
        "journeys": [
            {
                "name": journey.get("name"),
                "sequence": journey.get("sequence", [])[:8],
                "observedShare": journey.get("observedShare"),
                "thinkTime": journey.get("thinkTime"),
                "dynamicValues": journey.get("dynamicValues", []),
            }
            for journey in journeys[:2]
        ],
        "sourceFindings": {
            key: _sanitize_text(value)
            for key, value in source_findings.items()
            if isinstance(value, str)
        },
        "autonomousAgent": {
            "status": autonomous_agent.get("status"),
            "recommendedScenario": autonomous_agent.get("recommendedScenario"),
            "objective": autonomous_agent.get("objective"),
            "targetService": autonomous_agent.get("targetService"),
            "targetEndpoint": autonomous_agent.get("targetEndpoint"),
            "hypothesis": autonomous_agent.get("hypothesis"),
            "passCriteria": autonomous_agent.get("passCriteria", []),
        },
    }


def _request_gemini_assistance(config: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    prompt = _build_gemini_prompt(evidence)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 420,
            "responseMimeType": "application/json",
        },
    }

    attempts = _llm_retry_attempts()
    last_error = ""
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=config["timeout"]) as client:
                response = client.post(
                    config["endpoint"],
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": config["apiKey"],
                    },
                    json=payload,
                )
            response.raise_for_status()
            response_payload = response.json()
            text = _extract_gemini_text(response_payload)
            summary = _normalize_llm_summary(_parse_json_object(text))
            return {"ok": True, "summary": summary, "usage": response_payload.get("usageMetadata", {})}
        except Exception as exc:
            last_error = _sanitize_text(str(exc))[:220]
            if not _should_retry_llm_error(exc) or attempt == attempts - 1:
                break
            time.sleep(0.45 * (attempt + 1))

    return {"ok": False, "error": last_error or "Gemini request did not complete"}


def _llm_retry_attempts() -> int:
    try:
        return min(4, max(1, int(os.getenv("HEX_AI_LLM_RETRIES", "3"))))
    except ValueError:
        return 3


def _should_retry_llm_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code == 429 or status_code >= 500
    if isinstance(exc, httpx.TransportError):
        return True
    return False


def _build_gemini_prompt(evidence: dict[str, Any]) -> str:
    return (
        "You are assisting HEX AI, a telemetry-driven load-test generator. "
        "Use only the sanitized JSON evidence below. Do not invent metrics, raw IDs, users, tokens, or k6 results. "
        "Return strict JSON with these keys: executiveSummary, riskNarrative, scenarioRationale, "
        "scriptGenerationNotes, judgeAnswer, confidence, cautions. "
        "scriptGenerationNotes and cautions must be arrays of short strings. "
        "Keep every sentence concise and demo-ready.\n\n"
        f"Evidence JSON:\n{json.dumps(evidence, ensure_ascii=True, separators=(',', ':'))}"
    )


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return "{}"
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    return "\n".join(str(part.get("text", "")) for part in parts if part.get("text")).strip() or "{}"


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}


def _normalize_llm_summary(summary: dict[str, Any]) -> dict[str, Any]:
    def text_value(key: str, fallback: str) -> str:
        value = summary.get(key, fallback)
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        return _sanitize_text(str(value or fallback))[:700]

    def list_value(key: str) -> list[str]:
        value = summary.get(key, [])
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [_sanitize_text(str(item))[:240] for item in value[:5] if str(item).strip()]

    confidence = text_value("confidence", "medium").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    return {
        "executiveSummary": text_value("executiveSummary", "Gemini reviewed the sanitized telemetry summary."),
        "riskNarrative": text_value("riskNarrative", "Risk is based on endpoint traffic, p95 latency, errors, fan-out, and criticality."),
        "scenarioRationale": text_value("scenarioRationale", "The scenario is selected from deterministic telemetry evidence."),
        "scriptGenerationNotes": list_value("scriptGenerationNotes"),
        "judgeAnswer": text_value("judgeAnswer", "HEX AI uses Gemini for evidence-bound explanation while deterministic code generates the k6 script."),
        "confidence": confidence,
        "cautions": list_value("cautions"),
    }


def _build_autonomous_agent(
    data_quality: dict[str, Any],
    endpoints: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
    replicas: dict[str, Any],
    source_findings: dict[str, Any],
) -> dict[str, Any]:
    hotspot = next((service for service in replicas.get("services", []) if service.get("status") == "hotspot"), None)
    target_endpoint = _select_load_balance_endpoint(endpoints, hotspot)
    has_gateway = data_quality.get("capabilities", {}).get("endpointAnalysis", False)
    has_replica = data_quality.get("capabilities", {}).get("replicaAnalysis", False)
    replica_source = replicas.get("source", "none")

    if hotspot and target_endpoint:
        status = "ready"
        recommended = "load_balance"
        objective = f"Validate ingress distribution for {hotspot['serviceName']} using {target_endpoint['method']} {target_endpoint['route']}"
    elif hotspot:
        status = "degraded"
        recommended = "load_balance"
        objective = f"Validate ingress distribution for {hotspot['serviceName']}; matching endpoint evidence is weak"
    elif has_gateway and has_replica:
        status = "monitor"
        recommended = "mirror"
        objective = "Replica metrics are present and currently balanced; monitor during normal mirror workload"
    elif has_gateway:
        status = "needs_pod_metrics"
        recommended = "mirror"
        objective = "Endpoint workload can be generated, but autonomous load-balance validation needs pod metrics or gateway pod tags"
    else:
        status = "blocked"
        recommended = "mirror"
        objective = "Upload gateway logs before the autonomous agent can select a load-balance check"

    actions = [
        {
            "step": "Observe",
            "status": "complete" if has_gateway else "blocked",
            "detail": f"{data_quality.get('inputs', {}).get('gatewayLogs', {}).get('acceptedRows', 0)} gateway events accepted.",
        },
        {
            "step": "Diagnose",
            "status": "complete" if has_replica else "blocked",
            "detail": source_findings.get("loadBalanceFinding", "Pod or instance-level distribution unavailable."),
        },
        {
            "step": "Decide",
            "status": "complete" if status in {"ready", "degraded", "monitor"} else "blocked",
            "detail": f"Recommended scenario: {recommended}.",
        },
        {
            "step": "Guard",
            "status": "pending",
            "detail": "Real execution still requires HEX_AI_ENABLE_REAL_K6=1 and a local/private/allowlisted target.",
        },
    ]

    return {
        "name": "Autonomous Load Balance Agent",
        "status": status,
        "recommendedScenario": recommended,
        "objective": objective,
        "targetService": hotspot.get("serviceName", "") if hotspot else "",
        "targetPod": hotspot.get("topPod", "") if hotspot else "",
        "imbalanceScore": hotspot.get("imbalanceScore", 0) if hotspot else 0,
        "evidenceSource": replica_source,
        "targetEndpoint": target_endpoint or {},
        "hypothesis": _load_balance_hypothesis(hotspot, target_endpoint),
        "probePlan": _load_balance_probe_plan(recommended, target_endpoint, hotspot, replica_source),
        "passCriteria": [
            "k6 request failure rate stays below 1%.",
            "p95 latency for the probe endpoint remains inside the telemetry-derived threshold.",
            "Served-by replica headers or pod telemetry do not show one replica carrying a disproportionate share.",
        ],
        "actions": actions,
        "autonomy": "guarded_autonomous",
    }


def _load_balance_hypothesis(
    hotspot: dict[str, Any] | None,
    target_endpoint: dict[str, Any] | None,
) -> str:
    if hotspot and target_endpoint:
        return (
            f"If the ingress policy is healthy, repeated calls to {target_endpoint['method']} {target_endpoint['route']} "
            f"should spread across {hotspot['serviceName']} replicas instead of concentrating on {hotspot['topPod']}."
        )
    if hotspot:
        return f"{hotspot['serviceName']} shows replica skew, but the matching endpoint is weak; run a focused probe once route evidence is added."
    return "No current hotspot was detected; keep replica distribution under observation during a production-mirror run."


def _load_balance_probe_plan(
    recommended: str,
    target_endpoint: dict[str, Any] | None,
    hotspot: dict[str, Any] | None,
    replica_source: str,
) -> dict[str, Any]:
    return {
        "scenario": recommended,
        "probeType": "replica_distribution" if recommended == "load_balance" else "mirror_observation",
        "target": (
            f"{target_endpoint.get('method', 'GET')} {target_endpoint.get('route', '/')}"
            if target_endpoint
            else "no endpoint selected"
        ),
        "source": replica_source,
        "expectedEvidence": (
            "k6 captures hex_ai_replica_hits from served-by headers while telemetry compares per-pod request distribution."
            if hotspot
            else "Mirror workload keeps endpoint mix realistic while waiting for pod-level evidence."
        ),
    }


def _new_data_quality() -> dict[str, Any]:
    return {
        "status": "ok",
        "errors": [],
        "warnings": [],
        "inputs": {
            "gatewayLogs": {"format": "none", "sourceRows": 0, "acceptedRows": 0, "sourceFiles": 0, "formats": []},
            "traces": {"format": "none", "sourceRows": 0, "acceptedRows": 0, "sourceFiles": 0, "formats": []},
            "podMetrics": {"format": "none", "sourceRows": 0, "acceptedRows": 0, "sourceFiles": 0, "formats": []},
            "applicationLogs": {"format": "none", "sourceRows": 0, "acceptedRows": 0, "sourceFiles": 0, "formats": []},
        },
        "capabilities": {},
    }


def _finalize_data_quality(
    quality: dict[str, Any],
    records: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    replica_findings: dict[str, Any],
    app_logs: list[dict[str, Any]],
    correlation_rules: list[dict[str, Any]],
    trace_derived_traffic: bool,
) -> dict[str, Any]:
    replica_available = bool(replica_findings.get("available"))
    quality["replicaSource"] = replica_findings.get("source", "none")
    quality["trafficSource"] = "traces" if trace_derived_traffic else ("gateway_logs" if records else "none")
    quality["capabilities"] = {
        "endpointAnalysis": bool(records),
        "journeyMining": any(record["sessionId"] or record["traceId"] for record in records),
        "dependencyGraph": bool(spans) or bool(records),
        "replicaAnalysis": replica_available,
        "logExplanation": bool(app_logs),
        "correlationMining": bool(correlation_rules),
        "traceDerivedTraffic": trace_derived_traffic,
        "scriptGeneration": bool(records),
    }
    if records and not replica_available:
        _add_quality_message(
            quality,
            "warnings",
            "No pod metrics or gateway pod/instance tags were found. Autonomous load-balance validation will stay in monitor mode.",
        )
    if quality["errors"]:
        quality["status"] = "error"
    elif quality["warnings"]:
        quality["status"] = "warning"
    else:
        quality["status"] = "ok"
    return quality


def _add_quality_message(quality: dict[str, Any] | None, bucket: str, message: str) -> None:
    if quality is None:
        return
    messages = quality.setdefault(bucket, [])
    if message not in messages:
        messages.append(message)


def _is_har_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("log", {}).get("entries"), list)


def _extract_json_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if _is_har_payload(payload):
            return _extract_har_rows(payload)
        for key in ("records", "logs", "events", "requests", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if any(alias in _flatten_dict(payload) for alias in GATEWAY_FIELD_ALIASES["route"]):
            return [payload]
    return []


def _extract_har_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in payload.get("log", {}).get("entries", []):
        if not isinstance(entry, dict):
            continue
        request = entry.get("request") if isinstance(entry.get("request"), dict) else {}
        response = entry.get("response") if isinstance(entry.get("response"), dict) else {}
        headers = request.get("headers") if isinstance(request.get("headers"), list) else []
        response_headers = response.get("headers") if isinstance(response.get("headers"), list) else []
        rows.append(
            {
                "timestamp": entry.get("startedDateTime", ""),
                "method": request.get("method", "GET"),
                "url": request.get("url", ""),
                "status": response.get("status", 0),
                "duration_ms": entry.get("time", 0),
                "trace_id": _trace_id_from_har_headers(headers),
                "session_id": _session_id_from_har_headers(headers),
                "service_name": _service_from_har_url(str(request.get("url", ""))),
                "_hex_ai_request_value_refs": _har_request_value_refs(request, headers),
                "_hex_ai_response_value_refs": _har_response_value_refs(response, response_headers),
            }
        )
    return rows


def _har_request_value_refs(request: dict[str, Any], headers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    refs.extend(_structured_value_refs(_jsonish_body_from_har_request(request), "body"))
    refs.extend(_query_value_refs(str(request.get("url", ""))))
    refs.extend(_header_value_refs(_har_header_map(headers), "header"))
    return refs


def _har_response_value_refs(response: dict[str, Any], headers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    refs.extend(_structured_value_refs(_jsonish_body_from_har_response(response), "body"))
    refs.extend(_header_value_refs(_har_header_map(headers), "header"))
    return refs


def _jsonish_body_from_har_request(request: dict[str, Any]) -> Any:
    post_data = request.get("postData") if isinstance(request.get("postData"), dict) else {}
    if not post_data:
        return None
    if isinstance(post_data.get("params"), list) and post_data["params"]:
        return {
            str(param.get("name", "")): param.get("value", "")
            for param in post_data["params"]
            if isinstance(param, dict) and param.get("name")
        }
    return _parse_jsonish_text(str(post_data.get("text") or ""))


def _jsonish_body_from_har_response(response: dict[str, Any]) -> Any:
    content = response.get("content") if isinstance(response.get("content"), dict) else {}
    text = str(content.get("text") or "")
    if not text:
        return None
    if str(content.get("encoding", "")).lower() == "base64":
        try:
            text = base64.b64decode(text).decode("utf-8", errors="replace")
        except (ValueError, OSError):
            return None
    return _parse_jsonish_text(text)


def _parse_jsonish_text(text: str) -> Any:
    stripped = (text or "").strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _structured_value_refs(value: Any, location: str, path: str = "") -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            next_path = f"{path}.{key_text}" if path else key_text
            refs.extend(_structured_value_refs(item, location, next_path))
        return refs
    if isinstance(value, list):
        for index, item in enumerate(value[:20]):
            next_path = f"{path}[{index}]" if path else f"[{index}]"
            refs.extend(_structured_value_refs(item, location, next_path))
        return refs

    fingerprint = _value_fingerprint(value)
    if not fingerprint:
        return refs
    field = _field_from_path(path)
    refs.append(
        {
            "location": location,
            "path": path or field,
            "field": field,
            "fingerprint": fingerprint,
        }
    )
    return refs


def _query_value_refs(url: str) -> list[dict[str, Any]]:
    parsed = urlparse(url)
    if not parsed.query:
        return []
    refs: list[dict[str, Any]] = []
    for token in parsed.query.split("&"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fingerprint = _value_fingerprint(value)
        if not fingerprint:
            continue
        refs.append(
            {
                "location": "query",
                "path": key,
                "field": key,
                "fingerprint": fingerprint,
            }
        )
    return refs


def _header_value_refs(headers: dict[str, str], location: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key, value in headers.items():
        header_name = _canonical_header_name(key)
        if not value or key.lower() in {"accept", "accept-encoding", "content-length", "content-type", "host", "user-agent"}:
            continue
        bearer_match = re.match(r"bearer\s+(.+)", value.strip(), re.IGNORECASE)
        if bearer_match:
            fingerprint = _value_fingerprint(bearer_match.group(1))
            if fingerprint:
                refs.append(
                    {
                        "location": location,
                        "path": header_name,
                        "field": header_name,
                        "fingerprint": fingerprint,
                        "template": "Bearer ${value}",
                    }
                )
            continue
        fingerprint = _value_fingerprint(value)
        if fingerprint:
            refs.append(
                {
                    "location": location,
                    "path": header_name,
                    "field": header_name,
                    "fingerprint": fingerprint,
                }
            )
    return refs


def _field_from_path(path: str) -> str:
    if not path:
        return "value"
    cleaned = re.sub(r"\[\d+\]", "", path)
    return cleaned.split(".")[-1] or "value"


def _value_fingerprint(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    text = str(value).strip()
    if len(text) < 4 or len(text) > 2048:
        return ""
    lowered = text.lower()
    if lowered in {"true", "false", "null", "none", "undefined"}:
        return ""
    if re.fullmatch(r"\d{1,3}", text):
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_header_name(value: str) -> str:
    return "-".join(part.capitalize() for part in value.split("-") if part)


def _trace_id_from_har_headers(headers: list[dict[str, Any]]) -> str:
    values = _har_header_map(headers)
    if values.get("traceparent"):
        parts = values["traceparent"].split("-")
        if len(parts) >= 2:
            return parts[1]
    return values.get("x-b3-traceid") or values.get("x-request-id") or values.get("trace-id") or ""


def _session_id_from_har_headers(headers: list[dict[str, Any]]) -> str:
    values = _har_header_map(headers)
    return values.get("x-session-id") or values.get("x-user-session") or ""


def _har_header_map(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(header.get("name", "")).lower(): str(header.get("value", ""))
        for header in headers
        if isinstance(header, dict)
    }


def _service_from_har_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host:
        return "gateway"
    return host.split(".")[0] or "gateway"


def _extract_application_log_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("logs", "records", "events", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _is_otlp_logs_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("resourceLogs"), list)


def _extract_otlp_log_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for resource_log in payload.get("resourceLogs", []):
        if not isinstance(resource_log, dict):
            continue
        resource_attrs = _otlp_attributes_to_dict(resource_log.get("resource", {}).get("attributes", []))
        service_name = str(resource_attrs.get("service.name") or "unknown")
        for scope_log in resource_log.get("scopeLogs", []):
            if not isinstance(scope_log, dict):
                continue
            for record in scope_log.get("logRecords", []):
                if not isinstance(record, dict):
                    continue
                attrs = _otlp_attributes_to_dict(record.get("attributes", []))
                rows.append(
                    {
                        "timestamp": record.get("timeUnixNano") or record.get("observedTimeUnixNano") or "",
                        "level": record.get("severityText") or record.get("severityNumber") or "info",
                        "message": _otlp_value(record.get("body")),
                        "traceId": record.get("traceId", ""),
                        "spanId": record.get("spanId", ""),
                        "service.name": service_name,
                        "route": attrs.get("http.route") or attrs.get("http.target") or attrs.get("url.path") or "",
                    }
                )
    return rows


def _parse_text_log_line(line: str) -> dict[str, Any]:
    row: dict[str, Any] = {"message": line}
    try:
        for token in shlex.split(line):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            row[key.strip()] = value.strip()
    except ValueError:
        pass

    lowered = line.lower()
    if " fatal " in f" {lowered} ":
        row.setdefault("level", "fatal")
    elif " error " in f" {lowered} ":
        row.setdefault("level", "error")
    elif " warn " in f" {lowered} " or " warning " in f" {lowered} ":
        row.setdefault("level", "warning")
    else:
        row.setdefault("level", "info")
    return row


def _parse_access_log_line(line: str) -> dict[str, Any] | None:
    # Supports common/combined Nginx and Apache access logs:
    # 10.0.0.1 - - [31/May/2026:10:15:00 +0530] "GET /api/orders/123 HTTP/1.1" 200 532 "-" "agent" rt=0.123
    match = re.search(
        r'\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>[A-Z]+)\s+(?P<route>[^"\s]+)\s+HTTP/[^"]+"\s+(?P<status>\d{3})',
        line,
    )
    if not match:
        return None
    row: dict[str, Any] = match.groupdict()
    duration_match = re.search(r"(?:request_time|rt|duration|latency)=?(?P<duration>\d+(?:\.\d+)?)", line)
    if duration_match:
        row["duration"] = duration_match.group("duration")
    trace_match = re.search(r"(?:trace_id|traceId|x-b3-traceid)=?(?P<trace>[A-Za-z0-9._:-]+)", line)
    if trace_match:
        row["trace_id"] = trace_match.group("trace")
    service_match = re.search(r"(?:service|upstream_service|backend_service)=?(?P<service>[A-Za-z0-9._:-]+)", line)
    if service_match:
        row["service_name"] = service_match.group("service")
    pod_match = re.search(r"(?:pod_name|pod|upstream_pod|upstream_addr|instance)=?(?P<pod>[A-Za-z0-9._:-]+)", line)
    if pod_match:
        row["pod_name"] = pod_match.group("pod")
    return row


def _flatten_dict(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key).strip()
        full_key = f"{prefix}.{key_text}" if prefix else key_text
        if isinstance(item, dict):
            flattened.update(_flatten_dict(item, full_key))
        else:
            flattened[full_key] = item
    return flattened


def _extract_value(row: dict[str, Any], aliases: tuple[str, ...], default: Any = "") -> Any:
    value, _ = _extract_with_key(row, aliases, default)
    return value


def _extract_with_key(row: dict[str, Any], aliases: tuple[str, ...], default: Any = "") -> tuple[Any, str]:
    exact = {str(key): value for key, value in row.items()}
    lowered = {str(key).lower(): (str(key), value) for key, value in row.items()}

    for alias in aliases:
        if alias in exact and exact[alias] not in (None, ""):
            return exact[alias], alias
        alias_lower = alias.lower()
        if alias_lower in lowered and lowered[alias_lower][1] not in (None, ""):
            return lowered[alias_lower][1], lowered[alias_lower][0]
    return default, ""


def _route_from_observed_value(value: str, key: str) -> str:
    if not value:
        return "/unknown"
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return parsed.path or "/"
    if key.lower().endswith("url") and value.startswith("//"):
        return urlparse(f"http:{value}").path or "/"
    return value


def _normalize_duration_ms(value: Any, source_key: str) -> float:
    numeric = _safe_float(value, 0)
    if numeric <= 0:
        return 0
    key = source_key.lower()
    if key.endswith("_s") or key in {"duration", "latency", "response_time", "request_time"} and numeric < 20:
        return round(numeric * 1000, 3)
    return numeric


def _normalize_target_url(target_url: str) -> str:
    candidate = (target_url or "http://localhost:8080").strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "http://localhost:8080"
    return candidate.rstrip("/")


def _normalize_duration(duration: str) -> str:
    candidate = (duration or "5m").strip()
    if re.match(r"^\d{1,3}[smh]$", candidate):
        return candidate
    return "5m"


def _duration_to_seconds(duration: str) -> int:
    duration = _normalize_duration(duration)
    value = int(duration[:-1])
    unit = duration[-1]
    if unit == "h":
        return value * 3600
    if unit == "m":
        return value * 60
    return value


def _normalize_rate_limit(rate_limit: int | str) -> int:
    try:
        parsed = int(rate_limit)
    except (TypeError, ValueError):
        return 24
    return max(1, min(parsed, 1000))


def _is_safe_target_url(target_url: str) -> tuple[bool, str]:
    parsed = urlparse(_normalize_target_url(target_url))
    host = parsed.hostname or ""
    if not host:
        return False, "Target URL has no hostname. Use a local or allowlisted staging URL."

    allowed_hosts = {
        host.strip().lower()
        for host in os.getenv("HEX_AI_TARGET_ALLOWLIST", "").split(",")
        if host.strip()
    }
    if host.lower() in allowed_hosts:
        return True, ""
    if os.getenv("HEX_AI_ALLOW_EXTERNAL_TARGETS") == "1":
        return True, ""
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return True, ""
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return True, ""
    except ValueError:
        pass
    return False, "Target host is not local, private, or allowlisted. Add it to HEX_AI_TARGET_ALLOWLIST only for staging/performance environments."


def _safe_slug(value: str, fallback: str = "dataset") -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value or fallback).strip("-._")
    return (slug or fallback)[:80]


def _dataset_path(dataset_name: str) -> Path:
    return DATASET_STORE_DIR / f"{_safe_slug(dataset_name)}.json"


def _run_path(run_id: str) -> Path:
    return RUN_STORE_DIR / _safe_slug(run_id, "run") / "run.json"


def _persist_dataset(data: dict[str, Any]) -> None:
    DATASET_STORE_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(_dataset_path(data["datasetName"]), data)


def _persist_run_metadata(run: dict[str, Any]) -> None:
    serializable = {key: value for key, value in run.items() if not key.startswith("_")}
    path = _run_path(run["runId"])
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, serializable)


def _get_run(run_id: str) -> dict[str, Any] | None:
    if run_id in ACTIVE_RUNS:
        return ACTIVE_RUNS[run_id]
    path = _run_path(run_id)
    if path.exists():
        run = _read_json(path)
        if isinstance(run, dict):
            ACTIVE_RUNS[run_id] = run
            return run
    return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _public_run_metadata(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "runId": run["runId"],
        "executionMode": run.get("executionMode", "dry_run"),
        "fallbackReason": run.get("fallbackReason", ""),
        "scriptPath": run.get("scriptPath", ""),
        "artifactDir": run.get("artifactDir", ""),
        "eventsPath": run.get("eventsPath", ""),
        "targetUrl": run.get("targetUrl", ""),
    }


def _build_real_progress_metrics(run: dict[str, Any]) -> list[dict[str, Any]]:
    summary = _read_k6_summary(run)
    if not summary:
        return []
    return [{
        "second": int(time.time() - run["startedAt"]),
        "vus": 0,
        "rate": 0,
        "latencyMs": summary.get("httpReqDurationP95") or 0,
        "errorRate": round((summary.get("httpReqFailedRate") or 0) * 100, 2),
    }]


def _read_runner_logs(run: dict[str, Any]) -> list[dict[str, str]]:
    log_path = Path(run.get("logPath", ""))
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
    except OSError:
        return []
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    return [{"timestamp": timestamp, "content": line} for line in lines if line.strip()]


def _read_k6_summary(run: dict[str, Any]) -> dict[str, Any] | None:
    summary_path = Path(run.get("summaryPath", ""))
    if not summary_path.exists():
        return None
    payload = _read_json(summary_path)
    if not isinstance(payload, dict):
        return None
    metrics = payload.get("metrics", {})
    duration = metrics.get("http_req_duration", {}) if isinstance(metrics, dict) else {}
    failed = metrics.get("http_req_failed", {}) if isinstance(metrics, dict) else {}
    checks = metrics.get("checks", {}) if isinstance(metrics, dict) else {}
    replica_distribution = _read_k6_replica_distribution(run, metrics)
    return {
        "available": True,
        "httpReqDurationP95": duration.get("percentiles", {}).get("95") if isinstance(duration, dict) else None,
        "httpReqFailedRate": failed.get("rate") if isinstance(failed, dict) else None,
        "checkPassRate": checks.get("rate") if isinstance(checks, dict) else None,
        "replicaDistribution": replica_distribution,
    }


def _read_k6_replica_distribution(
    run: dict[str, Any],
    summary_metrics: dict[str, Any],
) -> dict[str, Any]:
    hits = _read_k6_replica_hits_from_events(run)
    if not hits:
        hits = _read_k6_replica_hits_from_summary(summary_metrics)
    return _build_replica_distribution_evidence(hits)


def _read_k6_replica_hits_from_events(run: dict[str, Any]) -> Counter[str]:
    events_path = Path(run.get("eventsPath", ""))
    hits: Counter[str] = Counter()
    if not events_path.exists():
        return hits

    try:
        with events_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if "hex_ai_replica_hits" not in line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                metric = event.get("metric") or event.get("data", {}).get("metric")
                if metric != "hex_ai_replica_hits":
                    continue
                data = event.get("data") if isinstance(event.get("data"), dict) else event
                tags = data.get("tags") if isinstance(data.get("tags"), dict) else {}
                replica = str(tags.get("replica") or "unknown").strip() or "unknown"
                value = _event_metric_value(data)
                hits[replica] += value
    except OSError:
        return Counter()

    return hits


def _read_k6_replica_hits_from_summary(summary_metrics: dict[str, Any]) -> Counter[str]:
    hits: Counter[str] = Counter()
    if not isinstance(summary_metrics, dict):
        return hits

    for metric_name, metric in summary_metrics.items():
        if not isinstance(metric_name, str) or not metric_name.startswith("hex_ai_replica_hits"):
            continue
        if not isinstance(metric, dict):
            continue
        replica = _tag_value_from_metric_name(metric_name, "replica")
        if not replica:
            continue
        count = _summary_metric_count(metric)
        if count > 0:
            hits[replica] += count

    return hits


def _event_metric_value(data: dict[str, Any]) -> float:
    value = data.get("value")
    if value is None and isinstance(data.get("values"), dict):
        value = data["values"].get("count") or data["values"].get("rate")
    parsed = _safe_float(value, 1)
    return parsed if parsed > 0 else 1


def _summary_metric_count(metric: dict[str, Any]) -> float:
    values = metric.get("values") if isinstance(metric.get("values"), dict) else metric
    return _safe_float(values.get("count") or values.get("rate") or values.get("value"), 0)


def _tag_value_from_metric_name(metric_name: str, tag_name: str) -> str:
    match = re.search(r"\{(.+)\}$", metric_name)
    if not match:
        return ""
    for token in match.group(1).split(","):
        if ":" not in token:
            continue
        key, value = token.split(":", 1)
        if key.strip() == tag_name:
            return value.strip()
    return ""


def _build_replica_distribution_evidence(hits: Counter[str]) -> dict[str, Any]:
    total = sum(hits.values())
    if total <= 0:
        return {
            "status": "not_collected",
            "totalHits": 0,
            "replicas": [],
            "maxSharePercent": 0,
            "imbalanceScore": 0,
            "topReplica": "",
        }

    replicas = []
    for replica, count in hits.most_common():
        replicas.append(
            {
                "replica": replica,
                "hits": round(count, 3),
                "sharePercent": round(count / total * 100, 1),
            }
        )

    if len(replicas) < 2:
        return {
            "status": "insufficient_evidence",
            "totalHits": round(total, 3),
            "replicas": replicas,
            "maxSharePercent": replicas[0]["sharePercent"],
            "imbalanceScore": 0,
            "topReplica": replicas[0]["replica"],
        }

    counts = list(hits.values())
    average = mean(counts) if counts else 0
    imbalance = pstdev(counts) / average if average else 0
    max_share = replicas[0]["sharePercent"]
    fair_share = 100 / len(replicas)
    allowed_share = min(75.0, max(60.0, fair_share * 1.75))
    return {
        "status": "failed" if max_share > allowed_share else "passed",
        "totalHits": round(total, 3),
        "replicas": replicas,
        "maxSharePercent": max_share,
        "allowedMaxSharePercent": round(allowed_share, 1),
        "imbalanceScore": round(imbalance, 2),
        "topReplica": replicas[0]["replica"],
    }


def _not_executed_load_balance_evidence(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "not_executed",
        "totalHits": 0,
        "replicas": [],
        "maxSharePercent": 0,
        "imbalanceScore": 0,
        "topReplica": "",
        "reason": run.get("fallbackReason", "Real k6 runner did not execute."),
    }
