from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any


class UpdateUserCommand(BaseModel):
	user_id: str
	first_name: Optional[str] = None
	last_name: Optional[str] = None

	@field_validator('first_name', mode='before')
	def first_name_not_empty_and_minlen(cls, v):
		if v is None:
			return v
		if isinstance(v, str):
			v = v.strip()
		if not v:
			raise ValueError('El nombre no puede estar vacío')
		if len(v) <= 2:
			raise ValueError('El nombre debe tener más de 2 caracteres')
		return v

	@field_validator('last_name', mode='before')
	def last_name_not_empty_and_minlen(cls, v):
		if v is None:
			return v
		if isinstance(v, str):
			v = v.strip()
		if not v:
			raise ValueError('El apellido no puede estar vacío')
		if len(v) <= 2:
			raise ValueError('El apellido debe tener más de 2 caracteres')
		return v

	#Este payload solo incluye campos que tienen valores diferentes de None
	def to_payload(self) -> Dict[str, Any]:
		payload: Dict[str, Any] = {}
		if self.first_name is not None:
			payload["firstName"] = self.first_name
		if self.last_name is not None:
			payload["lastName"] = self.last_name
		return payload

