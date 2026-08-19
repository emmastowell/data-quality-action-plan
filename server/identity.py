from starlette.requests import Request


def current_user(request: Request) -> str:
    return request.headers.get("X-Forwarded-Email") or "unknown@local"
