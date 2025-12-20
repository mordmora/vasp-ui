# VASP GUI - Interfaz Gráfica para VASP

Interfaz web para realizar cálculos VASP en un cluster remoto vía SSH, con integración de VASPKIT para generación automática de archivos de entrada.

## 🎯 MVP - Cálculos de Densidad de Estados (DOS)

El MVP permite realizar cálculos de DOS con el siguiente flujo:

1. **Crear Proyecto** → Definir nombre y tipo de cálculo
2. **Cargar POSCAR** → Estructura cristalina
3. **Generar Archivos** → VASPKIT crea INCAR, KPOINTS, POTCAR automáticamente
4. **Modificar (opcional)** → Editar parámetros
5. **Ejecutar** → Enviar al cluster
6. **Monitorear** → Ver progreso en tiempo real
7. **Visualizar** → Ver resultados DOS

## 🏗️ Arquitectura

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  React Frontend │ ◄─────► │  FastAPI Backend │ ◄─────► │  Cluster/GPU    │
│  (Navegador)    │   HTTP  │   (Servidor)     │   SSH   │  (Universidad)  │
│                 │  WebSkt │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
     Puerto 3000              Puerto 8000                  SSH Port 22
```

### Backend (FastAPI)
- **API RESTful** para operaciones CRUD de proyectos
- **SSH Manager** para conexión y ejecución remota
- **VASPKIT Service** para generación automática de archivos
- **SQLite** para persistencia local
- **WebSockets** para monitoreo en tiempo real

### Frontend (React - Por implementar)
- Editor de archivos VASP
- Visualización de estructuras 3D
- Monitor de trabajos
- Gráficas de resultados

## 📁 Estructura del Proyecto

```
vasp_gui/
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── main.py            # Punto de entrada FastAPI
│   │   ├── config.py          # Configuración
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── projects.py   # CRUD de proyectos
│   │   │       └── dos.py        # Endpoints específicos DOS
│   │   ├── core/
│   │   │   └── ssh_manager.py    # Gestión SSH/SFTP
│   │   ├── models/
│   │   │   ├── project.py        # Modelos SQLAlchemy
│   │   │   └── database.py       # Configuración BD
│   │   ├── schemas/
│   │   │   └── project.py        # Schemas Pydantic
│   │   └── services/
│   │       └── vaspkit_service.py # Interacción VASPKIT
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/                   # React App (Por crear)
```

## 🚀 Instalación y Configuración

### Prerequisitos

- Python 3.10+
- Acceso SSH al cluster
- VASP y VASPKIT instalados en el cluster

### 1. Configurar Backend

```powershell
# Navegar al directorio backend
cd backend

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env`:

```env
# Configuración del Cluster SSH
CLUSTER_HOST=tu-cluster.universidad.edu
CLUSTER_PORT=22
CLUSTER_USER=tu-usuario
CLUSTER_PASSWORD=tu-password
# O usar llave SSH (recomendado):
CLUSTER_SSH_KEY_PATH=C:/Users/TuUsuario/.ssh/id_rsa

# Rutas en el cluster
CLUSTER_VASP_PATH=/opt/vasp/bin/vasp_std
CLUSTER_VASPKIT_PATH=/opt/vaspkit/bin/vaspkit
CLUSTER_POTCAR_PATH=/opt/vasp/potcar
CLUSTER_WORK_DIR=/home/tu-usuario/vasp_calculations

# Base de datos local
DATABASE_URL=sqlite+aiosqlite:///./vasp_gui.db

# Configuración de la aplicación
SECRET_KEY=cambia-esto-en-produccion
CORS_ORIGINS=["http://localhost:3000"]
```

### 3. Ejecutar el Backend

```powershell
# Desde el directorio backend/
python -m app.main

# O con uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## 📡 API Endpoints

### Proyectos

- **POST** `/api/projects/` - Crear nuevo proyecto
- **GET** `/api/projects/` - Listar todos los proyectos
- **GET** `/api/projects/{id}` - Obtener proyecto específico
- **PATCH** `/api/projects/{id}` - Actualizar proyecto
- **DELETE** `/api/projects/{id}` - Eliminar proyecto

### Workflow DOS

- **POST** `/api/dos/generate` - Generar archivos VASP con VASPKIT
- **POST** `/api/dos/submit` - Enviar trabajo al cluster
- **GET** `/api/dos/status/{project_id}` - Ver estado del trabajo
- **GET** `/api/dos/results/{project_id}` - Obtener resultados

## 🔄 Flujo de Trabajo Ejemplo

### 1. Crear un proyecto

```bash
POST http://localhost:8000/api/projects/
Content-Type: application/json

{
  "name": "Silicon DOS",
  "description": "Cálculo de densidad de estados para Si",
  "calculation_type": "dos",
  "poscar": "Si\n1.0\n5.43 0.0 0.0\n0.0 5.43 0.0\n0.0 0.0 5.43\nSi\n8\nDirect\n0.0 0.0 0.0\n..."
}
```

Respuesta:
```json
{
  "id": 1,
  "name": "Silicon DOS",
  "status": "draft",
  "calculation_type": "dos",
  ...
}
```

### 2. Generar archivos con VASPKIT

```bash
POST http://localhost:8000/api/dos/generate
Content-Type: application/json

{
  "project_id": 1,
  "encut": 400,
  "kpoints_density": 0.04
}
```

Esto:
- Crea directorio en el cluster
- Sube POSCAR
- Ejecuta VASPKIT para generar INCAR y KPOINTS
- Genera POTCAR automáticamente
- Actualiza el proyecto con los archivos

### 3. Enviar trabajo al cluster

```bash
POST http://localhost:8000/api/dos/submit
Content-Type: application/json

{
  "project_id": 1,
  "ncores": 8,
  "walltime": "24:00:00"
}
```

Respuesta:
```json
{
  "project_id": 1,
  "job_id": "12345",
  "status": "running",
  "current_step": "Job submitted to queue"
}
```

### 4. Monitorear progreso

```bash
GET http://localhost:8000/api/dos/status/1
```

### 5. Obtener resultados

```bash
GET http://localhost:8000/api/dos/results/1
```

## 🔧 Configuración del Cluster

Asegúrate de que en el cluster:

1. **VASP está instalado** y accesible
2. **VASPKIT está instalado** (https://vaspkit.com)
3. **POTCARs están disponibles** en una ruta accesible
4. **Sistema de colas configurado** (SLURM, PBS, etc.)

### Ejemplo de estructura en el cluster:

```
/home/tu-usuario/
├── vasp_calculations/          # CLUSTER_WORK_DIR
│   └── project_1/
│       ├── POSCAR
│       ├── INCAR
│       ├── KPOINTS
│       ├── POTCAR
│       ├── job.sh
│       └── OUTCAR (después de ejecutar)
```

## 🐛 Troubleshooting

### Error de conexión SSH

- Verifica credenciales en `.env`
- Prueba conexión manual: `ssh usuario@cluster.edu`
- Si usas llave SSH, verifica permisos

### Error "pwsh.exe no se reconoce"

Este error es del sistema de colas al compilar spglib. No afecta el funcionamiento de la GUI.

### Archivos no generados

- Verifica que VASPKIT esté en la ruta correcta
- Revisa permisos de escritura en `CLUSTER_WORK_DIR`
- Checa logs: `tail -f vasp_*.out`

## 📝 TODO - Próximas Features

- [ ] Frontend React
- [ ] WebSockets para monitoreo en tiempo real
- [ ] Visualización de estructuras 3D
- [ ] Gráficas interactivas de DOS
- [ ] Soporte para Band Structure
- [ ] Autenticación de usuarios
- [ ] Descarga de resultados
- [ ] Templates de INCAR predefinidos
- [ ] Integración con Materials Project

## 📚 Documentación Adicional

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [VASP Manual](https://www.vasp.at/wiki/)
- [VASPKIT](https://vaspkit.com/tutorials.html)
- [Pymatgen](https://pymatgen.org/)

## 📄 Licencia

MIT License

---

**Desarrollado para facilitar cálculos VASP con acceso remoto a clusters universitarios.**
