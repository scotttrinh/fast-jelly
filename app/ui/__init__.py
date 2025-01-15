from __future__ import annotations

import logging

from typing import Any, Callable, Awaitable, Annotated
from htmy import Context, Component, html, component, HTMY
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from ..users import User
from ..edgedb_client import client
from ..queries import get_current_user_async_edgeql as get_current_user_qry

from .components import h1, head, labeled_input, button, link

logger = logging.getLogger("fast_jelly")
router = APIRouter()


def make_auth_context(request: Request, user: User | None) -> Context:
    return {
        Request: request,
        User: user,
    }


RendererFunction = Callable[[Component], Awaitable[HTMLResponse]]


def render(request: Request) -> RendererFunction:
    """FastAPI dependency that returns an HTMY renderer function."""

    async def exec(component: Component) -> HTMLResponse:
        auth_token = request.cookies.get("edgedb_auth_token")
        logger.info(f"auth_token: {auth_token}")
        user: User | None = None
        if auth_token:
            auth_client = client.with_globals({"ext::auth::client_token": auth_token})  # type: ignore
            user_result = await get_current_user_qry.get_current_user(auth_client)  # type: ignore
            logger.info(f"user_result: {user_result}")
            if user_result:
                user = User(
                    created_at=user_result.created_at,
                    id=user_result.id,
                    name=user_result.name,
                )
        htmy = HTMY(make_auth_context(request, user))
        return HTMLResponse(await htmy.render(component))

    return exec


DependsRenderFunc = Annotated[RendererFunction, Depends(render)]


@component
def IndexPage(_: Any, context: Context) -> Component:
    user: User | None = context[User]
    if user is None:
        return html.meta(http_equiv="refresh", content="0; url=/signin")
    return (
        html.DOCTYPE.html,
        html.html(
            head("Jellyroll"),
            html.body(
                # Page content: Index page
                h1(f"Welcome, {user.name} to Jellyroll"),
                class_=(
                    "h-screen w-screen flex flex-col items-center justify-center "
                    "gap-4 bg-slate-800 text-white"
                ),
            ),
        ),
    )


@component
def SignInPage(_: Any, context: Context) -> Component:
    request: Request = context[Request]
    error_message = request.query_params.get("error", "")
    match error_message:
        case "failure":
            error_message = "Sign in failed. Please try again."

    incomplete_message = request.query_params.get("incomplete", "")
    match incomplete_message:
        case "verification_required":
            incomplete_message = "Please verify your email address before signing in."
        case "verify":
            incomplete_message = (
                "Successfully verified email! Please sign in to continue."
            )
        case "reset_password":
            incomplete_message = (
                "Your password has been reset! Please sign in to continue."
            )
        case "password_reset_sent":
            incomplete_message = "Successfully sent password reset email! Please check your email for the link to reset your password."

    return (
        html.DOCTYPE.html,
        html.html(
            head("Sign in to Jellyroll"),
            html.body(
                # Page content: Email and password sign in form
                html.div(
                    h1("Sign in to Jellyroll"),
                    html.div(
                        error_message,
                        class_=(
                            "bg-red-500/30 border-l-2 border-red-500 text-white p-4 rounded mb-4"
                            if error_message
                            else "hidden"
                        ),
                    ),
                    html.div(
                        incomplete_message,
                        class_=(
                            "bg-green-500/30 border-l-2 border-green-500 text-white p-4 rounded mb-4"
                            if incomplete_message
                            else "hidden"
                        ),
                    ),
                    html.form(
                        html.div(
                            labeled_input(
                                "Email",
                                name="email",
                                type="email",
                                placeholder="Enter your email",
                            ),
                            class_="mb-4",
                        ),
                        html.div(
                            labeled_input(
                                "Password",
                                name="password",
                                type="password",
                                placeholder="Enter your password",
                            ),
                            class_="mb-4",
                        ),
                        html.div(
                            button(
                                "Sign in",
                                type="submit",
                                variant="primary",
                            ),
                            button(
                                "Sign up",
                                type="submit",
                                variant="secondary",
                                formaction="/auth/register",
                                formmethod="post",
                            ),
                            button(
                                "Forgot password?",
                                type="button",
                                variant="link",
                                class_="text-sm",
                                hx_get="/ui/forgot-password",
                                hx_include="#email",
                                hx_target="closest form",
                                hx_swap="outerHTML",
                            ),
                            class_="flex flex-col gap-2",
                        ),
                        action="/auth/authenticate",
                        method="post",
                        class_="bg-slate-800 p-6 rounded-lg shadow-lg w-80",
                    ),
                    class_="flex flex-col items-center justify-center gap-4",
                ),
                class_="h-screen w-screen flex items-center justify-center bg-slate-900 text-white",
            ),
        ),
    )


@component
def ForgotPasswordForm(_: Any, context: Context) -> Component:
    request: Request = context[Request]
    email = request.query_params.get("email", "")

    return html.form(
        html.div(
            labeled_input(
                "Email",
                name="email",
                type="email",
                value=email,
                placeholder="Enter your email",
            ),
            class_="mb-4",
        ),
        html.div(
            button(
                "Send Reset Link",
                type="submit",
                variant="primary",
            ),
            link(
                "Back to Sign In",
                href="/signin",
            ),
            class_="flex flex-col gap-2",
        ),
        action="/auth/send-password-reset",
        method="post",
        class_="bg-slate-800 p-6 rounded-lg shadow-lg w-80",
    )


@component
def ResetPasswordPage(_: Any, context: Context) -> Component:
    request: Request = context[Request]
    reset_token = request.query_params.get("reset_token", "")

    return (
        html.DOCTYPE.html,
        html.html(
            head("Reset your password"),
            html.body(
                # Page content: Reset password page
                html.div(
                    h1("Reset your password"),
                    html.form(
                        html.div(
                            labeled_input(
                                "New password",
                                name="password",
                                type="password",
                                placeholder="Enter your password",
                            ),
                            class_="mb-4",
                        ),
                        html.input_(
                            type="hidden",
                            name="reset_token",
                            value=reset_token,
                        ),
                        html.div(
                            button(
                                "Reset password",
                                type="submit",
                                variant="primary",
                            ),
                            class_="flex flex-col gap-2",
                        ),
                        action="/auth/reset-password",
                        method="post",
                        class_="bg-slate-800 p-6 rounded-lg shadow-lg w-80",
                    ),
                    class_="flex flex-col items-center justify-center gap-4",
                ),
                class_="h-screen w-screen flex items-center justify-center bg-slate-900 text-white",
            ),
        ),
    )


@router.get("/")
async def index(render: DependsRenderFunc):
    return await render(IndexPage(None))


@router.get("/signin")
async def signin(render: DependsRenderFunc):
    return await render(SignInPage(None))


@router.get("/ui/forgot-password")
async def forgot_password_form(render: DependsRenderFunc):
    return await render(ForgotPasswordForm(None))


@router.get("/ui/reset-password")
async def reset_password_page(render: DependsRenderFunc):
    return await render(ResetPasswordPage(None))
