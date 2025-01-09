import base64
import hashlib
import httpx
import logging
import secrets

from urllib.parse import urljoin

from .token_data import TokenData


logger = logging.getLogger("gel_auth")


class PKCE:
    def __init__(self, verifier: str, *, base_url: str):
        self.base_url = base_url
        self.verifier = verifier
        self.challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

    async def exchange_code_for_token(self, code: str) -> TokenData:
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.base_url, "token")
            logger.info(f"Exchanging code for token: {url}")
            token_response = await http_client.get(
                url,
                params={
                    "code": code,
                    "verifier": self.verifier,
                },
            )

            logger.info(f"Token response: {token_response.text}")
            token_response.raise_for_status()
            token_json = token_response.json()
            return TokenData(
                auth_token=token_json["auth_token"],
                identity_id=token_json["identity_id"],
                provider_token=token_json["provider_token"],
                provider_refresh_token=token_json["provider_refresh_token"],
            )


def generate_pkce(base_url: str) -> PKCE:
    verifier = secrets.token_urlsafe(32)
    return PKCE(verifier, base_url=base_url)
