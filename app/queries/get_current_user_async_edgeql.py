# AUTOGENERATED FROM 'app/queries/get_current_user.edgeql' WITH:
#     $ edgedb-py --dir app/queries


from __future__ import annotations
import dataclasses
import datetime
import edgedb
import uuid


Str50 = str


class NoPydanticValidation:
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        # Pydantic 2.x
        from pydantic_core.core_schema import any_schema
        return any_schema()

    @classmethod
    def __get_validators__(cls):
        # Pydantic 1.x
        from pydantic.dataclasses import dataclass as pydantic_dataclass
        _ = pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


@dataclasses.dataclass
class GetCurrentUserResult(NoPydanticValidation):
    name: Str50
    id: uuid.UUID
    created_at: datetime.datetime


async def get_current_user(
    executor: edgedb.AsyncIOExecutor,
) -> GetCurrentUserResult | None:
    return await executor.query_single(
        """\
        select (global current_user) { * }\
        """,
    )
