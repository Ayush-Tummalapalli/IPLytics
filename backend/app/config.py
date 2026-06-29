"""
IPLytics Backend — Configuration Module

WHY THIS FILE EXISTS:
    Instead of scattering os.getenv() calls throughout the codebase,
    we centralize ALL configuration here. This gives us:
    1. Type safety — Pydantic validates types automatically
    2. Single source of truth — one place to see every setting
    3. Fail-fast behavior — the app crashes immediately if required
       settings (like DATABASE_URL) are missing, instead of failing
       later at runtime in a confusing way

HOW IT WORKS:
    Pydantic-settings reads from a .env file (or real environment
    variables) and populates this Settings class. Access any setting
    via: settings.DATABASE_URL, settings.GEMINI_API_KEY, etc.

WHERE IT FITS:
    This is imported by every other backend module that needs
    configuration (database connection, AI service, main app, etc.)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden by:
    1. Setting an environment variable (highest priority)
    2. Placing the value in a .env file at the project root
    """

    # --- Application ---
    APP_NAME: str = "IPLytics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/iplytics"

    # --- Google Gemini AI ---
    GEMINI_API_KEY: str = "your_gemini_api_key_here"

    # --- Backend Server ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # --- Frontend ---
    BACKEND_URL: str = "http://localhost:8000"

    # Tell pydantic-settings to read from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unexpected env vars without crashing
    )


# Create a single settings instance used across the entire app
settings = Settings()
