from server.config import ASSESSMENT_PROVIDER
from .base import AssessmentProvider, Measurement
from .manual import ManualProvider
from .warehouse import WarehouseSqlProvider

_REGISTRY = {
    "manual": ManualProvider,
    "warehouse": WarehouseSqlProvider,
    # Phase 3: register "monitoring": LakehouseMonitoringProvider here.
}


def get_provider(name: str | None = None) -> AssessmentProvider:
    key = name or ASSESSMENT_PROVIDER
    if key not in _REGISTRY:
        raise ValueError(f"Unknown assessment provider: {key!r}")
    return _REGISTRY[key]()
