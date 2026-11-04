from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_VALUES = {
    "",
    "change-me",
    "local-demo-key-change-me",
    "replace-with-random-secret",
    "replace-with-a-different-random-secret",
    "replace-with-a-different-random-token",
    "test",
}

MIN_SECRET_LENGTH = 16


class Settings(BaseSettings):
    """Environment-backed settings with fail-closed secret validation."""

    model_config = SettingsConfigDict(env_prefix="GHOSTNET_", env_file=".env", extra="ignore")

    database: str = "data/ghostnet.sqlite3"
    hash_key: str = ""
    ingest_secret: str = ""
    admin_token: str = ""
    chain_key: str = ""
    cors_origin: str = "http://localhost:5173"
    retention_days: int = 30
    proposal_ttl_seconds: int = 300
    bandit_state_path: str = "data/bandit.json"
    canary_tokens: str = "gk_live_demo_web_4f2a"

    def _invalid_secret(self, name: str) -> bool:
        value = getattr(self, name)
        return value.strip().lower() in PLACEHOLDER_VALUES or len(value) < MIN_SECRET_LENGTH

    def require_secrets(self) -> None:
        """Raise a single, actionable error when any secret is missing or weak."""
        invalid = [
            name
            for name in ("hash_key", "ingest_secret", "admin_token", "chain_key")
            if self._invalid_secret(name)
        ]
        if invalid:
            names = ", ".join(f"GHOSTNET_{name.upper()}" for name in invalid)
            raise RuntimeError(
                "Missing or placeholder GhostNet secrets: "
                f"{names}. Generate at least {MIN_SECRET_LENGTH} random characters per secret."
            )

    def canaries(self) -> set[str]:
        """Return configured canary token values, never persisted as raw values."""
        return {item.strip() for item in self.canary_tokens.split(",") if item.strip()}
