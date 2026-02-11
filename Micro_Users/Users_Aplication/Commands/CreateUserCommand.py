from pydantic import BaseModel, EmailStr
from typing import Optional

from Users_Domain.Enums.role import RoleEnum


class CreateUserCommand(BaseModel):
    password: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    cedula: int
    rol: RoleEnum


