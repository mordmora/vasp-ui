# Ejemplos de Uso de la API - VASP GUI

Colección de ejemplos para probar la API del backend.

## 🔧 Usando Swagger UI (Recomendado)

La forma más fácil es usar la interfaz interactiva:

```
http://localhost:8000/docs
```

## 📡 Usando cURL / PowerShell

### 1. Health Check

```powershell
# cURL
curl http://localhost:8000/health

# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "cluster": {
    "host": "your-cluster.edu",
    "connected": false
  }
}
```

---

### 2. Crear un Proyecto

```powershell
# PowerShell
$body = @{
    name = "Silicon DOS Test"
    description = "Cálculo de densidad de estados para Si"
    calculation_type = "dos"
    poscar = @"
Si
1.0
5.43 0.0 0.0
0.0 5.43 0.0
0.0 0.0 5.43
Si
8
Direct
0.0 0.0 0.0
0.25 0.25 0.25
0.0 0.5 0.5
0.25 0.75 0.75
0.5 0.0 0.5
0.75 0.25 0.75
0.5 0.5 0.0
0.75 0.75 0.25
"@
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/projects/" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "name": "Silicon DOS Test",
  "description": "Cálculo de densidad de estados para Si",
  "calculation_type": "dos",
  "status": "draft",
  "poscar": "Si\n1.0\n...",
  "created_at": "2025-11-07T12:00:00",
  ...
}
```

---

### 3. Listar Todos los Proyectos

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/projects/" -Method Get

# Con parámetros de paginación
Invoke-RestMethod -Uri "http://localhost:8000/api/projects/?skip=0&limit=10" -Method Get
```

---

### 4. Ver un Proyecto Específico

```powershell
# PowerShell (reemplaza {id} con el ID real)
Invoke-RestMethod -Uri "http://localhost:8000/api/projects/1" -Method Get
```

---

### 5. Actualizar un Proyecto

```powershell
# PowerShell
$updateBody = @{
    description = "Descripción actualizada"
    poscar = "Nuevo POSCAR..."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/projects/1" `
    -Method Patch `
    -ContentType "application/json" `
    -Body $updateBody
```

---

### 6. Generar Archivos DOS con VASPKIT

```powershell
# PowerShell
$generateBody = @{
    project_id = 1
    encut = 400
    kpoints_density = 0.04
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/dos/generate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $generateBody
```

**Esto hará:**
1. Conectar SSH al cluster
2. Crear directorio remoto
3. Subir POSCAR
4. Ejecutar VASPKIT para generar INCAR y KPOINTS
5. Generar POTCAR automáticamente
6. Actualizar el proyecto con los archivos generados

**Respuesta esperada:**
```json
{
  "id": 1,
  "status": "ready",
  "incar": "SYSTEM = Si\nENCUT = 400\n...",
  "kpoints": "Automatic mesh\n0\nGamma\n8 8 8\n...",
  "potcar_info": "Si",
  "remote_path": "/home/user/vasp_calculations/project_1",
  ...
}
```

---

### 7. Enviar Trabajo al Cluster

```powershell
# PowerShell
$submitBody = @{
    project_id = 1
    ncores = 8
    walltime = "24:00:00"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/dos/submit" `
    -Method Post `
    -ContentType "application/json" `
    -Body $submitBody
```

**Respuesta esperada:**
```json
{
  "project_id": 1,
  "job_id": "12345",
  "status": "running",
  "current_step": "Job submitted to queue"
}
```

---

### 8. Verificar Estado del Trabajo

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/dos/status/1" -Method Get
```

**Posibles respuestas:**

Mientras corre:
```json
{
  "project_id": 1,
  "job_id": "12345",
  "status": "running",
  "current_step": "Running on cluster"
}
```

Completado:
```json
{
  "project_id": 1,
  "job_id": "12345",
  "status": "completed",
  "current_step": "Completed successfully"
}
```

---

### 9. Obtener Resultados

```powershell
# PowerShell (solo cuando status = "completed")
Invoke-RestMethod -Uri "http://localhost:8000/api/dos/results/1" -Method Get
```

**Respuesta esperada:**
```json
{
  "project_id": 1,
  "doscar": "# DOSCAR content...",
  "outcar_excerpt": "... últimas líneas del OUTCAR ..."
}
```

---

### 10. Eliminar un Proyecto

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/projects/1" -Method Delete
```

---

## 🐍 Usando Python (Requests)

Si prefieres usar Python para testing:

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Crear proyecto
response = requests.post(
    f"{BASE_URL}/api/projects/",
    json={
        "name": "Test Project",
        "calculation_type": "dos",
        "description": "Test",
        "poscar": "Si\n1.0\n..."
    }
)
project = response.json()
project_id = project["id"]
print(f"Proyecto creado: {project_id}")

# 2. Generar archivos
response = requests.post(
    f"{BASE_URL}/api/dos/generate",
    json={
        "project_id": project_id,
        "encut": 400,
        "kpoints_density": 0.04
    }
)
print("Archivos generados")

# 3. Ver proyecto actualizado
response = requests.get(f"{BASE_URL}/api/projects/{project_id}")
project = response.json()
print(f"INCAR generado: {project['incar'][:100]}...")

# 4. Enviar al cluster
response = requests.post(
    f"{BASE_URL}/api/dos/submit",
    json={
        "project_id": project_id,
        "ncores": 8,
        "walltime": "24:00:00"
    }
)
job = response.json()
print(f"Job ID: {job['job_id']}")

# 5. Monitorear estado
import time
while True:
    response = requests.get(f"{BASE_URL}/api/dos/status/{project_id}")
    status = response.json()
    print(f"Estado: {status['status']}")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(30)  # Esperar 30 segundos

# 6. Obtener resultados
if status['status'] == 'completed':
    response = requests.get(f"{BASE_URL}/api/dos/results/{project_id}")
    results = response.json()
    print("Resultados obtenidos!")
```

---

## 🧪 Script de Test Completo

Guarda este script como `test_api.py`:

```python
#!/usr/bin/env python3
"""
Script de prueba completa del flujo DOS
Uso: python test_api.py
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test 1: Health check"""
    print("Test 1: Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health: {response.json()}")
    return response.status_code == 200

def test_create_project():
    """Test 2: Crear proyecto"""
    print("\nTest 2: Crear Proyecto...")
    
    poscar = """Si
1.0
5.43 0.0 0.0
0.0 5.43 0.0
0.0 0.0 5.43
Si
8
Direct
0.0 0.0 0.0
0.25 0.25 0.25
0.0 0.5 0.5
0.25 0.75 0.75
0.5 0.0 0.5
0.75 0.25 0.75
0.5 0.5 0.0
0.75 0.75 0.25
"""
    
    response = requests.post(
        f"{BASE_URL}/api/projects/",
        json={
            "name": "Test Silicon DOS",
            "description": "Proyecto de prueba",
            "calculation_type": "dos",
            "poscar": poscar
        }
    )
    
    if response.status_code == 201:
        project = response.json()
        print(f"✅ Proyecto creado: ID={project['id']}, Status={project['status']}")
        return project['id']
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_list_projects():
    """Test 3: Listar proyectos"""
    print("\nTest 3: Listar Proyectos...")
    response = requests.get(f"{BASE_URL}/api/projects/")
    
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Proyectos encontrados: {len(projects)}")
        for p in projects:
            print(f"   - {p['id']}: {p['name']} ({p['status']})")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("VASP GUI - Test de API")
    print("=" * 60)
    
    # Test 1: Health
    if not test_health():
        print("\n❌ El servidor no está respondiendo")
        print("Asegúrate de que el backend esté corriendo:")
        print("  cd backend && python -m app.main")
        sys.exit(1)
    
    # Test 2: Crear proyecto
    project_id = test_create_project()
    if not project_id:
        print("\n❌ No se pudo crear el proyecto")
        sys.exit(1)
    
    # Test 3: Listar proyectos
    test_list_projects()
    
    print("\n" + "=" * 60)
    print("✅ Tests básicos completados exitosamente")
    print("=" * 60)
    
    print(f"\n📝 Proyecto de prueba creado con ID: {project_id}")
    print("Puedes continuar probando manualmente en:")
    print(f"  http://localhost:8000/docs")

if __name__ == "__main__":
    main()
```

---

## 📚 Más Información

- Documentación completa de la API: http://localhost:8000/docs
- Documentación alternativa (ReDoc): http://localhost:8000/redoc
- Ver README.md para guía completa
- Ver ARCHITECTURE.md para detalles técnicos
