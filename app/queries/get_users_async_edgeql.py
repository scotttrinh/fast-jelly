# AUTOGENERATED FROM 'app/queries/get_users.edgeql' WITH:
#     $ edgedb-py


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
class GetUsersResult(NoPydanticValidation):
    created_at: datetime.datetime
    id: uuid.UUID
    name: Str50


async def get_users(
    executor: edgedb.AsyncIOExecutor,
) -> list[GetUsersResult]:
    return await executor.query(
        """\
        select default::User { * };\
        """,
    )
