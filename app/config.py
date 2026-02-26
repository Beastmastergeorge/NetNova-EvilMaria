from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Settings:
    app_name: str = "NET NOVA ISP BILLING"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./netnova.db"
    allowed_origins: str = "*"
    public_base_url: str = "http://127.0.0.1:8000"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @staticmethod
    def _database_url_from_parts() -> str | None:
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_driver = os.getenv("DB_DRIVER", "mysql+pymysql")

        if not (db_name and db_user and db_password):
            return None

        return (
            f"{db_driver}://{quote_plus(db_user)}:{quote_plus(db_password)}"
            f"@{db_host}:{db_port}/{db_name}"
        )

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL") or cls._database_url_from_parts() or cls.database_url
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            environment=os.getenv("ENVIRONMENT", cls.environment),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            host=os.getenv("HOST", cls.host),
            port=int(os.getenv("PORT", str(cls.port))),
            database_url=database_url,
            allowed_origins=os.getenv("ALLOWED_ORIGINS", cls.allowed_origins),
            public_base_url=os.getenv("PUBLIC_BASE_URL", cls.public_base_url),
        )
