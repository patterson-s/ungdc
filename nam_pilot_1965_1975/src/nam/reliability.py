"""Inter-coder reliability between two independent RA1 instances on the same lot
(nam_discourse_plan.md S6).

Span-overlap based, not code-label-string based: when two instances independently propose
codes against an empty/early grid, they invent their own label vocabulary from scratch (e.g.
"anti_colonialism" vs "colonialism_and_racial_discrimination" for the same observation) --
exact label matching would read as total disagreement purely as an artifact of vocabulary,
not because the coders actually noticed different things. So agreement is measured on *what
text each instance flagged* (character-span overlap), with a secondary check on whether they
agreed on the *level* (lexical/phraseological/etc.) where their spans do overlap.

Disagreement is not an error -- it marks exactly where the typology is under-specified, and
becomes a candidate escalation when the score is low (see config thresholds.reliability_escalate_below).
"""


def _intervals_by_speech(annotations: list) -> dict:
    out = {}
    for a in annotations:
        out.setdefault(a["speech_id"], []).append((a["char_start"], a["char_end"], a["level"]))
    return out


def _interval_overlap_len(a: tuple, b: tuple) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def span_overlap_agreement(annotations_a: list, annotations_b: list) -> float:
    """Per speech: (total overlapping chars between any A-span and any B-span) /
    (total chars covered by the union of all A- and B-spans). Averaged across speeches that
    either instance touched."""
    a_map = _intervals_by_speech(annotations_a)
    b_map = _intervals_by_speech(annotations_b)
    speech_ids = set(a_map) | set(b_map)
    if not speech_ids:
        return 1.0
    scores = []
    for sid in speech_ids:
        a_spans, b_spans = a_map.get(sid, []), b_map.get(sid, [])
        if not a_spans or not b_spans:
            scores.append(0.0)
            continue
        overlap = sum(
            _interval_overlap_len(a, b) for a in a_spans for b in b_spans
        )
        a_cov = sum(e - s for s, e, _ in a_spans)
        b_cov = sum(e - s for s, e, _ in b_spans)
        union = a_cov + b_cov - overlap
        scores.append(overlap / union if union else 0.0)
    return sum(scores) / len(scores)


def level_agreement_on_overlap(annotations_a: list, annotations_b: list) -> tuple:
    """Of all (A-span, B-span) pairs that overlap at all, what fraction share the same
    level tag? Returns (agreement_fraction, n_overlapping_pairs) -- the count matters because
    this is undefined (0 pairs) when spans don't overlap at all."""
    a_map = _intervals_by_speech(annotations_a)
    b_map = _intervals_by_speech(annotations_b)
    matches, total = 0, 0
    for sid in set(a_map) & set(b_map):
        for a in a_map[sid]:
            for b in b_map[sid]:
                if _interval_overlap_len(a, b) > 0:
                    total += 1
                    if a[2] == b[2]:
                        matches += 1
    return (matches / total if total else None, total)
