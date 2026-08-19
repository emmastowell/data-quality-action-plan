# tests/test_uc_sync_tables.py
import datetime as dt
import uuid
from decimal import Decimal

import pytest

from jobs.uc_sync_tables import TABLE_SPECS, coerce_value, coerce_row, column_list


def test_all_seven_app_tables_specified():
    assert set(TABLE_SPECS) == {
        "data_assets", "quality_rules", "measurements",
        "issues", "actions", "asset_step_status", "asset_tables",
    }


def test_none_passes_through_for_every_token():
    for token in ["string", "double", "int", "bool", "timestamp", "date", "array<string>"]:
        assert coerce_value(None, token) is None


def test_uuid_and_enum_become_string():
    u = uuid.uuid4()
    assert coerce_value(u, "string") == str(u)
    assert coerce_value("completeness", "string") == "completeness"


def test_numeric_becomes_float():
    assert coerce_value(Decimal("96.50"), "double") == 96.5
    assert isinstance(coerce_value(Decimal("96.50"), "double"), float)


def test_int_and_bool():
    assert coerce_value(5, "int") == 5
    assert coerce_value(True, "bool") is True


def test_text_array_becomes_list_of_str():
    assert coerce_value(["a", "b"], "array<string>") == ["a", "b"]


def test_timestamp_and_date_pass_through_as_objects():
    ts = dt.datetime(2026, 8, 19, 6, 0, 0)
    d = dt.date(2026, 8, 19)
    assert coerce_value(ts, "timestamp") == ts
    assert coerce_value(d, "date") == d


def test_coerce_row_orders_by_spec_and_handles_missing_keys():
    spec = [("id", "string"), ("score", "double"), ("tags", "array<string>")]
    row = {"id": uuid.UUID("00000000-0000-0000-0000-000000000001"), "score": Decimal("1")}
    out = coerce_row(row, spec)
    assert out == ["00000000-0000-0000-0000-000000000001", 1.0, None]


def test_column_list_matches_spec_order():
    spec = [("id", "string"), ("name", "string")]
    assert column_list(spec) == "id, name"
