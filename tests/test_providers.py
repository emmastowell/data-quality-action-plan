import pytest
from datetime import datetime
from server.providers import get_provider
from server.providers.base import Measurement


def test_manual_provider_builds_measurement():
    p = get_provider("manual")
    m = p.measure({"id": "r1"}, {"score": 98.5, "evidence_note": "sampled 200"})
    assert isinstance(m, Measurement)
    assert m.score == 98.5 and m.method == "manual" and m.source == "manual"
    assert isinstance(m.measured_at, datetime)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("nonexistent_provider")
