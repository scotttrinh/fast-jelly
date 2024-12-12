from __future__ import annotations

import datetime
import uuid

from typing import Any, Callable, Awaitable, Annotated
from htmy import Context, Component, html, component, HTMY
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from ..users import User
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
        user = User(
            created_at=datetime.datetime.now(),
            id=uuid.uuid4(),
            name="test",
        )
        htmy = HTMY(make_auth_context(request, user))
        return HTMLResponse(await htmy.render(component))

    return exec


DependsRenderFunc = Annotated[RendererFunction, Depends(render)]


@component
def IndexPage(_: Any, context: Context) -> Component:
    user: User | None = context[User]
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
    return (
        html.DOCTYPE.html,
        html.html(
            html.head(
                # Some metadata
                html.title("Sign in to Jellyroll"),
                html.meta.charset(),
                html.meta.viewport(),
                # TailwindCSS
                html.script(src="https://cdn.tailwindcss.com"),
                # HTMX
                html.script(src="https://unpkg.com/htmx.org@2.0.2"),
            ),
            html.body(
                # Page content: Sign in page
                Heading("Sign in to Jellyroll"),
                class_=(
                    "h-screen w-screen flex flex-col items-center justify-center "
                    "gap-4 bg-slate-800 text-white"
                ),
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


@router.get("/ui/signin")
async def signin(render: DependsRenderFunc):
    return await render(SignInPage(None))


@router.get("/ui/verify")
async def verify(render: DependsRenderFunc):
    return await render(VerifyPage(None))
