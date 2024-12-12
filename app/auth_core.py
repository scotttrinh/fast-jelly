from __future__ import annotations

import secrets
import hashlib
import base64
import httpx
import uuid

from typing import Literal, Union
from pydantic import BaseModel


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
            token_response = await http_client.post(
                f"{self.base_url}/token",
                json={
                    "code": code,
                    "verifier": self.verifier,
                },
            )

            token_json = await token_response.json()
            return TokenData(
                auth_token=token_json["auth_token"],
                identity_id=token_json["identity_id"],
                provider_token=token_json["provider_token"],
                provider_refresh_token=token_json["provider_refresh_token"],
            )


def generate_pkce(base_url: str) -> PKCE:
    verifier = secrets.token_urlsafe(32)
    return PKCE(verifier, base_url=base_url)


class TokenData(BaseModel):
    auth_token: str
    identity_id: uuid.UUID | None
    provider_token: str | None
    provider_refresh_token: str | None


class EmailPasswordBody(BaseModel):
    email: str
    password: str


class EmailPasswordCompleteResponse(BaseModel):
    status: Literal["complete"]
    verifier: str
    token_data: TokenData


class EmailPasswordVerificationRequiredResponse(BaseModel):
    status: Literal["verification_required"]
    verifier: str
    token_data: None


EmailPasswordResponse = Union[
    EmailPasswordCompleteResponse, EmailPasswordVerificationRequiredResponse
]


class EmailPasswordSignInBody(BaseModel):
    email: str
    password: str


class LocalIdentity(BaseModel):
    id: str


class EmailPassword:

    def __init__(
        self,
        *,
        verify_url: str,
        auth_ext_url: str,
    ):
        self.auth_ext_url = auth_ext_url
        self.verify_url = verify_url
        pass

    async def sign_up(self, email: str, password: str) -> EmailPasswordResponse:
        pkce = generate_pkce(self.auth_ext_url)
        async with httpx.AsyncClient() as http_client:
            register_response = await http_client.post(
                f"{self.auth_ext_url}/register",
                json={
                    "email": email,
                    "password": password,
                    "verify_url": self.verify_url,
                    "provider": "builtin::local_emailpassword",
                    "challenge": pkce.challenge,
                },
            )

            register_json = await register_response.json()
            # If there is a "code" key in the response JSON, we can exchange
            # for a token. Otherwise, we need to wait for the email
            # verification flow to complete
            if "code" in register_json:
                # Exchange for a token
                token_data = await pkce.exchange_code_for_token(
                    register_json["code"],
                )
                return EmailPasswordCompleteResponse(
                    status="complete",
                    verifier=pkce.verifier,
                    token_data=token_data,
                )
            else:
                return EmailPasswordVerificationRequiredResponse(
                    status="verification_required",
                    verifier=pkce.verifier,
                    token_data=None,
                )

    async def sign_in(self, email: str, password: str) -> EmailPasswordResponse:
        pkce = generate_pkce(self.auth_ext_url)
        async with httpx.AsyncClient() as http_client:
            sign_in_response = await http_client.post(
                f"{self.auth_ext_url}/authenticate",
                json={
                    "email": email,
                    "provider": "builtin::local_emailpassword",
                    "password": password,
                    "challenge": pkce.challenge,
                },
            )

            sign_in_json = await sign_in_response.json()
            if "code" in sign_in_json:
                token_data = await pkce.exchange_code_for_token(
                    sign_in_json["code"],
                )
                return EmailPasswordCompleteResponse(
                    status="complete",
                    verifier=pkce.verifier,
                    token_data=token_data,
                )
            else:
                return EmailPasswordVerificationRequiredResponse(
                    status="verification_required",
                    verifier=pkce.verifier,
                    token_data=None,
                )

    async def verify_email(self, verification_token: str, verifier: str) -> None:
        pass

    async def send_reset_password_email(self, email: str) -> None:
        pass

    async def reset_password(self, reset_token: str, password: str) -> None:
        pass
