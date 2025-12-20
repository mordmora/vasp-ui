import sys
from pathlib import Path

# Agregar el directorio actual al path para poder importar app
sys.path.insert(0, str(Path(__file__).parent))

from app.core.ssh_manager import SSHManager
from app.config import settings

def test_connection():
    print("=" * 60)
    print(f"Probando conexión SSH a {settings.cluster_user}@{settings.cluster_host}:{settings.cluster_port}")
    print("=" * 60)

    try:
        with SSHManager() as ssh:
            print("✅ Conexión establecida exitosamente!")
            
            # Probar ejecución de comando
            print("\nEjecutando comando 'whoami'...")
            stdout, stderr, exit_code = ssh.execute_command("whoami")
            
            if exit_code == 0:
                print(f"✅ Comando ejecutado correctamente. Usuario remoto: {stdout.strip()}")
            else:
                print(f"❌ Error ejecutando comando: {stderr}")

            # Probar ejecución de comando hostname
            print("\nEjecutando comando 'hostname'...")
            stdout, stderr, exit_code = ssh.execute_command("hostname")
            
            if exit_code == 0:
                print(f"✅ Hostname remoto: {stdout.strip()}")
            else:
                print(f"❌ Error ejecutando comando: {stderr}")
                
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("\nVerifica:")
        print("1. Que la VPN esté conectada (si es necesaria)")
        print("2. Que las credenciales en .env sean correctas")
        print("3. Que el servidor esté accesible")

if __name__ == "__main__":
    test_connection()
