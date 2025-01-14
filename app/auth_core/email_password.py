from __future__ import annotations

import httpx
import uuid
import logging
import edgedb
import json

from urllib.parse import urljoin
from typing import Union, Optional
from pydantic import BaseModel

from .pkce import PKCE, generate_pkce
from .token_data import TokenData

logger = logging.getLogger("gel_auth")


class SignUpBody(BaseModel):
    email: str
    password: str


class BaseServerFailedResponse(BaseModel):
    status_code: int
    message: str


class SignUpCompleteResponse(BaseModel):
    verifier: str
    token_data: TokenData
    identity_id: uuid.UUID


class SignUpVerificationRequiredResponse(BaseModel):
    verifier: str
    token_data: None
    identity_id: uuid.UUID | None


class SignUpFailedResponse(BaseServerFailedResponse):
    verifier: str


SignUpResponse = Union[
    SignUpCompleteResponse, SignUpVerificationRequiredResponse, SignUpFailedResponse
]


class SignInBody(BaseModel):
    email: str
    password: str


class SignInCompleteResponse(BaseModel):
    verifier: str
    token_data: TokenData
    identity_id: uuid.UUID


class SignInVerificationRequiredResponse(BaseModel):
    verifier: str
    token_data: None
    identity_id: uuid.UUID | None


class SignInFailedResponse(BaseServerFailedResponse):
    verifier: str


SignInResponse = Union[
    SignInCompleteResponse, SignInVerificationRequiredResponse, SignInFailedResponse
]


class VerifyBody(BaseModel):
    verification_token: str
    verifier: str


class EmailVerificationCompleteResponse(BaseModel):
    token_data: TokenData


class EmailVerificationMissingProofResponse(BaseModel):
    pass


class EmailVerificationFailedResponse(BaseServerFailedResponse):
    pass


EmailVerificationResponse = Union[
    EmailVerificationCompleteResponse,
    EmailVerificationMissingProofResponse,
    EmailVerificationFailedResponse,
]


class SendPasswordResetBody(BaseModel):
    email: str
    reset_url: str


class SendPasswordResetEmailCompleteResponse(BaseModel):
    verifier: str


class SendPasswordResetEmailFailedResponse(BaseServerFailedResponse):
    verifier: str


SendPasswordResetEmailResponse = Union[
    SendPasswordResetEmailCompleteResponse, SendPasswordResetEmailFailedResponse
]


class PasswordResetBody(BaseModel):
    reset_token: str
    password: str


class PasswordResetCompleteResponse(BaseModel):
    token_data: TokenData


class PasswordResetMissingProofResponse(BaseModel):
    pass


class PasswordResetFailedResponse(BaseServerFailedResponse):
    pass


PasswordResetResponse = Union[
    PasswordResetCompleteResponse,
    PasswordResetMissingProofResponse,
    PasswordResetFailedResponse,
]


class LocalIdentity(BaseModel):
    id: str


async def make(
    *,
    client: edgedb.AsyncIOClient,
    verify_url: str,
    reset_url: str,
) -> EmailPassword:
    await client.ensure_connected()
    pool = client._impl
    host, port = pool._working_addr
    params = pool._working_params
    proto = "http" if params.tls_security == "insecure" else "https"
    branch = params.branch
    auth_ext_url = f"{proto}://{host}:{port}/branch/{branch}/ext/auth/"
    return EmailPassword(
        auth_ext_url=auth_ext_url, verify_url=verify_url, reset_url=reset_url
    )


class EmailPassword:
    def __init__(
        self,
        *,
        verify_url: str,
        auth_ext_url: str,
        reset_url: str,
    ):
        self.auth_ext_url = auth_ext_url
        self.verify_url = verify_url
        self.reset_url = reset_url

    async def sign_up(self, email: str, password: str) -> SignUpResponse:
        pkce = generate_pkce(self.auth_ext_url)
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.auth_ext_url, "register")
            logger.info(f"Signing up user {email}: {url}")
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
            try:
                register_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Register error: {e}")
                return SignUpFailedResponse(
                    verifier=pkce.verifier,
                    status_code=e.response.status_code,
                    message=e.response.text,
                )
            register_json = register_response.json()
            match register_json:
                case {"error": error}:
                    logger.error(f"Register error: {error}")
                    return SignUpFailedResponse(
                        verifier=pkce.verifier,
                        status_code=register_response.status_code,
                        message=error,
                    )
                case {"code": code}:
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return SignUpCompleteResponse(
                        verifier=pkce.verifier,
                        token_data=token_data,
                        identity_id=token_data.identity_id,
                    )
                case _:
                    logger.info(
                        "No code in register response, assuming verification required"
                    )
                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    return SignUpVerificationRequiredResponse(
                        verifier=pkce.verifier,
                        token_data=None,
                        identity_id=register_json.get("identity_id"),
                    )

    async def sign_in(self, email: str, password: str) -> SignInResponse:
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
            try:
                sign_in_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Sign in error: {e}")
                return SignInFailedResponse(
                    verifier=pkce.verifier,
                    status_code=e.response.status_code,
                    message=e.response.text,
                )
            sign_in_json = sign_in_response.json()
            match sign_in_json:
                case {"error": error}:
                    logger.error(f"Sign in error: {error}")
                    return SignInFailedResponse(
                        verifier=pkce.verifier,
                        status_code=sign_in_response.status_code,
                        message=error,
                    )
                case {"code": code}:
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return SignInCompleteResponse(
                        verifier=pkce.verifier,
                        token_data=token_data,
                        identity_id=token_data.identity_id,
                    )
                case _:
                    logger.info(
                        "No code in sign in response, assuming verification required"
                    )
                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    return SignInVerificationRequiredResponse(
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
            try:
                verify_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Verify error: {e}")
                return EmailVerificationFailedResponse(
                    status_code=e.response.status_code,
                    message=e.response.text,
                )
            verify_json = verify_response.json()
            match verify_json:
                case {"error": error}:
                    logger.error(f"Verify error: {error}")
                    return EmailVerificationFailedResponse(
                        status_code=verify_response.status_code,
                        message=error,
                    )
                case {"code": code}:
                    if verifier is None:
                        return EmailVerificationMissingProofResponse()

                    pkce = PKCE(verifier, base_url=self.auth_ext_url)
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)

                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Token data: {token_data}")
                    return EmailVerificationCompleteResponse(
                        token_data=token_data,
                    )
                case _:
                    logger.error(
                        f"No code in verify response: {json.dumps(verify_json)}"
                    )
                    return EmailVerificationMissingProofResponse()

    async def send_password_reset_email(
        self, email: str
    ) -> SendPasswordResetEmailResponse:
        pkce = generate_pkce(self.auth_ext_url)
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.auth_ext_url, "send-reset-email")
            reset_response = await http_client.post(
                url,
                json={
                    "email": email,
                    "provider": "builtin::local_emailpassword",
                    "challenge": pkce.challenge,
                    "reset_url": self.reset_url,
                },
            )

            logger.info(f"Reset response: {reset_response.text}")
            try:
                reset_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Reset error: {e}")
                return SendPasswordResetEmailFailedResponse(
                    verifier=pkce.verifier,
                    status_code=e.response.status_code,
                    message=e.response.text,
                )
            reset_json = reset_response.json()
            match reset_json:
                case {"error": error}:
                    logger.error(f"Reset error: {error}")
                    return SendPasswordResetEmailFailedResponse(
                        verifier=pkce.verifier,
                        status_code=reset_response.status_code,
                        message=error,
                    )
                case _:
                    logger.info(f"PKCE verifier: {pkce.verifier}")
                    logger.info(f"Reset response: {reset_json}")
                    return SendPasswordResetEmailCompleteResponse(
                        verifier=pkce.verifier,
                    )

    async def reset_password(
        self, reset_token: str, verifier: Optional[str], password: str
    ) -> PasswordResetResponse:
        async with httpx.AsyncClient() as http_client:
            url = urljoin(self.auth_ext_url, "reset-password")
            reset_response = await http_client.post(
                url,
                json={
                    "provider": "builtin::local_emailpassword",
                    "reset_token": reset_token,
                    "password": password,
                },
            )

            logger.info(f"Reset response: {reset_response.text}")
            try:
                reset_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Reset error: {e}")
                return PasswordResetFailedResponse(
                    status_code=e.response.status_code,
                    message=e.response.text,
                )
            reset_json = reset_response.json()
            match reset_json:
                case {"error": error}:
                    logger.error(f"Reset error: {error}")
                    return PasswordResetFailedResponse(
                        status_code=reset_response.status_code,
                        message=error,
                    )
                case {"code": code}:
                    if verifier is None:
                        return PasswordResetMissingProofResponse()

                    pkce = PKCE(verifier, base_url=self.auth_ext_url)
                    logger.info(f"Exchanging code for token: {code}")
                    token_data = await pkce.exchange_code_for_token(code)
                    return PasswordResetCompleteResponse(
                        token_data=token_data,
                    )
                case _:
                    logger.error(f"No code in reset response: {json.dumps(reset_json)}")
                    return PasswordResetMissingProofResponse()
