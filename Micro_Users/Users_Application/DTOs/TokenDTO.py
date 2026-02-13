from pydantic import BaseModel
from typing import Optional, Dict, Any


class TokenDTO(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None


