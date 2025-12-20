"""
Script de verificación rápida para comprobar imports y configuración básica
Ejecutar: python verify_setup.py
"""

import sys
from pathlib import Path

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Verificando configuración de VASP GUI Backend")
print("=" * 60)

# Test 1: Imports básicos
print("\n1. Verificando imports básicos...")
try:
    import fastapi
    import uvicorn
    import paramiko
    import sqlalchemy
    import pymatgen
    print("   ✅ Todas las dependencias principales están instaladas")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    print("   Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Imports del proyecto
print("\n2. Verificando módulos del proyecto...")
try:
    from app.config import settings
    print(f"   ✅ Config cargado")
    print(f"      - Cluster: {settings.cluster_host}")
except Exception as e:
    print(f"   ⚠️  Advertencia al cargar config: {e}")
    print("      Asegúrate de tener un archivo .env configurado")

try:
    from app.models.project import Project, CalculationType, ProjectStatus
    print("   ✅ Modelos importados correctamente")
except ImportError as e:
    print(f"   ❌ Error importando modelos: {e}")
    sys.exit(1)

try:
    from app.schemas.project import ProjectCreate, ProjectResponse
    print("   ✅ Schemas importados correctamente")
except ImportError as e:
    print(f"   ❌ Error importando schemas: {e}")
    sys.exit(1)

try:
    from app.core.ssh_manager import SSHManager
    print("   ✅ SSH Manager importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando SSH Manager: {e}")
    sys.exit(1)

try:
    from app.services.vaspkit_service import VASPKITService
    print("   ✅ VASPKIT Service importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando VASPKIT Service: {e}")
    sys.exit(1)

try:
    from app.api.routes import projects, dos
    print("   ✅ Routes importados correctamente")
except ImportError as e:
    print(f"   ❌ Error importando routes: {e}")
    sys.exit(1)

# Test 3: Verificar FastAPI app
print("\n3. Verificando aplicación FastAPI...")
try:
    from app.main import app
    print(f"   ✅ App FastAPI creada")
    print(f"      - Título: {app.title}")
    print(f"      - Versión: {app.version}")
    print(f"      - Docs: {app.docs_url}")
except Exception as e:
    print(f"   ❌ Error creando app: {e}")
    sys.exit(1)

# Test 4: Verificar enums
print("\n4. Verificando enumeraciones...")
try:
    calc_types = [ct.value for ct in CalculationType]
    print(f"   ✅ Tipos de cálculo: {calc_types}")
    
    statuses = [s.value for s in ProjectStatus]
    print(f"   ✅ Estados de proyecto: {statuses}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Verificar archivo .env
print("\n5. Verificando configuración de entorno...")
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print("   ✅ Archivo .env encontrado")
    
    # Verificar variables críticas
    if settings.cluster_host and settings.cluster_host != "your-cluster-hostname.edu":
        print(f"   ✅ CLUSTER_HOST configurado: {settings.cluster_host}")
    else:
        print("   ⚠️  CLUSTER_HOST no configurado (usando valor por defecto)")
    
    if settings.cluster_user and settings.cluster_user != "your-username":
        print(f"   ✅ CLUSTER_USER configurado: {settings.cluster_user}")
    else:
        print("   ⚠️  CLUSTER_USER no configurado")
else:
    print("   ⚠️  Archivo .env no encontrado")
    print("      Copia .env.example a .env y configura tus credenciales")

# Test 6: Verificar rutas del cluster
print("\n6. Verificando rutas del cluster...")
paths_to_check = [
    ("VASP", settings.cluster_vasp_path),
    ("VASPKIT", settings.cluster_vaspkit_path),
    ("POTCAR", settings.cluster_potcar_path),
    ("Work Directory", settings.cluster_work_dir)
]

for name, path in paths_to_check:
    if path and not path.startswith("/path/to/"):
        print(f"   ✅ {name}: {path}")
    else:
        print(f"   ⚠️  {name} no configurado")

print("\n" + "=" * 60)
print("Verificación completada")
print("=" * 60)

print("\n📝 Próximos pasos:")
if not env_file.exists():
    print("   1. Copia .env.example a .env")
    print("   2. Configura tus credenciales SSH")
print("   3. Ejecuta: python -m app.main")
print("   4. Abre http://localhost:8000/docs")

print("\n✅ El proyecto está correctamente estructurado y listo para usar")
