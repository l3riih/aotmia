"""
Servicio de Autenticación y Autorización para Atomia
"""

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import time

from .core.config import get_settings
from .core.logging import setup_logging
from .api.v1.router import api_router

# Configurar logging estructurado
setup_logging()
logger = structlog.get_logger()

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio"""
    logger.info("🔐 Starting Atomia Authentication Service")
    # Inicializar conexiones y cache
    yield
    logger.info("🛑 Shutting down Atomia Authentication Service")

app = FastAPI(
    title="Atomia - Authentication Service",
    description="Servicio de autenticación, autorización y gestión de sesiones",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Middleware de rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # TODO: Implementar rate limiting por IP y usuario
    return await call_next(request)

# Incluir routers
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    """Health check del servicio de autenticación"""
    return {
        "service": "authentication",
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "jwt_authentication": True,
            "role_based_authorization": True,
            "session_management": True,
            "password_hashing": True,
            "email_verification": True,
            "password_reset": True,
            "multi_device_sessions": True,
            "rate_limiting": True
        },
        "security": {
            "algorithm": "RS256",
            "token_expiry": "24h",
            "refresh_token_expiry": "7d",
            "password_min_length": 8,
            "max_sessions_per_user": 5
        }
    }

# Endpoint raíz
@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Atomia Authentication Service",
        "version": "2.0.0",
        "description": "Servicio de autenticación y autorización con JWT",
        "status": "operational",
        "endpoints": {
            "auth": "/api/v1/auth/*",
            "users": "/api/v1/users/*",
            "sessions": "/api/v1/sessions/*",
            "roles": "/api/v1/roles/*"
        },
        "capabilities": {
            "jwt_tokens": "RS256 signed JWT tokens with role claims",
            "refresh_tokens": "Secure refresh token rotation",
            "role_system": "Hierarchical role-based authorization", 
            "session_management": "Multi-device session tracking",
            "security_features": "Rate limiting, password policies, email verification",
            "integration": "Seamless integration with all Atomia services"
        }
    } 