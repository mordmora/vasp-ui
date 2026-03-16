from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from datetime import datetime
from pathlib import Path

from app.models.database import get_db
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    DOSGenerateRequest,
    JobSubmitRequest,
    JobStatusResponse,
    ProjectResponse
)
from app.core.ssh_manager import SSHManager, get_ssh_manager
from app.services.vaspkit_service import VASPKITService
from app.config import settings
from pymatgen.core import Structure

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dos", tags=["DOS Calculations"])

@router.post("/generate", response_model=ProjectResponse)
async def generate_dos_files(
    request: DOSGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate INCAR and KPOINTS files for DOS calculation using VASPKIT.

    This endpoint creates the necessary input files for a Density of States (DOS)
    calculation by connecting to a remote cluster via SSH, uploading the POSCAR file,
    and using VASPKIT to generate INCAR, KPOINTS, and POTCAR files.

    Args:
        request: DOSGenerateRequest containing project_id, encut, and kpoints_density.
        db: Async database session dependency.

    Returns:
        ProjectResponse: The updated project with generated files and READY status.

    Raises:
        HTTPException: 404 if project not found, 400 if no POSCAR defined,
                       500 for other errors during file generation.
    """
    try:
        # Obtener proyecto
        result = await db.execute(
            select(Project).where(Project.id == request.project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto {request.project_id} no encontrado"
            )
        
        if not project.poscar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proyecto no tiene un POSCAR definido"
            )
        
        # Crear directorio remoto
        remote_path = f"{settings.cluster_work_dir}/project_{project.id}"
        
        with SSHManager() as ssh:
            # Crear directorio
            ssh.create_remote_directory(remote_path)
            
            # Subir POSCAR
            ssh.upload_text_file(project.poscar, f"{remote_path}/POSCAR")
            
            # Usar VASPKIT para generar archivos
            vaspkit = VASPKITService(ssh)
            
            generated_files = vaspkit.generate_dos_inputs(
                work_dir=remote_path,
                encut=request.encut,
                kpoints_density=request.kpoints_density
            )
            
            # Extraer elementos del POSCAR para POTCAR
            structure = Structure.from_str(project.poscar, fmt="poscar")
            elements = [str(el) for el in structure.composition.elements]
            
            # Generar POTCAR
            vaspkit.generate_potcar(remote_path, elements)
            
            # Actualizar proyecto con archivos generados
            project.incar = generated_files["incar"]
            project.kpoints = generated_files["kpoints"]
            project.potcar_info = ','.join(elements)
            project.remote_path = remote_path
            project.status = ProjectStatus.READY
            
            await db.commit()
            await db.refresh(project)
        
        logger.info(f"Archivos DOS generados para proyecto {project.id}")
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generando archivos DOS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar archivos DOS: {str(e)}"
        )


@router.post("/submit", response_model=JobStatusResponse)
async def submit_dos_job(
    request: JobSubmitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Envía un trabajo DOS al cluster
    """
    try:
        # Obtener proyecto
        result = await db.execute(
            select(Project).where(Project.id == request.project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto {request.project_id} no encontrado"
            )
        
        if project.status != ProjectStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El proyecto debe estar en estado READY. Estado actual: {project.status}"
            )
        
        if not project.remote_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proyecto no tiene una ruta remota asignada"
            )
        
        with SSHManager() as ssh:
            vaspkit = VASPKITService(ssh)
            
            # Validar que todos los archivos existan
            validation = vaspkit.validate_inputs(project.remote_path)
            
            missing_files = [f for f, exists in validation.items() if not exists]
            if missing_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Faltan archivos de entrada: {', '.join(missing_files)}"
                )
            
            # Crear script de trabajo
            job_script = vaspkit.create_job_script(
                work_dir=project.remote_path,
                job_name=f"dos_{project.id}",
                ncores=request.ncores,
                walltime=request.walltime
            )
            
            # Subir script
            script_path = f"{project.remote_path}/job.sh"
            ssh.upload_text_file(job_script, script_path)
            
            # Ejecutar script (enviar al sistema de colas)
            submit_cmd = f"cd {project.remote_path} && sbatch job.sh"
            stdout, stderr, exit_code = ssh.execute_command(submit_cmd)
            
            if exit_code != 0:
                raise RuntimeError(f"Error al enviar trabajo: {stderr}")
            
            # Extraer job ID (formato SLURM: "Submitted batch job 12345")
            job_id = stdout.strip().split()[-1]
            
            # Actualizar proyecto
            project.job_id = job_id
            project.status = ProjectStatus.RUNNING
            project.started_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(project)
        
        # Programar monitoreo en background
        # background_tasks.add_task(monitor_job, project.id)
        
        logger.info(f"Trabajo enviado: proyecto {project.id}, job_id {job_id}")
        
        return JobStatusResponse(
            project_id=project.id,
            job_id=job_id,
            status=ProjectStatus.RUNNING,
            current_step="Job submitted to queue"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error enviando trabajo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar trabajo: {str(e)}"
        )


@router.get("/status/{project_id}", response_model=JobStatusResponse)
async def get_job_status(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el estado actual de un trabajo DOS
    """
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto {project_id} no encontrado"
            )
        
        # Si el trabajo está corriendo, verificar estado en el cluster
        if project.status == ProjectStatus.RUNNING and project.job_id:
            with SSHManager() as ssh:
                # Comando para verificar estado (SLURM)
                cmd = f"squeue -j {project.job_id} --noheader"
                stdout, stderr, exit_code = ssh.execute_command(cmd)
                
                if exit_code == 0 and stdout.strip():
                    # Job todavía en cola/corriendo
                    current_step = "Running on cluster"
                else:
                    # Job ya no está en cola, verificar si completó
                    outcar_exists = ssh.file_exists(f"{project.remote_path}/OUTCAR")
                    
                    if outcar_exists:
                        # Leer últimas líneas para verificar completación
                        cmd = f"tail -n 20 {project.remote_path}/OUTCAR"
                        stdout, stderr, _ = ssh.execute_command(cmd)
                        
                        if "General timing and accounting informations for this job" in stdout:
                            project.status = ProjectStatus.COMPLETED
                            project.completed_at = datetime.utcnow()
                            await db.commit()
                            current_step = "Completed successfully"
                        else:
                            project.status = ProjectStatus.FAILED
                            await db.commit()
                            current_step = "Job failed"
                    else:
                        project.status = ProjectStatus.FAILED
                        await db.commit()
                        current_step = "No output found"
        else:
            current_step = f"Status: {project.status.value}"
        
        return JobStatusResponse(
            project_id=project.id,
            job_id=project.job_id,
            status=project.status,
            current_step=current_step
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado: {str(e)}"
        )


@router.get("/results/{project_id}")
async def get_dos_results(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga y parsea resultados DOS
    """
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto {project_id} no encontrado"
            )
        
        if project.status != ProjectStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El proyecto no está completado. Estado: {project.status}"
            )
        
        with SSHManager() as ssh:
            # Leer archivo DOSCAR
            doscar_path = f"{project.remote_path}/DOSCAR"
            
            if not ssh.file_exists(doscar_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Archivo DOSCAR no encontrado"
                )
            
            doscar_content = ssh.read_remote_file(doscar_path)
            
            # También leer OUTCAR para información adicional
            outcar_path = f"{project.remote_path}/OUTCAR"
            outcar_content = ssh.read_remote_file(outcar_path)
        
        # Aquí podrías parsear con pymatgen
        # from pymatgen.io.vasp import Vasprun, Doscar
        # doscar = Doscar.from_file(doscar_path)
        
        return {
            "project_id": project_id,
            "doscar": doscar_content,
            "outcar_excerpt": outcar_content[-2000:]  # Últimos caracteres
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resultados: {str(e)}"
        )
