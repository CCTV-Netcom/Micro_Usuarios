from pydantic import BaseModel


class RefreshTokenCommand(BaseModel):
    refresh_token: str
