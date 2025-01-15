from __future__ import annotations

from typing import Optional, Literal, TypedDict, Unpack
from htmy import Fragment, html, ComponentType, PropertyValue


def Heading(*args: ComponentType) -> html.h1:
    return html.h1(*args, class_="text-3xl font-semibold")


def Subheading(*args: ComponentType) -> html.h2:
    return html.h2(*args, class_="text-2xl")


def head(title: str) -> ComponentType:
    return html.head(
        html.title(title),
        html.meta.charset(),
        html.meta.viewport(),
        html.script(src="https://cdn.tailwindcss.com"),
        html.script(src="https://unpkg.com/htmx.org@2.0.2"),
    )


class InputProps(TypedDict, total=False):
    placeholder: str
    value: str
    type: str


def Input(
    *args: ComponentType,
    name: str,
    class_: Optional[str] = None,
    **kwargs: Unpack[InputProps],
) -> Fragment:
    merged_class_ = f"w-full border border-slate-600 bg-slate-800 text-white rounded-md p-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 {class_ if class_ else ''}"

    return Fragment(
        html.label(
            *args,
            for_=name,
            class_="block text-sm font-medium text-slate-300 mb-1 pl-2",
        ),
        html.input_(
            name=name,
            id=name,
            class_=merged_class_,
            **kwargs,
        ),
    )


LINK_STYLE = "text-blue-400 hover:text-blue-300 underline"


def Link(
    *args: ComponentType,
    href: str,
    class_: Optional[str] = None,
    **kwargs: PropertyValue,
) -> html.a:
    merged_class_ = f"{LINK_STYLE} {class_ if class_ else ''}"
    return html.a(*args, href=href, class_=merged_class_, **kwargs)


ButtonVariant = Literal["primary", "secondary", "link"]


_variant_classes: dict[ButtonVariant, str] = {
    "primary": "bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700",
    "secondary": "bg-slate-600 text-white py-2 px-4 rounded hover:bg-slate-700",
    "link": f"{LINK_STYLE} inline-block",
}


class ButtonProps(TypedDict, total=False):
    type: str
    formaction: str
    formmethod: str
    hx_get: str
    hx_include: str
    hx_target: str
    hx_swap: str


def Button(
    *args: ComponentType,
    variant: ButtonVariant,
    class_: Optional[str] = None,
    **kwargs: Unpack[ButtonProps],
) -> html.button:
    merged_class_ = f"{_variant_classes[variant]} {class_ if class_ else ''}"

    return html.button(*args, class_=merged_class_, **kwargs)
