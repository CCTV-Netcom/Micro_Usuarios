from pydantic import BaseModel
from typing import Optional


class VerifyTotpCommand(BaseModel):
    user_id: str
    code: str
    secret: Optional[str] = None
