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


settings = Settings()
