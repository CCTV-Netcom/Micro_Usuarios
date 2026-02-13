from typing import Optional, Dict, Any

from Users_Application.DTOs.UserDTO import UserDTO
from Users_Domain.Enums.role import RoleEnum


# Mapea los usuarios de Keycloak a `UserDTO` usando `model_validate`.
def user_from_keycloak(data: Dict[str, Any]) -> Optional[UserDTO]:
    if not data:
        return None
    attributes = data.get("attributes") or {}
    role_values = (
        data.get("realmRoles")
        or attributes.get("Rol")
        or attributes.get("rol")
        or attributes.get("role")
        or attributes.get("Role")
    )
    rol = None
    if isinstance(role_values, list):
        for role_name in (RoleEnum.ADMINISTRADOR.value, RoleEnum.OPERADOR.value):
            if role_name in role_values:
                rol = role_name
                break
        if rol is None and role_values:
            rol = role_values[0]
    # Pydantic acepta aliases (e.g., firstName) gracias a la configuración
    return UserDTO.model_validate({**data, "rol": rol})
