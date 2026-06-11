# Petrix Agent — Installeur Windows (PowerShell)
# Lancer: powershell -ExecutionPolicy Bypass -File install-windows.ps1 -Server URL -Token TOKEN

param(
    [Parameter(Mandatory=$true)]  [string]$Server,
    [Parameter(Mandatory=$true)]  [string]$Token
)

Write-Host ""
Write-Host "╔══════════════════════════════════════╗"
Write-Host "║  Petrix Agent — Installeur Windows   ║"
Write-Host "╚══════════════════════════════════════╝"
Write-Host ""

# Python via winget
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[*] Installation de Python..."
    winget install --id Python.Python.3.11 -e --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Vérifier Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Python non trouvé. Installez Python 3.9+ depuis https://python.org"
    exit 1
}

# nmap
if (-not (Get-Command nmap -ErrorAction SilentlyContinue)) {
    Write-Host "[*] Installation de nmap..."
    winget install --id Insecure.Nmap -e --silent 2>$null
}

# petrix-agent
Write-Host "[*] Installation de petrix-agent..."
python -m pip install --upgrade "git+https://gitlab.com/petrix1/petrix.git#subdirectory=agent" --quiet

# Config
$ConfigDir = "$env:USERPROFILE\.petrix-agent"
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

@"
PETRIX_SERVER=$Server
PETRIX_TOKEN=$Token
"@ | Set-Content "$ConfigDir\config.env"

# Raccourci de lancement
@"
@echo off
petrix-agent --server $Server --token $Token %*
"@ | Set-Content "$ConfigDir\run.bat"

Write-Host "[✓] Petrix Agent installé."
Write-Host "  Lancer: $ConfigDir\run.bat"
Write-Host ""

$confirm = Read-Host "Lancer un scan maintenant ? [O/n]"
if ($confirm -ne "n" -and $confirm -ne "N") {
    petrix-agent --server $Server --token $Token
}
