import logging
from typing import Dict, Optional
from app.core.ssh_manager import SSHManager
from app.config import settings

logger = logging.getLogger(__name__)


class VASPKITService:
    """Servicio para interactuar con VASPKIT en el cluster"""
    
    def __init__(self, ssh: SSHManager):
        self.ssh = ssh
        self.vaspkit_path = settings.cluster_vaspkit_path
    
    def generate_dos_inputs(
        self,
        work_dir: str,
        encut: float = 400,
        kpoints_density: float = 0.04,
        **kwargs
    ) -> Dict[str, str]:
        """
        Genera archivos INCAR y KPOINTS para cálculo DOS usando VASPKIT
        
        Args:
            work_dir: Directorio de trabajo en el cluster
            encut: Energía de corte (eV)
            kpoints_density: Densidad de k-points
            
        Returns:
            Dict con contenido de archivos generados
        """
        logger.info(f"Generando archivos DOS en {work_dir}")
        
        # Navegar al directorio de trabajo
        cd_cmd = f"cd {work_dir}"
        
        # VASPKIT opción 102: Generate INCAR
        # Opción 5: DOS calculation
        vaspkit_incar_cmd = f"{cd_cmd} && echo -e '102\\n5\\n' | {self.vaspkit_path}"
        
        stdout, stderr, exit_code = self.ssh.execute_command(vaspkit_incar_cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Error ejecutando VASPKIT para INCAR: {stderr}")
        
        # Leer INCAR generado y modificar parámetros
        incar_content = self.ssh.read_remote_file(f"{work_dir}/INCAR")
        
        # Modificar ENCUT en INCAR
        incar_lines = incar_content.split('\n')
        modified_lines = []
        encut_found = False
        
        for line in incar_lines:
            if line.strip().startswith('ENCUT'):
                modified_lines.append(f'ENCUT = {encut}')
                encut_found = True
            else:
                modified_lines.append(line)
        
        if not encut_found:
            modified_lines.insert(1, f'ENCUT = {encut}')
        
        incar_content = '\n'.join(modified_lines)
        
        # Subir INCAR modificado
        self.ssh.upload_text_file(incar_content, f"{work_dir}/INCAR")
        
        # VASPKIT opción 101: Generate KPOINTS
        # Modo automático con densidad
        vaspkit_kpoints_cmd = (
            f"{cd_cmd} && echo -e '101\\n2\\n{kpoints_density}\\n' | {self.vaspkit_path}"
        )
        
        stdout, stderr, exit_code = self.ssh.execute_command(vaspkit_kpoints_cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Error ejecutando VASPKIT para KPOINTS: {stderr}")
        
        # Leer archivos generados
        kpoints_content = self.ssh.read_remote_file(f"{work_dir}/KPOINTS")
        
        logger.info("Archivos DOS generados exitosamente")
        
        return {
            "incar": incar_content,
            "kpoints": kpoints_content
        }
    
    def generate_potcar(self, work_dir: str, elements: list[str]) -> None:
        """
        Genera POTCAR para los elementos especificados
        
        Args:
            work_dir: Directorio de trabajo
            elements: Lista de símbolos químicos (ej: ['Si', 'O'])
        """
        logger.info(f"Generando POTCAR para elementos: {elements}")
        
        # VASPKIT opción 103: Generate POTCAR
        # Usando POTCAR recomendados (PBE)
        elements_str = ' '.join(elements)
        
        cd_cmd = f"cd {work_dir}"
        vaspkit_cmd = f"{cd_cmd} && echo -e '103\\n{elements_str}\\n' | {self.vaspkit_path}"
        
        stdout, stderr, exit_code = self.ssh.execute_command(vaspkit_cmd)
        
        if exit_code != 0:
            # Fallback: copiar POTCAR manualmente desde directorio de POTCARs
            self._copy_potcar_manual(work_dir, elements)
        
        logger.info("POTCAR generado exitosamente")
    
    def _copy_potcar_manual(self, work_dir: str, elements: list[str]) -> None:
        """
        Copia POTCAR manualmente desde el directorio de POTCARs del cluster
        """
        potcar_dir = settings.cluster_potcar_path
        
        # Concatenar POTCARs individuales
        potcar_files = [f"{potcar_dir}/{elem}/POTCAR" for elem in elements]
        potcar_list = ' '.join(potcar_files)
        
        cmd = f"cat {potcar_list} > {work_dir}/POTCAR"
        stdout, stderr, exit_code = self.ssh.execute_command(cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Error copiando POTCAR: {stderr}")
    
    def validate_inputs(self, work_dir: str) -> Dict[str, bool]:
        """
        Valida que todos los archivos de entrada VASP existan
        
        Returns:
            Dict con status de cada archivo
        """
        required_files = ['POSCAR', 'INCAR', 'KPOINTS', 'POTCAR']
        
        validation = {}
        for filename in required_files:
            file_path = f"{work_dir}/{filename}"
            validation[filename] = self.ssh.file_exists(file_path)
        
        return validation
    
    def create_job_script(
        self,
        work_dir: str,
        job_name: str,
        ncores: int = 4,
        walltime: str = "24:00:00"
    ) -> str:
        """
        Crea un script de trabajo para SLURM/PBS
        
        Returns:
            Contenido del script
        """
        # Este es un template básico para SLURM
        # Ajusta según el sistema de colas de tu cluster
        
        script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --ntasks={ncores}
#SBATCH --time={walltime}
#SBATCH --output=vasp_%j.out
#SBATCH --error=vasp_%j.err

# Cambiar al directorio de trabajo
cd {work_dir}

# Ejecutar VASP
mpirun -np {ncores} {settings.cluster_vasp_path}

# Opcional: ejecutar post-procesamiento con VASPKIT
# echo -e '11\\n' | {self.vaspkit_path}  # Calcular DOS
"""
        
        return script
