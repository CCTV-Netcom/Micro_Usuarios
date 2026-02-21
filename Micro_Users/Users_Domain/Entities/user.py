from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from Users_Domain.Enums.role import RoleEnum
#No uso esta clase pero es el modelo de usuario
#Se puede usar para si se va a empezar a guardar usuarios en una base de datos y no en keycloak directamente
#Tambien se puede usar para validaciones de datos antes de enviarlos a keycloak


class User(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=3)
    last_name: str
    password: str
    cedula: int
    rol: RoleEnum 
    @field_validator('first_name', mode='before')
    def first_name_not_empty_and_minlen(cls, v: str) -> str:
        if v is None:
            raise ValueError('El nombre no puede estar vacío')
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('El nombre no puede estar vacío')
        if len(v) <= 2:
            raise ValueError('El nombre debe tener más de 2 caracteres')
        return v

    @field_validator('last_name', mode='before')
    def last_name_not_empty_and_minlen(cls, v: str) -> str:
        if v is None:
            raise ValueError('El apellido no puede estar vacío')
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('El apellido no puede estar vacío')
        if len(v) <= 2:
            raise ValueError('El apellido debe tener más de 2 caracteres')
        return v
    
    
    @field_validator('password')
    def password_strong(cls, v: str) -> str:
        if v is None or not v:
            raise ValueError('La contraseña no puede estar vacía')
        if len(v) <= 6:
            raise ValueError('La contraseña debe tener más de 6 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[^\w\s]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
        return v

    @field_validator('cedula', mode='before')
    def validate_cedula(cls, v):
        # Convertimos a int si llega como float o string numérico
        try:
            cedula_int = int(v)
        except (ValueError, TypeError):
            raise ValueError('La cédula debe ser un número válido')

        # Las cédulas en Venezuela actualmente van desde ~100.000 hasta ~35.000.000
        # Un rango de 100k a 50M es seguro y evita errores de entrada
        if not (100_000 <= cedula_int <= 50_000_000):
            raise ValueError('El número de cédula es inválido o está fuera de rango')
        
        return cedula_int

    def Update_User(self, first_name: str = None, last_name: str = None):
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name


    def Update_Password(self, password: str):
        self.password = password
