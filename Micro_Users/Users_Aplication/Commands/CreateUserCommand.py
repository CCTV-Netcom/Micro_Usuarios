from pydantic import BaseModel, EmailStr
from typing import Optional


class CreateUserCommand(BaseModel):
	password: str
	email: EmailStr
	first_name: Optional[str] = None
	last_name: Optional[str] = None
	cedula: float


