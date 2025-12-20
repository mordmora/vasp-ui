# Guía de Inicio Rápido - VASP GUI

## 🚀 Setup Rápido (5 minutos)

### 1. Clonar/Descargar el Proyecto

Ya tienes el proyecto en:
```
c:\Users\MordMora\Documents\Programación\vasp_gui
```

### 2. Ejecutar Script de Setup

```powershell
cd c:\Users\MordMora\Documents\Programación\vasp_gui
.\setup.ps1
```

Este script:
- ✅ Crea un entorno virtual Python
- ✅ Instala todas las dependencias
- ✅ Crea el archivo `.env` desde el template
- ✅ Inicializa la base de datos SQLite

### 3. Configurar Credenciales SSH

Edita el archivo `backend/.env`:

```env
CLUSTER_HOST=tu-cluster.universidad.edu
CLUSTER_USER=tu-usuario
CLUSTER_SSH_KEY_PATH=C:/Users/TuUsuario/.ssh/id_rsa

CLUSTER_VASP_PATH=/ruta/a/vasp
CLUSTER_VASPKIT_PATH=/ruta/a/vaspkit
CLUSTER_POTCAR_PATH=/ruta/a/potcars
CLUSTER_WORK_DIR=/home/tu-usuario/vasp_calculations
```

### 4. Ejecutar el Backend

```powershell
cd backend
python -m app.main
```

### 5. Probar la API

Abre en tu navegador:
```
http://localhost:8000/docs
```

Verás la documentación interactiva de Swagger UI.

## 📝 Ejemplo de Uso

### 1. Crear un Proyecto

En Swagger UI o usando `curl`:

```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Silicon DOS Test",
    "description": "Prueba de DOS para Si",
    "calculation_type": "dos",
    "poscar": "Si\n1.0\n5.43 0.0 0.0\n0.0 5.43 0.0\n0.0 0.0 5.43\nSi\n8\nDirect\n0.0 0.0 0.0\n0.25 0.25 0.25\n0.0 0.5 0.5\n0.25 0.75 0.75\n0.5 0.0 0.5\n0.75 0.25 0.75\n0.5 0.5 0.0\n0.75 0.75 0.25"
  }'
```

Respuesta:
```json
{
  "id": 1,
  "name": "Silicon DOS Test",
  "status": "draft",
  ...
}
```

### 2. Generar Archivos VASP

```bash
curl -X POST "http://localhost:8000/api/dos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "encut": 400,
    "kpoints_density": 0.04
  }'
```

Esto conecta al cluster y:
- Crea el directorio de trabajo
- Sube el POSCAR
- Ejecuta VASPKIT para generar INCAR y KPOINTS
- Genera POTCAR automáticamente

### 3. Revisar Archivos Generados

```bash
curl "http://localhost:8000/api/projects/1"
```

Verás el proyecto actualizado con `incar`, `kpoints`, etc.

### 4. Enviar al Cluster

```bash
curl -X POST "http://localhost:8000/api/dos/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "ncores": 8,
    "walltime": "24:00:00"
  }'
```

### 5. Monitorear Estado

```bash
curl "http://localhost:8000/api/dos/status/1"
```

### 6. Obtener Resultados

Cuando el estado sea `completed`:

```bash
curl "http://localhost:8000/api/dos/results/1"
```

## 🔧 Troubleshooting

### Error: "No module named 'app'"

Asegúrate de estar en el directorio `backend/` y que el entorno virtual esté activado:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.main
```

### Error de conexión SSH

Verifica:
1. Credenciales correctas en `.env`
2. Acceso SSH manual funciona: `ssh usuario@cluster.edu`
3. Rutas correctas en el cluster

### Base de datos bloqueada

```powershell
# Eliminar y recrear
rm vasp_gui.db
python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 📚 Próximos Pasos

1. **Familiarízate con la API** usando Swagger UI
2. **Prueba el flujo completo** con un cálculo real
3. **Explora el código** en `backend/app/`
4. **Comienza el Frontend** (React)

## 🆘 Soporte

- Ver documentación completa: `README.md`
- Arquitectura detallada: `docs/ARCHITECTURE.md`
- Reportar issues: Crea un issue en el repositorio

---

**¡Listo para empezar a calcular DOS! 🚀**
