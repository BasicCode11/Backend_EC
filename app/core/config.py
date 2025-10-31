import secrets
import warnings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from datetime import timedelta


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-please-change-me-32chars!!", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v.startswith("dev-secret-key"):
            warnings.warn("⚠️ Using default SECRET_KEY in production is insecure!", UserWarning)
        return v

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        if v not in ["HS256", "HS384", "HS512"]:
            raise ValueError(
                f"System only supports HMAC algorithms (HS256/384/512), not {v}"
            )
        return v

    # JWT config
    WEB_SESSION_NO_EXPIRE: bool = Field(True, env="WEB_SESSION_NO_EXPIRE")
    WEB_INACTIVITY_TIMEOUT_MINUTES: int = Field(1, env="WEB_INACTIVITY_TIMEOUT_MINUTES")
    CUSTOMER_IDLE_TIMEOUT_DAYS: int = Field(7, env="CUSTOMER_IDLE_TIMEOUT_DAYS")

    REFRESH_TOKEN_ENABLED: bool = Field(False, env="REFRESH_TOKEN_ENABLED")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(365, env="REFRESH_TOKEN_EXPIRE_DAYS")

    JWT_ISSUER: str = Field("attendance-system-api", env="JWT_ISSUER")
    JWT_AUDIENCE: str = Field("attendance-web-mobile", env="JWT_AUDIENCE")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        env="ALLOWED_ORIGINS",
    )

    AUTO_TOKEN_REFRESH_DAYS: int = Field(30, env="AUTO_TOKEN_REFRESH_DAYS")

    # Database - matches .env.example variable names
    DB_TYPE: str = Field("mysql", env="DB_TYPE")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(3306, env="DB_PORT")
    DB_NAME: str = Field(..., env="DB_NAME")

    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(..., env="SMTP_USER")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(..., env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field(default="E-commerce Platform", env="SMTP_FROM_NAME")

    @property
    def web_inactivity_timeout(self) -> timedelta:
        return timedelta(minutes=self.WEB_INACTIVITY_TIMEOUT_MINUTES)

    @property
    def customer_idle_timeout(self) -> timedelta:
        return timedelta(days=self.CUSTOMER_IDLE_TIMEOUT_DAYS)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
