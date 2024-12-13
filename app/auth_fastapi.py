import edgedb
import jwt
import datetime

from typing import Union
from fastapi import Response, Request

from .auth_core import (
    EmailPassword as CoreEmailPassword,
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
    def __init__(self, *, verify_url: str, auth_ext_url: str):
        self.auth_ext_url = auth_ext_url
        self.verify_url = verify_url

    async def handle_sign_up(
        self,
        request: Request,
        response: Response,
    ) -> EmailPasswordResponse:
        email_password_client = CoreEmailPassword(
            auth_ext_url=self.auth_ext_url, verify_url=self.verify_url
        )
        body = await get_body(request)
        sign_up_response = await email_password_client.sign_up(
            body.email, body.password
        )
        if sign_up_response.status == "complete":
            auth_token = sign_up_response.token_data.auth_token
            jwt_payload = jwt.decode(auth_token, options={"verify_signature": False})
            expiration_time = datetime.datetime.fromtimestamp(jwt_payload["exp"])
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
        email_password_client = CoreEmailPassword(
            auth_ext_url=self.auth_ext_url, verify_url=self.verify_url
        )
        body = await get_body(request)
        sign_in_response = await email_password_client.sign_in(
            body.email, body.password
        )
        if sign_in_response.status == "complete":
            auth_token = sign_in_response.token_data.auth_token
            jwt_payload = jwt.decode(auth_token, options={"verify_signature": False})
            expiration_time = datetime.datetime.fromtimestamp(jwt_payload["exp"])
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
    client: Union[edgedb.Client, edgedb.AsyncIOClient], *, verify_url: str
) -> EmailPassword:
    pool = client._impl
    host, port = pool._working_addr
    params = pool._working_params
    proto = "http" if params.tls_security == "insecure" else "https"
    branch = params.branch
    auth_ext_url = f"{proto}://{host}:{port}/branch/{branch}/ext/auth/"
    return EmailPassword(auth_ext_url=auth_ext_url, verify_url=verify_url)
