import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from nam.verbatim import VerbatimError, verify_span


def test_correct_span_passes():
    body = "The quick brown fox jumps."
    verify_span(body, 4, 9, "quick")


def test_wrong_quote_rejected():
    body = "The quick brown fox jumps."
    with pytest.raises(VerbatimError):
        verify_span(body, 4, 9, "slow")


def test_offset_drift_rejected():
    body = "The quick brown fox jumps."
    with pytest.raises(VerbatimError):
        verify_span(body, 5, 10, "quick")


def test_out_of_range_rejected():
    body = "short"
    with pytest.raises(VerbatimError):
        verify_span(body, 0, 999, "short")
