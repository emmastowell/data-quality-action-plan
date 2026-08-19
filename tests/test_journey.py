"""Tests for the enriched journey endpoint and step-status PUT."""
import uuid


def _asset(client):
    return client.post("/api/assets", json={"name": "Test Asset", "status": "active"}).json()["id"]


def _journey_map(client, aid):
    """Return {step_num: item_dict} from the journey response."""
    steps = client.get(f"/api/assets/{aid}/journey").json()
    return {s["step"]: s for s in steps}


# ---------------------------------------------------------------------------
# Shape & defaults
# ---------------------------------------------------------------------------

def test_new_asset_journey_shape(client):
    """Fresh asset: 7 steps, 2 substeps each, all substep done=False, source='auto'."""
    aid = _asset(client)
    steps = client.get(f"/api/assets/{aid}/journey").json()
    assert len(steps) == 7
    for s in steps:
        assert "step" in s and "done" in s   # backward-compat fields present
        assert "source" in s and "substeps" in s
        assert s["source"] == "auto"
        assert len(s["substeps"]) == 2
        for sub in s["substeps"]:
            assert sub["done"] is False


# ---------------------------------------------------------------------------
# Sub-step persistence & parent derivation
# ---------------------------------------------------------------------------

def test_put_substep_persists_and_parent_becomes_substeps(client):
    """PUT one substep → persists; PUT second → parent done=True, source='substeps'."""
    aid = _asset(client)

    # Mark step 2a done
    r = client.put(f"/api/assets/{aid}/journey/2a", json={"done": True})
    assert r.status_code == 200
    jm = {s["step"]: s for s in r.json()}
    step2 = jm[2]
    assert step2["substeps"][0]["done"] is True   # 2a
    assert step2["substeps"][1]["done"] is False  # 2b
    # Only one sub done → falls back to manual/auto check (no manual row for "2"), auto=False
    assert step2["done"] is False
    assert step2["source"] == "auto"

    # Mark step 2b done → both subs done → parent flips
    r2 = client.put(f"/api/assets/{aid}/journey/2b", json={"done": True})
    assert r2.status_code == 200
    jm2 = {s["step"]: s for s in r2.json()}
    step2_after = jm2[2]
    assert step2_after["done"] is True
    assert step2_after["source"] == "substeps"
    # Verify GET also shows the change
    jm3 = _journey_map(client, aid)
    assert jm3[2]["done"] is True and jm3[2]["source"] == "substeps"


# ---------------------------------------------------------------------------
# Manual parent override
# ---------------------------------------------------------------------------

def test_put_parent_manual_when_subs_not_both_done(client):
    """PUT parent key '3' done=True while subs are not both done → source='manual'."""
    aid = _asset(client)
    r = client.put(f"/api/assets/{aid}/journey/3", json={"done": True})
    assert r.status_code == 200
    jm = {s["step"]: s for s in r.json()}
    step3 = jm[3]
    assert step3["done"] is True
    assert step3["source"] == "manual"
    # Substeps remain false
    assert step3["substeps"][0]["done"] is False
    assert step3["substeps"][1]["done"] is False


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_put_invalid_item_key_returns_422(client):
    """Attempt to PUT an out-of-range key returns 4xx."""
    aid = _asset(client)
    r = client.put(f"/api/assets/{aid}/journey/8", json={"done": True})
    assert r.status_code in (400, 422)

    r2 = client.put(f"/api/assets/{aid}/journey/1c", json={"done": True})
    assert r2.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Unknown asset
# ---------------------------------------------------------------------------

def test_put_unknown_asset_returns_404(client):
    """PUT to a non-existent asset UUID returns 404."""
    fake_id = str(uuid.uuid4())
    r = client.put(f"/api/assets/{fake_id}/journey/1a", json={"done": True})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Backward compatibility: auto-derived values still work when nothing overridden
# ---------------------------------------------------------------------------

def test_put_parent_explicit_false_honours_manual(client):
    """
    Manual false on a step whose auto value is True (step 1 = asset exists) must
    win — source='manual', done=False.  Guards against a truthiness regression
    where `if parent_key in statuses` passes but the stored value is ignored.
    """
    aid = _asset(client)
    r = client.put(f"/api/assets/{aid}/journey/1", json={"done": False})
    assert r.status_code == 200
    step1 = {s["step"]: s for s in r.json()}[1]
    assert step1["done"] is False
    assert step1["source"] == "manual"
    # GET confirms persistence
    step1_get = {s["step"]: s for s in client.get(f"/api/assets/{aid}/journey").json()}[1]
    assert step1_get["done"] is False and step1_get["source"] == "manual"


def test_substep_carries_audit_fields_after_put(client):
    """After PUTting a sub-step done, its substep object carries updated_by and updated_at."""
    aid = _asset(client)
    r = client.put(f"/api/assets/{aid}/journey/2a", json={"done": True})
    assert r.status_code == 200
    steps = {s["step"]: s for s in r.json()}
    step2 = steps[2]
    sub_2a = next(s for s in step2["substeps"] if s["key"] == "2a")
    # updated_by comes from X-Forwarded-Email set in conftest.py
    assert sub_2a["updated_by"] == "tester@gov.uk"
    assert sub_2a["updated_at"] is not None
    # Unset substep has null audit fields
    sub_2b = next(s for s in step2["substeps"] if s["key"] == "2b")
    assert sub_2b["updated_by"] is None
    assert sub_2b["updated_at"] is None


def test_existing_journey_tests_still_pass_via_auto(client):
    """
    The step+done fields from auto-derivation still work as before when no
    manual overrides are set.  Mirrors the assertions in test_export.py.
    """
    aid = _asset(client)
    # step 1 done because asset exists
    jm = _journey_map(client, aid)
    assert jm[1]["done"] is True and jm[2]["done"] is False

    rid = client.post(f"/api/assets/{aid}/rules",
                      json={"name": "R1", "dimension": "validity"}).json()["id"]
    client.post(f"/api/rules/{rid}/measurements", json={"score": 99})
    client.post(f"/api/assets/{aid}/actions", json={"title": "fix"})

    jm2 = _journey_map(client, aid)
    assert jm2[2]["done"] is True
    assert jm2[3]["done"] is True
    assert jm2[4]["done"] is True

    # Step 7: requires >=2 measurements on same rule
    client.post(f"/api/rules/{rid}/measurements", json={"score": 95})
    jm3 = _journey_map(client, aid)
    assert jm3[7]["done"] is True
