"""RA1 -- inductive coder (nam_discourse_plan.md S4). Reads a lot of speeches plus the
current grid, proposes new codes and/or applies existing ones, tags every observation with
its level, and grounds each in an exact span. Does not see/use the nam_flag.
"""
from pathlib import Path

from ..llm import call_json

PROMPT_VERSION = "inductive_v1"
_PROMPT_PATH = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"
LEVELS = ["lexical", "phraseological", "rhetorical_move", "thematic_frame", "positionality"]

_SCHEMA = {
    "type": "object",
    "properties": {
        "lot_reflection": {"type": "string"},
        "proposed_codes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "definition": {"type": "string"},
                    "level": {"type": "string", "enum": LEVELS},
                },
                "required": ["label", "definition", "level"],
            },
        },
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speech_id": {"type": "string"},
                    "code_label": {"type": "string"},
                    "level": {"type": "string", "enum": LEVELS},
                    "quote": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["speech_id", "code_label", "level", "quote"],
            },
        },
    },
    "required": ["proposed_codes", "annotations"],
}


def _format_grid(active_codes: list) -> str:
    if not active_codes:
        return "(empty -- no codes exist yet, you are proposing the first ones)"
    return "\n".join(
        f"- {c['label']} [{c['level']}]: {c['definition']}" for c in active_codes
    )


def _format_lot(lot: list) -> str:
    parts = []
    for s in lot:
        parts.append(f"### speech_id: {s['speech_id']}\n{s['body']}")
    return "\n\n".join(parts)


def run_inductive(lot: list, active_codes: list, model: str, temperature: float, instance_label: str):
    system = _PROMPT_PATH.read_text(encoding="utf-8")
    user = (
        f"CURRENT GRID:\n{_format_grid(active_codes)}\n\n"
        f"LOT OF SPEECHES:\n{_format_lot(lot)}"
    )
    parsed, meta = call_json(
        model=model,
        system=system,
        user=user,
        json_schema=_SCHEMA,
        prompt_version=PROMPT_VERSION,
        temperature=temperature,
    )
    meta["agent"] = f"RA1-{instance_label}"
    return parsed, meta
