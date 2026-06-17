#Requires -RunAsAdministrator
# Petrix Agent — Installeur Windows
# Valeurs pré-configurées au téléchargement :
$PETRIX_SERVER = ""
$PETRIX_TOKEN = ""

param(
    [string]$Server = $PETRIX_SERVER,
    [string]$Token  = $PETRIX_TOKEN
)

$ErrorActionPreference = "Stop"
$ConfigDir = "$env:ProgramData\PetrixAgent"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Petrix Agent — Installeur Windows"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Server -or -not $Token) {
    Write-Host "[!] Token ou serveur manquant — telechargez ce script depuis Petrix." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Serveur : $Server"
Write-Host "[*] Token   : $($Token.Substring(0, [Math]::Min(20, $Token.Length)))..."
Write-Host ""

# ──────────────────────────────────────────
# 1. Python
# ──────────────────────────────────────────
Write-Host "[1/5] Python..." -ForegroundColor Yellow

$python = $null
foreach ($cmd in @("python", "py", "python3")) {
    try { if ((& $cmd --version 2>&1) -match "Python 3\.") { $python = $cmd; break } } catch {}
}

if (-not $python) {
    Write-Host "  Installation via winget..."
    try {
        winget install --id Python.Python.3.11 -e --silent --accept-source-agreements --accept-package-agreements
    } catch {
        Write-Host "  [!] winget echoue — installez Python depuis https://python.org" -ForegroundColor Red; exit 1
    }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 3
    foreach ($cmd in @("python", "py", "python3")) {
        try { if ((& $cmd --version 2>&1) -match "Python 3\.") { $python = $cmd; break } } catch {}
    }
    if (-not $python) { Write-Host "  [!] Python introuvable — redemarrez et relancez." -ForegroundColor Red; exit 1 }
}
Write-Host "  OK — $( & $python --version 2>&1 )" -ForegroundColor Green

# ──────────────────────────────────────────
# 2. nmap
# ──────────────────────────────────────────
Write-Host "[2/5] nmap..." -ForegroundColor Yellow

if (-not (Get-Command nmap -ErrorAction SilentlyContinue)) {
    try {
        winget install --id Insecure.Nmap -e --silent --accept-source-agreements --accept-package-agreements 2>$null
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {}
    if (Get-Command nmap -ErrorAction SilentlyContinue) { Write-Host "  OK — nmap installe" -ForegroundColor Green }
    else { Write-Host "  [!] nmap non installe — scan de ports limite" -ForegroundColor Yellow }
} else { Write-Host "  OK — nmap disponible" -ForegroundColor Green }

# ──────────────────────────────────────────
# 3. Git
# ──────────────────────────────────────────
Write-Host "[3/5] Git..." -ForegroundColor Yellow

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    try {
        winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {}
    if (Get-Command git -ErrorAction SilentlyContinue) { Write-Host "  OK — git installe" -ForegroundColor Green }
    else { Write-Host "  [!] git non installe" -ForegroundColor Yellow }
} else { Write-Host "  OK — git disponible" -ForegroundColor Green }

# ──────────────────────────────────────────
# 4. petrix-agent
# ──────────────────────────────────────────
Write-Host "[4/5] petrix-agent..." -ForegroundColor Yellow

try {
    & $python -m pip install --upgrade --quiet "git+https://gitlab.com/petrix1/petrix.git#subdirectory=agent"
} catch {
    Write-Host "  [!] Installation echouee : $_" -ForegroundColor Red; exit 1
}

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "  OK — petrix-agent installe" -ForegroundColor Green

# Config
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
Set-Content -Path "$ConfigDir\config.env" -Value @("PETRIX_SERVER=$Server", "PETRIX_TOKEN=$Token") -Encoding UTF8

# ──────────────────────────────────────────
# 5. Service Windows (via NSSM)
# ──────────────────────────────────────────
Write-Host "[5/5] Service Windows..." -ForegroundColor Yellow

# Trouve l'executable petrix-agent
$agentExe = $null
$pythonExe = (Get-Command $python).Source
foreach ($path in @(
    "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\petrix-agent.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\petrix-agent.exe",
    "C:\Python311\Scripts\petrix-agent.exe",
    "C:\Python312\Scripts\petrix-agent.exe"
)) {
    if (Test-Path $path) { $agentExe = $path; break }
}
if (-not $agentExe) {
    try { $agentExe = (Get-Command petrix-agent -ErrorAction Stop).Source } catch {}
}

# NSSM — gestionnaire de services (standard industrie pour les services Windows Python)
$nssmExe = "$ConfigDir\nssm.exe"
$nssmInstalled = $false

if (-not (Test-Path $nssmExe)) {
    Write-Host "  Telechargement de NSSM..."
    try {
        $nssmZip = "$env:TEMP\nssm.zip"
        (New-Object Net.WebClient).DownloadFile("https://nssm.cc/release/nssm-2.24.zip", $nssmZip)
        Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm-extract" -Force
        Copy-Item "$env:TEMP\nssm-extract\nssm-2.24\win64\nssm.exe" $nssmExe -Force
        $nssmInstalled = $true
        Write-Host "  OK — NSSM disponible" -ForegroundColor Green
    } catch {
        Write-Host "  [!] NSSM non disponible ($_ ) — utilisation du planificateur de taches" -ForegroundColor Yellow
    }
} else {
    $nssmInstalled = $true
    Write-Host "  OK — NSSM deja present" -ForegroundColor Green
}

# Supprime l'ancien service s'il existe
& sc.exe stop PetrixAgent 2>$null | Out-Null
if ($nssmInstalled) { & $nssmExe remove PetrixAgent confirm 2>$null | Out-Null }
else { & sc.exe delete PetrixAgent 2>$null | Out-Null }
Start-Sleep -Seconds 2

if ($nssmInstalled -and $agentExe) {
    # NSSM wraps petrix-agent --daemon as a proper Windows service
    & $nssmExe install PetrixAgent $agentExe "--server $Server --token $Token --daemon"
    & $nssmExe set PetrixAgent DisplayName "Petrix Agent"
    & $nssmExe set PetrixAgent Description "Agent de scan reseau Petrix — remontee automatique dans Petrix"
    & $nssmExe set PetrixAgent Start SERVICE_AUTO_START
    & $nssmExe set PetrixAgent AppStdout "$ConfigDir\agent.log"
    & $nssmExe set PetrixAgent AppStderr "$ConfigDir\agent-error.log"
    & $nssmExe set PetrixAgent AppRotateFiles 1
    & $nssmExe set PetrixAgent AppRotateBytes 5242880
    & sc.exe start PetrixAgent | Out-Null
    Write-Host "  Service 'PetrixAgent' installe et demarre" -ForegroundColor Green
    Write-Host "  Logs : $ConfigDir\agent.log"
} elseif ($agentExe) {
    # Fallback : tâche planifiée toutes les 5 min
    Write-Host "  Fallback : tache planifiee (toutes les 5 min)..."
    Unregister-ScheduledTask -TaskName "PetrixAgent" -Confirm:$false -ErrorAction SilentlyContinue
    $action   = New-ScheduledTaskAction -Execute $agentExe -Argument "--server $Server --token $Token --daemon --interval 1"
    $trigger  = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName "PetrixAgent" -TaskPath "\Petrix\" -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
    Start-ScheduledTask -TaskPath "\Petrix\" -TaskName "PetrixAgent"
    Write-Host "  Tache planifiee 'PetrixAgent' creee et demarree" -ForegroundColor Green
} else {
    Write-Host "  [!] petrix-agent introuvable dans PATH — relancez apres redemarrage." -ForegroundColor Yellow
}

# ──────────────────────────────────────────
# Enregistrement immédiat dans Assets
# ──────────────────────────────────────────
Write-Host ""
Write-Host "  Enregistrement dans Petrix Assets..." -ForegroundColor Cyan

try {
    $ips = @((Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -notmatch "^127\." -and $_.PrefixOrigin -ne "WellKnown"
    }).IPAddress)

    $osCaption = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue).Caption
    if (-not $osCaption) { $osCaption = "Windows" }

    $body = @{
        hostname     = $env:COMPUTERNAME
        ips          = $ips
        os           = "Windows"
        os_version   = $osCaption
        architecture = $env:PROCESSOR_ARCHITECTURE
    } | ConvertTo-Json -Depth 3

    $hdrs = @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" }
    $reg  = Invoke-RestMethod -Uri "$Server/api/v1/assets/register-self" -Method POST -Headers $hdrs -Body $body -TimeoutSec 15

    Write-Host "  Machine visible dans Petrix !" -ForegroundColor Green
    Write-Host "  ID asset  : $($reg.id)"
    Write-Host "  IP locale : $($ips -join ', ')"
    Write-Host "  Hostname  : $($env:COMPUTERNAME)"
} catch {
    Write-Host "  [!] Enregistrement echoue : $_" -ForegroundColor Yellow
    Write-Host "  L'agent reessaiera au prochain poll."
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Installation terminee !" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  L'agent tourne en arriere-plan comme service Windows."
Write-Host "  Depuis Petrix > Assets : cliquez 'Scanner' sur cette machine"
Write-Host "  pour lancer un scan a distance — l'agent l'executera automatiquement."
Write-Host ""
Write-Host "  Logs : $ConfigDir\agent.log"
Write-Host "  Serveur : $Server"
Write-Host ""
