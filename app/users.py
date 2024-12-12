from __future__ import annotations

import edgedb

from http import HTTPStatus
from typing import List
from fastapi import APIRouter, HTTPException, Query
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


type UserResponse = List[
    get_users_qry.GetUsersResult
] | get_user_by_name_qry.GetUserByNameResult


@router.get("/users")
async def get_users(
    name: str = Query(default=None, max_length=50),
) -> UserResponse:
    if not name:
        users = await get_users_qry.get_users(client)
        return users
    else:
        user = await get_user_by_name_qry.get_user_by_name(client, name=name)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail={"error": f"Username '{name}' does not exist."},
            )
        return user


@router.post("/users", status_code=HTTPStatus.CREATED)
async def post_user(user: RequestData) -> create_user_qry.CreateUserResult:
    try:
        created_user = await create_user_qry.create_user(client, name=user.name)
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"error": f"User '{user.name}' already exists."},
        )

    return created_user


@router.put("/users")
async def put_user(
    user: RequestData, current_name: str
) -> update_user_qry.UpdateUserResult:
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

    return updated_user


@router.delete("/users")
async def delete_user(name: str) -> delete_user_qry.DeleteUserResult:
    try:
        deleted_user = await delete_user_qry.delete_user(client, name=name)
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": f"User attached to an event. Cannot delete."},
        )
    
    if not deleted_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"User '{name}' does not exist."},
        )
    
    return deleted_user
