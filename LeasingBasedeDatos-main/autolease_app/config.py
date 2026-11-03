"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    server: str = os.getenv("AUTOLEASE_DB_SERVER", r".\SQLEXPRESS")
    database: str = os.getenv("AUTOLEASE_DB_NAME", "db_leasing_vehicular")
    driver: str = os.getenv("AUTOLEASE_DB_DRIVER", "ODBC Driver 17 for SQL Server")
    auth_mode: str = os.getenv("AUTOLEASE_DB_AUTH", "sql").lower()
    default_user: str = os.getenv("AUTOLEASE_DB_USER", "estudiante1")
    default_password: str = os.getenv("AUTOLEASE_DB_PASSWORD", "Password123!")
    trust_server_certificate: bool = os.getenv(
        "AUTOLEASE_TRUST_CERT", "yes"
    ).lower() in {"yes", "true", "1"}


settings = Settings()
