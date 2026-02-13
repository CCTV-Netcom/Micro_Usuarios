from pydantic import BaseModel


class RefreshTokenDTO(BaseModel):
    refresh_token: str
