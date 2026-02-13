from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UserDTO(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    rol: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

