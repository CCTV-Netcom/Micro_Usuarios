from pydantic import BaseModel
from typing import Optional


class RegisterTotpDeviceCommand(BaseModel):
    user_id: str
    device_name: Optional[str] = None
