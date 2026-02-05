from pydantic import BaseModel

# Query para encontrar un usuario por su ID
class FindUserByIdQuery(BaseModel):
	user_id: str
