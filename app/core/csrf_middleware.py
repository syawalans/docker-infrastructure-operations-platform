from urllib.parse import parse_qs

from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response

from app.core.config import settings
from app.core.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    SAFE_METHODS,
    generate_csrf_token,
    validate_csrf_token,
)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        cookie_token = request.cookies.get(
            CSRF_COOKIE_NAME
        )

        csrf_token = (
            cookie_token
            or generate_csrf_token()
        )

        request.state.csrf_token = csrf_token

        if request.method not in SAFE_METHODS:
            submitted_token = request.headers.get(
                "X-CSRF-Token"
            )

            content_type = request.headers.get(
                "content-type",
                "",
            )

            if (
                not submitted_token
                and "application/x-www-form-urlencoded"
                in content_type
            ):
                body = await request.body()

                try:
                    form_data = parse_qs(
                        body.decode("utf-8"),
                        keep_blank_values=True,
                    )

                    values = form_data.get(
                        CSRF_FORM_FIELD,
                        [],
                    )

                    if values:
                        submitted_token = values[0]

                except UnicodeDecodeError:
                    submitted_token = None

            if not validate_csrf_token(
                cookie_token,
                submitted_token,
            ):
                return PlainTextResponse(
                    "CSRF validation failed.",
                    status_code=403,
                )

        response = await call_next(request)

        if not cookie_token:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=csrf_token,
                httponly=True,
                samesite="lax",
                secure=settings.CSRF_COOKIE_SECURE,
                path="/",
            )

        return response
