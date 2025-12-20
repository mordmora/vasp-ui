# Script de inicialización rápida del backend
# Ejecutar: .\setup.ps1

Write-Host "=== VASP GUI - Setup Script ===" -ForegroundColor Cyan

# Verificar Python
Write-Host "`nVerificando Python..." -ForegroundColor Yellow
python --version

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

# Navegar a backend
Set-Location backend

# Crear entorno virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "`nCreando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
Write-Host "`nActivando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Instalar dependencias
Write-Host "`nInstalando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Crear .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "`nCreando archivo .env desde template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "¡IMPORTANTE! Edita el archivo .env con tus credenciales del cluster" -ForegroundColor Red
}

# Inicializar base de datos
Write-Host "`nInicializando base de datos..." -ForegroundColor Yellow
python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"

Write-Host "`n=== Setup completado ===" -ForegroundColor Green
Write-Host "`nPróximos pasos:" -ForegroundColor Cyan
Write-Host "1. Edita backend/.env con tus credenciales SSH"
Write-Host "2. Ejecuta: python -m app.main"
Write-Host "3. Abre http://localhost:8000/docs en tu navegador"
