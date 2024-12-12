from __future__ import annotations

import dataclasses
import datetime
import uuid

import edgedb

from http import HTTPStatus
from typing import List
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from .queries import (
    get_user_by_name_async_edgeql as get_user_by_name_qry,
    get_users_async_edgeql as get_users_qry,
    create_user_async_edgeql as create_user_qry,
    update_user_async_edgeql as update_user_qry,
    delete_user_async_edgeql as delete_user_qry,
)
from .edgedb_client import client


router = APIRouter()


class RequestData(BaseModel):
    name: str


@dataclasses.dataclass(kw_only=True)
class User:
    created_at: datetime.datetime
    id: uuid.UUID
    name: str


type UserResponse = List[User] | User


@router.get("/users")
async def get_users(
    name: str = Query(default=None, max_length=50),
) -> UserResponse:
    if not name:
        users = await get_users_qry.get_users(client)
        return [
            User(created_at=user.created_at, id=user.id, name=user.name)
            for user in users
        ]
    else:
        user = await get_user_by_name_qry.get_user_by_name(client, name=name)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail={"error": f"Username '{name}' does not exist."},
            )
        return User(created_at=user.created_at, id=user.id, name=user.name)


@router.post("/users", status_code=HTTPStatus.CREATED)
async def post_user(user: RequestData) -> User:
    try:
        created_user = await create_user_qry.create_user(client, name=user.name)
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"error": f"User '{user.name}' already exists."},
        )

    return User(
        created_at=created_user.created_at,
        id=created_user.id,
        name=created_user.name,
    )


@router.put("/users")
async def put_user(user: RequestData, current_name: str) -> User:
    try:
        updated_user = await update_user_qry.update_user(
            client,
            new_name=user.name,
            current_name=current_name,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"error": f"User '{user.name}' already exists."},
        )

    if not updated_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"User '{current_name}' does not exist."},
        )

    return User(
        created_at=updated_user.created_at,
        id=updated_user.id,
        name=updated_user.name,
    )


@router.delete("/users", status_code=HTTPStatus.NO_CONTENT)
async def delete_user(name: str):
    try:
        deleted_user = await delete_user_qry.delete_user(client, name=name)
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": "User attached to an event. Cannot delete."},
        )

    if not deleted_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"User '{name}' does not exist."},
        )

    return Response(status_code=HTTPStatus.NO_CONTENT)
