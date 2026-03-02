# Micro_Usuarios 🔐👤

![banner](https://dummyimage.com/1200x300/0b1b2b/ffffff&text=Micro_Usuarios+%E2%80%94+Netcom+CCTV)

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.12.5-e92063?logo=pydantic&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.40.0-4051b5?logo=uvicorn&logoColor=white)

Microservicio de **usuarios y autenticación** para el sistema CCTV Netcom. Incluye registro, login, refresh token y manejo de TOTP.

---

## 🧱 Arquitectura
Se usa una **arquitectura por capas** (inspirada en Clean/Hexagonal):

- **API**: controladores HTTP y orquestación de casos de uso.
- **Application**: comandos/queries, handlers y DTOs.
- **Domain**: entidades y excepciones de negocio.
- **Infrastructure**: adaptadores externos (Keycloak y persistencia/servicios).

Esta separación mantiene la lógica de negocio independiente de frameworks y detalles de infraestructura.

---

## 🧰 Tecnologías y versiones
- **Python**: 3.x
- **FastAPI**: 0.128.0
- **Pydantic**: 2.12.5
- **Uvicorn**: 0.40.0
- **Starlette**: 0.50.0
- **python-dotenv**: 1.2.1
- **qrcode / Pillow**: generación de QR para TOTP

> Las versiones provienen de [Micro_Usuarios/Micro_Users/requirements.txt](Micro_Users/requirements.txt).

---

## 🗂️ Estructura de carpetas

```
Micro_Usuarios/
├── Micro_Users/
│   ├── Users_API/
│   ├── Users_Aplication/
│   ├── Users_Domain/
│   ├── Users_Infraestruture/
│   ├── .env
│   ├── .env.example
│   └── requirements.txt
└── README.md
```

---

## ⚙️ Configuración de entorno

1) **Crear entorno virtual**

```bash
python -m venv venv
```

2) **Activar entorno virtual**

**Linux/macOS**
```bash
source venv/bin/activate
```

**Windows (PowerShell)**
```bash
venv\Scripts\Activate.ps1
```

3) **Instalar dependencias**

```bash
pip install -r requirements.txt
```

---

## 🔐 Variables de entorno

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

Variables esperadas:
- `KEYCLOAK_URL`
- `KEYCLOAK_REALM`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET`
- (Opcionales) `KEYCLOAK_ADMIN_USER`, `KEYCLOAK_ADMIN_PASS`

---

## ▶️ Ejecutar el servidor

Desde la carpeta [Micro_Usuarios/Micro_Users](Micro_Users):

```bash
uvicorn Users_API.main:app --host 127.0.0.1 --port 8001 --reload
```

Documentación interactiva:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## ✅ Checklist rápido
- [ ] Crear `.env` con las credenciales correctas
- [ ] Activar entorno virtual
- [ ] Instalar dependencias
- [ ] Ejecutar Uvicorn

---

## 🧩 Endpoints principales (resumen)
- `/users` (POST) crear usuario
- `/users/{user_id}` (GET/PUT) consultar/actualizar
- `/auth/login` (POST) login
- `/auth/refresh` (POST) refresh token
- `/users/{user_id}/totp/register` (POST) registrar TOTP
- `/users/{user_id}/totp/verify` (POST) verificar TOTP

---

## 📸 Imagen/diagramas
#Poner diagrama de Arquitectura si me lo piden 

![architecture-placeholder](https://dummyimage.com/900x400/1b263b/ffffff&text=Diagrama+de+Arquitectura)
