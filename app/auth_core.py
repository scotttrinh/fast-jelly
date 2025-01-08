from __future__ import annotations

import secrets
import hashlib
import base64
import httpx
import uuid
import edgedb
import logging
import sys

from urllib.parse import urljoin
from typing import Literal, Union, Optional
from pydantic import BaseModel


logger = logging.getLogger("gel_auth")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)


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


class TokenData(BaseModel):
    auth_token: str
    identity_id: uuid.UUID
    provider_token: str | None
    provider_refresh_token: str | None


class EmailPasswordBody(BaseModel):
    email: str
    password: str


class EmailPasswordCompleteResponse(BaseModel):
    status: Literal["complete"]
    verifier: str
    token_data: TokenData
    identity_id: uuid.UUID


class EmailPasswordVerificationRequiredResponse(BaseModel):
    status: Literal["verification_required"]
    verifier: str
    token_data: None
    identity_id: uuid.UUID | None


EmailPasswordResponse = Union[
    EmailPasswordCompleteResponse, EmailPasswordVerificationRequiredResponse
]


class EmailPasswordVerifyBody(BaseModel):
    verification_token: str
    verifier: str


class EmailVerificationCompleteResponse(BaseModel):
    status: Literal["complete"]
    token_data: TokenData


class EmailVerificationMissingProofResponse(BaseModel):
    status: Literal["missing_proof"]
    token_data: None


EmailVerificationResponse = Union[
    EmailVerificationCompleteResponse, EmailVerificationMissingProofResponse
]


class EmailPasswordSignInBody(BaseModel):
    email: str
    password: str


class LocalIdentity(BaseModel):
    id: str


async def make_email_password(
    *,
    client: edgedb.AsyncIOClient,
    verify_url: str,
) -> EmailPassword:
    await client.ensure_connected()
    pool = client._impl
    host, port = pool._working_addr
    params = pool._working_params
    proto = "http" if params.tls_security == "insecure" else "https"
    branch = params.branch
    auth_ext_url = f"{proto}://{host}:{port}/branch/{branch}/ext/auth/"
    return EmailPassword(auth_ext_url=auth_ext_url, verify_url=verify_url)


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
            url = urljoin(self.auth_ext_url, "register")
            logger.info(f"Registering user {email}: {url}")
            register_response = await http_client.post(
                url,
                json={
                    "email": email,
                    "password": password,
                    "verify_url": self.verify_url,
                    "provider": "builtin::local_emailpassword",
                    "challenge": pkce.challenge,
                },
            )

            logger.info(f"Register response: {register_response.text}")
            register_json = register_response.json()
            match register_json:
                case {"error": error}:
                    logger.error(f"Register error: {error}")
                    raise Exception(f"Register error: {error}")
                case {"code": code}:
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return EmailPasswordCompleteResponse(
                        status="complete",
                        verifier=pkce.verifier,
                        token_data=token_data,
                        identity_id=token_data.identity_id,
                    )
                case _:
                    logger.info(
                        "No code in register response, assuming verification required"
                    )
                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    return EmailPasswordVerificationRequiredResponse(
                        status="verification_required",
                        verifier=pkce.verifier,
                        token_data=None,
                        identity_id=register_json.get("identity_id"),
                    )

    async def sign_in(self, email: str, password: str) -> EmailPasswordResponse:
        pkce = generate_pkce(self.auth_ext_url)
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.auth_ext_url, "authenticate")
            logger.info(f"Signing in user {email}: {url}")
            sign_in_response = await http_client.post(
                url,
                json={
                    "email": email,
                    "provider": "builtin::local_emailpassword",
                    "password": password,
                    "challenge": pkce.challenge,
                },
            )

            logger.info(f"Sign in response: {sign_in_response.text}")
            sign_in_json = sign_in_response.json()
            match sign_in_json:
                case {"error": error}:
                    logger.error(f"Sign in error: {error}")
                    raise Exception(f"Sign in error: {error}")
                case {"code": code}:
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return EmailPasswordCompleteResponse(
                        status="complete",
                        verifier=pkce.verifier,
                        token_data=token_data,
                        identity_id=token_data.identity_id,
                    )
                case _:
                    logger.info(
                        "No code in sign in response, assuming verification required"
                    )
                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    return EmailPasswordVerificationRequiredResponse(
                        status="verification_required",
                        verifier=pkce.verifier,
                        token_data=None,
                        identity_id=sign_in_json.get("identity_id"),
                    )

    async def verify_email(
        self, verification_token: str, verifier: Optional[str]
    ) -> EmailVerificationResponse:
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.auth_ext_url, "verify")
            logger.info(f"Verifying email: {url}")
            verify_response = await http_client.post(
                url,
                json={
                    "verification_token": verification_token,
                    "provider": "builtin::local_emailpassword",
                },
            )
            verify_json = verify_response.json()
            match verify_json:
                case {"error": error}:
                    logger.error(f"Verify error: {error}")
                    raise Exception(f"Verify error: {error}")
                case {"code": code}:
                    if verifier is None:
                        return EmailVerificationMissingProofResponse(
                            status="missing_proof", token_data=None
                        )

                    pkce = PKCE(verifier, base_url=self.auth_ext_url)
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return EmailVerificationCompleteResponse(
                        status="complete",
                        token_data=token_data,
                    )
                case _:
                    logger.error("No code in verify response")
                    raise Exception("No code in verify response")

    async def send_reset_password_email(self, email: str) -> None:
        pass

    async def reset_password(self, reset_token: str, password: str) -> None:
        pass
