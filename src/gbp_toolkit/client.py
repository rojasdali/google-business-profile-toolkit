"""Low-level Google Business Profile HTTP client with automated OAuth2 refresh."""

import logging
import os
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)
TOKEN_URL = "https://oauth2.googleapis.com/token"


class GBPClientError(Exception):
    """Base exception for Google Business Profile API errors."""


class GBPQuotaExceededError(GBPClientError):
    """Raised when GBP API returns 429 quota exceeded (e.g. pending allowlist)."""


class GBPClient:
    """Manages OAuth2 token refresh and HTTP dispatch to Google Business Profile APIs."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        account_id: Optional[str] = None,
        location_id: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.account_id = account_id or ""
        self.location_id = location_id or ""
        self.dry_run = dry_run
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    @classmethod
    def from_env(cls, env_path: Optional[str] = None, dry_run: bool = False) -> "GBPClient":
        """Instantiate client from environment variables."""
        if env_path and os.path.exists(env_path):
            from dotenv import load_dotenv
            load_dotenv(env_path)

        client_id = os.getenv("GBP_OAUTH_CLIENT_ID", "")
        client_secret = os.getenv("GBP_OAUTH_CLIENT_SECRET", "")
        refresh_token = os.getenv("GBP_OAUTH_REFRESH_TOKEN", "")
        account_id = os.getenv("GBP_ACCOUNT_ID", "")
        location_id = os.getenv("GBP_LOCATION_ID", "")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            account_id=account_id,
            location_id=location_id,
            dry_run=dry_run,
        )

    def get_access_token(self) -> str:
        """Exchanges refresh token for access token or returns cached valid token."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(TOKEN_URL, data=payload, timeout=15)
        if resp.status_code != 200:
            raise GBPClientError(f"OAuth token refresh failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        return self._access_token

    def request(self, method: str, url: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatches an authenticated API request with error handling and dry-run guard."""
        if self.dry_run and method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            logger.info("[DRY RUN] Intercepted %s %s payload: %s", method, url, json_data)
            return {"simulated": True, "method": method, "url": url, "payload": json_data}

        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        resp = requests.request(method, url, headers=headers, json=json_data, timeout=30)

        if resp.status_code == 429:
            raise GBPQuotaExceededError(
                f"GBP API Quota limit reached (HTTP 429). Check project allowlist approval: {resp.text}"
            )
        if not (200 <= resp.status_code < 300):
            raise GBPClientError(f"GBP API request failed ({resp.status_code}): {resp.text}")

        return resp.json() if resp.text else {}
