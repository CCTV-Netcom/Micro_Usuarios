#Esta clase estan todas las ecxepciones personalizadas relacionadas con el dominio de usuarios
class UserNotFoundException(Exception):
    """Exception raised when a user is not found."""
    pass
class InvalidCredentialsException(Exception):
    """Exception raised for invalid user credentials."""
    pass
class InvalidEmailFormatException(Exception):
    """Exception raised for invalid email format."""
    pass
class EmailAlreadyExistsException(Exception):
    """Exception raised when an email already exists."""
    pass
