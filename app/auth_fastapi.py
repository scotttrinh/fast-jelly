import edgedb
import jwt
import datetime

from typing import Optional, Annotated
from fastapi import Response, Request, Query, Cookie

from .auth_core import email_password


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
        sign_up_body = email_password.SignUpBody.model_validate(
            await _get_request_body(request)
        )
        sign_up_response = await email_password_client.sign_up(
            sign_up_body.email, sign_up_body.password
        )

        match sign_up_response:
            case email_password.SignUpCompleteResponse():
                _set_auth_cookie(sign_up_response.token_data.auth_token, response)
            case _:
                _set_verifier_cookie(sign_up_response.verifier, response)

        return sign_up_response

    async def handle_sign_in(
        self,
        request: Request,
        response: Response,
    ) -> email_password.SignInResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        sign_in_body = email_password.SignInBody.model_validate(
            await _get_request_body(request)
        )
        sign_in_response = await email_password_client.sign_in(
            sign_in_body.email, sign_in_body.password
        )

        match sign_in_response:
            case email_password.SignInCompleteResponse():
                _set_auth_cookie(sign_in_response.token_data.auth_token, response)
            case _:
                _set_verifier_cookie(sign_in_response.verifier, response)

        return sign_in_response

    async def handle_verify_email(
        self,
        request: Request,
        response: Response,
        verification_token: Annotated[str, Query()],
        verifier: Annotated[Optional[str], Cookie(alias="edgedb_verifier")] = None,
    ) -> email_password.EmailVerificationResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        return await email_password_client.verify_email(verification_token, verifier)

    async def handle_send_password_reset(
        self,
        request: Request,
        response: Response,
    ) -> email_password.SendPasswordResetEmailResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        send_password_reset_body = email_password.SendPasswordResetBody.model_validate(
            await _get_request_body(request)
        )
        return await email_password_client.send_password_reset_email(
            send_password_reset_body.email, send_password_reset_body.reset_url
        )

    async def handle_reset_password(
        self,
        request: Request,
        response: Response,
        verifier: Annotated[Optional[str], Cookie(alias="edgedb_verifier")],
    ) -> email_password.PasswordResetResponse:
        email_password_client = await email_password.make(
            client=self.client, verify_url=self.verify_url
        )
        password_reset_body = email_password.PasswordResetBody.model_validate(
            await _get_request_body(request)
        )
        return await email_password_client.reset_password(
            reset_token=password_reset_body.reset_token,
            verifier=verifier,
            password=password_reset_body.password,
        )


def make_email_password(
    client: edgedb.AsyncIOClient, *, verify_url: str
) -> EmailPassword:
    return EmailPassword(client=client, verify_url=verify_url)


def _get_unchecked_exp(token: str) -> Optional[datetime.datetime]:
    jwt_payload = jwt.decode(token, options={"verify_signature": False})
    if "exp" not in jwt_payload:
        return None
    return datetime.datetime.fromtimestamp(jwt_payload["exp"], tz=datetime.timezone.utc)


def _set_auth_cookie(token: str, response: Response) -> None:
    exp = _get_unchecked_exp(token)
    response.set_cookie(
        key="edgedb_auth_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=exp,
    )


def _set_verifier_cookie(verifier: str, response: Response) -> None:
    response.set_cookie(
        key="edgedb_verifier",
        value=verifier,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=int(datetime.timedelta(days=7).total_seconds()),
    )


async def _get_request_body(request: Request) -> dict:
    content_type = request.headers.get("content-type")
    match content_type:
        case "application/x-www-form-urlencoded" | "multipart/form-data":
            return dict(await request.form())
        case "application/json":
            return await request.json()
        case _:
            raise ValueError("Unsupported content type")
