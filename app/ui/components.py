from __future__ import annotations

from htmy import Context, Component, html, component, ComponentType


@component
def Heading(children: ComponentType, context: Context) -> Component:
    return html.h1(children, class_="text-3xl font-semibold")


@component
def Subheading(children: ComponentType, context: Context) -> Component:
    return html.h2(children, class_="text-2xl")


@component
def head(title: str, context: Context) -> Component:
    return (
        html.title(title),
        html.meta.charset(),
        html.meta.viewport(),
        html.script(src="https://cdn.tailwindcss.com"),
        html.script(src="https://unpkg.com/htmx.org@2.0.2"),
    )
