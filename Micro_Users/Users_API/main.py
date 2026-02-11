"""Entrypoint runner: importa la app desde `program` y arranca uvicorn cuando se ejecuta como script."""
from .program import app
#Este es el codigo de arranque del microservicio, importa la app desde el programa y la ejecuta con uvicorn

if __name__ == "__main__":
    import uvicorn

    # el reload colocalo en true cuando estes en desarrollo
    uvicorn.run("Micro_Users.Users_API.main:app", host="127.0.0.1", port=8001, reload=False)
