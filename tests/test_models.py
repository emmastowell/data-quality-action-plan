import pytest
from pydantic import ValidationError
from server.models import AssetCreate, AssetUpdate, RuleCreate, RuleUpdate, IssueUpdate, ActionUpdate


def test_asset_create_defaults():
    a = AssetCreate(name="UK Ship Register")
    assert a.criticality == "medium" and a.status == "draft"


def test_rule_dimension_is_constrained():
    with pytest.raises(ValidationError):
        RuleCreate(name="x", dimension="punctuality", target_threshold=99)
    ok = RuleCreate(name="IMO present", dimension="completeness", target_threshold=99.5)
    assert ok.unit == "%"


def test_asset_update_exclude_none_no_defaults_leak():
    assert AssetUpdate(status="active").model_dump(exclude_none=True) == {"status": "active"}


def test_rule_update_exclude_none_no_defaults_leak():
    assert RuleUpdate(target_threshold=98).model_dump(exclude_none=True) == {"target_threshold": 98}


def test_issue_update_exclude_none_no_defaults_leak():
    assert IssueUpdate(status="resolved").model_dump(exclude_none=True) == {"status": "resolved"}


def test_action_update_exclude_none_no_defaults_leak():
    assert ActionUpdate(status="done").model_dump(exclude_none=True) == {"status": "done"}
