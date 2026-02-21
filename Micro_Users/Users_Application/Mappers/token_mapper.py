from typing import Optional, Dict, Any

from Users_Application.DTOs.TokenDTO import TokenDTO


# Mapea los tokens de Keycloak a `TokenDTO` usando `model_validate`.
def token_from_keycloak(data: Dict[str, Any]) -> Optional[TokenDTO]:
    if not data:
        return None
    return TokenDTO.model_validate(data)
