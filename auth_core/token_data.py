import uuid

from pydantic import BaseModel


class TokenData(BaseModel):
    auth_token: str
    identity_id: uuid.UUID
    provider_token: str | None
    provider_refresh_token: str | None
