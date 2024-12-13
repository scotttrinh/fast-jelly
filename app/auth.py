from __future__ import annotations

import json

from http import HTTPStatus
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from typing import Annotated

from .edgedb_client import client
from .auth_core import EmailPasswordResponse
from .auth_fastapi import make_email_password
from .queries import create_user_async_edgeql as create_user_qry

router = APIRouter()
email_password = make_email_password(client, verify_url="http://localhost:5001/verify")


@router.post("/auth/register")
async def register(
    email: Annotated[str, Form()],
    sign_up_response: Annotated[
        EmailPasswordResponse, Depends(email_password.handle_sign_up)
    ],
):
    if sign_up_response.status == "complete":
        user = await create_user_qry.create_user(
            client,
            name=email,
            identity_id=sign_up_response.token_data.identity_id,
        )
        print(f"Created user: {json.dumps(user, default=str)}")

        return RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    else:
        return RedirectResponse(
            url="/signin?error=verification_required", status_code=HTTPStatus.SEE_OTHER
        )


@router.post("/auth/authenticate")
async def authenticate(
    sign_in_response: Annotated[
        EmailPasswordResponse, Depends(email_password.handle_sign_in)
    ],
):
    if sign_in_response.status == "complete":
        return RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    else:
        return RedirectResponse(
            url="/signin?error=verification_required", status_code=HTTPStatus.SEE_OTHER
        )
