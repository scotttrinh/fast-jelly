import edgedb

from typing import Annotated, Optional, Union
from fastapi import Cookie, Depends

ClientDep = Annotated[edgedb.AsyncIOClient, Depends(edgedb.create_async_client)]


class BaseSession:
    client: edgedb.AsyncIOClient

    def __init__(self, *, client: edgedb.AsyncIOClient):
        self.client = client

    async def is_authenticated(self) -> bool:
        return await self.client.query_required_single(  # type: ignore
            "select exists ext::auth::ClientTokenIdentity"
        )

class AuthenticatedSession(BaseSession):
    auth_token: str

    def __init__(self, *, client: edgedb.AsyncIOClient, auth_token: str):
        self.auth_token = auth_token
        self.client = client.with_globals(  # type: ignore
            {"ext::auth::ClientTokenIdentity": auth_token}
        )


class AnonymousSession(BaseSession):
    pass


Session = Union[AuthenticatedSession, AnonymousSession]


def extract_session(
    auth_token: Annotated[Optional[str], Cookie(alias="edgedb_auth_token")],
    client: ClientDep,
) -> Session:
    if auth_token:
        return AuthenticatedSession(client=client, auth_token=auth_token)
    else:
        return AnonymousSession(client=client)


SessionDep = Annotated[Session, Depends(extract_session)]
