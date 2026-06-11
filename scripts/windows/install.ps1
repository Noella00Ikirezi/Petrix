# PentestAI Installation Script for Windows
# Run as Administrator in PowerShell
# Usage: .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PentestAI Installation for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "[!] Warning: Not running as Administrator. Some features may not work." -ForegroundColor Yellow
}

# Check Python version
Write-Host "[*] Checking Python installation..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "[!] Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
            Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "    Found: $pythonVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "[!] Python not found. Please install Python 3.11+" -ForegroundColor Red
    Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check nmap installation
Write-Host "[*] Checking nmap installation..." -ForegroundColor Green
$nmapPaths = @(
    "C:\Program Files (x86)\Nmap\nmap.exe",
    "C:\Program Files\Nmap\nmap.exe",
    "C:\Nmap\nmap.exe"
)
$nmapFound = $false
foreach ($path in $nmapPaths) {
    if (Test-Path $path) {
        Write-Host "    Found: $path" -ForegroundColor Gray
        $nmapFound = $true
        break
    }
}
if (-not $nmapFound) {
    $nmapInPath = Get-Command nmap -ErrorAction SilentlyContinue
    if ($nmapInPath) {
        Write-Host "    Found in PATH: $($nmapInPath.Source)" -ForegroundColor Gray
        $nmapFound = $true
    }
}
if (-not $nmapFound) {
    Write-Host "[!] nmap not found. Please install nmap:" -ForegroundColor Red
    Write-Host "    Download from: https://nmap.org/download.html" -ForegroundColor Yellow
    Write-Host "    Install to default location (C:\Program Files (x86)\Nmap)" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "[*] Creating virtual environment..." -ForegroundColor Green
if (Test-Path "venv") {
    Write-Host "    Virtual environment already exists" -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "    Created: venv\" -ForegroundColor Gray
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "[*] Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "[*] Installing dependencies..." -ForegroundColor Green
pip install -e . --quiet
Write-Host "    Dependencies installed" -ForegroundColor Gray

# Create configuration file
Write-Host "[*] Creating configuration..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"

    # Generate secret key
    $secretKey = python -c "import secrets; print(secrets.token_hex(32))"
    (Get-Content ".env") -replace "CHANGE_ME_IN_PRODUCTION_USE_STRONG_KEY_HERE", $secretKey | Set-Content ".env"

    Write-Host "    Created .env with secure secret key" -ForegroundColor Gray
} else {
    Write-Host "    .env already exists" -ForegroundColor Gray
}

# Create directories
Write-Host "[*] Creating directories..." -ForegroundColor Green
$dirs = @("data", "logs", "reports")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "    Created: $dir\" -ForegroundColor Gray
    }
}

# Test installation
Write-Host "[*] Testing installation..." -ForegroundColor Green
try {
    python -c "from src.core import settings; from src.scanners.nmap_scanner import NmapScanner; print('OK')" 2>&1 | Out-Null
    Write-Host "    All modules loaded successfully" -ForegroundColor Gray
} catch {
    Write-Host "[!] Module import failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor White
Write-Host "  1. Activate environment:  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. Run CLI demo:          python -m src.cli.main demo" -ForegroundColor Gray
Write-Host "  3. Scan a target:         python -m src.cli.main scan 192.168.1.1" -ForegroundColor Gray
Write-Host "  4. Start web interface:   uvicorn src.web.app:app --host 127.0.0.1 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "First time setup:" -ForegroundColor White
Write-Host "  1. Start web server" -ForegroundColor Gray
Write-Host "  2. Go to http://localhost:8000/api/setup" -ForegroundColor Gray
Write-Host "  3. Save the generated admin password" -ForegroundColor Gray
Write-Host ""
