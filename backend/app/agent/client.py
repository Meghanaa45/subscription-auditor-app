"""Builds the Azure OpenAI client used by the agent. Isolated in its own
module so the rest of the agent code doesn't need to know about Azure-
specific configuration, and so a different provider could be swapped in here
without touching assistant.py or tools.py.
"""

from __future__ import annotations

from openai import AzureOpenAI

from app.config import load_azure_openai_config


class AzureNotConfiguredError(RuntimeError):
    """Raised when the agent is used before Azure OpenAI credentials are set."""


def get_client() -> AzureOpenAI:
    config = load_azure_openai_config()
    if not config.is_configured:
        raise AzureNotConfiguredError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT in your .env file."
        )
    return AzureOpenAI(
        azure_endpoint=config.endpoint,
        api_key=config.api_key,
        api_version=config.api_version,
    )


def get_deployment_name() -> str:
    config = load_azure_openai_config()
    if not config.deployment:
        raise AzureNotConfiguredError("AZURE_OPENAI_DEPLOYMENT is not set.")
    return config.deployment
