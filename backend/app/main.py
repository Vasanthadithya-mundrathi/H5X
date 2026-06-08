from __future__ import annotations

import gzip
import io
import zipfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .analyzer import (
    analyze_dataset,
    build_k6_script,
    get_dataset,
    get_run_status,
    get_run_results,
    start_run_execution,
)


app = FastAPI(title="HEX AI API", version="0.1.0")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 100
MAX_ARCHIVE_ENTRY_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_EXPANDED_BYTES = 100 * 1024 * 1024
SUPPORTED_TEXT_EXTENSIONS = (
    ".csv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".log",
    ".txt",
    ".otel",
    ".har",
    ".prom",
    ".openmetrics",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScenarioGenerateRequest(BaseModel):
    datasetName: str
    testMode: str
    targetUrl: str = "http://localhost:8080"
    duration: str = "5m"
    rateLimit: int = 24


class RunStartRequest(BaseModel):
    datasetName: str
    testMode: str
    targetUrl: str = "http://localhost:8080"
    duration: str = "5m"
    rateLimit: int = 24


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hex-ai-api"}


@app.post("/api/datasets/upload")
async def upload_dataset(
    gateway_logs: list[UploadFile] | None = File(None),
    traces: list[UploadFile] | None = File(None),
    pod_metrics: list[UploadFile] | None = File(None),
    application_logs: list[UploadFile] | None = File(None),
) -> dict:
    if not _has_uploads(gateway_logs) and not _has_uploads(traces):
        raise HTTPException(status_code=400, detail="Upload gateway_logs or OpenTelemetry traces with HTTP route data")

    gateway_text = await _read_upload_texts(gateway_logs, "gateway_logs")
    traces_text = await _read_upload_texts(traces, "traces")
    pod_metrics_text = await _read_upload_texts(pod_metrics, "pod_metrics")
    application_logs_text = await _read_upload_texts(application_logs, "application_logs")
    analysis = analyze_dataset(
        gateway_text,
        traces_text,
        pod_metrics_text,
        application_logs_text,
        dataset_name=_dataset_name_from_uploads([*(gateway_logs or []), *(traces or [])]),
    )
    if analysis["dataQuality"]["errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Telemetry upload could not be analyzed. Upload gateway logs or OpenTelemetry HTTP spans with route/path/url data.",
                "dataQuality": analysis["dataQuality"],
            },
        )
    return analysis


@app.post("/api/scenarios/generate")
def generate_scenario(req: ScenarioGenerateRequest) -> dict[str, str]:
    dataset = get_dataset(req.datasetName)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{req.datasetName}' was not found")

    script = build_k6_script(
        journeys=dataset["journeys"],
        endpoints=dataset["endpoints"],
        test_mode=req.testMode,
        target_url=req.targetUrl,
        duration=req.duration,
        rate_limit=req.rateLimit,
        markov_matrix=dataset.get("markovMatrix"),
        focus_endpoint=(dataset.get("autonomousAgent") or {}).get("targetEndpoint") if req.testMode == "load_balance" else None,
        correlation_rules=dataset.get("correlationRules"),
    )
    return {"k6Script": script}


@app.post("/api/runs/start")
def start_run(req: RunStartRequest) -> dict:
    try:
        return start_run_execution(
            dataset_name=req.datasetName,
            test_mode=req.testMode,
            target_url=req.targetUrl,
            duration=req.duration,
            rate_limit=req.rateLimit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}/status")
def run_status(run_id: str) -> dict:
    status = get_run_status(run_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/api/runs/{run_id}/results")
def run_results(run_id: str) -> dict:
    results = get_run_results(run_id)
    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
    return results


async def _read_upload_texts(uploads: list[UploadFile] | None, label: str) -> list[str]:
    texts = []
    for upload in uploads or []:
        if not upload.filename:
            continue
        texts.extend(await _read_upload_text_entries(upload, label))
    return texts


def _has_uploads(uploads: list[UploadFile] | None) -> bool:
    return bool(uploads and any(upload.filename for upload in uploads))


async def _read_upload_text_entries(upload: UploadFile, label: str) -> list[str]:
    data = await upload.read()
    filename = upload.filename or label
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"{filename} is too large. Upload files must be 50 MB or smaller.")

    lowered = filename.lower()
    if lowered.endswith(".zip") or zipfile.is_zipfile(io.BytesIO(data)):
        return _read_zip_upload_texts(data, label, filename)
    if lowered.endswith(".gz") or data.startswith(b"\x1f\x8b"):
        try:
            inflated = gzip.decompress(data)
        except (OSError, gzip.BadGzipFile) as exc:
            raise HTTPException(status_code=400, detail=f"{filename} could not be decompressed as gzip") from exc
        if len(inflated) > MAX_ARCHIVE_ENTRY_BYTES:
            raise HTTPException(status_code=400, detail=f"{filename} expands beyond the 25 MB per-file limit.")
        return [_decode_upload_text(inflated, f"{label}:{filename}")]

    return [_decode_upload_text(data, f"{label}:{filename}")]


async def _read_upload_text(upload: UploadFile, label: str) -> str:
    data = await upload.read()
    return _decode_upload_text(data, label)


def _read_zip_upload_texts(data: bytes, label: str, filename: str) -> list[str]:
    texts = []
    total_expanded = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [member for member in archive.infolist() if _is_supported_zip_member(member)]
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise HTTPException(status_code=400, detail=f"{filename} contains too many telemetry files.")
            for member in members:
                if member.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                    raise HTTPException(status_code=400, detail=f"{member.filename} expands beyond the 25 MB per-file limit.")
                member_data = archive.read(member)
                total_expanded += len(member_data)
                if total_expanded > MAX_ARCHIVE_EXPANDED_BYTES:
                    raise HTTPException(status_code=400, detail=f"{filename} expands beyond the 100 MB archive limit.")
                texts.append(_decode_upload_text(member_data, f"{label}:{member.filename}"))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail=f"{filename} could not be read as a zip archive") from exc

    if not texts:
        raise HTTPException(status_code=400, detail=f"{filename} did not contain supported telemetry text files.")
    return texts


def _is_supported_zip_member(member: zipfile.ZipInfo) -> bool:
    if member.is_dir():
        return False
    normalized = member.filename.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    if normalized.startswith("__MACOSX/") or basename.startswith("."):
        return False
    return basename.lower().endswith(SUPPORTED_TEXT_EXTENSIONS)


def _decode_upload_text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"{label} must be UTF-8 text") from exc


def _dataset_name_from_uploads(uploads: list[UploadFile]) -> str:
    filenames = [upload.filename for upload in uploads if upload.filename]
    if not filenames:
        return "uploaded-dataset"
    if len(filenames) == 1:
        return filenames[0]
    return f"{filenames[0]}+{len(filenames) - 1}-files"
