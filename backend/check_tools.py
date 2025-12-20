import sys
from pathlib import Path
import asyncio

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.ssh_manager import SSHManager
from app.config import settings

def check_remote_paths():
    print("=" * 60)
    print(f"Verificando herramientas en el cluster {settings.cluster_host}")
    print("=" * 60)

    with SSHManager() as ssh:
        # 1. Verificar VASP
        print(f"\n[INFO] Verificando VASP en: {settings.cluster_vasp_path}")
        if ssh.file_exists(settings.cluster_vasp_path):
            print("[OK] VASP encontrado")
        else:
            print("[ERROR] VASP no encontrado en esa ruta")
            # Intentar buscarlo
            stdout, _, _ = ssh.execute_command("which vasp_std")
            if stdout.strip():
                print(f"   [INFO] Sugerencia: encontrado en {stdout.strip()}")

        # 2. Verificar VASPKIT
        print(f"\n[INFO] Verificando VASPKIT en: {settings.cluster_vaspkit_path}")
        if ssh.file_exists(settings.cluster_vaspkit_path):
            print("[OK] VASPKIT encontrado")
        else:
            print("[ERROR] VASPKIT no encontrado en esa ruta")
            # Intentar buscarlo
            stdout, _, _ = ssh.execute_command("which vaspkit")
            if stdout.strip():
                print(f"   [INFO] Sugerencia: encontrado en {stdout.strip()}")

        # 3. Verificar POTCARs
        print(f"\n[INFO] Verificando directorio POTCAR en: {settings.cluster_potcar_path}")
        # file_exists sirve para archivos, para directorios usamos un comando
        stdout, stderr, exit_code = ssh.execute_command(f"test -d {settings.cluster_potcar_path} && echo 'exists'")
        if exit_code == 0 and 'exists' in stdout:
            print("[OK] Directorio POTCAR encontrado")
        else:
            print("[ERROR] Directorio POTCAR no encontrado")

if __name__ == "__main__":
    check_remote_paths()
