from __future__ import annotations

from typing import Any, Callable, Awaitable, Annotated
from htmy import Context, Component, html, component, HTMY
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from ..users import User
from ..edgedb_client import client
from ..queries import get_current_user_async_edgeql as get_current_user_qry
from .components import Heading, head

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
        # TODO: Get user from cookies->database
        auth_token = request.cookies.get("edgedb_auth_token")
        user: User | None = None
        if auth_token:
            auth_client = client.with_globals({"ext::auth::client_token": auth_token})  # type: ignore
            user_result = await get_current_user_qry.get_current_user(auth_client)  # type: ignore
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
                (
                    Heading(f"Welcome, {user.name} to Jellyroll")
                    if user
                    else Heading("Who are you?")
                ),
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
    if error_message == "verification_required":
        error_message = "Please verify your email address before signing in."

    return (
        html.DOCTYPE.html,
        html.html(
            head("Sign in to Jellyroll"),
            html.body(
                # Page content: Email and password sign in form
                html.div(
                    Heading("Sign in to Jellyroll"),
                    html.div(
                        error_message,
                        class_=(
                            "bg-red-500/30 border-l-2 border-red-500 text-white p-4 rounded mb-4"
                            if error_message
                            else "hidden"
                        ),
                    ),
                    html.form(
                        html.div(
                            html.label(
                                "Email",
                                for_="email",
                                class_="block text-sm font-medium text-slate-300 mb-1 pl-2",
                            ),
                            html.input_(
                                type="email",
                                name="email",
                                id="email",
                                placeholder="Enter your email",
                                class_="w-full border border-slate-600 bg-slate-800 text-white rounded-md p-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500",
                            ),
                            class_="mb-4",
                        ),
                        html.div(
                            html.label(
                                "Password",
                                for_="password",
                                class_="block text-sm font-medium text-slate-300 mb-1 pl-2",
                            ),
                            html.input_(
                                type="password",
                                name="password",
                                id="password",
                                placeholder="Enter your password",
                                class_="w-full border border-slate-600 bg-slate-800 text-white rounded-md p-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500",
                            ),
                            class_="mb-4",
                        ),
                        html.div(
                            html.button(
                                "Sign in",
                                type="submit",
                                class_="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 mb-2",
                            ),
                            html.button(
                                "Sign up",
                                type="submit",
                                formaction="/api/auth/register",
                                formmethod="post",
                                class_="w-full bg-slate-600 text-white font-bold py-2 px-4 rounded hover:bg-slate-700",
                            ),
                            class_="flex flex-col gap-2",
                        ),
                        action="/api/auth/authenticate",
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
def VerifyPage(_: Any, context: Context) -> Component:
    return (
        html.DOCTYPE.html,
        html.html(
            html.head(
                # Some metadata
                html.title("Verifying your email"),
                html.meta.charset(),
                html.meta.viewport(),
                # TailwindCSS
                html.script(src="https://cdn.tailwindcss.com"),
                # HTMX
                html.script(src="https://unpkg.com/htmx.org@2.0.2"),
            ),
            html.body(
                # Page content:
                Heading("Verifying your email"),
                class_=(
                    "h-screen w-screen flex flex-col items-center justify-center "
                    "gap-4 bg-slate-800 text-white"
                ),
            ),
        ),
    )


@router.get("/")
async def index(render: DependsRenderFunc):
    return await render(IndexPage(None))


@router.get("/signin")
async def signin(render: DependsRenderFunc):
    return await render(SignInPage(None))


@router.get("/verify")
async def verify(render: DependsRenderFunc):
    return await render(VerifyPage(None))
