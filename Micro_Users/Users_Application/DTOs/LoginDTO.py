from pydantic import BaseModel, Field


class LoginDTO(BaseModel):
    username: str = Field(..., description="Nombre de usuario o correo")
    password: str = Field(..., description="Contraseña del usuario")
