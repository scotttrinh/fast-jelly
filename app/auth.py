from __future__ import annotations

import json
import logging

from http import HTTPStatus
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from typing import Annotated

from .config import BASE_URL
from .edgedb_client import client
from .auth_fastapi import (
    make_email_password,
    email_password as core_email_password,
)
from .queries import create_user_async_edgeql as create_user_qry

logger = logging.getLogger("fast_jelly")
router = APIRouter()
email_password = make_email_password(client, verify_url=f"{BASE_URL}/auth/verify")


@router.post(
    "/auth/register",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def register(
    email: Annotated[str, Form()],
    sign_up_response: Annotated[
        core_email_password.SignUpResponse, Depends(email_password.handle_sign_up)
    ],
):
    logger.info(f"sign_up_response: {sign_up_response}")
    if not isinstance(sign_up_response, core_email_password.SignUpFailedResponse):
        user = await create_user_qry.create_user(
            client,
            name=email,
            identity_id=sign_up_response.identity_id,
        )
        print(f"Created user: {json.dumps(user, default=str)}")

    match sign_up_response:
        case core_email_password.SignUpCompleteResponse():
            return "/"
        case core_email_password.SignUpVerificationRequiredResponse():
            return "/signin?incomplete=verification_required"
        case core_email_password.SignUpFailedResponse():
            logger.error(f"Sign up failed: {sign_up_response}")
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid sign up response")


@router.post(
    "/auth/authenticate",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def authenticate(
    sign_in_response: Annotated[
        core_email_password.SignInResponse, Depends(email_password.handle_sign_in)
    ],
):
    match sign_in_response:
        case core_email_password.SignInCompleteResponse():
            return "/"
        case core_email_password.SignInVerificationRequiredResponse():
            return "/signin?incomplete=verification_required"
        case core_email_password.SignInFailedResponse():
            logger.error(f"Sign in failed: {sign_in_response}")
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid sign in response")


@router.get(
    "/auth/verify",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def verify(
    verify_response: Annotated[
        core_email_password.EmailVerificationResponse,
        Depends(email_password.handle_verify_email),
    ],
):
    match verify_response:
        case core_email_password.EmailVerificationCompleteResponse():
            return "/"
        case core_email_password.EmailVerificationMissingProofResponse():
            return "/signin?incomplete=verify"
        case core_email_password.EmailVerificationFailedResponse():
            logger.error(f"Verify email failed: {verify_response}")
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid verify email response")


@router.post(
    "/auth/send-password-reset",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def send_password_reset(
    send_password_reset_response: Annotated[
        core_email_password.SendPasswordResetEmailResponse,
        Depends(email_password.handle_send_password_reset),
    ],
):
    match send_password_reset_response:
        case core_email_password.SendPasswordResetEmailCompleteResponse():
            return "/signin?incomplete=password_reset_sent"
        case core_email_password.SendPasswordResetEmailFailedResponse():
            logger.error(f"Send password reset failed: {send_password_reset_response}")
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid send password reset response")


@router.post(
    "/auth/reset-password",
    response_class=RedirectResponse,
    status_code=HTTPStatus.SEE_OTHER,
)
async def reset_password(
    reset_password_response: Annotated[
        core_email_password.PasswordResetResponse,
        Depends(email_password.handle_reset_password),
    ],
):
    match reset_password_response:
        case core_email_password.PasswordResetCompleteResponse():
            return "/"
        case core_email_password.PasswordResetMissingProofResponse():
            return "/signin?incomplete=reset_password"
        case _:
            raise Exception("Invalid reset password response")
