"""
Regression tests for SPA catch-all routing.

The /assets/* URL namespace is shared by React Router client routes AND the
built static file tree.  The catch-all must serve index.html for client routes
(deep links, refreshes) rather than 404ing because there is no physical file
named after a UUID.
"""


def test_spa_deep_link_serves_index(client):
    # A client-route deep link that has no API/file match must return the SPA
    # shell, not a 404 JSON response.
    r = client.get("/assets/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert 'id="root"' in r.text or "govuk-template" in r.text


def test_spa_root_serves_index(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]


def test_api_still_wins_over_spa(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
