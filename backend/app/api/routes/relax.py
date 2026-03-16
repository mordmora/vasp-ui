from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import re
import json
from datetime import datetime

from app.models.database import get_db
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    RelaxGenerateRequest,
    RelaxResultsResponse,
    JobSubmitRequest,
    JobStatusResponse,
    ProjectResponse
)

from app.core.ssh_manager import SSHManager
from app.services.vaspkit_service import VASPKITService
from app.config import settings
from pymatgen.core import Structure

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relax", tags=["RELAX Calculations"])


@router.post("/generate", response_model=ProjectResponse)
async def generate_relax_files(
    request: RelaxGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Genera archivos INCAR, KPOINTS y POTCAR para cálculo de relajación estructural.
    
    Si el usuario proporciona archivos personalizados (incar, kpoints), se usan
    directamente. Si no se proveen, se generan automáticamente con VASPKIT.
    
    Args:
        request: RelaxGenerateRequest con project_id, parámetros de cálculo y
                 archivos opcionales (incar, kpoints, potcar_elements).
        db: Sesión de base de datos async.
    
    Returns:
        ProjectResponse: Proyecto actualizado con archivos generados y estado READY.
    
    Raises:
        HTTPException: 404 si proyecto no existe, 400 si no tiene POSCAR,
                       500 para errores durante generación.
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
            
            # Subir POSCAR del proyecto
            ssh.upload_text_file(project.poscar, f"{remote_path}/POSCAR")
            
            # Usar VASPKIT para generar archivos
            vaspkit = VASPKITService(ssh)
            
            generated_files = vaspkit.generate_relax_inputs(
                work_dir=remote_path,
                encut=request.encut,
                kpoints_density=request.kpoints_density,
                isif=request.isif,
                nsw=request.nsw,
                ibrion=request.ibrion,
                ediffg=request.ediffg,
                custom_incar=request.incar,
                custom_kpoints=request.kpoints
            )
            
            # Extraer elementos del POSCAR para POTCAR
            structure = Structure.from_str(project.poscar, fmt="poscar")
            
            # Usar elementos personalizados o extraer del POSCAR
            if request.potcar_elements:
                elements = request.potcar_elements
            else:
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
        
        logger.info(f"Archivos RELAX generados para proyecto {project.id}")
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generando archivos RELAX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar archivos RELAX: {str(e)}"
        )


@router.post("/submit", response_model=JobStatusResponse)
async def submit_relax_job(
    request: JobSubmitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Envía un trabajo RELAX al cluster mediante SLURM.
    
    Args:
        request: JobSubmitRequest con project_id, ncores y walltime.
        background_tasks: Para tareas de monitoreo en segundo plano.
        db: Sesión de base de datos async.
    
    Returns:
        JobStatusResponse: Estado inicial del trabajo enviado.
    
    Raises:
        HTTPException: 404 si proyecto no existe, 400 si no está en estado READY
                       o faltan archivos, 500 para errores de envío.
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
            
            # Crear script de trabajo para RELAX
            job_script = vaspkit.create_job_script(
                work_dir=project.remote_path,
                job_name=f"relax_{project.id}",
                ncores=request.ncores,
                walltime=request.walltime,
                nodelist=request.nodelist,
                partition=request.partition,
                execution_commands=request.execution_commands,
                calc_type="relax"
            )
            
            # Subir script
            script_path = f"{project.remote_path}/job.sh"
            ssh.upload_text_file(job_script, script_path)
            
            # Ejecutar script (enviar al sistema de colas o ejecución directa)
            submit_cmd = f"cd {project.remote_path} && source ~/.bashrc && sbatch job.sh"
            stdout, stderr, exit_code = ssh.execute_command(submit_cmd)
            
            job_id = None
            
            if exit_code == 0:
                # Éxito con SLURM
                # Extraer job ID (formato SLURM: "Submitted batch job 12345")
                job_id = stdout.strip().split()[-1]
                logger.info(f"Job enviado via SLURM: {job_id}")
            else:
                # Fallo SLURM, intentar ejecución directa (nohup)
                logger.warning(f"Fallo sbatch ({stderr}), intentando ejecución directa con nohup...")
                
                # Ejecutar en background con nohup y guardar PID
                # Redirigimos stderr y stdout a los mismos archivos que usaría SLURM
                direct_cmd = (
                    f"cd {project.remote_path} && "
                    f"source ~/.bashrc && "
                    f"nohup bash job.sh > vasp_nohup.out 2> vasp_nohup.err & "
                    f"echo $!"  # Imprimir PID del proceso en background
                )
                
                stdout, stderr, exit_code = ssh.execute_command(direct_cmd)
                
                if exit_code != 0:
                    raise RuntimeError(f"Error al enviar trabajo (SLURM y Directo fallaron): {stderr}")
                
                job_id = stdout.strip()
                logger.info(f"Job enviado via Direct Execution (nohup): PID {job_id}")
            
            # Actualizar proyecto
            
            # Actualizar proyecto
            project.job_id = job_id
            project.status = ProjectStatus.RUNNING
            project.started_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(project)
        
        logger.info(f"Trabajo RELAX enviado: proyecto {project.id}, job_id {job_id}")
        
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
        logger.error(f"Error enviando trabajo RELAX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar trabajo: {str(e)}"
        )


@router.get("/status/{project_id}", response_model=JobStatusResponse)
async def get_relax_status(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el estado actual de un trabajo RELAX.
    
    Verifica el estado en el cluster si el trabajo está corriendo, y actualiza
    el estado en la base de datos según corresponda.
    
    Args:
        project_id: ID del proyecto a consultar.
        db: Sesión de base de datos async.
    
    Returns:
        JobStatusResponse: Estado actual del trabajo.
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
        
        current_step = f"Status: {project.status.value}"
        progress = None
        
        # Si el trabajo está corriendo, verificar estado en el cluster
        if project.status == ProjectStatus.RUNNING and project.job_id:
            with SSHManager() as ssh:
                # Comando para verificar estado (SLURM)
                cmd = f"squeue -j {project.job_id} --noheader"
                stdout, stderr, exit_code = ssh.execute_command(cmd)
                
                is_running = False
                
                if exit_code == 0 and stdout.strip():
                    # Job todavía en cola/corriendo en SLURM
                    is_running = True
                    current_step = "Running on cluster (SLURM)"
                else:
                    # Verificar si es un proceso directo (PID)
                    # ps -p <PID> -o comm=  devuelve el nombre del comando si existe
                    cmd_pid = f"ps -p {project.job_id} -o comm="
                    stdout_pid, _, exit_code_pid = ssh.execute_command(cmd_pid)
                    
                    if exit_code_pid == 0 and stdout_pid.strip():
                        is_running = True
                        current_step = f"Running on cluster (PID: {project.job_id})"
                
                if is_running:
                    # Intentar leer progreso del OSZICAR
                    oszicar_path = f"{project.remote_path}/OSZICAR"
                    if ssh.file_exists(oszicar_path):
                        oszicar_content = ssh.read_remote_file(oszicar_path)
                        ionic_steps = len(re.findall(r'^\s*\d+\s+F=', oszicar_content, re.MULTILINE))
                        current_step += f" - {ionic_steps} ionic steps"
                else:
                    # Job ya no está en cola/corriendo, verificar si completó
                    outcar_exists = ssh.file_exists(f"{project.remote_path}/OUTCAR")
                    # Job ya no está en cola, verificar si completó
                    outcar_exists = ssh.file_exists(f"{project.remote_path}/OUTCAR")
                    contcar_exists = ssh.file_exists(f"{project.remote_path}/CONTCAR")
                    
                    if outcar_exists:
                        # Leer últimas líneas para verificar completación
                        cmd = f"tail -n 30 {project.remote_path}/OUTCAR"
                        stdout, stderr, _ = ssh.execute_command(cmd)
                        
                        if "reached required accuracy" in stdout or \
                           "General timing and accounting informations for this job" in stdout:
                            project.status = ProjectStatus.COMPLETED
                            project.completed_at = datetime.utcnow()
                            
                            # Guardar CONTCAR en results si existe
                            if contcar_exists:
                                contcar_content = ssh.read_remote_file(f"{project.remote_path}/CONTCAR")
                                results_data = {
                                    "contcar": contcar_content,
                                    "converged": "reached required accuracy" in stdout
                                }
                                project.results = json.dumps(results_data)
                            
                            await db.commit()
                            current_step = "Completed successfully"
                        else:
                            project.status = ProjectStatus.FAILED
                            current_step = "Job failed - not converged"
                            
                            # Intentar leer stderr para más detalles (SLURM o nohup)
                            err_file = f"{project.remote_path}/vasp_{project.job_id}.err"
                            nohup_err = f"{project.remote_path}/vasp_nohup.err"
                            
                            found_err = False
                            if ssh.file_exists(err_file):
                                err_content = ssh.read_remote_file(err_file)
                                project.error_log = err_content
                                error_details = err_content
                                found_err = True
                            elif ssh.file_exists(nohup_err):
                                err_content = ssh.read_remote_file(nohup_err)
                                project.error_log = err_content
                                error_details = err_content
                                found_err = True
                            
                            if not found_err:
                                project.error_log = "Job finished but did not converge"

                            await db.commit()
                            
                    else:
                        # No OUTCAR found - probable startup failure
                        project.status = ProjectStatus.FAILED
                        current_step = "Job failed - startup error"
                        
                        # Leer stderr y stdout para diagnóstico
                        err_file = f"{project.remote_path}/vasp_{project.job_id}.err"
                        out_file = f"{project.remote_path}/vasp_{project.job_id}.out"
                        nohup_err = f"{project.remote_path}/vasp_nohup.err"
                        nohup_out = f"{project.remote_path}/vasp_nohup.out"
                        
                        error_msg = "No OUTCAR found after job completion."
                        
                        # Check stderr
                        if ssh.file_exists(err_file):
                            err_content = ssh.read_remote_file(err_file)
                            if err_content.strip():
                                error_msg += f"\nSTDERR (SLURM):\n{err_content}"
                                error_details = err_content
                        elif ssh.file_exists(nohup_err):
                            err_content = ssh.read_remote_file(nohup_err)
                            if err_content.strip():
                                error_msg += f"\nSTDERR (Nohup):\n{err_content}"
                                error_details = err_content
                        
                        # Check stdout
                        if ssh.file_exists(out_file):
                            out_content = ssh.read_remote_file(out_file)
                            if out_content.strip():
                                error_msg += f"\nSTDOUT Excerpt:\n{out_content[-1000:]}"
                                stdout_excerpt = out_content[-2000:]
                        elif ssh.file_exists(nohup_out):
                            out_content = ssh.read_remote_file(nohup_out)
                            if out_content.strip():
                                error_msg += f"\nSTDOUT Excerpt (Nohup):\n{out_content[-1000:]}"
                                stdout_excerpt = out_content[-2000:]
                        
                        project.error_log = error_msg
                        await db.commit()
        
        # Preparar respuesta incluyendo detalles de error si existen
        response_error_details = error_details if 'error_details' in locals() else project.error_log
        
        return JobStatusResponse(
            project_id=project.id,
            job_id=project.job_id,
            status=project.status,
            progress=progress,
            current_step=current_step,
            error_details=response_error_details,
            stdout_excerpt=stdout_excerpt if 'stdout_excerpt' in locals() else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado RELAX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado: {str(e)}"
        )


@router.get("/results/{project_id}", response_model=RelaxResultsResponse)
async def get_relax_results(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los resultados de un cálculo RELAX completado.
    
    Descarga y parsea el CONTCAR (estructura relajada), extrae información
    energética del OUTCAR, y devuelve datos de convergencia.
    
    Args:
        project_id: ID del proyecto a consultar.
        db: Sesión de base de datos async.
    
    Returns:
        RelaxResultsResponse: Resultados del cálculo incluyendo CONTCAR,
                              energía final, pasos iónicos y estado de convergencia.
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
        
        # Intentar cargar resultados guardados
        contcar_content = None
        converged = None
        
        if project.results:
            try:
                results_data = json.loads(project.results)
                contcar_content = results_data.get("contcar")
                converged = results_data.get("converged")
            except json.JSONDecodeError:
                pass
        
        with SSHManager() as ssh:
            # Leer CONTCAR si no está en results
            if not contcar_content:
                contcar_path = f"{project.remote_path}/CONTCAR"
                if ssh.file_exists(contcar_path):
                    contcar_content = ssh.read_remote_file(contcar_path)
                    
                    # Actualizar results en proyecto
                    results_data = {"contcar": contcar_content, "converged": converged}
                    project.results = json.dumps(results_data)
                    await db.commit()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Archivo CONTCAR no encontrado"
                    )
            
            # Leer OUTCAR para información energética
            outcar_path = f"{project.remote_path}/OUTCAR"
            outcar_content = ""
            final_energy = None
            energy_per_atom = None
            ionic_steps = None
            max_force = None
            
            if ssh.file_exists(outcar_path):
                outcar_content = ssh.read_remote_file(outcar_path)
                
                # Extraer energía final (última ocurrencia de "free  energy   TOTEN")
                energy_matches = re.findall(
                    r'free\s+energy\s+TOTEN\s*=\s*([-\d.]+)\s*eV',
                    outcar_content
                )
                if energy_matches:
                    final_energy = float(energy_matches[-1])
                
                # Contar pasos iónicos
                ionic_steps = len(re.findall(r'LOOP\+:', outcar_content))
                
                # Extraer fuerza máxima (última ocurrencia)
                force_matches = re.findall(
                    r'TOTAL-FORCE.*?total drift:\s*([-\d.]+)',
                    outcar_content,
                    re.DOTALL
                )
                
                # Buscar max force de otra forma
                force_lines = re.findall(
                    r'RMS\s*=\s*([-\d.E+]+)',
                    outcar_content
                )
                if force_lines:
                    try:
                        max_force = float(force_lines[-1])
                    except ValueError:
                        pass
                
                # Verificar convergencia
                if converged is None:
                    converged = "reached required accuracy" in outcar_content
                
                # Calcular energía por átomo
                if final_energy and contcar_content:
                    try:
                        structure = Structure.from_str(contcar_content, fmt="poscar")
                        energy_per_atom = final_energy / len(structure)
                    except Exception:
                        pass
        
        return RelaxResultsResponse(
            project_id=project_id,
            status=project.status,
            contcar=contcar_content,
            final_energy=final_energy,
            energy_per_atom=energy_per_atom,
            ionic_steps=ionic_steps,
            converged=converged,
            max_force=max_force,
            outcar_excerpt=outcar_content[-3000:] if outcar_content else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo resultados RELAX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resultados: {str(e)}"
        )
