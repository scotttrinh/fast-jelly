import edgedb
import jwt
import datetime

from typing import Optional
from fastapi import Response, Request

from .auth_core import (
    make_email_password as make_core_email_password,
    EmailPasswordBody,
    EmailPasswordResponse,
)


async def get_body(request: Request) -> EmailPasswordBody:
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
        body = await get_body(request)
        sign_up_response = await email_password_client.sign_up(
            body.email, body.password
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
        body = await get_body(request)
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


def make_email_password(
    client: edgedb.AsyncIOClient, *, verify_url: str
) -> EmailPassword:
    return EmailPassword(client=client, verify_url=verify_url)


def get_unchecked_exp(token: str) -> Optional[datetime.datetime]:
    jwt_payload = jwt.decode(token, options={"verify_signature": False})
    if "exp" not in jwt_payload:
        return None
    return datetime.datetime.fromtimestamp(jwt_payload["exp"], tz=datetime.timezone.utc)
