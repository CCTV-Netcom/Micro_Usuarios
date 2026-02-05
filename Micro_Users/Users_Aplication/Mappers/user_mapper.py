from typing import Optional, Dict, Any

from Users_Aplication.DTOs.UserDTO import UserDTO


# Mapea los usuarios de Keycloak a `UserDTO` usando `model_validate`.
def user_from_keycloak(data: Dict[str, Any]) -> Optional[UserDTO]:
    if not data:
        return None
    # Pydantic acepta aliases (e.g., firstName) gracias a la configuración
    return UserDTO.model_validate(data)
