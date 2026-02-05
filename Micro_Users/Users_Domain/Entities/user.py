from pydantic import BaseModel, EmailStr
#No uso esta clase pero es el modelo de usuario 
#Se puede usar para si se va empezar a guardar usuarios en una base de datos y no en keycloak directamente
#Tambien se puede usar para validaciones de datos antes de enviarlos a keycloak

class User(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    cedula:float

    def __init__(self, email: str, first_name: str, last_name: str, password: str, cedula:float):
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        cedula=cedula
        
    def Update_User(self, first_name: str = None, last_name: str = None):
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name


    def Update_Password(self, password: str):
        self.password = password
