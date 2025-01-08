# AUTOGENERATED FROM 'app/queries/create_user.edgeql' WITH:
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
class CreateUserResult(NoPydanticValidation):
    name: Str50
    id: uuid.UUID
    created_at: datetime.datetime


async def create_user(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str | None = None,
    identity_id: uuid.UUID | None = None,
) -> CreateUserResult:
    return await executor.query_single(
        """\
        with
            name := <optional str>$name,
            identity_id := <optional uuid>$identity_id,
            IDENTITY := (select ext::auth::Identity filter .id = identity_id),
            NEW_USER := (
              insert default::User {
                name := name ??
                  assert_single(
                    IDENTITY.<identity[is ext::auth::EmailFactor].email
                  ) ??
                  to_str(datetime_of_statement()),
                identities := IDENTITY
              }
            ),
        select NEW_USER { * };\
        """,
        name=name,
        identity_id=identity_id,
    )
