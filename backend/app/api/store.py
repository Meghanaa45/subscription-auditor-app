"""In-memory storage of computed audit reports, keyed by audit_id, so the
chat endpoint can reference the results of a prior /api/audit call without
the client re-sending all the data on every question.

This is intentionally simple (a process-local dict) rather than a database:
it's the right scope for a single-user demo/portfolio deployment. Restarting
the server clears all audits. If this were extended into a real multi-user
product, this module is the seam where a database or cache would go.
"""

from __future__ import annotations

import uuid
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}


def save_report(report: dict[str, Any]) -> str:
    audit_id = str(uuid.uuid4())
    _STORE[audit_id] = report
    return audit_id


def get_report(audit_id: str) -> dict[str, Any] | None:
    return _STORE.get(audit_id)
