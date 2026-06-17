#Requires -RunAsAdministrator
# Petrix Agent — Installeur Windows (PowerShell)
# Valeurs pré-configurées au téléchargement depuis Petrix :
$PETRIX_SERVER = ""
$PETRIX_TOKEN = ""

# Surcharge possible via paramètres
param(
    [string]$Server = $PETRIX_SERVER,
    [string]$Token  = $PETRIX_TOKEN
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================"
Write-Host "  Petrix Agent — Installeur Windows"
Write-Host "============================================"
Write-Host ""

if (-not $Server -or -not $Token) {
    Write-Host "[!] Serveur ou token manquant." -ForegroundColor Red
    Write-Host "    Ce script doit etre telecharge depuis Petrix (bouton Telecharger)."
    Write-Host "    Il est pre-configure avec votre serveur et token."
    exit 1
}

Write-Host "[*] Serveur : $Server"
Write-Host "[*] Token   : $($Token.Substring(0, [Math]::Min(20, $Token.Length)))..."
Write-Host ""

# ──────────────────────────────────────────
# 1. Python
# ──────────────────────────────────────────
Write-Host "[1/4] Verification de Python..."

$python = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        $v = & $cmd --version 2>&1
        if ($v -match "Python 3\.") { $python = $cmd; break }
    } catch {}
}

if (-not $python) {
    Write-Host "  Python non trouve — installation via winget..."
    try {
        winget install --id Python.Python.3.11 -e --silent --accept-source-agreements --accept-package-agreements
    } catch {
        Write-Host "[!] winget a echoue. Installez Python 3.9+ depuis https://python.org" -ForegroundColor Red
        exit 1
    }
    # Rafraichir PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 3
    foreach ($cmd in @("python", "py", "python3")) {
        try {
            $v = & $cmd --version 2>&1
            if ($v -match "Python 3\.") { $python = $cmd; break }
        } catch {}
    }
    if (-not $python) {
        Write-Host "[!] Python introuvable apres installation. Redemarrez PowerShell et relancez." -ForegroundColor Red
        exit 1
    }
}

$pyVer = & $python --version 2>&1
Write-Host "  OK — $pyVer"

# ──────────────────────────────────────────
# 2. nmap
# ──────────────────────────────────────────
Write-Host "[2/4] Verification de nmap..."

$hasNmap = $null -ne (Get-Command nmap -ErrorAction SilentlyContinue)
if (-not $hasNmap) {
    Write-Host "  nmap non trouve — installation via winget..."
    try {
        winget install --id Insecure.Nmap -e --silent --accept-source-agreements --accept-package-agreements 2>$null
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path","User")
        $hasNmap = $null -ne (Get-Command nmap -ErrorAction SilentlyContinue)
    } catch {}
    if (-not $hasNmap) {
        Write-Host "  [avertissement] nmap non installe — le scan de ports sera limite." -ForegroundColor Yellow
    } else {
        Write-Host "  OK — nmap installe"
    }
} else {
    Write-Host "  OK — nmap disponible"
}

# ──────────────────────────────────────────
# 3. Git (requis pour l'installation depuis GitLab)
# ──────────────────────────────────────────
Write-Host "[3/4] Verification de Git..."

$hasGit = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
if (-not $hasGit) {
    Write-Host "  Git non trouve — installation via winget..."
    try {
        winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path","User")
        $hasGit = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
    } catch {}
    if (-not $hasGit) {
        Write-Host "  [avertissement] Git non installe — essai installation directe..." -ForegroundColor Yellow
    } else {
        Write-Host "  OK — git installe"
    }
}

# ──────────────────────────────────────────
# 4. petrix-agent
# ──────────────────────────────────────────
Write-Host "[4/4] Installation de petrix-agent..."

$installOk = $false
try {
    & $python -m pip install --upgrade --quiet "git+https://gitlab.com/petrix1/petrix.git#subdirectory=agent"
    $installOk = $true
} catch {
    Write-Host "  [!] Installation depuis GitLab echouee : $_" -ForegroundColor Yellow
}

if (-not $installOk) {
    Write-Host "[!] Impossible d'installer petrix-agent." -ForegroundColor Red
    Write-Host "    Verifiez votre connexion internet et que Git est installe."
    exit 1
}

# Rafraichir PATH une derniere fois
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "  OK — petrix-agent installe"

# ──────────────────────────────────────────
# Config + raccourci
# ──────────────────────────────────────────
$ConfigDir = "$env:USERPROFILE\.petrix-agent"
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

Set-Content -Path "$ConfigDir\config.env" -Value @(
    "PETRIX_SERVER=$Server",
    "PETRIX_TOKEN=$Token"
) -Encoding UTF8

Set-Content -Path "$ConfigDir\run.bat" -Value @(
    "@echo off",
    "echo Petrix Agent - Scan en cours...",
    "petrix-agent --server $Server --token $Token %*",
    "pause"
) -Encoding Default

Write-Host ""
Write-Host "============================================"
Write-Host "  Installation terminee !" -ForegroundColor Green
Write-Host "============================================"
Write-Host "  Raccourci : $ConfigDir\run.bat"
Write-Host ""

$confirm = Read-Host "Lancer un scan maintenant ? [O/n]"
if ($confirm -ne "n" -and $confirm -ne "N") {
    Write-Host ""
    Write-Host "Demarrage du scan..." -ForegroundColor Cyan
    try {
        & petrix-agent --server $Server --token $Token
    } catch {
        Write-Host "[!] Commande 'petrix-agent' introuvable. Essai avec Python..." -ForegroundColor Yellow
        & $python -m petrix_agent.cli --server $Server --token $Token
    }
}
