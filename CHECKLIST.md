# ✅ Checklist de Verificación - VASP GUI

Usa este checklist antes de ejecutar por primera vez.

## 📋 Pre-requisitos

### Sistema Local (Windows)
- [ ] Python 3.10 o superior instalado
- [ ] Git instalado (opcional)
- [ ] Editor de código (VS Code recomendado)
- [ ] Acceso a internet para instalar dependencias

### Cluster Remoto
- [ ] Tienes acceso SSH al cluster
- [ ] Conoces el hostname del cluster
- [ ] Tienes usuario y contraseña (o SSH key)
- [ ] VASP está instalado en el cluster
- [ ] VASPKIT está instalado en el cluster
- [ ] Tienes acceso a archivos POTCAR
- [ ] Sistema de colas funciona (SLURM/PBS/etc)

---

## 🔧 Instalación del Backend

### 1. Navegación al Proyecto
```powershell
cd c:\Users\MordMora\Documents\Programación\vasp_gui
```
- [ ] Estás en el directorio correcto

### 2. Instalación Automática
```powershell
.\setup.ps1
```
- [ ] Script ejecutado sin errores
- [ ] Entorno virtual creado en `backend/venv/`
- [ ] Dependencias instaladas
- [ ] Archivo `.env` creado

### 3. Verificación de Instalación
```powershell
cd backend
python verify_setup.py
```
- [ ] Todas las dependencias importadas correctamente
- [ ] Módulos del proyecto cargados sin errores
- [ ] FastAPI app creada exitosamente

---

## 🔐 Configuración de Credenciales

### Editar `backend/.env`

#### Información SSH del Cluster
```env
CLUSTER_HOST=_________________
CLUSTER_PORT=22
CLUSTER_USER=_________________
```
- [ ] `CLUSTER_HOST` configurado (ej: `cluster.universidad.edu`)
- [ ] `CLUSTER_USER` configurado (tu usuario SSH)

#### Autenticación (elige una)

**Opción A: SSH Key (Recomendado)**
```env
CLUSTER_SSH_KEY_PATH=C:/Users/TuUsuario/.ssh/id_rsa
```
- [ ] Ruta a tu clave privada SSH configurada
- [ ] Archivo de clave existe y tiene permisos correctos

**Opción B: Password**
```env
CLUSTER_PASSWORD=tu-password
```
- [ ] Password configurado (menos seguro)

#### Rutas en el Cluster
```env
CLUSTER_VASP_PATH=/opt/vasp/bin/vasp_std
CLUSTER_VASPKIT_PATH=/opt/vaspkit/bin/vaspkit
CLUSTER_POTCAR_PATH=/opt/vasp/potcar
CLUSTER_WORK_DIR=/home/tu-usuario/vasp_calculations
```
- [ ] `CLUSTER_VASP_PATH` apunta al ejecutable de VASP
- [ ] `CLUSTER_VASPKIT_PATH` apunta al ejecutable de VASPKIT
- [ ] `CLUSTER_POTCAR_PATH` apunta al directorio de POTCARs
- [ ] `CLUSTER_WORK_DIR` es un directorio donde tienes permisos de escritura

---

## 🔍 Verificación SSH Manual

### Test de Conexión SSH
```powershell
ssh tu-usuario@cluster.universidad.edu
```
- [ ] Conexión SSH funciona
- [ ] Puedes autenticarte correctamente
- [ ] No hay mensajes de error

### Verificar VASP en el Cluster
```bash
which vasp_std
# O la ruta completa:
ls -la /opt/vasp/bin/vasp_std
```
- [ ] VASP está instalado y accesible

### Verificar VASPKIT en el Cluster
```bash
which vaspkit
# O:
/opt/vaspkit/bin/vaspkit --version
```
- [ ] VASPKIT está instalado y accesible

### Verificar POTCARs
```bash
ls /opt/vasp/potcar/
```
- [ ] Directorio de POTCARs existe
- [ ] Contiene subdirectorios de elementos (Si, O, etc.)

### Verificar Directorio de Trabajo
```bash
mkdir -p /home/tu-usuario/vasp_calculations
cd /home/tu-usuario/vasp_calculations
touch test.txt
rm test.txt
```
- [ ] Puedes crear directorios
- [ ] Puedes escribir archivos
- [ ] Tienes permisos adecuados

### Verificar Sistema de Colas
```bash
# SLURM
squeue
sbatch --version

# PBS
qstat
qsub --version
```
- [ ] Sistema de colas está activo
- [ ] Puedes ejecutar comandos básicos

---

## 🚀 Ejecutar el Backend

### Iniciar el Servidor
```powershell
cd c:\Users\MordMora\Documents\Programación\vasp_gui\backend
python -m app.main
```
- [ ] Servidor inicia sin errores
- [ ] Ves mensaje: "Application startup complete"
- [ ] Ves URL: "http://0.0.0.0:8000"

### Verificar en el Navegador
```
http://localhost:8000
```
- [ ] Navegador muestra respuesta JSON
- [ ] Mensaje: "VASP GUI API"

### Verificar Swagger UI
```
http://localhost:8000/docs
```
- [ ] Documentación interactiva se carga
- [ ] Ves todos los endpoints listados
- [ ] Puedes expandir las secciones

---

## 🧪 Test Básico de la API

### Test 1: Health Check
En Swagger UI o con PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```
- [ ] Respuesta: `{"status": "healthy", ...}`
- [ ] Sin errores

### Test 2: Crear Proyecto
En Swagger UI:
1. Expandir `POST /api/projects/`
2. Click "Try it out"
3. Usar este JSON:
```json
{
  "name": "Test Project",
  "description": "Proyecto de prueba",
  "calculation_type": "dos"
}
```
4. Click "Execute"

- [ ] Código de respuesta: 201
- [ ] Proyecto creado con ID
- [ ] Status: "draft"

### Test 3: Listar Proyectos
En Swagger UI:
1. Expandir `GET /api/projects/`
2. Click "Try it out"
3. Click "Execute"

- [ ] Código de respuesta: 200
- [ ] Lista contiene el proyecto creado

---

## 🔗 Test de Conexión SSH (Avanzado)

### Test desde Python
Crea un archivo `test_ssh.py`:
```python
from app.core.ssh_manager import SSHManager

ssh = SSHManager()
try:
    ssh.connect()
    print("✅ Conexión SSH exitosa")
    
    stdout, stderr, code = ssh.execute_command("pwd")
    print(f"Directorio actual: {stdout.strip()}")
    
    stdout, stderr, code = ssh.execute_command("ls -la")
    print(f"Archivos: {stdout[:200]}")
    
    ssh.disconnect()
    print("✅ Desconexión exitosa")
except Exception as e:
    print(f"❌ Error: {e}")
```

Ejecutar:
```powershell
cd backend
python test_ssh.py
```

- [ ] Conexión SSH funciona desde Python
- [ ] Comandos se ejecutan correctamente
- [ ] No hay errores de autenticación

---

## 🎯 Test Completo del Flujo DOS

### Requisito: POSCAR de Prueba
Usa este POSCAR simple para Silicon:
```
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
```

### Paso 1: Crear Proyecto con POSCAR
- [ ] Proyecto creado exitosamente
- [ ] POSCAR guardado en el proyecto

### Paso 2: Generar Archivos (CRÍTICO)
```json
POST /api/dos/generate
{
  "project_id": 1,
  "encut": 400,
  "kpoints_density": 0.04
}
```
- [ ] Conexión SSH establecida
- [ ] Directorio remoto creado
- [ ] POSCAR subido al cluster
- [ ] VASPKIT ejecutado (INCAR generado)
- [ ] VASPKIT ejecutado (KPOINTS generado)
- [ ] POTCAR generado
- [ ] Proyecto actualizado con archivos
- [ ] Status cambió a "ready"

### Paso 3: Verificar Archivos Generados
```json
GET /api/projects/1
```
- [ ] Campo `incar` contiene texto
- [ ] Campo `kpoints` contiene texto
- [ ] Campo `potcar_info` contiene elementos
- [ ] Campo `remote_path` tiene valor

### Paso 4: Enviar al Cluster
```json
POST /api/dos/submit
{
  "project_id": 1,
  "ncores": 4,
  "walltime": "24:00:00"
}
```
- [ ] Archivos validados
- [ ] Script de trabajo creado
- [ ] Comando `sbatch` ejecutado
- [ ] `job_id` recibido
- [ ] Status cambió a "running"

### Paso 5: Monitorear Estado
```json
GET /api/dos/status/1
```
- [ ] Estado se actualiza correctamente
- [ ] Detecta cuando el trabajo completa

---

## 🐛 Troubleshooting

### Problema: Dependencias no se instalan
**Solución:**
```powershell
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Problema: Error "No module named 'app'"
**Solución:**
Asegúrate de estar en el directorio correcto:
```powershell
cd c:\Users\MordMora\Documents\Programación\vasp_gui\backend
python -m app.main
```

### Problema: Error de conexión SSH
**Solución:**
1. Verifica credenciales en `.env`
2. Prueba SSH manual: `ssh user@cluster`
3. Revisa firewall/VPN si es necesario

### Problema: VASPKIT no ejecuta
**Solución:**
1. Verifica ruta en `.env`
2. Ejecuta manualmente en cluster:
   ```bash
   /path/to/vaspkit --version
   ```
3. Revisa permisos de ejecución

### Problema: Base de datos bloqueada
**Solución:**
```powershell
cd backend
rm vasp_gui.db
python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"
```

---

## ✅ Checklist Final

### Antes de Producción
- [ ] `.env` configurado correctamente
- [ ] Conexión SSH probada
- [ ] VASPKIT funciona en cluster
- [ ] Flujo completo probado (crear → generar → enviar)
- [ ] Documentación leída

### Seguridad
- [ ] Usando SSH key en lugar de password
- [ ] `.env` NO está en control de versiones
- [ ] Permisos de archivos correctos

### Siguientes Pasos
- [ ] Frontend React (opcional)
- [ ] WebSockets para monitoreo en tiempo real
- [ ] Visualización de resultados
- [ ] Descarga de archivos

---

## 📞 Soporte

Si algo no funciona:
1. Revisa los logs del servidor
2. Verifica el archivo `.env`
3. Prueba conexión SSH manualmente
4. Consulta `README.md` y `ARCHITECTURE.md`
5. Revisa `API_EXAMPLES.md` para ejemplos

---

**¡Cuando todos los checks estén marcados, estarás listo para producción! 🚀**
