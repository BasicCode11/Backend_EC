import secrets
import warnings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from datetime import timedelta
import cloudinary
import cloudinary.uploader

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
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://ecommerce-pannel.vercel.app",
            "http://127.0.0.1:8000",
            "http://192.168.10.10:5173",
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

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")
    TELEGRAM_ALERTS_ENABLED: bool = Field(default=False, env="TELEGRAM_ALERTS_ENABLED")

    # ABA PayWay Configuration
    ABA_PAYWAY_MERCHANT_ID: str = Field(..., env="ABA_PAYWAY_MERCHANT_ID")
    ABA_PAYWAY_API_URL: str = Field(..., env="ABA_PAYWAY_API_URL")
    ABA_PAYWAY_PUBLIC_KEY: str = Field(..., env="ABA_PAYWAY_PUBLIC_KEY")
    ABA_PAYWAY_RSA_PUBLIC_KEY: str = Field(..., env="ABA_PAYWAY_RSA_PUBLIC_KEY")
    ABA_PAYWAY_RSA_PRIVATE_KEY: str = Field(..., env="ABA_PAYWAY_RSA_PRIVATE_KEY")
    ABA_PAYWAY_RETURN_URL: str = Field(default="http://localhost:3000/payment/callback", env="ABA_PAYWAY_RETURN_URL")
    ABA_PAYWAY_CONTINUE_URL: str = Field(default="http://localhost:3000/payment/success", env="ABA_PAYWAY_CONTINUE_URL")
    ABA_PAYWAY_CANCEL_URL: str = Field(default="http://localhost:3000/payment/cancel", env="ABA_PAYWAY_CANCEL_URL")
    ABA_PAYWAY_CALLBACK_URL: str = Field(default="http://localhost:8000/api/payments/aba-payway/callback", env="ABA_PAYWAY_CALLBACK_URL")
    ABA_PAYWAY_QR_API_URL: str = Field(default="https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/generate-qr", env="ABA_PAYWAY_QR_API_URL")
    ABA_PAYWAY_CHECK_TRANSACTION_URL: str = Field(default="https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/check-transaction-2", env="ABA_PAYWAY_CHECK_TRANSACTION_URL")
    CLOUDINARY_CLOUD_NAME: str = Field(default="dvaocanqr", env="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = Field(default="398686351654423", env="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = Field(default="jPRCzb3XzGqVswvzYbDld2uD07Y", env="CLOUDINARY_API_SECRET")

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
# Configure Cloudinary AFTER loading settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)
