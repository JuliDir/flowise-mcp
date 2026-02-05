"""
HTTP client for Flowise API interactions.

This module provides a simple HTTP client for communicating with Flowise instances
using API key authentication.
"""

import os
from typing import Any

import httpx


class FlowiseClientError(Exception):
    """Base exception for Flowise client errors."""

    pass


class AuthenticationError(FlowiseClientError):
    """Raised when authentication fails or API key is missing."""

    pass


class ConnectionError(FlowiseClientError):
    """Raised when connection to Flowise fails."""

    pass


def get_config() -> dict[str, str | float]:
    """
    Get Flowise configuration from environment variables.

    Returns:
        Dictionary containing:
        - base_url: Flowise instance URL
        - api_key: API key for authentication
        - timeout: Request timeout in seconds
    """
    return {
        "base_url": os.getenv("FLOWISE_BASE_URL", "http://localhost:3000"),
        "api_key": os.getenv("FLOWISE_API_KEY", ""),
        "timeout": float(os.getenv("FLOWISE_TIMEOUT", "60.0")),
    }


async def make_api_request(
    endpoint: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Make an authenticated API request to the Flowise instance.

    Args:
        endpoint: API endpoint path (without base URL or /api/v1 prefix)
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data for POST/PUT requests
        params: Query parameters

    Returns:
        Response data as dict or list depending on endpoint

    Raises:
        AuthenticationError: If API key is missing or invalid
        ConnectionError: If unable to connect to Flowise
        FlowiseClientError: For other API errors
    """
    config = get_config()
    url = f"{config['base_url']}/api/v1/{endpoint}"

    headers: dict[str, str] = {"Content-Type": "application/json"}

    if config["api_key"]:
        headers["Authorization"] = f"Bearer {config['api_key']}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=float(config["timeout"]),
            )
            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()

            return response.text

        except httpx.HTTPStatusError as e:
            raise FlowiseClientError(
                f"API request failed with status {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise ConnectionError("Request timed out") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to Flowise: {e}") from e


def handle_api_error(e: Exception) -> str:
    """
    Format API errors into user-friendly messages.

    Args:
        e: The exception that occurred

    Returns:
        Human-readable error message
    """
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return (
                "Error: Authentication failed. Please check your FLOWISE_API_KEY "
                "environment variable."
            )
        elif status == 403:
            return "Error: Permission denied. Your API key may not have access to this resource."
        elif status == 404:
            return "Error: Resource not found. Please verify the flow ID is correct."
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        elif status >= 500:
            return f"Error: Flowise server error (status {status}). Check if Flowise is running."
        return f"Error: API request failed with status {status}: {e.response.text}"

    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The Flowise server may be overloaded or unreachable."

    elif isinstance(e, httpx.ConnectError):
        return (
            "Error: Could not connect to Flowise. "
            "Verify FLOWISE_BASE_URL and that Flowise is running."
        )

    return f"Error: {type(e).__name__}: {str(e)}"
