from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agent.assistant import run_agent_turn
from app.agent.client import AzureNotConfiguredError
from app.api.schemas import AuditResponse, ChatRequest, ChatResponse, HealthResponse
from app.api.store import get_report, save_report
from app.config import load_azure_openai_config
from app.core.detector import detect_subscriptions
from app.core.ingest import UnrecognizedFormatError, load_transactions_multi
from app.core.normalize import normalize_merchants
from app.core.report import build_report_dict

router = APIRouter(prefix="/api")

_BUNDLED_SAMPLE = Path(__file__).resolve().parent.parent.parent / "data" / "sample_transactions.csv"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", agent_configured=load_azure_openai_config().is_configured)


def _run_audit(csv_paths: list[Path]) -> AuditResponse:
    try:
        transactions = load_transactions_multi(csv_paths)
    except UnrecognizedFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if transactions.empty:
        raise HTTPException(status_code=400, detail="No usable transactions found in the uploaded file(s).")

    normalized = normalize_merchants(transactions)
    matches = detect_subscriptions(normalized)
    report = build_report_dict(matches)

    audit_id = save_report(report)
    return AuditResponse(audit_id=audit_id, summary=report["summary"], subscriptions=report["subscriptions"])


@router.post("/audit", response_model=AuditResponse)
async def run_audit(files: list[UploadFile] = File(...)) -> AuditResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one CSV file is required.")

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for upload in files:
            dest = Path(tmpdir) / upload.filename
            dest.write_bytes(await upload.read())
            paths.append(dest)
        return _run_audit(paths)


@router.get("/audit/sample", response_model=AuditResponse)
def run_sample_audit() -> AuditResponse:
    if not _BUNDLED_SAMPLE.exists():
        raise HTTPException(
            status_code=500,
            detail="Bundled sample data not found. Run scripts/generate_synthetic_data.py first.",
        )
    return _run_audit([_BUNDLED_SAMPLE])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    report = get_report(request.audit_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Unknown audit_id. Run /api/audit first.")

    try:
        answer = run_agent_turn(
            question=request.question,
            report=report,
            history=[turn.model_dump() for turn in request.history],
        )
    except AzureNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(answer=answer)
