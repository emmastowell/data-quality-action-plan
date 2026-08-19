from starlette.requests import Request
from server.identity import current_user


def _req(headers):
    scope = {"type": "http", "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()]}
    return Request(scope)


def test_current_user_from_header():
    assert current_user(_req({"X-Forwarded-Email": "alice@gov.uk"})) == "alice@gov.uk"


def test_current_user_fallback():
    assert current_user(_req({})) == "unknown@local"
