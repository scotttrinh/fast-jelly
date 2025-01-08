import edgedb
import jwt
import datetime

from typing import Optional, Annotated
from fastapi import Response, Request, Query, Cookie

from .auth_core import (
    make_email_password as make_core_email_password,
    EmailPasswordBody,
    EmailPasswordResponse,
    EmailPasswordVerifyBody,
    EmailVerificationResponse,
)


async def get_email_password_body(request: Request) -> EmailPasswordBody:
    content_type = request.headers.get("content-type")
    match content_type:
        case "application/x-www-form-urlencoded" | "multipart/form-data":
            form = await request.form()
            body = EmailPasswordBody(
                email=str(form.get("email")), password=str(form.get("password"))
            )
        case "application/json":
            json_body = await request.json()
            body = EmailPasswordBody(
                email=json_body.get("email", ""),
                password=json_body.get("password", ""),
            )
        case _:
            raise ValueError("Unsupported content type")
    return body


async def get_email_password_verify_body(request: Request) -> EmailPasswordVerifyBody:
    content_type = request.headers.get("content-type")
    match content_type:
        case "application/x-www-form-urlencoded" | "multipart/form-data":
            form = await request.form()
            body = EmailPasswordVerifyBody(
                verification_token=str(form.get("verification_token")),
                verifier=str(form.get("verifier")),
            )
        case "application/json":
            json_body = await request.json()
            body = EmailPasswordVerifyBody(
                verification_token=json_body.get("verification_token", ""),
                verifier=json_body.get("verifier", ""),
            )
        case _:
            raise ValueError("Unsupported content type")
    return body


class EmailPassword:

    def __init__(self, *, client: edgedb.AsyncIOClient, verify_url: str):
        self.client = client
        self.verify_url = verify_url

    async def handle_sign_up(
        self,
        request: Request,
        response: Response,
    ) -> EmailPasswordResponse:
        email_password_client = await make_core_email_password(
            client=self.client, verify_url=self.verify_url
        )
        body = await get_email_password_body(request)
        sign_up_response = await email_password_client.sign_up(
            body.email, body.password
        )
        response.set_cookie(
            key="edgedb_verifier",
            value=sign_up_response.verifier,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=int(datetime.timedelta(days=7).total_seconds()),
        )
        if sign_up_response.status == "complete":
            auth_token = sign_up_response.token_data.auth_token
            expiration_time = get_unchecked_exp(auth_token)
            response.set_cookie(
                key="edgedb_auth_token",
                value=auth_token,
                httponly=True,
                secure=True,
                samesite="lax",
                expires=expiration_time,
            )
        return sign_up_response

    async def handle_sign_in(
        self,
        request: Request,
        response: Response,
    ) -> EmailPasswordResponse:
        email_password_client = await make_core_email_password(
            client=self.client, verify_url=self.verify_url
        )
        body = await get_email_password_body(request)
        sign_in_response = await email_password_client.sign_in(
            body.email, body.password
        )
        if sign_in_response.status == "complete":
            auth_token = sign_in_response.token_data.auth_token
            expiration_time = get_unchecked_exp(auth_token)
            response.set_cookie(
                key="edgedb_auth_token",
                value=auth_token,
                httponly=True,
                secure=True,
                samesite="lax",
                expires=expiration_time,
            )
        return sign_in_response

    async def handle_verify_email(
        self,
        request: Request,
        verification_token: Annotated[str, Query()],
        verifier: Annotated[Optional[str], Cookie(alias="edgedb_verifier")],
        response: Response,
    ) -> EmailVerificationResponse:
        email_password_client = await make_core_email_password(
            client=self.client, verify_url=self.verify_url
        )
        return await email_password_client.verify_email(verification_token, verifier)


def make_email_password(
    client: edgedb.AsyncIOClient, *, verify_url: str
) -> EmailPassword:
    return EmailPassword(client=client, verify_url=verify_url)


def get_unchecked_exp(token: str) -> Optional[datetime.datetime]:
    jwt_payload = jwt.decode(token, options={"verify_signature": False})
    if "exp" not in jwt_payload:
        return None
    return datetime.datetime.fromtimestamp(jwt_payload["exp"], tz=datetime.timezone.utc)
