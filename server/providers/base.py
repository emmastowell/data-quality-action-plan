from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass
class Measurement:
    score: float
    measured_at: datetime
    method: str
    source: str
    evidence_note: Optional[str] = None
    sample_size: Optional[int] = None


class AssessmentProvider(Protocol):
    def measure(self, rule: dict, payload: dict) -> Measurement: ...
