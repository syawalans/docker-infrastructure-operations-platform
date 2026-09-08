import os


class Settings:
    APP_NAME = os.getenv(
        "APP_NAME",
        "Infrastructure Operations Portal"
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "0.1.0"
    )

    APP_ENV = os.getenv(
        "APP_ENV",
        "development"
    )

    MONITORING_SCHEDULER_POLL_SECONDS = int(
        os.getenv(
            "MONITORING_SCHEDULER_POLL_SECONDS",
            "5",
        )
    )

    AUTH_SESSION_LIFETIME_HOURS = int(
        os.getenv(
            "AUTH_SESSION_LIFETIME_HOURS",
            "8",
        )
    )

    AUTH_LOGIN_MAX_ATTEMPTS = int(
        os.getenv(
            "AUTH_LOGIN_MAX_ATTEMPTS",
            "5",
        )
    )

    AUTH_LOGIN_WINDOW_SECONDS = int(
        os.getenv(
            "AUTH_LOGIN_WINDOW_SECONDS",
            "300",
        )
    )

    AUTH_LOGIN_BLOCK_SECONDS = int(
        os.getenv(
            "AUTH_LOGIN_BLOCK_SECONDS",
            "600",
        )
    )

    AUTH_COOKIE_SECURE = (
        os.getenv(
            "AUTH_COOKIE_SECURE",
            "false",
        ).lower()
        == "true"
    )

    CSRF_COOKIE_SECURE = (
        os.getenv(
            "CSRF_COOKIE_SECURE",
            "false",
        ).lower()
        == "true"
    )


settings = Settings()
