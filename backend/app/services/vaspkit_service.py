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
        
        # VASPKIT opción 101: Generate INCAR (v1.3.5: 1 -> 101)
        # Opción 5: DOS calculation
        # Prepend '1' to enter VASP Input-Files Kit menu
        vaspkit_incar_cmd = f"{cd_cmd} && echo -e '1\\n101\\n5\\n' | {self.vaspkit_path}"
        
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
        
        # VASPKIT opción 102: Generate KPOINTS (v1.3.5: 1 -> 102)
        # Modo automático con densidad
        vaspkit_kpoints_cmd = (
            f"{cd_cmd} && echo -e '1\\n102\\n2\\n{kpoints_density}\\n' | {self.vaspkit_path}"
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
    
    def generate_relax_inputs(
        self,
        work_dir: str,
        encut: float = 500,
        kpoints_density: float = 0.03,
        isif: int = 3,
        nsw: int = 100,
        ibrion: int = 2,
        ediffg: float = -0.01,
        custom_incar: Optional[str] = None,
        custom_kpoints: Optional[str] = None,
        **kwargs
    ) -> Dict[str, str]:
        """
        Genera archivos INCAR y KPOINTS para cálculo RELAX usando VASPKIT
        o usa archivos personalizados si se proveen.
        
        Args:
            work_dir: Directorio de trabajo en el cluster
            encut: Energía de corte (eV)
            kpoints_density: Densidad de k-points
            isif: Tipo de relajación (0-7)
            nsw: Máximo de pasos iónicos
            ibrion: Algoritmo de optimización
            ediffg: Criterio de convergencia de fuerzas
            custom_incar: INCAR personalizado (si se provee, se usa directamente)
            custom_kpoints: KPOINTS personalizado (si se provee, se usa directamente)
            
        Returns:
            Dict con contenido de archivos generados/usados
        """
        logger.info(f"Generando archivos RELAX en {work_dir}")
        
        cd_cmd = f"cd {work_dir}"
        
        # --- INCAR ---
        if custom_incar:
            # Usar INCAR personalizado del usuario
            logger.info("Usando INCAR personalizado")
            incar_content = custom_incar
            self.ssh.upload_text_file(incar_content, f"{work_dir}/INCAR")
        else:
            # Generar con VASPKIT opción 101 + 6 (Structure Optimization)
            # v1.3.5: 1 -> 101 (INCAR) -> 6
            vaspkit_incar_cmd = f"{cd_cmd} && echo -e '1\\n101\\n6\\n' | {self.vaspkit_path}"
            
            stdout, stderr, exit_code = self.ssh.execute_command(vaspkit_incar_cmd)
            
            if exit_code != 0:
                raise RuntimeError(f"Error ejecutando VASPKIT para INCAR: {stderr}")
            
            # Leer INCAR generado y modificar parámetros RELAX
            incar_content = self.ssh.read_remote_file(f"{work_dir}/INCAR")
            incar_content = self._modify_relax_incar(
                incar_content, encut, isif, nsw, ibrion, ediffg
            )
            
            # Subir INCAR modificado
            self.ssh.upload_text_file(incar_content, f"{work_dir}/INCAR")
        
        # --- KPOINTS ---
        if custom_kpoints:
            # Usar KPOINTS personalizado del usuario
            logger.info("Usando KPOINTS personalizado")
            kpoints_content = custom_kpoints
            self.ssh.upload_text_file(kpoints_content, f"{work_dir}/KPOINTS")
        else:
            # Generar con VASPKIT opción 102 + 2 (Monkhorst-Pack automático)
            # v1.3.5: 1 -> 102 (KPOINTS) -> 2
            vaspkit_kpoints_cmd = (
                f"{cd_cmd} && echo -e '1\\n102\\n2\\n{kpoints_density}\\n' | {self.vaspkit_path}"
            )

            stdout, stderr, exit_code = self.ssh.execute_command(vaspkit_kpoints_cmd)

            if exit_code != 0:
                raise RuntimeError(f"Error ejecutando VASPKIT para KPOINTS: {stderr}")

            kpoints_content = self.ssh.read_remote_file(f"{work_dir}/KPOINTS")

        logger.info("Archivos RELAX generados exitosamente")

        return {
            "incar": incar_content,
            "kpoints": kpoints_content
        }
    
    def _modify_relax_incar(
        self,
        incar_content: str,
        encut: float,
        isif: int,
        nsw: int,
        ibrion: int,
        ediffg: float
    ) -> str:
        """
        Modifica el INCAR generado por VASPKIT con parámetros RELAX específicos.
        """
        # Parámetros a establecer/modificar
        relax_params = {
            'ENCUT': str(encut),
            'ISIF': str(isif),
            'NSW': str(nsw),
            'IBRION': str(ibrion),
            'EDIFFG': str(ediffg),
            'EDIFF': '1E-6',  # Convergencia electrónica
            'PREC': 'Accurate',
            'LREAL': 'Auto',
            'LWAVE': '.FALSE.',  # No guardar WAVECAR (ahorra espacio)
            'LCHARG': '.FALSE.',  # No guardar CHGCAR
        }

        incar_lines = incar_content.split('\n')
        found_params = set()
        modified_lines = []

        for line in incar_lines:
            line_stripped = line.strip()
            modified = False

            for param, value in relax_params.items():
                if line_stripped.startswith(param):
                    modified_lines.append(f'{param} = {value}')
                    found_params.add(param)
                    modified = True
                    break

            if not modified:
                modified_lines.append(line)

        # Añadir parámetros faltantes al final
        missing_params = set(relax_params.keys()) - found_params
        if missing_params:
            modified_lines.append('')
            modified_lines.append('# RELAX parameters added by VASP GUI')
            for param in missing_params:
                modified_lines.append(f'{param} = {relax_params[param]}')

        return '\n'.join(modified_lines)

    def generate_potcar(self, work_dir: str, elements: list[str]) -> None:
        """
        Genera POTCAR para los elementos especificados

        Args:
            work_dir: Directorio de trabajo
            elements: Lista de símbolos químicos (ej: ['Si', 'O'])
        """
        logger.info(f"Generando POTCAR para elementos: {elements}")

        # VASPKIT opción 103: Generate POTCAR (v1.3.5: 1 -> 103)
        # Usando POTCAR recomendados (PBE)
        elements_str = ' '.join(elements)

        cd_cmd = f"cd {work_dir}"
        # Prepend '1' to enter menu
        vaspkit_cmd = f"{cd_cmd} && echo -e '1\\n103\\n{elements_str}\\n' | {self.vaspkit_path}"

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
        walltime: str = "24:00:00",
        nodelist: Optional[str] = None,
        partition: Optional[str] = None,
        execution_commands: Optional[list[str]] = [],
        calc_type: str = "dos"
    ) -> str:
        """
        Crea un script de trabajo para SLURM/PBS

        Args:
            work_dir: Directorio de trabajo
            job_name: Nombre del job
            ncores: Número de cores
            walltime: Tiempo máximo de ejecución
            calc_type: Tipo de cálculo ('dos', 'relax', 'band')
        
        Returns:
            Contenido del script
        """
        # Ajustar walltime por defecto según tipo de cálculo
        if walltime == "24:00:00" and calc_type == "relax":
            walltime = "48:00:00"  # RELAX suele necesitar más tiempo

        # Este es un template básico para SLURM
        # Ajusta según el sistema de colas de tu cluster

        script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --ntasks={ncores}
#SBATCH --time={walltime}
{f'#SBATCH --nodelist={nodelist}' if nodelist else ''}
{f'#SBATCH --partition={partition}' if partition else ''}
#SBATCH --output=vasp_%j.out
#SBATCH --error=vasp_%j.err

# Cambiar al directorio de trabajo
cd {work_dir}

# Comandos de configuración del entorno (añadidos dinámicamente)
{chr(10).join(execution_commands) if execution_commands else ''}

# Ejecutar VASP
mpirun -np {ncores} {settings.cluster_vasp_path}

# Opcional: ejecutar post-procesamiento con VASPKIT
# echo -e '11\\n' | {self.vaspkit_path}  # Calcular DOS
"""
        
        return script
