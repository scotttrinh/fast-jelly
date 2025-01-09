import edgedb
import jwt
import datetime

from typing import Optional, Annotated
from fastapi import Response, Request, Query, Cookie

import auth_core.email_password as email_password


class EmailPassword:
    def __init__(self, *, client: edgedb.AsyncIOClient, verify_url: str):
        self.client = client
        self.verify_url = verify_url

    async def handle_sign_up(
        self,
        request: Request,
        response: Response,
    ) -> email_password.SignUpResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        body = await self.get_sign_up_body(request)
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
            set_auth_cookie(auth_token, response)
        return sign_up_response

    async def handle_sign_in(
        self,
        request: Request,
        response: Response,
    ) -> email_password.SignInResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        body = await self.get_sign_in_body(request)
        sign_in_response = await email_password_client.sign_in(
            body.email, body.password
        )
        if sign_in_response.status == "complete":
            auth_token = sign_in_response.token_data.auth_token
            set_auth_cookie(auth_token, response)
        return sign_in_response

    async def handle_verify_email(
        self,
        request: Request,
        verification_token: Annotated[str, Query()],
        verifier: Annotated[Optional[str], Cookie(alias="edgedb_verifier")],
        response: Response,
    ) -> email_password.EmailVerificationResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        return await email_password_client.verify_email(verification_token, verifier)

    async def get_sign_up_body(self, request: Request) -> email_password.SignUpBody:
        content_type = request.headers.get("content-type")
        match content_type:
            case "application/x-www-form-urlencoded" | "multipart/form-data":
                form = await request.form()
                body = email_password.SignUpBody(
                    email=str(form.get("email")), password=str(form.get("password"))
                )
            case "application/json":
                json_body = await request.json()
                body = email_password.SignUpBody(
                    email=json_body.get("email", ""),
                    password=json_body.get("password", ""),
                )
            case _:
                raise ValueError("Unsupported content type")
        return body

    async def get_sign_in_body(self, request: Request) -> email_password.SignInBody:
        content_type = request.headers.get("content-type")
        match content_type:
            case "application/x-www-form-urlencoded" | "multipart/form-data":
                form = await request.form()
                body = email_password.SignInBody(
                    email=str(form.get("email")), password=str(form.get("password"))
                )
            case "application/json":
                json_body = await request.json()
                body = email_password.SignInBody(
                    email=json_body.get("email", ""),
                    password=json_body.get("password", ""),
                )
            case _:
                raise ValueError("Unsupported content type")
        return body


def make_email_password(
    client: edgedb.AsyncIOClient, *, verify_url: str
) -> EmailPassword:
    return EmailPassword(client=client, verify_url=verify_url)


def get_unchecked_exp(token: str) -> Optional[datetime.datetime]:
    jwt_payload = jwt.decode(token, options={"verify_signature": False})
    if "exp" not in jwt_payload:
        return None
    return datetime.datetime.fromtimestamp(jwt_payload["exp"], tz=datetime.timezone.utc)


def set_auth_cookie(token: str, response: Response) -> None:
    exp = get_unchecked_exp(token)
    response.set_cookie(
        key="edgedb_auth_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=exp,
    )
