# ==============================================================================
# Document Anonymizer - Unified PowerShell Launcher
# Запускает все сервисы в одном окне PowerShell с цветным выводом
# ==============================================================================

$Host.UI.RawUI.WindowTitle = "Document Anonymizer - All Services"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     DOCUMENT ANONYMIZER - STARTING ALL SERVICES" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Определяем корневую директорию проекта
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Путь к Python из виртуального окружения
$PythonExe = Join-Path $ProjectRoot "python\python-3.11.0-embed-amd64\python.exe"

# Создаем папку для логов
$LogsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -Path $LogsDir -ItemType Directory -Force | Out-Null
}

# Проверяем наличие Python в .venv
if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Portable Python not found!" -ForegroundColor Red
    Write-Host "Expected path: $PythonExe" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Found Portable Python: $PythonExe" -ForegroundColor Green

Write-Host ""
Write-Host "Starting backend services..." -ForegroundColor Yellow
Write-Host ""

# Массив для хранения процессов
$global:ServiceProcesses = @()

# Функция для запуска сервиса
function Start-BackendService {
    param(
        [string]$Name,
        [string]$Path,
        [int]$Port
    )
    
    $Count = $global:ServiceProcesses.Count + 1
    Write-Host "[$Count/5] Starting $Name (Port $Port)..." -ForegroundColor Cyan
    
    $ServicePath = Join-Path $ProjectRoot $Path
    $LogFile = Join-Path $LogsDir "$Name.log"
    $ErrFile = Join-Path $LogsDir "$Name.err.log"
    
    $Process = Start-Process -FilePath $PythonExe `
        -ArgumentList "-m","uvicorn","main:app","--host","0.0.0.0","--port",$Port `
        -WorkingDirectory $ServicePath `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $ErrFile `
        -NoNewWindow `
        -PassThru
    
    $global:ServiceProcesses += $Process
    Write-Host "  OK - $Name started (PID: $($Process.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Запускаем все сервисы
Start-BackendService -Name "RuleEngine" -Path "rule_engine\app" -Port 8003
Start-BackendService -Name "Orchestrator" -Path "orchestrator\app" -Port 8004
Start-BackendService -Name "UnifiedDocService" -Path "unified_document_service\app" -Port 8009
Start-BackendService -Name "NLPService" -Path "nlp_service\app" -Port 8006
Start-BackendService -Name "Gateway" -Path "gateway\app" -Port 8002

Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Проверяем статус сервисов
Write-Host ""
Write-Host "Checking services health..." -ForegroundColor Yellow

$HealthChecks = @(
    @{Name="Gateway"; Url="http://localhost:8002/health"}
    @{Name="Rule Engine"; Url="http://localhost:8003/healthz"}
    @{Name="Orchestrator"; Url="http://localhost:8004/healthz"}
    @{Name="NLP Service"; Url="http://localhost:8006/healthz"}
    @{Name="Unified Service"; Url="http://localhost:8009/health"}
)

foreach ($check in $HealthChecks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "  OK - $($check.Name) is responding" -ForegroundColor Green
    } catch {
        Write-Host "  WARN - $($check.Name) is not responding yet (this is OK, it may still be loading)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[6/6] Starting Frontend (Streamlit - Port 8501)..." -ForegroundColor Cyan
Write-Host "Opening browser..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     ALL SERVICES RUNNING - STREAMLIT UI STARTING" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:8501" -ForegroundColor White
Write-Host "Gateway:  http://localhost:8002/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Итоговая таблица статусов сервисов
Write-Host "Service status summary before starting Streamlit:" -ForegroundColor Magenta

# Массив имен сервисов по порядку
$ServiceNames = @("RuleEngine", "Orchestrator", "UnifiedDocService", "NLPService", "Gateway")
$allRunning = $true
for ($i = 0; $i -lt $global:ServiceProcesses.Count; $i++) {
    $proc = $global:ServiceProcesses[$i]
    $svcName = if ($i -lt $ServiceNames.Count) { $ServiceNames[$i] } else { "Unknown" }
    if ($proc -and -not $proc.HasExited) {
        Write-Host ("  [OK]  {0,-20} PID: {1}" -f $svcName, $proc.Id) -ForegroundColor Green
    } else {
        Write-Host ("  [FAIL] {0,-20} NOT RUNNING" -f $svcName) -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host "[ERROR] Not all backend services are running! Streamlit will NOT be started." -ForegroundColor Red
    Write-Host "Check logs in $LogsDir for details." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 2
}

# Запускаем Streamlit через wrapper-скрипт
$StreamlitBat = Join-Path $ProjectRoot "run_streamlit.bat"

# Устанавливаем критические переменные окружения для Python


if (Test-Path $StreamlitBat) {
    & cmd.exe /c $StreamlitBat
} else {
    Write-Host "[ERROR] Streamlit launcher not found: $StreamlitBat" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

# Cleanup при закрытии
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     SHUTTING DOWN ALL SERVICES" -ForegroundColor Red
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($process in $global:ServiceProcesses) {
    if (-not $process.HasExited) {
        Write-Host "Stopping process $($process.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "All services stopped" -ForegroundColor Green
Write-Host "Logs are available in: $LogsDir" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot
Read-Host "Press Enter to exit"
