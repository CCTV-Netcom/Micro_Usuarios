import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from Users_Domain.Exceptions.exceptions import (
    UserNotFoundException,
    InvalidCredentialsException,
    InvalidEmailFormatException,
    EmailAlreadyExistsException,
)

logger = logging.getLogger("uvicorn.error")


class DomainExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except UserNotFoundException as e:
            return JSONResponse(status_code=404, content={"detail": str(e) or "User not found"})
        except InvalidCredentialsException as e:
            return JSONResponse(status_code=401, content={"detail": str(e) or "Invalid credentials"})
        except InvalidEmailFormatException as e:
            return JSONResponse(status_code=400, content={"detail": str(e) or "Invalid email format"})
        except EmailAlreadyExistsException as e:
            return JSONResponse(status_code=409, content={"detail": str(e) or "Email already exists"})
        except RuntimeError as e:
            return JSONResponse(status_code=400, content={"detail": str(e)})
        except ValidationError as e:
            safe_errors = jsonable_encoder(
                e.errors(),
                custom_encoder={Exception: lambda exc: str(exc)},
            )
            return JSONResponse(status_code=422, content={"detail": safe_errors})
        except Exception as e:
            logger.exception("Unhandled exception during request")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
