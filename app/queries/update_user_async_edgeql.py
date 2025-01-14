# AUTOGENERATED FROM 'app/queries/update_user.edgeql' WITH:
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
class UpdateUserResult(NoPydanticValidation):
    created_at: datetime.datetime
    id: uuid.UUID
    name: Str50


async def update_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    current_name: str,
    new_name: str,
) -> UpdateUserResult | None:
    return await executor.query_single(
        """\
        with
            current_name := <str>$current_name,
            new_name := <str>$new_name,
            USER := (select default::User filter .name = current_name),
            UPDATED := (
                update USER
                set {
                    name := new_name,
                }
            ),
        select UPDATED { * };\
        """,
        current_name=current_name,
        new_name=new_name,
    )
