import edgedb

from typing import Annotated, Optional
from fastapi import Cookie, Depends

ClientDep = Annotated[edgedb.AsyncIOClient, Depends(edgedb.create_async_client)]


class Session:
    def __init__(
        self, *, client: edgedb.AsyncIOClient, auth_token: Optional[str] = None
    ):
        self.auth_token = auth_token
        self.client = client.with_globals(
            {"ext::auth::ClientTokenIdentity": auth_token}
        )

    async def is_authenticated(self) -> bool:
        if self.auth_token is None:
            return False
        return await self.client.query_required_single(  # type: ignore
            "select exists ext::auth::ClientTokenIdentity"
        )


def extract_session(
    auth_token: Annotated[Optional[str], Cookie(alias="edgedb_auth_token")],
    client: ClientDep,
) -> Session:
    return Session(client=client, auth_token=auth_token)
