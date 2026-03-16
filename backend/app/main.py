from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.models.database import init_db
from app.api.routes import projects, dos, relax

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="VASP GUI API",
    description="API Backend para interfaz gráfica de VASP con soporte para cálculos DOS",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(projects.router, prefix="/api")
app.include_router(dos.router, prefix="/api")
app.include_router(relax.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar"""
    logger.info("Iniciando aplicación VASP GUI API")
    await init_db()
    logger.info("Base de datos inicializada")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar"""
    logger.info("Cerrando aplicación")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "VASP GUI API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cluster_status = False
    error_msg = None
    
    try:
        from app.core.ssh_manager import SSHManager
        with SSHManager() as ssh:
            # Intentar ejecutar un comando simple
            stdout, stderr, exit_code = ssh.execute_command("echo 'connected'")
            if exit_code == 0:
                cluster_status = True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Health check cluster error: {e}")

    return {
        "status": "healthy",
        "cluster": {
            "host": settings.cluster_host,
            "connected": cluster_status,
            "error": error_msg
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
