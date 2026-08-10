"""Batch + matched-control sampling (nam_discourse_plan.md S5). A plain NAM-vs-all-non-NAM
contrast is invalid because NAM membership is confounded with region, era, development tier,
and recency of independence. For each NAM speech in a batch, draw non-NAM controls matched on
year (implicit: same batch), region, development tier, and independence-cohort proximity.

If country_metadata is missing/sparse for a match, the batch is flagged `needs_question` rather
than silently falling back to an unmatched pool, per the plan's explicit instruction.
"""
import itertools
from dataclasses import dataclass, field

# Deliberate hard cases for the skeptic/RA2 boundary-testing step: states understood as
# de facto non-aligned (Cold War neutrals) but never formal NAM members. Always included
# as controls when present in a batch's year, regardless of matching score.
HARD_CASE_CONTROL_ISOS = {"FIN", "AUT", "SWE"}


def _match_score(nam_meta: dict, candidate_meta: dict) -> float:
    score = 0.0
    if nam_meta.get("region") != candidate_meta.get("region"):
        score += 3.0
    if nam_meta.get("development_tier") != candidate_meta.get("development_tier"):
        score += 2.0
    a, b = nam_meta.get("independence_year"), candidate_meta.get("independence_year")
    if a is not None and b is not None:
        score += min(abs(a - b) / 10.0, 5.0)
    else:
        score += 1.0  # one or both unknown -- can't judge cohort proximity, mild penalty
    return score


@dataclass
class Batch:
    year: int
    speech_ids: list
    control_ids: list
    sample_method: str
    needs_question: bool = False
    question_reason: str = ""
    match_notes: dict = field(default_factory=dict)


def sample_batch(
    year: int,
    speeches_by_year: list,
    country_metadata: dict,
    controls_per_nam_speech: int = 1,
) -> Batch:
    nam_speeches = [s for s in speeches_by_year if s["nam_flag"]]
    non_nam_speeches = [s for s in speeches_by_year if not s["nam_flag"]]

    control_use_count = {s["speech_id"]: 0 for s in non_nam_speeches}
    chosen_control_ids = []
    match_notes = {}
    needs_question = False
    reasons = []

    for nam_s in nam_speeches:
        nam_meta = country_metadata.get(nam_s["iso"], {})
        if nam_meta.get("development_tier") is None and nam_meta.get("independence_year") is None:
            needs_question = True
            reasons.append(
                f"{nam_s['iso']}: no usable country_metadata (tier and independence_year both null)"
            )
        candidates = [s for s in non_nam_speeches if s["iso"] != nam_s["iso"]]
        if not candidates:
            continue
        scored = sorted(
            candidates,
            key=lambda s: (
                _match_score(nam_meta, country_metadata.get(s["iso"], {})),
                control_use_count[s["speech_id"]],
            ),
        )
        picked = scored[:controls_per_nam_speech]
        for p in picked:
            control_use_count[p["speech_id"]] += 1
            chosen_control_ids.append(p["speech_id"])
        match_notes[nam_s["speech_id"]] = [p["speech_id"] for p in picked]

    hard_case_ids = [
        s["speech_id"]
        for s in non_nam_speeches
        if s["iso"] in HARD_CASE_CONTROL_ISOS and s["speech_id"] not in chosen_control_ids
    ]
    chosen_control_ids.extend(hard_case_ids)

    return Batch(
        year=year,
        speech_ids=[s["speech_id"] for s in nam_speeches],
        control_ids=chosen_control_ids,
        sample_method="region+development_tier+independence_cohort, hard-case neutrals always included",
        needs_question=needs_question,
        question_reason="; ".join(reasons),
        match_notes=match_notes,
    )


def speeches_for_year(all_speeches: dict, year: int) -> list:
    return [s for s in all_speeches.values() if s["year"] == year]
