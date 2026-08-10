"""Exact-span verification -- the primary defence against hallucinated evidence
(nam_discourse_plan.md S2, non-goal 2). An annotation is only accepted if its stored
span_text is character-for-character identical to speech body[char_start:char_end].
"""


class VerbatimError(ValueError):
    pass


def verify_span(body: str, char_start: int, char_end: int, span_text: str) -> None:
    if char_start < 0 or char_end > len(body) or char_start >= char_end:
        raise VerbatimError(
            f"invalid span [{char_start}:{char_end}] for body of length {len(body)}"
        )
    actual = body[char_start:char_end]
    if actual != span_text:
        raise VerbatimError(
            f"span mismatch: stored quote {span_text!r} != body[{char_start}:{char_end}] {actual!r}"
        )


def verify_annotation(speeches: dict, annotation: dict) -> None:
    speech = speeches.get(annotation["speech_id"])
    if speech is None:
        raise VerbatimError(f"unknown speech_id {annotation['speech_id']!r}")
    verify_span(
        speech["body"],
        annotation["char_start"],
        annotation["char_end"],
        annotation["span_text"],
    )
