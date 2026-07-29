# ==============================================================================
# Petrix Audit Agent  -  Windows (ANSSI-BP-028)
# 7 modules - verifications de durcissement Windows
#
# Referentiel : ANSSI-BP-028 v2.0 adapte Windows + recommandations CIS Microsoft Windows
# Auteur  : Noella IKIREZI - ESGI 4SI4 / Projet annuel Petrix
# Version : 1.0.0
#
# Ce script s'execute LOCALEMENT sur la machine cible (aucun acces SSH requis).
# Il genere un rapport XML structure importable dans la plateforme Petrix via
# l'endpoint POST /api/v1/hardening/import-xml.
#
# Usage (PowerShell en tant qu'Administrateur) :
#   .\petrix_agent_windows.ps1
#   .\petrix_agent_windows.ps1 -PetrixUrl "http://PETRIX_URL"
#   .\petrix_agent_windows.ps1 -OutFile "C:\temp\audit.xml"
#
# Resultat : fichier XML dans le meme dossier que le script (ou -OutFile)
#            Score /100 + Grade (A->F) affiches dans le terminal
# ==============================================================================

# Requires -RunAsAdministrator : PowerShell refusera l'execution si le terminal
# n'est pas ouvert en tant qu'administrateur - garantit l'acces aux APIs systeme.
#Requires -RunAsAdministrator

param(
    [string]$PetrixUrl = "",
    [string]$OutFile   = ""
)

# Set-StrictMode : equivalent de "set -u" en bash - toute variable non
# initialisee provoque une erreur. ErrorActionPreference = "Continue" permet
# de continuer l'audit meme si un check individuel echoue.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# -- Variables globales -------------------------------------------------------
# Informations systeme collectees via WMI/CIM pour le rapport XML.
$HostName     = [System.Net.Dns]::GetHostName()
$OSInfo       = Get-CimInstance Win32_OperatingSystem
$OSName       = $OSInfo.Caption
$Arch         = $OSInfo.OSArchitecture
$DateISO      = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$stamp = (Get-Date -Format "yyyyMMdd_HHmmss")
$FName = "petrix_audit_${HostName}_${stamp}.xml"
if (-not $OutFile) {
    # Rapport dans le meme dossier que le script
    $OutFile = Join-Path $PSScriptRoot $FName
}

# Compteurs globaux - mis a jour par chaque appel a Add-Finding
$Script:Total  = 0; $Script:Passed = 0
$Script:Crit   = 0; $Script:High   = 0; $Script:Med = 0; $Script:Low = 0

# Buffers XML construits au fil des checks, serialises dans Generate-XML
$Script:FindXML = [System.Text.StringBuilder]::new()
$Script:ModScores = [System.Text.StringBuilder]::new()

# -- Helpers ------------------------------------------------------------------

# Esc-Xml : echappe les 4 caracteres speciaux XML (&, <, >, ") pour garantir
#           un rapport XML valide meme si une valeur systeme contient ces caracteres.
function Esc-Xml([string]$s) {
    $s -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' -replace '"','&quot;'
}

# Add-Finding : coeur du moteur de reporting - enregistre un resultat de check.
#   Id       : identifiant unique du check (ex : USR-001, FW-Domain, POL-003...)
#   Module   : nom du module (users | firewall | services | network | ...)
#   Severity : severite (CRITICAL | HIGH | MEDIUM | LOW | INFO)
#   Status   : PASS ou FAIL
#   Name     : libelle lisible du check
#   Found    : valeur observee sur le systeme
#   Expected : valeur attendue selon le referentiel
#   Rem      : commande de remediation prete a copier-coller
#   Ctx      : contexte additionnel - facultatif
#   Dangerous: "true" si le port/service est dans la liste des dangereux
function Add-Finding {
    param(
        [string]$Id, [string]$Module, [string]$Severity, [string]$Status,
        [string]$Name, [string]$Found, [string]$Expected, [string]$Rem,
        [string]$Ctx = "", [string]$Dangerous = "false"
    )
    $Script:Total++
    if ($Status -eq "PASS") { $Script:Passed++ }
    else {
        switch ($Severity) {
            "CRITICAL" { $Script:Crit++ }
            "HIGH"     { $Script:High++ }
            "MEDIUM"   { $Script:Med++  }
            "LOW"      { $Script:Low++  }
        }
    }
    $extra = if ($Dangerous -eq "true") { ' dangerous="true"' } else { "" }
    $null = $Script:FindXML.AppendLine("  <Finding id=`"$(Esc-Xml $Id)`" module=`"$(Esc-Xml $Module)`" severity=`"$(Esc-Xml $Severity)`" status=`"$(Esc-Xml $Status)`"$extra>")
    $null = $Script:FindXML.AppendLine("    <Name>$(Esc-Xml $Name)</Name>")
    $null = $Script:FindXML.AppendLine("    <Found>$(Esc-Xml $Found)</Found>")
    $null = $Script:FindXML.AppendLine("    <Expected>$(Esc-Xml $Expected)</Expected>")
    $null = $Script:FindXML.AppendLine("    <Remediation>$(Esc-Xml $Rem)</Remediation>")
    $null = $Script:FindXML.AppendLine("    <Context>$(Esc-Xml $Ctx)</Context>")
    $null = $Script:FindXML.AppendLine("  </Finding>")
}

# Pass : alias PASS - found == expected, aucune remediation necessaire.
function Pass([string]$Id, [string]$Mod, [string]$Name, [string]$Found, [string]$Ctx = "") {
    Add-Finding -Id $Id -Module $Mod -Severity "INFO" -Status "PASS" `
        -Name $Name -Found $Found -Expected $Found -Rem "" -Ctx $Ctx
}

# Fail : alias FAIL - ecart constate avec severite et commande de correction.
function Fail([string]$Id, [string]$Mod, [string]$Sev, [string]$Name,
              [string]$Found, [string]$Expected, [string]$Rem, [string]$Ctx = "") {
    Add-Finding -Id $Id -Module $Mod -Severity $Sev -Status "FAIL" `
        -Name $Name -Found $Found -Expected $Expected -Rem $Rem -Ctx $Ctx
}

# Add-ModScore : calcule le score du module (checks reussis / total x 100) et
#               l'enregistre comme balise XML <Module name="..." score="nn" />.
function Add-ModScore([string]$Name, [int]$T, [int]$P) {
    $sc = if ($T -gt 0) { [int]($P * 100 / $T) } else { 100 }
    $null = $Script:ModScores.AppendLine("      <Module name=`"$Name`" score=`"$sc`" />")
}

# -- [1] COMPTES UTILISATEURS ─────────────────────────────────────────────────
# Verifie les comptes locaux a risque et la politique de mot de passe.
#
# Checks cles :
#   Compte Administrateur integre : cible privilegiee des attaques par force brute
#     car son nom est previsible - il doit etre desactive si non utilise
#   Compte Invite : acces anonyme a Windows meme limite - toujours desactiver
#   Longueur min mdp >= 12 : longueur recommandee par l'ANSSI-BP-028
#     Un mdp de 8 caracteres est crackable en quelques heures sur GPU moderne
# -----------------------------------------------------------------------------

function Audit-Users {
    $t = 0; $p = 0

    # Compte Administrateur integre actif
    $t++
    $adm = Get-LocalUser -Name "Administrator" -ErrorAction SilentlyContinue
    if ($adm -and $adm.Enabled) {
        Fail "USR-001" "users" "MEDIUM" "Compte Administrateur integre actif" `
            "Active" "Desactive" `
            'Disable-LocalUser -Name "Administrator"' `
            "Compte par defaut  -  cible de bruteforce"
    } else { Pass "USR-001" "users" "Compte Administrateur" "Desactive"; $p++ }

    # Compte Invite actif
    $t++
    $guest = Get-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
    if ($guest -and $guest.Enabled) {
        Fail "USR-002" "users" "HIGH" "Compte Invite actif" `
            "Active" "Desactive" `
            'Disable-LocalUser -Name "Guest"' "Acces anonyme possible"
    } else { Pass "USR-002" "users" "Compte Invite" "Desactive"; $p++ }

    # Utilisateurs administrateurs locaux - inventaire
    $t++
    $admins = (Get-LocalGroupMember -Group "Administrators" -ErrorAction SilentlyContinue |
              Where-Object { $_.ObjectClass -eq "User" } |
              ForEach-Object { $_.Name }) -join ", "
    Pass "USR-003" "users" "Administrateurs locaux" "${admins:-aucun}" "Inventaire des comptes admin locaux"; $p++

    # Politique de mot de passe - longueur minimum
    $t++
    try {
        $secpol = net accounts 2>&1 | Select-String "Minimum password length" | ForEach-Object { ($_ -split ":")[1].Trim() }
        $minLen = if ($secpol) { [int]$secpol } else { 0 }
        if ($minLen -ge 12) {
            Pass "USR-004" "users" "Longueur min mot de passe" "$minLen caracteres"; $p++
        } else {
            Fail "USR-004" "users" "MEDIUM" "Longueur min mot de passe insuffisante" `
                "$minLen caracteres" ">= 12 caracteres" `
                "secpol.msc > Password Policy > Minimum password length = 12" `
                "Brute force facilite"
        }
    } catch { Pass "USR-004" "users" "Politique mot de passe" "Non lisible"; $p++ }

    Add-ModScore "users" $t $p
}

# -- [2] PARE-FEU WINDOWS ─────────────────────────────────────────────────────
# Windows Firewall fonctionne avec 3 profils independants selon le type de reseau :
#   Domain  : reseau d'entreprise authentifie (Active Directory)
#   Private : reseau de confiance (domicile, bureau)
#   Public  : reseau non fiable (hotspot, reseau inconnu)
#
# Chaque profil doit etre actif - un profil desactive laisse les connexions
# entrantes non filtrees pour ce type de reseau.
# -----------------------------------------------------------------------------

function Audit-Firewall {
    $t = 0; $p = 0
    $profiles = @("Domain", "Private", "Public")
    foreach ($prof in $profiles) {
        $t++
        try {
            $fw = Get-NetFirewallProfile -Name $prof -ErrorAction Stop
            if ($fw.Enabled) {
                Pass "FW-${prof}" "firewall" "Pare-feu $prof" "Active"; $p++
            } else {
                Fail "FW-${prof}" "firewall" "HIGH" "Pare-feu $prof desactive" `
                    "Desactive" "Active" `
                    "Set-NetFirewallProfile -Name $prof -Enabled True" `
                    "Pas de filtrage reseau pour le profil $prof"
            }
        } catch { Pass "FW-${prof}" "firewall" "Pare-feu $prof" "Non lisible"; $p++ }
    }
    Add-ModScore "firewall" $t $p
}

# -- [3] SERVICES DANGEREUX ───────────────────────────────────────────────────
# Verifie que les services reseau a risque sont desactives.
# Un service en etat "Running" signifie qu'un port est ouvert et qu'un
# processus attend des connexions - chaque service inutile est une surface
# d'attaque supplémentaire.
#
# Services controles :
#   Telnet      : protocole teletype non chiffre, remplace par SSH depuis 25 ans
#   RemoteRegistry: expose la base de registre Windows en lecture/ecriture reseau
#   TlntSvr     : serveur Telnet Windows legacy
#   SNMP        : v1/v2 utilisent des community strings en clair dans le reseau
#   Fax         : service inutile en production (vecteur d'exploitation historique)
# -----------------------------------------------------------------------------

function Audit-Services {
    $t = 0; $p = 0
    $dangerous = @(
        @{ Name="Telnet"; Id="SVC-001"; Desc="Telnet  -  protocole non chiffre" },
        @{ Name="RemoteRegistry"; Id="SVC-002"; Desc="Registre distant expose" },
        @{ Name="TlntSvr"; Id="SVC-003"; Desc="Serveur Telnet" },
        @{ Name="SNMP"; Id="SVC-004"; Desc="SNMP v1/v2  -  community strings en clair" },
        @{ Name="Fax"; Id="SVC-005"; Desc="Service Fax inutile en prod" }
    )
    foreach ($svc in $dangerous) {
        $t++
        $s = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
        if ($s -and $s.Status -eq "Running") {
            Fail $svc.Id "services" "HIGH" "Service $($svc.Name) actif" `
                "Running" "Stopped/Disabled" `
                "Stop-Service -Name '$($svc.Name)' -Force; Set-Service -Name '$($svc.Name)' -StartupType Disabled" `
                $svc.Desc
        } else { Pass $svc.Id "services" "Service $($svc.Name)" "Inactif/Absent"; $p++ }
    }
    Add-ModScore "services" $t $p
}

# -- [4] PORTS RESEAU ─────────────────────────────────────────────────────────
# Liste tous les ports TCP en ecoute (Get-NetTCPConnection) et qualifie chacun.
# Identifie le processus associe a chaque port via Get-Process pour faciliter
# le diagnostic et la remediation.
#
# DangerPorts liste les ports historiquement exploites :
#   Bases de donnees exposees reseau (1433 MSSQL, 3306 MySQL, 6379 Redis...)
#   Protocols non chiffres (21 FTP, 23 Telnet, 5900 VNC...)
#   Services Windows/RPC (135 RPC Mapper, 139/445 NetBIOS/SMB)
#   RDP (3389) : controle avec severite MEDIUM - acceptable si necessite mais
#                doit etre restreint par IP, protege par NLA et surveille
# -----------------------------------------------------------------------------

$DangerPorts = @(21,23,69,110,135,137,138,139,143,389,445,512,513,514,1433,1521,3306,5432,5900,6379,27017)

function Get-PortInfo([int]$Port) {
    switch ($Port) {
        21    { return @{ Desc="FTP  -  protocole non chiffre"; Sev="HIGH"; Rem="Desactiver le service FTP" } }
        22    { return @{ Desc="SSH"; Sev="INFO"; Rem="" } }
        23    { return @{ Desc="Telnet  -  non chiffre, remplace par SSH"; Sev="CRITICAL"; Rem="Desactiver le service Telnet" } }
        25    { return @{ Desc="SMTP  -  verifier exposition externe"; Sev="MEDIUM"; Rem="Restreindre aux interfaces internes" } }
        69    { return @{ Desc="TFTP  -  pas d'authentification"; Sev="HIGH"; Rem="Desactiver le service TFTP" } }
        80    { return @{ Desc="HTTP  -  trafic non chiffre"; Sev="LOW"; Rem="Configurer HTTPS" } }
        110   { return @{ Desc="POP3  -  authentification en clair"; Sev="HIGH"; Rem="Utiliser POP3S (995)" } }
        135   { return @{ Desc="RPC Endpoint Mapper"; Sev="HIGH"; Rem="Bloquer via Windows Firewall si inutile" } }
        137   { return @{ Desc="NetBIOS Name Service"; Sev="HIGH"; Rem="Desactiver NetBIOS over TCP/IP si inutile" } }
        138   { return @{ Desc="NetBIOS Datagram"; Sev="HIGH"; Rem="Desactiver NetBIOS over TCP/IP" } }
        139   { return @{ Desc="NetBIOS Session"; Sev="HIGH"; Rem="Desactiver NetBIOS over TCP/IP" } }
        143   { return @{ Desc="IMAP  -  authentification en clair"; Sev="HIGH"; Rem="Utiliser IMAPS (993)" } }
        389   { return @{ Desc="LDAP non chiffre"; Sev="HIGH"; Rem="Utiliser LDAPS (636)" } }
        443   { return @{ Desc="HTTPS  -  chiffre"; Sev="INFO"; Rem="" } }
        445   { return @{ Desc="SMB/CIFS  -  vecteur de propagation"; Sev="HIGH"; Rem="Bloquer si inutile" } }
        1433  { return @{ Desc="MSSQL Server expose reseau"; Sev="HIGH"; Rem="Configurer SQL Server pour ecouter uniquement sur 127.0.0.1" } }
        1521  { return @{ Desc="Oracle DB expose reseau"; Sev="HIGH"; Rem="Restreindre l'acces reseau Oracle" } }
        3306  { return @{ Desc="MySQL/MariaDB expose reseau"; Sev="HIGH"; Rem="bind-address=127.0.0.1 dans my.cnf" } }
        3389  { return @{ Desc="RDP  -  acces bureau distant"; Sev="MEDIUM"; Rem="Restreindre par IP, activer NLA, changer port si possible" } }
        5432  { return @{ Desc="PostgreSQL expose reseau"; Sev="HIGH"; Rem="listen_addresses='localhost' dans postgresql.conf" } }
        5900  { return @{ Desc="VNC  -  acces graphique non chiffre"; Sev="HIGH"; Rem="Utiliser un tunnel SSH pour VNC" } }
        6379  { return @{ Desc="Redis expose sans auth"; Sev="CRITICAL"; Rem="bind 127.0.0.1 + requirepass dans redis.conf" } }
        8080  { return @{ Desc="HTTP alternatif"; Sev="LOW"; Rem="Verifier si HTTPS est disponible" } }
        27017 { return @{ Desc="MongoDB expose reseau"; Sev="HIGH"; Rem="bindIp: 127.0.0.1 dans mongod.conf" } }
        default { return @{ Desc="Port ouvert  -  verifier si necessaire"; Sev="INFO"; Rem="" } }
    }
}

function Audit-Network {
    $t = 0; $p = 0
    $seenPorts = @{}

    try {
        $conns = Get-NetTCPConnection -State Listen -ErrorAction Stop |
                 Select-Object LocalPort, @{N="PID";E={$_.OwningProcess}} |
                 Sort-Object LocalPort -Unique
    } catch {
        Pass "NET-000" "network" "Inventaire ports" "Get-NetTCPConnection indisponible"
        $p++; Add-ModScore "network" 1 1; return
    }

    foreach ($c in $conns) {
        $port = $c.LocalPort
        if ($seenPorts.ContainsKey($port)) { continue }
        $seenPorts[$port] = $true

        # Identifier le processus proprietaire du port pour faciliter la remediation
        $proc = "inconnu"
        try {
            $prc = Get-Process -Id $c.PID -ErrorAction SilentlyContinue
            if ($prc) { $proc = $prc.Name }
        } catch {}

        $info  = Get-PortInfo $port
        $dangerous = if ($DangerPorts -contains $port) { "true" } else { "false" }
        $id    = "NET-{0:D4}" -f $port
        $t++

        if ($info.Sev -eq "INFO" -or $info.Sev -eq "LOW") {
            Add-Finding -Id $id -Module "network" -Severity $info.Sev -Status "PASS" `
                -Name "Port $port/tcp  -  $($info.Desc)" `
                -Found "LISTEN" -Expected "LISTEN" -Rem $info.Rem `
                -Ctx "Processus: $proc" -Dangerous $dangerous
            $p++
        } else {
            Add-Finding -Id $id -Module "network" -Severity $info.Sev -Status "FAIL" `
                -Name "Port $port/tcp DANGEREUX  -  $($info.Desc)" `
                -Found "LISTEN" -Expected "Ferme ou filtre" -Rem $info.Rem `
                -Ctx "Processus: $proc" -Dangerous $dangerous
        }
    }

    if ($t -eq 0) { Pass "NET-000" "network" "Aucun port" "Aucun port TCP en ecoute"; $p++; $t++ }
    Add-ModScore "network" $t $p
}

# -- [5] WINDOWS UPDATE ───────────────────────────────────────────────────────
# Verifie si des mises a jour de securite Windows sont en attente via l'API
# Microsoft.Update.Session (Windows Update Agent COM).
#
# Tout systeme Windows non patche est expose aux CVE connues et exploitees.
# Les vulnerabilites critiques comme EternalBlue (SMB, WannaCry 2017) ou
# PrintNightmare (spouleur, 2021) sont exploitables meme a distance et sans
# authentification sur des systemes non mis a jour.
# -----------------------------------------------------------------------------

function Audit-Updates {
    $t = 0; $p = 0
    $t++
    try {
        $wu = New-Object -ComObject Microsoft.Update.Session -ErrorAction Stop
        $searcher = $wu.CreateUpdateSearcher()
        $result   = $searcher.Search("IsInstalled=0 and Type='Software'")
        $count    = $result.Updates.Count
        if ($count -eq 0) {
            Pass "UPD-001" "updates" "Windows Update" "Systeme a jour"; $p++
        } else {
            Fail "UPD-001" "updates" "MEDIUM" "Mises a jour Windows en attente" `
                "$count mise(s) a jour disponible(s)" "0 (systeme a jour)" `
                "Lancer Windows Update ou : Install-WindowsUpdate -AcceptAll -AutoReboot" `
                "Exposition aux CVE connues"
        }
    } catch {
        Pass "UPD-001" "updates" "Windows Update" "Non verifiable (WMI indisponible)"; $p++
    }
    Add-ModScore "updates" $t $p
}

# -- [6] ANTIVIRUS / DEFENDER ─────────────────────────────────────────────────
# Windows Defender (Microsoft Defender Antivirus) est la protection antivirale
# integree a Windows depuis Windows 8. Il s'appuie sur :
#   - Des signatures de malwares mises a jour en continu
#   - L'analyse comportementale en temps reel (heuristique)
#   - L'integration avec Microsoft Security Center
#
# BitLocker : chiffrement integral de volume (AES-XTS 128 ou 256 bits).
# Sans BitLocker, un attaquant avec acces physique peut lire toutes les donnees
# en bootant sur un OS externe - aucun mot de passe Windows ne protege contre ca.
# -----------------------------------------------------------------------------

function Audit-Security {
    $t = 0; $p = 0

    # Windows Defender - protection en temps reel
    $t++
    try {
        $mps = Get-MpComputerStatus -ErrorAction Stop
        if ($mps.AntivirusEnabled) {
            Pass "SEC-001" "security" "Windows Defender Antivirus" "Active"; $p++
        } else {
            Fail "SEC-001" "security" "HIGH" "Windows Defender desactive" `
                "Desactive" "Active" `
                "Set-MpPreference -DisableRealtimeMonitoring $false" "Protection en temps reel absente"
        }
    } catch { Pass "SEC-001" "security" "Windows Defender" "Statut non lisible"; $p++ }

    # Fraicheur des signatures - signatures > 3 jours = detection degradee
    $t++
    try {
        $mps = Get-MpComputerStatus -ErrorAction Stop
        $sigAge = (Get-Date) - $mps.AntivirusSignatureLastUpdated
        if ($sigAge.TotalDays -le 3) {
            Pass "SEC-002" "security" "Signatures antivirus" "Mises a jour il y a $([int]$sigAge.TotalHours)h"; $p++
        } else {
            Fail "SEC-002" "security" "MEDIUM" "Signatures antivirus obsoletes" `
                "Derniere maj : $($mps.AntivirusSignatureLastUpdated.ToString('yyyy-MM-dd'))" `
                "< 3 jours" "Update-MpSignature" "Detection degradee"
        }
    } catch { Pass "SEC-002" "security" "Signatures Defender" "Non lisible"; $p++ }

    # BitLocker - chiffrement du disque systeme C:
    $t++
    try {
        $bl = Get-BitLockerVolume -MountPoint "C:" -ErrorAction Stop
        if ($bl.VolumeStatus -eq "FullyEncrypted") {
            Pass "SEC-003" "security" "BitLocker (C:)" "Chiffre"; $p++
        } else {
            Fail "SEC-003" "security" "HIGH" "Disque C: non chiffre (BitLocker)" `
                $bl.VolumeStatus.ToString() "FullyEncrypted" `
                "Enable-BitLocker -MountPoint 'C:' -EncryptionMethod Aes256 -UsedSpaceOnly" `
                "Donnees non protegees en cas de vol physique"
        }
    } catch { Pass "SEC-003" "security" "BitLocker" "Non disponible/non applicable"; $p++ }

    Add-ModScore "security" $t $p
}

# -- [7] REGISTRE / STRATEGIES ────────────────────────────────────────────────
# Verifie les parametres de securite Windows configures dans la base de registre
# et les journaux d'evenements.
#
# Checks cles :
#   UAC (User Account Control) : mecanisme d'elevation de privileges - invite
#     l'utilisateur a confirmer avant toute operation administrative.
#     Sans UAC, tout programme lance par un administrateur obtient automatiquement
#     les privileges maximum - un malware admin devient silencieusement "SYSTEM"
#
#   ExecutionPolicy PowerShell : controle quels scripts PowerShell peuvent s'executer.
#     "Unrestricted" ou "Bypass" permettent a n'importe quel script de s'executer
#     sans validation, incluant les payloads malveillants telecharges
#
#   Journal Securite Windows : trace les connexions, echecs d'auth, elevations de
#     privileges. Sans lui, la detection d'intrusion post-incident est impossible.
# -----------------------------------------------------------------------------

function Audit-Policies {
    $t = 0; $p = 0

    # UAC
    $t++
    $uac = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
        -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA
    if ($uac -eq 1) { Pass "POL-001" "policies" "UAC (User Account Control)" "Active"; $p++ }
    else {
        Fail "POL-001" "policies" "HIGH" "UAC desactive" `
            "Desactive" "Active" `
            'Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name EnableLUA -Value 1' `
            "Elevation silencieuse de privileges"
    }

    # Ecran de verrouillage
    $t++
    $lockProp = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
        -Name "DisableLockWorkstation" -ErrorAction SilentlyContinue
    $lock = if ($lockProp) { $lockProp.DisableLockWorkstation } else { 0 }
    if (-not $lock -or $lock -eq 0) { Pass "POL-002" "policies" "Verrouillage de session" "Active"; $p++ }
    else {
        Fail "POL-002" "policies" "MEDIUM" "Verrouillage de session desactive" `
            "Desactive" "Active" `
            'Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name DisableLockWorkstation -Value 0' `
            "Sessions non verrouillees automatiquement"
    }

    # PowerShell ExecutionPolicy
    $t++
    $ep = Get-ExecutionPolicy -Scope LocalMachine -ErrorAction SilentlyContinue
    if ($ep -in @("AllSigned","RemoteSigned")) { Pass "POL-003" "policies" "PowerShell ExecutionPolicy" $ep.ToString(); $p++ }
    elseif ($ep -eq "Restricted") { Pass "POL-003" "policies" "PowerShell ExecutionPolicy" "Restricted"; $p++ }
    else {
        Fail "POL-003" "policies" "MEDIUM" "ExecutionPolicy trop permissive" `
            $ep.ToString() "RemoteSigned ou AllSigned" `
            "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine" `
            "Scripts non signes peuvent s'executer"
    }

    Add-ModScore "policies" $t $p
}

function Audit-Logging {
    $t = 0; $p = 0

    # Journal de securite Windows
    $t++
    try {
        $secLog = Get-WinEvent -ListLog "Security" -ErrorAction Stop
        if ($secLog.IsEnabled) { Pass "LOG-001" "logging" "Journal Securite Windows" "Active"; $p++ }
        else {
            Fail "LOG-001" "logging" "HIGH" "Journal Securite desactive" `
                "Desactive" "Active" "wevtutil sl Security /enabled:true" "Absence de traces de securite"
        }
    } catch { Pass "LOG-001" "logging" "Journal Securite" "Non lisible"; $p++ }

    # Taille max du journal de securite - trop petit = rotation rapide = perte d'historique
    $t++
    try {
        $secLog = Get-WinEvent -ListLog "Security" -ErrorAction Stop
        $maxMB  = [int]($secLog.MaximumSizeInBytes / 1MB)
        if ($maxMB -ge 128) { Pass "LOG-002" "logging" "Taille journal Securite" "${maxMB} MB"; $p++ }
        else {
            Fail "LOG-002" "logging" "LOW" "Journal Securite trop petit" `
                "${maxMB} MB" ">= 128 MB" `
                "wevtutil sl Security /ms:134217728" "Rotation trop rapide  -  perte d'historique"
        }
    } catch { Pass "LOG-002" "logging" "Taille journal Securite" "Non lisible"; $p++ }

    Add-ModScore "logging" $t $p
}

# -- SCORE GLOBAL ── Formule de deduction -------------------------------------
# CRITICAL x15 + HIGH x8 + MEDIUM x3 + LOW x1
# Bareme : A (>=90) · B (>=75) · C (>=60) · D (>=40) · F (<40)
# Le score est plafonne entre 0 et 100 (jamais negatif).
# -----------------------------------------------------------------------------

function Compute-Score {
    $ded  = $Script:Crit * 15 + $Script:High * 8 + $Script:Med * 3 + $Script:Low
    $sc   = 100 - $ded
    if ($sc -lt 0)   { $sc = 0 }
    if ($sc -gt 100) { $sc = 100 }
    $grade = switch ($sc) {
        { $_ -ge 90 } { "A"; break }
        { $_ -ge 75 } { "B"; break }
        { $_ -ge 60 } { "C"; break }
        { $_ -ge 40 } { "D"; break }
        default         { "F" }
    }
    return @{ Score = $sc; Grade = $grade }
}

# -- GENERATION XML ── Rapport importable dans Petrix ─────────────────────────
# Structure : <PetrixAuditReport> -> <Metadata> + <Scores> + <Findings>
# Encode en UTF-8 pour la compatibilite avec l'API Petrix.
# -----------------------------------------------------------------------------

function Generate-XML([int]$Score, [string]$Grade) {
    $failed = $Script:Total - $Script:Passed
    $xml = @"
<?xml version="1.0" encoding="UTF-8"?>
<PetrixAuditReport Referential="ANSSI-BP-028" AgentVersion="1.0.0">
  <Metadata>
    <Hostname>$(Esc-Xml $HostName)</Hostname>
    <OS>$(Esc-Xml $OSName)</OS>
    <OSType>windows</OSType>
    <Architecture>$(Esc-Xml $Arch)</Architecture>
    <GenerationDate>$DateISO</GenerationDate>
  </Metadata>
  <Scores>
    <GlobalScore>$Score</GlobalScore>
    <GlobalGrade>$Grade</GlobalGrade>
    <TotalChecks>$($Script:Total)</TotalChecks>
    <PassedChecks>$($Script:Passed)</PassedChecks>
    <CriticalCount>$($Script:Crit)</CriticalCount>
    <HighCount>$($Script:High)</HighCount>
    <MediumCount>$($Script:Med)</MediumCount>
    <LowCount>$($Script:Low)</LowCount>
    <ModuleScores>
$($Script:ModScores.ToString())
    </ModuleScores>
  </Scores>
  <Findings>
$($Script:FindXML.ToString())
  </Findings>
</PetrixAuditReport>
"@
    $xml | Out-File -FilePath $OutFile -Encoding UTF8
}

# -- UPLOAD ── Envoi du rapport vers la plateforme Petrix ─────────────────────
# Si -PetrixUrl est fourni, envoie le rapport XML via multipart/form-data
# sur POST /api/v1/hardening/import-xml en utilisant HttpClient (.NET natif).
# -----------------------------------------------------------------------------

function Upload-XML {
    if (-not $PetrixUrl) { return }
    Write-Host ""
    Write-Host -NoNewline "-> Upload vers $PetrixUrl ... "
    try {
        $form = [System.Net.Http.MultipartFormDataContent]::new()
        $bytes = [System.IO.File]::ReadAllBytes($OutFile)
        $fc = [System.Net.Http.ByteArrayContent]::new($bytes)
        $fc.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/xml")
        $form.Add($fc, "file", [System.IO.Path]::GetFileName($OutFile))
        $client = [System.Net.Http.HttpClient]::new()
        $resp   = $client.PostAsync("$PetrixUrl/api/v1/hardening/import-xml", $form).Result
        if ($resp.IsSuccessStatusCode) { Write-Host "OK" }
        else { Write-Host "ERREUR HTTP $($resp.StatusCode)" }
    } catch { Write-Host "ERREUR : $_" }
}

# -- MAIN ----------------------------------------------------------------------

Write-Host "================================================================"
Write-Host "  Petrix Audit Agent 1.0  -  Windows  -  ANSSI-BP-028"
Write-Host "  Hote : $HostName"
Write-Host "  OS   : $OSName ($Arch)"
Write-Host "================================================================"

Write-Host "[1/7] Comptes utilisateurs..."   ; Audit-Users
Write-Host "[2/7] Pare-feu Windows..."       ; Audit-Firewall
Write-Host "[3/7] Services dangereux..."      ; Audit-Services
Write-Host "[4/7] Ports reseau..."           ; Audit-Network
Write-Host "[5/7] Windows Update..."          ; Audit-Updates
Write-Host "[6/7] Securite (Defender)..."    ; Audit-Security
Write-Host "[7/7] Strategies & journaux..."   ; Audit-Policies; Audit-Logging

$result = Compute-Score
Generate-XML -Score $result.Score -Grade $result.Grade

$failed = $Script:Total - $Script:Passed
Write-Host ""
Write-Host "================================================================"
Write-Host ("  Score : {0}/100  Grade : {1}" -f $result.Score, $result.Grade)
Write-Host ("  Checks : {0} total | {1} OK | {2} echecs" -f $Script:Total, $Script:Passed, $failed)
Write-Host ("  CRITICAL:{0}  HIGH:{1}  MEDIUM:{2}  LOW:{3}" -f $Script:Crit, $Script:High, $Script:Med, $Script:Low)
Write-Host "  Rapport : $OutFile"
Write-Host "================================================================"

Upload-XML
