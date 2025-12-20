from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Cluster SSH
    cluster_host: str
    cluster_port: int = 19022
    cluster_user: str
    cluster_password: str | None = None
    cluster_ssh_key_path: str | None = None
    
    # Rutas en el cluster
    cluster_vasp_path: str
    cluster_vaspkit_path: str
    cluster_potcar_path: str
    cluster_work_dir: str
    
    # Base de datos
    database_url: str = "sqlite+aiosqlite:///./vasp_gui.db"
    
    # Aplicación
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Monitoreo
    job_check_interval: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
