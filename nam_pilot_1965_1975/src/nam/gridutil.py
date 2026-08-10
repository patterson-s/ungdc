"""Helpers shared by the orchestrator (and ad-hoc runner scripts) for resolving an agent's
raw output into substrate writes: locating a quoted span in its source speech, and resolving
a proposed code label against the current grid (reusing an existing code or creating a new
candidate one).
"""
from .verbatim import VerbatimError, verify_span


def locate_span(body: str, quote: str) -> tuple:
    """LLMs can't reliably count characters, so they give us a quote and we find its offset
    ourselves -- then verify_span re-checks it (belt and suspenders for the same gate)."""
    start = body.find(quote)
    if start == -1:
        raise VerbatimError(f"quote not found verbatim in speech body: {quote!r}")
    end = start + len(quote)
    verify_span(body, start, end, quote)
    return start, end


def get_active_codes(store, version_id: int) -> list:
    return [
        c for c in store.filter("codes", version_id=version_id) if c["status"] in ("candidate", "active")
    ]


def resolve_code(store, version_id: int, label: str, definition: str, level: str) -> dict:
    """Case-insensitive match on label within the current grid version; else create a new
    candidate code. Returns the code record (existing or newly created)."""
    for c in get_active_codes(store, version_id):
        if c["label"].strip().lower() == label.strip().lower():
            return c
    code = {
        "code_id": store.next_id("codes"),
        "version_id": version_id,
        "label": label,
        "definition": definition,
        "level": level,
        "status": "candidate",
        "exemplars": [],
    }
    store.append("codes", code)
    return code
