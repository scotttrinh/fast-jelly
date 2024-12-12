from __future__ import annotations

import edgedb
import datetime

from http import HTTPStatus
from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .queries import (
    create_event_async_edgeql as create_event_qry,
)


router = APIRouter()
client = edgedb.create_async_client()


class RequestData(BaseModel):
    name: str
    address: str
    schedule: datetime.datetime
    host_name: str


@router.post("/events", status_code=HTTPStatus.CREATED)
async def post_event(event: RequestData) -> create_event_qry.CreateEventResult:
    try:
        created_event = await create_event_qry.create_event(
            client,
            name=event.name,
            address=event.address,
            schedule=event.schedule,
            host_name=event.host_name,
        )
    except edgedb.errors.InvalidValueError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": str(ex)},
        )

    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": "Event '{event.name}' already exists"},
        )

    return created_event
