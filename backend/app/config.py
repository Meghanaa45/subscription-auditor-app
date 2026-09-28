"""Loads configuration from environment variables (via a .env file in
development, or real environment variables in deployment). Nothing else in
the app should call os.getenv directly - import from here instead, so all
config is defined and validated in one place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AzureOpenAIConfig:
    endpoint: str | None
    api_key: str | None
    deployment: str | None
    api_version: str

    @property
    def is_configured(self) -> bool:
        if not (self.endpoint and self.api_key and self.deployment):
            return False
        placeholders = ("your-resource-name", "your-key", "your-deployment-name")
        return not any(
            p in val for p in placeholders for val in (self.endpoint, self.api_key, self.deployment)
        )


def load_azure_openai_config() -> AzureOpenAIConfig:
    return AzureOpenAIConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )


# CORS origins the frontend will be served from during local dev / deploy.
# Override with FRONTEND_ORIGIN in production (e.g. your Vercel/Netlify URL).
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
