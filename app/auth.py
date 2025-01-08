from __future__ import annotations

import json

from http import HTTPStatus
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from typing import Annotated

from .edgedb_client import client
from .auth_fastapi import (
    make_email_password,
    EmailPasswordResponse,
    EmailVerificationResponse,
)
from .queries import create_user_async_edgeql as create_user_qry

router = APIRouter()
email_password = make_email_password(
    client, verify_url="http://localhost:5001/auth/verify"
)


@router.post(
    "/auth/register",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def register(
    email: Annotated[str, Form()],
    sign_up_response: Annotated[
        EmailPasswordResponse, Depends(email_password.handle_sign_up)
    ],
):
    if sign_up_response.identity_id is not None:
        user = await create_user_qry.create_user(
            client,
            name=email,
            identity_id=sign_up_response.identity_id,
        )
        print(f"Created user: {json.dumps(user, default=str)}")

    return (
        "/"
        if sign_up_response.status == "complete"
        else "/signin?error=verification_required"
    )


@router.post(
    "/auth/authenticate",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def authenticate(
    sign_in_response: Annotated[
        EmailPasswordResponse, Depends(email_password.handle_sign_in)
    ],
):
    return (
        "/"
        if sign_in_response.status == "complete"
        else "/signin?error=verification_required"
    )


@router.get(
    "/auth/verify",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def verify(
    verify_response: Annotated[
        EmailVerificationResponse, Depends(email_password.handle_verify_email)
    ],
):
    if verify_response.status == "complete":
        user = await create_user_qry.create_user(
            client,
            name="",
            identity_id=verify_response.token_data.identity_id,
        )
        print(f"Created user: {json.dumps(user, default=str)}")

        return "/"

    return "/signin?error=missing_proof"
