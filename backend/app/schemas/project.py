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
    nodelist: Optional[str] = None
    partition: Optional[str] = None
    execution_commands: Optional[list[str]] = []


class JobStatusResponse(BaseModel):
    """Respuesta de estado de trabajo"""
    project_id: int
    job_id: Optional[str]
    status: ProjectStatus
    progress: Optional[float] = None  # Porcentaje de progreso
    current_step: Optional[str] = None
    progress: Optional[float] = None  # Porcentaje de progreso
    current_step: Optional[str] = None
    estimated_time: Optional[int] = None  # Segundos restantes
    error_details: Optional[str] = None
    stdout_excerpt: Optional[str] = None


class RelaxGenerateRequest(BaseModel):
    """Request para generar archivos RELAX con VASPKIT o archivos personalizados"""
    project_id: int
    
    # Parámetros de cálculo (usados si no se proveen archivos)
    encut: float = Field(default=500, description="Energía de corte (eV)")
    kpoints_density: float = Field(default=0.03, description="Densidad de k-points (Å⁻¹)")
    isif: int = Field(default=3, ge=0, le=7, description="Tipo de relajación (0-7)")
    nsw: int = Field(default=100, ge=1, description="Máximo de pasos iónicos")
    ibrion: int = Field(default=2, ge=-1, le=3, description="Algoritmo de optimización")
    ediffg: float = Field(default=-0.01, description="Criterio de convergencia de fuerzas (eV/Å)")
    
    # Archivos opcionales (si se proveen, se usan en lugar de generar)
    incar: Optional[str] = Field(default=None, description="Contenido INCAR personalizado")
    kpoints: Optional[str] = Field(default=None, description="Contenido KPOINTS personalizado")
    potcar_elements: Optional[list[str]] = Field(default=None, description="Lista de elementos para POTCAR")


class RelaxResultsResponse(BaseModel):
    """Respuesta con resultados de cálculo RELAX"""
    project_id: int
    status: ProjectStatus
    
    # Estructura relajada
    contcar: Optional[str] = None  # Contenido del CONTCAR
    
    # Información energética
    final_energy: Optional[float] = None  # Energía final (eV)
    energy_per_atom: Optional[float] = None
    
    # Información de convergencia
    ionic_steps: Optional[int] = None  # Número de pasos iónicos realizados
    converged: Optional[bool] = None
    max_force: Optional[float] = None  # Fuerza máxima residual (eV/Å)
    
    # Extracto del OUTCAR
    outcar_excerpt: Optional[str] = None
