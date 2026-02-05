from pydantic import BaseModel
from typing import Optional, Dict, Any


class UpdateUserCommand(BaseModel):
	user_id: str
	first_name: Optional[str] = None
	last_name: Optional[str] = None
	#Este payload solo incluye campos que tienen valores diferentes de None
	def to_payload(self) -> Dict[str, Any]:
		payload: Dict[str, Any] = {}
		if self.first_name is not None:
			payload["firstName"] = self.first_name
		if self.last_name is not None:
			payload["lastName"] = self.last_name
		return payload

