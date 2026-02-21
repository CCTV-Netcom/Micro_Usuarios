from pydantic import BaseModel, Field
from typing import Optional


class UpdateUserDTO(BaseModel):
    first_name: Optional[str] = Field(None, description="Nombre del usuario")
    last_name: Optional[str] = Field(None, description="Apellido del usuario")
