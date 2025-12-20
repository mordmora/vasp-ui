from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class CalculationType(str, enum.Enum):
    """Tipos de cálculo disponibles"""
    DOS = "dos"
    BAND = "band"
    OPT = "optimization"
    MD = "molecular_dynamics"


class ProjectStatus(str, enum.Enum):
    """Estados del proyecto"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Project(Base):
    """Modelo de proyecto VASP"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    calculation_type = Column(SQLEnum(CalculationType), nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    
    # Archivos VASP (almacenados como texto)
    poscar = Column(Text, nullable=True)
    incar = Column(Text, nullable=True)
    kpoints = Column(Text, nullable=True)
    potcar_info = Column(Text, nullable=True)  # JSON con info de POTCAR
    
    # Información del cluster
    remote_path = Column(String(500), nullable=True)
    job_id = Column(String(100), nullable=True)  # ID del sistema de colas
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resultados (JSON serializado)
    results = Column(Text, nullable=True)
    error_log = Column(Text, nullable=True)
