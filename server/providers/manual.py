from datetime import datetime, timezone
from .base import Measurement


class ManualProvider:
    def measure(self, rule: dict, payload: dict) -> Measurement:
        return Measurement(
            score=float(payload["score"]),
            measured_at=payload.get("measured_at") or datetime.now(timezone.utc),
            method="manual",
            source="manual",
            evidence_note=payload.get("evidence_note"),
            sample_size=payload.get("sample_size"),
        )
