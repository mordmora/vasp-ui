from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CalculationType(str, Enum):
    """Tipos de cálculo"""
    DOS = "dos"
    BAND = "band"
    OPT = "optimization"
    MD = "molecular_dynamics"


class ProjectStatus(str, Enum):
    """Estados del proyecto"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectBase(BaseModel):
    """Schema base para Project"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    calculation_type: CalculationType


class ProjectCreate(ProjectBase):
    """Schema para crear un proyecto"""
    poscar: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema para actualizar un proyecto"""
    name: Optional[str] = None
    description: Optional[str] = None
    poscar: Optional[str] = None
    incar: Optional[str] = None
    kpoints: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    """Schema para respuesta de proyecto"""
    id: int
    status: ProjectStatus
    poscar: Optional[str] = None
    incar: Optional[str] = None
    kpoints: Optional[str] = None
    potcar_info: Optional[str] = None
    remote_path: Optional[str] = None
    job_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[str] = None
    error_log: Optional[str] = None
    
    class Config:
        from_attributes = True


class DOSGenerateRequest(BaseModel):
    """Request para generar archivos DOS con VASPKIT"""
    project_id: int
    nelect: Optional[int] = None  # Número de electrones
    encut: Optional[float] = 400  # Energía de corte (eV)
    kpoints_density: Optional[float] = 0.04  # Densidad de k-points (Å⁻¹)


class JobSubmitRequest(BaseModel):
    """Request para enviar un trabajo al cluster"""
    project_id: int
    ncores: int = Field(default=4, ge=1, le=128)
    walltime: str = "24:00:00"  # Formato HH:MM:SS


class JobStatusResponse(BaseModel):
    """Respuesta de estado de trabajo"""
    project_id: int
    job_id: Optional[str]
    status: ProjectStatus
    progress: Optional[float] = None  # Porcentaje de progreso
    current_step: Optional[str] = None
    estimated_time: Optional[int] = None  # Segundos restantes
