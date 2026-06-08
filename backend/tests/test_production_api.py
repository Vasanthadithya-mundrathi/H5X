from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import zipfile

from fastapi.testclient import TestClient

from backend.app.analyzer import ACTIVE_RUNS
from backend.app.main import app


client = TestClient(app)


def test_demo_api_is_not_available() -> None:
    response = client.get("/api/demo")
    assert response.status_code == 404


def test_upload_accepts_jsonl_gateway_and_application_logs() -> None:
    gateway = (
        b'{"timestamp":"2026-05-31T10:00:00Z","method":"GET","url":"http://shop.internal/products/123",'
        b'"status":200,"duration_ms":85,"traceId":"t1","sessionId":"s1","service.name":"gateway"}\n'
        b'{"timestamp":"2026-05-31T10:00:02Z","method":"POST","path":"/cart",'
        b'"status_code":201,"latency_ms":140,"trace_id":"t1","session_id":"s1","service":"cart"}\n'
    )
    application_logs = b'2026-05-31T10:00:03Z level=error service=cart trace_id=t1 message="cart validation warning"\n'

    response = client.post(
        "/api/datasets/upload",
        files={
            "gateway_logs": ("gateway.jsonl", gateway, "application/x-ndjson"),
            "application_logs": ("app.log", application_logs, "text/plain"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["requestsImported"] == 2
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["format"] == "jsonl"
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["acceptedRows"] == 1
    assert payload["dataQuality"]["capabilities"]["logExplanation"] is True
    assert payload["aiAssistance"]["mode"] == "rules_engine"


def test_upload_accepts_nginx_style_access_logs() -> None:
    access_log = (
        b'10.0.0.1 - - [31/May/2026:10:15:00 +0530] "GET /orders/123 HTTP/1.1" 200 532 "-" "agent" rt=0.123 trace_id=t9\n'
        b'10.0.0.1 - - [31/May/2026:10:15:02 +0530] "POST /orders/123/pay HTTP/1.1" 201 100 "-" "agent" request_time=0.245 trace_id=t9\n'
    )

    response = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("access.log", access_log, "text/plain")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["routesFound"] == 2
    assert payload["endpoints"][0]["route"] in {"/orders/{id}", "/orders/{id}/pay"}
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["format"] == "access_log"


def test_upload_accepts_multiple_gateway_and_application_log_files() -> None:
    gateway_csv = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/products,200,80,t1,s1,catalog,catalog-pod-1
2026-05-31T10:00:01Z,POST,/cart,201,120,t1,s1,cart,cart-pod-1
"""
    gateway_access = (
        b'10.0.0.1 - - [31/May/2026:10:15:00 +0530] "GET /products/42 HTTP/1.1" 200 532 "-" "agent" rt=0.123 trace_id=t2\n'
    )
    app_json = b'{"timestamp":"2026-05-31T10:00:01Z","level":"error","message":"cart failed once","service":"cart","traceId":"t1"}'
    app_text = b'2026-05-31T10:00:02Z level=warning service=catalog trace_id=t2 message="slow catalog lookup"\n'

    response = client.post(
        "/api/datasets/upload",
        files=[
            ("gateway_logs", ("gateway-a.csv", gateway_csv, "text/csv")),
            ("gateway_logs", ("gateway-b.log", gateway_access, "text/plain")),
            ("application_logs", ("app-a.json", app_json, "application/json")),
            ("application_logs", ("app-b.log", app_text, "text/plain")),
        ],
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["datasetName"] == "gateway-a.csv+1-files"
    assert payload["summary"]["requestsImported"] == 3
    assert payload["summary"]["routesFound"] == 3
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["sourceFiles"] == 2
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["acceptedRows"] == 3
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["format"] == "multi:access_log,csv"
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["sourceFiles"] == 2
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["acceptedRows"] == 2
    assert payload["dataQuality"]["capabilities"]["logExplanation"] is True


def test_upload_expands_gzip_and_zip_telemetry_archives() -> None:
    gateway_csv = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/orders,200,75,t1,s1,orders,orders-pod-1
"""
    gateway_access = (
        b'10.0.0.1 - - [31/May/2026:10:15:00 +0530] "POST /orders/42/pay HTTP/1.1" 201 532 "-" "agent" rt=0.223 trace_id=t1\n'
    )
    gateway_archive = io.BytesIO()
    with zipfile.ZipFile(gateway_archive, "w") as archive:
        archive.writestr("gateway-a.csv", gateway_csv)
        archive.writestr("gateway-b.log", gateway_access)
        archive.writestr("__MACOSX/ignored.txt", "ignored")

    application_log = gzip.compress(
        b'{"timestamp":"2026-05-31T10:00:01Z","level":"error","message":"payment retry","service":"payment","traceId":"t1"}'
    )

    response = client.post(
        "/api/datasets/upload",
        files=[
            ("gateway_logs", ("gateway-archive.zip", gateway_archive.getvalue(), "application/zip")),
            ("application_logs", ("app-log.json.gz", application_log, "application/gzip")),
        ],
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["requestsImported"] == 2
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["sourceFiles"] == 2
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["format"] == "multi:access_log,csv"
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["sourceFiles"] == 1
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["format"] == "json"
    assert payload["dataQuality"]["capabilities"]["logExplanation"] is True


def test_upload_accepts_har_gateway_and_otlp_resource_logs() -> None:
    har_payload = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-05-31T10:00:00Z",
                    "time": 110,
                    "request": {
                        "method": "GET",
                        "url": "https://shop.example.com/api/products/123",
                        "headers": [{"name": "traceparent", "value": "00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01"}],
                    },
                    "response": {"status": 200},
                },
                {
                    "startedDateTime": "2026-05-31T10:00:02Z",
                    "time": 180,
                    "request": {
                        "method": "POST",
                        "url": "https://shop.example.com/api/cart",
                        "headers": [{"name": "x-session-id", "value": "session-1"}],
                    },
                    "response": {"status": 201},
                },
            ]
        }
    }
    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "checkout"}},
                    ]
                },
                "scopeLogs": [
                    {
                        "logRecords": [
                            {
                                "timeUnixNano": "1780212000000000000",
                                "severityText": "ERROR",
                                "body": {"stringValue": "checkout payment timeout"},
                                "traceId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                "spanId": "bbbbbbbbbbbbbbbb",
                                "attributes": [
                                    {"key": "http.route", "value": {"stringValue": "/api/cart"}},
                                ],
                            }
                        ]
                    }
                ],
            }
        ]
    }

    response = client.post(
        "/api/datasets/upload",
        files={
            "gateway_logs": ("browser-traffic.har", json.dumps(har_payload).encode("utf-8"), "application/json"),
            "application_logs": ("otlp-logs.json", json.dumps(otlp_logs).encode("utf-8"), "application/json"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["requestsImported"] == 2
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["format"] == "har"
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["format"] == "otlp_logs"
    assert payload["dataQuality"]["inputs"]["applicationLogs"]["acceptedRows"] == 1
    assert payload["dataQuality"]["capabilities"]["logExplanation"] is True
    assert {endpoint["route"] for endpoint in payload["endpoints"]} == {"/api/products/{id}", "/api/cart"}
    assert payload["applicationLogs"][0]["serviceName"] == "checkout"
    assert payload["applicationLogs"][0]["level"] == "error"
    assert payload["applicationLogs"][0]["route"] == "/api/cart"


def test_upload_accepts_trace_only_otlp_http_spans_as_traffic_source() -> None:
    traces = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "gateway"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "trace-a",
                                "spanId": "span-1",
                                "name": "GET /catalog/items",
                                "kind": "SPAN_KIND_SERVER",
                                "startTimeUnixNano": "1780212000000000000",
                                "endTimeUnixNano": "1780212000080000000",
                                "attributes": [
                                    {"key": "http.request.method", "value": {"stringValue": "GET"}},
                                    {"key": "http.route", "value": {"stringValue": "/catalog/items"}},
                                    {"key": "http.response.status_code", "value": {"intValue": "200"}},
                                ],
                            },
                            {
                                "traceId": "trace-a",
                                "spanId": "span-2",
                                "parentSpanId": "span-1",
                                "name": "POST /cart",
                                "kind": "SPAN_KIND_SERVER",
                                "startTimeUnixNano": "1780212000100000000",
                                "endTimeUnixNano": "1780212000260000000",
                                "attributes": [
                                    {"key": "http.request.method", "value": {"stringValue": "POST"}},
                                    {"key": "http.route", "value": {"stringValue": "/cart"}},
                                    {"key": "http.response.status_code", "value": {"intValue": "201"}},
                                ],
                            },
                        ]
                    }
                ],
            }
        ]
    }

    response = client.post(
        "/api/datasets/upload",
        files={"traces": ("otlp-traces.json", json.dumps(traces).encode("utf-8"), "application/json")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["datasetName"] == "otlp-traces.json"
    assert payload["summary"]["requestsImported"] == 2
    assert payload["summary"]["traceDerivedTraffic"] is True
    assert payload["dataQuality"]["inputs"]["gatewayLogs"]["acceptedRows"] == 0
    assert payload["dataQuality"]["inputs"]["traces"]["acceptedRows"] == 2
    assert payload["dataQuality"]["capabilities"]["endpointAnalysis"] is True
    assert payload["dataQuality"]["capabilities"]["scriptGeneration"] is True
    assert {endpoint["route"] for endpoint in payload["endpoints"]} == {"/catalog/items", "/cart"}
    assert payload["markovMatrix"]["__START__"] == {"GET /catalog/items": 1.0}
    assert "POST /cart" in payload["k6Script"]


def test_sensitive_values_are_redacted_from_persisted_analysis() -> None:
    gateway = (
        b'{"timestamp":"2026-05-31T10:00:00Z","method":"GET",'
        b'"url":"https://shop.example.com/account?email=alice@example.com&token=secret-token",'
        b'"status":200,"duration_ms":85,"traceId":"t1","sessionId":"alice@example.com",'
        b'"authorization":"Bearer eyJabc.def.ghi"}\n'
    )
    application_logs = (
        b'{"timestamp":"2026-05-31T10:00:01Z","level":"error","service":"account","traceId":"t1",'
        b'"message":"login failed for alice@example.com password=hunter2 card=4111 1111 1111 1111 Authorization: Bearer eyJabc.def.ghi"}'
    )

    response = client.post(
        "/api/datasets/upload",
        files={
            "gateway_logs": ("sensitive.jsonl", gateway, "application/x-ndjson"),
            "application_logs": ("sensitive-app.json", application_logs, "application/json"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = json.dumps(payload)
    assert "alice@example.com" not in serialized
    assert "hunter2" not in serialized
    assert "4111 1111 1111 1111" not in serialized
    assert "secret-token" not in serialized
    assert "eyJabc.def.ghi" not in serialized
    assert payload["applicationLogs"][0]["message"] == (
        "login failed for {MASKED_EMAIL} password={MASKED_PASSWORD} card={MASKED_CARD} Authorization={MASKED_TOKEN}"
    )
    assert payload["endpoints"][0]["route"] == "/account"
    assert payload["summary"]["maskedFields"] >= 4


def test_autonomous_agent_selects_load_balance_for_hotspot() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/inventory/items,200,80,t1,s1,inventory,inventory-pod-1
2026-05-31T10:00:01Z,GET,/inventory/items,200,90,t2,s2,inventory,inventory-pod-1
2026-05-31T10:00:02Z,POST,/checkout,200,620,t3,s3,checkout,checkout-pod-1
"""
    pods = b"""service_name,pod_name,requests,cpu_percent,p95_latency_ms,error_rate
inventory,inventory-pod-1,9000,92,700,0.02
inventory,inventory-pod-2,1100,40,130,0
inventory,inventory-pod-3,950,37,120,0
checkout,checkout-pod-1,3000,60,620,0.01
checkout,checkout-pod-2,2900,57,590,0
"""

    response = client.post(
        "/api/datasets/upload",
        files={
            "gateway_logs": ("gateway.csv", gateway, "text/csv"),
            "pod_metrics": ("pods.csv", pods, "text/csv"),
        },
    )

    assert response.status_code == 200, response.text
    agent = response.json()["autonomousAgent"]
    assert agent["status"] == "ready"
    assert agent["recommendedScenario"] == "load_balance"
    assert agent["targetService"] == "inventory"
    assert agent["targetEndpoint"]["route"] == "/inventory/items"
    assert agent["actions"][2]["detail"] == "Recommended scenario: load_balance."

    scenario = client.post(
        "/api/scenarios/generate",
        json={
            "datasetName": "gateway.csv",
            "testMode": "load_balance",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert scenario.status_code == 200, scenario.text
    script = scenario.json()["k6Script"]
    assert 'exec: "loadBalanceProbeFlow"' in script
    assert 'export function loadBalanceProbeFlow()' in script
    assert 'new Counter("hex_ai_replica_hits")' in script
    assert "recordReplicaHit(res, tags)" in script
    assert "function responseHeader(response, headerName)" in script
    assert '"route": "/inventory/items"' in script
    assert 'journey: "load_balance"' in script


def test_prometheus_pod_metrics_drive_autonomous_load_balance() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name
2026-05-31T10:00:00Z,GET,/inventory/items,200,80,t1,s1,inventory
2026-05-31T10:00:01Z,GET,/inventory/items,200,90,t2,s2,inventory
2026-05-31T10:00:02Z,GET,/inventory/items,200,85,t3,s3,inventory
"""
    prometheus_metrics = b"""
# HELP http_requests_total Total HTTP requests per pod.
# TYPE http_requests_total counter
http_requests_total{service="inventory",pod="inventory-pod-1"} 9000
http_requests_total{service="inventory",pod="inventory-pod-2"} 1100
http_requests_total{service="inventory",pod="inventory-pod-3"} 950
pod_cpu_percent{service="inventory",pod="inventory-pod-1"} 92
pod_cpu_percent{service="inventory",pod="inventory-pod-2"} 40
pod_cpu_percent{service="inventory",pod="inventory-pod-3"} 37
http_request_duration_p95_ms{service="inventory",pod="inventory-pod-1"} 700
http_request_duration_p95_ms{service="inventory",pod="inventory-pod-2"} 130
http_request_duration_p95_ms{service="inventory",pod="inventory-pod-3"} 120
http_error_rate{service="inventory",pod="inventory-pod-1"} 0.02
http_error_rate{service="inventory",pod="inventory-pod-2"} 0
http_error_rate{service="inventory",pod="inventory-pod-3"} 0
"""

    response = client.post(
        "/api/datasets/upload",
        files={
            "gateway_logs": ("gateway.csv", gateway, "text/csv"),
            "pod_metrics": ("pods.prom", prometheus_metrics, "text/plain"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["dataQuality"]["inputs"]["podMetrics"]["format"] == "prometheus"
    assert payload["dataQuality"]["inputs"]["podMetrics"]["acceptedRows"] == 3
    assert payload["dataQuality"]["capabilities"]["replicaAnalysis"] is True
    assert payload["replicas"]["source"] == "pod_metrics"
    hotspot = payload["replicas"]["services"][0]
    assert hotspot["serviceName"] == "inventory"
    assert hotspot["status"] == "hotspot"
    assert hotspot["topPod"] == "inventory-pod-1"
    assert payload["autonomousAgent"]["recommendedScenario"] == "load_balance"
    assert payload["autonomousAgent"]["targetEndpoint"]["route"] == "/inventory/items"


def test_generated_k6_uses_runtime_test_data_instead_of_embedded_demo_values() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/products/123,200,80,t1,s1,catalog,catalog-pod-1
2026-05-31T10:00:01Z,POST,/login,200,120,t1,s1,identity,identity-pod-1
2026-05-31T10:00:02Z,POST,/cart,201,140,t1,s1,cart,cart-pod-1
2026-05-31T10:00:03Z,POST,/checkout,200,220,t1,s1,checkout,checkout-pod-1
2026-05-31T10:00:04Z,POST,/payment,200,260,t1,s1,payment,payment-pod-1
"""

    upload = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("runtime-data-gateway.csv", gateway, "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    scenario = client.post(
        "/api/scenarios/generate",
        json={
            "datasetName": "runtime-data-gateway.csv",
            "testMode": "mirror",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert scenario.status_code == 200, scenario.text
    script = scenario.json()["k6Script"]

    assert "HEX_AI_TEST_DATA_JSON" in script
    assert "function requestPayload(state, fallback = {})" in script
    assert "test-user" not in script
    assert "test-password" not in script
    assert "/products/42" not in script
    assert 'productId: "42"' not in script
    assert "direct-cart" not in script
    assert "direct-order" not in script
    assert 'paymentMethod: "credit-card"' not in script


def test_generated_k6_supports_runtime_auth_and_extra_headers_without_embedded_secrets() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name
2026-05-31T10:00:00Z,GET,/secure/profile,200,80,t1,s1,account
2026-05-31T10:00:01Z,POST,/secure/orders,201,140,t1,s1,orders
"""

    upload = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("secure-gateway.csv", gateway, "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    scenario = client.post(
        "/api/scenarios/generate",
        json={
            "datasetName": "secure-gateway.csv",
            "testMode": "mirror",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert scenario.status_code == 200, scenario.text
    script = scenario.json()["k6Script"]

    assert "HEX_AI_AUTH_TOKEN" in script
    assert "HEX_AI_AUTH_SCHEME" in script
    assert "HEX_AI_API_KEY" in script
    assert "HEX_AI_API_KEY_HEADER" in script
    assert "HEX_AI_EXTRA_HEADERS_JSON" in script
    assert "function runtimeHeaders(baseHeaders = {})" in script
    assert "runtimeHeaders(baseHeaders)" in script
    assert "secret-token" not in script
    assert "real-api-key" not in script


def test_har_request_response_values_generate_safe_correlation_rules() -> None:
    har_payload = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-05-31T10:00:00Z",
                    "time": 70,
                    "request": {
                        "method": "GET",
                        "url": "https://shop.example.com/session",
                        "headers": [{"name": "x-session-id", "value": "session-42"}],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps({"csrfToken": "csrf-123456", "cartId": "cart-abcdef"}),
                        },
                    },
                },
                {
                    "startedDateTime": "2026-05-31T10:00:03Z",
                    "time": 180,
                    "request": {
                        "method": "POST",
                        "url": "https://shop.example.com/checkout",
                        "headers": [{"name": "x-session-id", "value": "session-42"}],
                        "postData": {
                            "mimeType": "application/json",
                            "text": json.dumps({"csrfToken": "csrf-123456", "cartId": "cart-abcdef"}),
                        },
                    },
                    "response": {"status": 200, "content": {"mimeType": "application/json", "text": "{}"}},
                },
            ]
        }
    }

    response = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("correlated.har", json.dumps(har_payload).encode("utf-8"), "application/json")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    serialized = json.dumps(payload)
    assert "csrf-123456" not in serialized
    assert "cart-abcdef" not in serialized
    assert payload["summary"]["dynamicCorrelations"] == 2
    assert payload["dataQuality"]["capabilities"]["correlationMining"] is True

    rules = payload["correlationRules"]
    fields = {rule["name"] for rule in rules}
    assert {"csrfToken", "cartId"}.issubset(fields)
    assert all(rule["sourceState"] == "GET /session" for rule in rules)
    assert all(rule["targetState"] == "POST /checkout" for rule in rules)
    assert all(rule["targetLocation"] == "body" for rule in rules)

    script = payload["k6Script"]
    assert "const correlationRules =" in script
    assert "function applyCorrelationRulesAfterResponse" in script
    assert "function correlatedPayload" in script
    assert "csrf-123456" not in script
    assert "cart-abcdef" not in script


def test_gateway_pod_tags_can_drive_autonomous_load_balance_without_pod_metrics() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/catalog/search,200,90,t1,s1,catalog,catalog-pod-1
2026-05-31T10:00:01Z,GET,/catalog/search,200,92,t2,s2,catalog,catalog-pod-1
2026-05-31T10:00:02Z,GET,/catalog/search,200,88,t3,s3,catalog,catalog-pod-1
2026-05-31T10:00:03Z,GET,/catalog/search,200,95,t4,s4,catalog,catalog-pod-1
2026-05-31T10:00:04Z,GET,/catalog/search,200,91,t5,s5,catalog,catalog-pod-1
2026-05-31T10:00:05Z,GET,/catalog/search,200,89,t6,s6,catalog,catalog-pod-1
2026-05-31T10:00:06Z,GET,/catalog/search,200,93,t7,s7,catalog,catalog-pod-2
2026-05-31T10:00:07Z,GET,/catalog/search,200,94,t8,s8,catalog,catalog-pod-3
"""

    response = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("gateway-pod-tags.csv", gateway, "text/csv")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["dataQuality"]["capabilities"]["replicaAnalysis"] is True
    assert payload["dataQuality"]["replicaSource"] == "gateway_pod_tags"
    assert payload["replicas"]["source"] == "gateway_pod_tags"
    assert payload["autonomousAgent"]["recommendedScenario"] == "load_balance"
    assert payload["autonomousAgent"]["evidenceSource"] == "gateway_pod_tags"
    assert payload["autonomousAgent"]["targetEndpoint"]["route"] == "/catalog/search"
    assert "repeated calls to GET /catalog/search" in payload["autonomousAgent"]["hypothesis"]


def test_guarded_run_does_not_create_fake_metrics_without_real_k6() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/inventory/items,200,80,t1,s1,inventory,inventory-pod-1
"""
    upload = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("dry-run-gateway.csv", gateway, "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    run = client.post(
        "/api/runs/start",
        json={
            "datasetName": "dry-run-gateway.csv",
            "testMode": "load_balance",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert run.status_code == 200, run.text
    assert run.json()["executionMode"] == "dry_run"

    run_id = run.json()["runId"]
    status = client.get(f"/api/runs/{run_id}/status")
    assert status.status_code == 200, status.text
    assert status.json()["status"] == "blocked"
    assert status.json()["metrics"] == []

    results = client.get(f"/api/runs/{run_id}/results")
    assert results.status_code == 200, results.text
    payload = results.json()
    assert payload["results"]["status"] == "not_executed"
    assert payload["results"]["verdictReason"].startswith("Load test was not executed:")
    assert payload["comparisons"]["endpoints"][0]["testRunLatency"] is None


def test_real_k6_replica_events_are_reported_as_load_balance_evidence() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/catalog/search,200,80,t1,s1,catalog,catalog-pod-1
2026-05-31T10:00:01Z,GET,/catalog/search,200,90,t2,s2,catalog,catalog-pod-2
"""
    upload = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("real-k6-gateway.csv", gateway, "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    run = client.post(
        "/api/runs/start",
        json={
            "datasetName": "real-k6-gateway.csv",
            "testMode": "load_balance",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert run.status_code == 200, run.text
    run_id = run.json()["runId"]
    active_run = ACTIVE_RUNS[run_id]
    active_run["executionMode"] = "real"
    active_run["status"] = "completed"

    Path(active_run["summaryPath"]).write_text(
        json.dumps(
            {
                "metrics": {
                    "http_req_duration": {"percentiles": {"95": 120}},
                    "http_req_failed": {"rate": 0},
                    "checks": {"rate": 1},
                }
            }
        ),
        encoding="utf-8",
    )
    Path(active_run["eventsPath"]).write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "Point",
                        "metric": "hex_ai_replica_hits",
                        "data": {"value": 1, "tags": {"replica": "catalog-pod-1"}},
                    }
                )
                for _ in range(8)
            ]
            + [
                json.dumps(
                    {
                        "type": "Point",
                        "metric": "hex_ai_replica_hits",
                        "data": {"value": 1, "tags": {"replica": "catalog-pod-2"}},
                    }
                )
                for _ in range(2)
            ]
        ),
        encoding="utf-8",
    )

    results = client.get(f"/api/runs/{run_id}/results")
    assert results.status_code == 200, results.text
    payload = results.json()
    evidence = payload["loadBalanceEvidence"]
    assert payload["executionMode"] == "real"
    assert payload["artifacts"]["eventsPath"] == active_run["eventsPath"]
    assert evidence["status"] == "failed"
    assert evidence["topReplica"] == "catalog-pod-1"
    assert evidence["totalHits"] == 10
    assert evidence["maxSharePercent"] == 80
    assert payload["results"]["status"] == "failed"
    assert payload["results"]["verdictReason"].startswith("Load-balance probe observed 80%")
    assert "Real k6 observed 10 replica-hit samples" in payload["results"]["loadBalanceFinding"]


def test_real_k6_success_result_reports_success_reason() -> None:
    gateway = b"""timestamp,method,route,status,duration_ms,trace_id,session_id,service_name,pod_name
2026-05-31T10:00:00Z,GET,/catalog/search,200,80,t1,s1,catalog,catalog-pod-1
2026-05-31T10:00:01Z,GET,/catalog/search,200,90,t2,s2,catalog,catalog-pod-2
"""
    upload = client.post(
        "/api/datasets/upload",
        files={"gateway_logs": ("real-k6-success-gateway.csv", gateway, "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    run = client.post(
        "/api/runs/start",
        json={
            "datasetName": "real-k6-success-gateway.csv",
            "testMode": "mirror",
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert run.status_code == 200, run.text
    run_id = run.json()["runId"]
    active_run = ACTIVE_RUNS[run_id]
    active_run["executionMode"] = "real"
    active_run["status"] = "completed"

    Path(active_run["summaryPath"]).write_text(
        json.dumps(
            {
                "metrics": {
                    "http_req_duration": {"percentiles": {"95": 120}},
                    "http_req_failed": {"rate": 0},
                    "checks": {"rate": 1},
                }
            }
        ),
        encoding="utf-8",
    )

    results = client.get(f"/api/runs/{run_id}/results")
    assert results.status_code == 200, results.text
    payload = results.json()
    assert payload["executionMode"] == "real"
    assert payload["results"]["status"] == "passed"
    assert payload["results"]["verdictReason"] == "k6 summary did not breach default failure thresholds"
    assert payload["results"]["firstFailure"] == payload["results"]["verdictReason"]


def test_sample_telemetry_fixture_exercises_full_mvp_flow() -> None:
    sample_dir = Path(__file__).resolve().parents[2] / "public" / "sample-telemetry"

    response = client.post(
        "/api/datasets/upload",
        files=[
            ("gateway_logs", ("hex-ai-gateway.har", (sample_dir / "hex-ai-gateway.har").read_bytes(), "application/json")),
            ("traces", ("hex-ai-traces.json", (sample_dir / "hex-ai-traces.json").read_bytes(), "application/json")),
            ("pod_metrics", ("hex-ai-pods.csv", (sample_dir / "hex-ai-pods.csv").read_bytes(), "text/csv")),
            ("application_logs", ("hex-ai-app.json", (sample_dir / "hex-ai-app.json").read_bytes(), "application/json")),
        ],
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["requestsImported"] >= 10
    assert payload["summary"]["routesFound"] >= 6
    assert payload["summary"]["journeyDetection"] is True
    assert payload["summary"]["replicaAnalysis"] is True
    assert payload["summary"]["dynamicCorrelations"] >= 2
    assert payload["dataQuality"]["capabilities"]["scriptGeneration"] is True
    assert payload["dataQuality"]["capabilities"]["logExplanation"] is True
    assert payload["dataQuality"]["capabilities"]["replicaAnalysis"] is True
    assert payload["autonomousAgent"]["recommendedScenario"] == "load_balance"

    scenario = client.post(
        "/api/scenarios/generate",
        json={
            "datasetName": payload["datasetName"],
            "testMode": payload["autonomousAgent"]["recommendedScenario"],
            "targetUrl": "http://localhost:8080",
            "duration": "1m",
            "rateLimit": 10,
        },
    )
    assert scenario.status_code == 200, scenario.text
    script = scenario.json()["k6Script"]
    assert "loadBalanceProbeFlow" in script
    assert "correlationRules" in script
