import hmac
import secrets

from fastapi import Request


CSRF_COOKIE_NAME = "infrastructure_ops_csrf"
CSRF_FORM_FIELD = "csrf_token"

SAFE_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def get_csrf_token(
    request: Request,
) -> str | None:
    return request.cookies.get(
        CSRF_COOKIE_NAME
    )


def validate_csrf_token(
    cookie_token: str | None,
    form_token: str | None,
) -> bool:
    if not cookie_token or not form_token:
        return False

    return hmac.compare_digest(
        cookie_token,
        form_token,
    )
