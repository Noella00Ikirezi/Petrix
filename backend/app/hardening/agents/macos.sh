#!/usr/bin/env bash
# ==============================================================================
# Petrix Audit Agent — macOS (ANSSI-BP-028 adapté)
# Génère un rapport XML de durcissement sans connexion SSH distante.
#
# Usage :
#   sudo bash petrix_agent_macos.sh
#   sudo bash petrix_agent_macos.sh http://PETRIX_URL   # upload automatique
#   sudo OUTFILE=/tmp/mon_audit.xml bash petrix_agent_macos.sh
# ==============================================================================
set -u

PETRIX_URL="${1:-}"
HOSTNAME_VAL=$(hostname -f 2>/dev/null || hostname)
OS_VER=$(sw_vers -productVersion 2>/dev/null || echo "macOS")
OS_NAME="macOS $OS_VER"
ARCH=$(uname -m)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Rapport dans le dossier courant (là où la commande est lancée)
_FNAME="petrix_audit_${HOSTNAME_VAL}_$(date +%Y%m%d_%H%M%S).xml"
OUTFILE="${OUTFILE:-$(pwd)/${_FNAME}}"

TOTAL=0; PASSED=0; CRIT=0; HIGH_C=0; MED=0; LOW=0
FINDINGS_XML=""; MODULE_SCORES=""

# ── Helpers ──────────────────────────────────────────────────────────────────

xml_esc() { printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g'; }

_finding() {
  local id="$1" module="$2" sev="$3" st="$4" name="$5"
  local found="$6" expected="$7" rem="$8" ctx="${9:-}" extra="${10:-}"
  TOTAL=$((TOTAL+1))
  if [ "$st" = "PASS" ]; then
    PASSED=$((PASSED+1))
  else
    case "$sev" in
      CRITICAL) CRIT=$((CRIT+1)) ;;
      HIGH)     HIGH_C=$((HIGH_C+1)) ;;
      MEDIUM)   MED=$((MED+1)) ;;
      LOW)      LOW=$((LOW+1)) ;;
    esac
  fi
  FINDINGS_XML="${FINDINGS_XML}
  <Finding id=\"$(xml_esc "$id")\" module=\"$(xml_esc "$module")\" severity=\"$(xml_esc "$sev")\" status=\"$(xml_esc "$st")\"${extra}>
    <Name>$(xml_esc "$name")</Name>
    <Found>$(xml_esc "$found")</Found>
    <Expected>$(xml_esc "$expected")</Expected>
    <Remediation>$(xml_esc "$rem")</Remediation>
    <Context>$(xml_esc "$ctx")</Context>
  </Finding>"
}

ok()   { _finding "$1" "$2" "INFO" "PASS" "$3" "$4" "$4" ""    "$5" ""; }
warn() { _finding "$1" "$2" "$3" "FAIL" "$4" "$5" "$6" "$7"   "$8" ""; }

sshd_val() {
  local d="$1" def="${2:-}"
  local v
  v=$(sshd -T 2>/dev/null | grep -i "^${d,,} " | awk '{print $2}' | head -1)
  [ -z "$v" ] && v=$(grep -iE "^[[:space:]]*${d}[[:space:]]" /etc/ssh/sshd_config 2>/dev/null | tail -1 | awk '{print $2}')
  echo "${v:-$def}"
}

mod_score() {
  local name="$1" t="$2" p="$3"
  local sc=0; [ "$t" -gt 0 ] && sc=$(( p * 100 / t ))
  MODULE_SCORES="${MODULE_SCORES}      <Module name=\"$(xml_esc "$name")\" score=\"$sc\" />\n"
}

# ── SSH ───────────────────────────────────────────────────────────────────────

audit_ssh() {
  local t=0 p=0

  # Vérifier si SSH est activé
  t=$((t+1))
  local ssh_status
  ssh_status=$(launchctl list com.openssh.sshd 2>/dev/null | grep -c "com.openssh.sshd" || echo "0")
  if [ "$ssh_status" = "0" ]; then
    ok "SSH-000" "ssh" "SSH server" "Désactivé (recommandé)" "SSH distant non exposé"; p=$((p+1))
  else
    ok "SSH-000" "ssh" "SSH server" "Actif" "SSH distant exposé — vérifier la configuration"; p=$((p+1))

    ssh_chk() {
      local id="$1" dir="$2" exp="$3" sev="$4" desc="$5" rem="$6" def="${7:-}"
      local val; val=$(sshd_val "$dir" "$def")
      t=$((t+1))
      if [ "${val,,}" = "${exp,,}" ]; then
        ok "$id" "ssh" "$dir" "$val" "$desc"; p=$((p+1))
      else
        warn "$id" "ssh" "$sev" "$dir" "${val:-défaut OpenSSH}" "$exp" "$rem" "$desc"
      fi
    }

    ssh_chk "SSH-001" "PermitRootLogin"        "no"  "HIGH"     "Connexion root SSH"           "sudo sed -i '' 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && sudo launchctl stop com.openssh.sshd && sudo launchctl start com.openssh.sshd" "yes"
    ssh_chk "SSH-002" "PasswordAuthentication" "no"  "HIGH"     "Auth par mot de passe SSH"    "sudo sed -i '' 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && sudo launchctl stop com.openssh.sshd && sudo launchctl start com.openssh.sshd" "yes"
    ssh_chk "SSH-003" "PermitEmptyPasswords"   "no"  "CRITICAL" "Mots de passe vides SSH"      "Ajouter 'PermitEmptyPasswords no' dans /etc/ssh/sshd_config" "no"
    ssh_chk "SSH-004" "X11Forwarding"          "no"  "MEDIUM"   "X11 Forwarding"               "Ajouter 'X11Forwarding no' dans /etc/ssh/sshd_config" "yes"
  fi

  mod_score "ssh" "$t" "$p"
}

# ── SYSTEM INTEGRITY PROTECTION ───────────────────────────────────────────────

audit_sip() {
  local t=0 p=0
  t=$((t+1))
  local sip
  sip=$(csrutil status 2>/dev/null | head -1)
  if echo "$sip" | grep -qi "enabled"; then
    ok "SIP-001" "sip" "System Integrity Protection" "enabled" "Protection de l'intégrité système"; p=$((p+1))
  else
    warn "SIP-001" "sip" "CRITICAL" "SIP désactivé" "${sip:-inconnu}" "enabled" \
      "Redémarrer en Recovery, ouvrir Terminal : csrutil enable" \
      "Protection noyau et système de fichiers désactivée"
  fi

  # Gatekeeper
  t=$((t+1))
  local gk
  gk=$(spctl --status 2>/dev/null | head -1)
  if echo "$gk" | grep -qi "enabled\|assessments enabled"; then
    ok "SIP-002" "sip" "Gatekeeper" "enabled" "Contrôle des applications téléchargées"; p=$((p+1))
  else
    warn "SIP-002" "sip" "HIGH" "Gatekeeper désactivé" "${gk:-inconnu}" "enabled" \
      "sudo spctl --master-enable" "Applications non signées peuvent s'exécuter"
  fi

  mod_score "sip" "$t" "$p"
}

# ── FILEVAULT ─────────────────────────────────────────────────────────────────

audit_filevault() {
  local t=0 p=0
  t=$((t+1))
  local fv
  fv=$(fdesetup status 2>/dev/null | head -1)
  if echo "$fv" | grep -qi "^FileVault is On"; then
    ok "FV-001" "filevault" "FileVault" "Activé" "Chiffrement disque complet"; p=$((p+1))
  else
    warn "FV-001" "filevault" "HIGH" "FileVault désactivé" "${fv:-inconnu}" "FileVault is On" \
      "Préférences Système → Confidentialité et sécurité → FileVault → Activer" \
      "Disque non chiffré — données exposées en cas de vol"
  fi
  mod_score "filevault" "$t" "$p"
}

# ── PARE-FEU macOS ────────────────────────────────────────────────────────────

audit_firewall() {
  local t=0 p=0
  t=$((t+1))
  local fw_state
  fw_state=$(defaults read /Library/Preferences/com.apple.alf globalstate 2>/dev/null || echo "0")
  if [ "$fw_state" = "1" ] || [ "$fw_state" = "2" ]; then
    ok "FW-001" "firewall" "Pare-feu application" "Activé (mode $fw_state)" "Filtrage des connexions entrantes"; p=$((p+1))
  else
    warn "FW-001" "firewall" "HIGH" "Pare-feu application désactivé" "Désactivé" "Activé" \
      "Préférences Système → Sécurité → Pare-feu → Activer  OU  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on" \
      "Aucun filtrage des connexions entrantes"
  fi

  # Stealth mode
  t=$((t+1))
  local stealth
  stealth=$(defaults read /Library/Preferences/com.apple.alf stealthenabled 2>/dev/null || echo "0")
  if [ "$stealth" = "1" ]; then
    ok "FW-002" "firewall" "Mode furtif (Stealth)" "Activé" "Pas de réponse aux requêtes ICMP non sollicitées"; p=$((p+1))
  else
    warn "FW-002" "firewall" "LOW" "Mode furtif désactivé" "Désactivé" "Activé" \
      "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on" \
      "Réponse aux pings — découverte réseau plus facile"
  fi

  mod_score "firewall" "$t" "$p"
}

# ── PARTAGE & SERVICES ────────────────────────────────────────────────────────

audit_sharing() {
  local t=0 p=0

  svc_chk() {
    local id="$1" label="$2" nice="$3" desc="$4"
    t=$((t+1))
    if launchctl list "$label" &>/dev/null; then
      warn "$id" "sharing" "MEDIUM" "$nice actif" "actif" "inactif" \
        "Préférences Système → Partage → Décocher '$nice'" "$desc"
    else
      ok "$id" "sharing" "$nice" "inactif" "$desc"; p=$((p+1))
    fi
  }

  svc_chk "SHR-001" "com.apple.screensharing"   "Partage d'écran"        "Accès graphique distant"
  svc_chk "SHR-002" "com.apple.smbd"             "Partage de fichiers SMB" "Exposition fichiers réseau"
  svc_chk "SHR-003" "com.apple.mDNSResponder"    "mDNS/Bonjour"           "Découverte réseau"
  svc_chk "SHR-004" "com.apple.ftpd"             "FTP (partageFTP)"        "FTP non chiffré"
  svc_chk "SHR-005" "com.apple.RemoteDesktop.agent" "Remote Desktop (ARD)" "Administration à distance"
  svc_chk "SHR-006" "com.apple.InternetSharing"  "Partage de connexion"    "Routage non contrôlé"

  mod_score "sharing" "$t" "$p"
}

# ── PORTS RÉSEAU ─────────────────────────────────────────────────────────────

DANGER_PORTS="21 23 69 110 135 137 138 139 143 389 445 512 513 514 1433 1521 3306 5432 5900 6379 27017"

_port_info() {
  local p="$1"
  case "$p" in
    21)    echo "FTP — protocole non chiffré|HIGH|Désactiver le service FTP"; return ;;
    22)    echo "SSH — port standard|INFO|"; return ;;
    23)    echo "Telnet — non chiffré|CRITICAL|Désactiver Telnet"; return ;;
    25)    echo "SMTP — vérifier exposition|MEDIUM|Restreindre aux interfaces internes"; return ;;
    69)    echo "TFTP — pas d'authentification|HIGH|Désactiver TFTP"; return ;;
    80)    echo "HTTP — trafic non chiffré|LOW|Configurer HTTPS"; return ;;
    110)   echo "POP3 — authentification en clair|HIGH|Utiliser POP3S (995)"; return ;;
    135)   echo "RPC Endpoint Mapper|HIGH|Bloquer si inutile"; return ;;
    137|138|139) echo "NetBIOS — vecteur de propagation|HIGH|Désactiver SMB si inutile"; return ;;
    143)   echo "IMAP — authentification en clair|HIGH|Utiliser IMAPS (993)"; return ;;
    389)   echo "LDAP non chiffré|HIGH|Utiliser LDAPS (636)"; return ;;
    443)   echo "HTTPS — chiffré|INFO|"; return ;;
    445)   echo "SMB/CIFS — vecteur de propagation|HIGH|Désactiver le partage SMB"; return ;;
    548)   echo "AFP (Apple Filing Protocol)|MEDIUM|Utiliser SMB ou désactiver"; return ;;
    1433)  echo "MSSQL Server exposé|HIGH|Lier à 127.0.0.1"; return ;;
    1521)  echo "Oracle DB exposé|HIGH|Restreindre l'accès Oracle"; return ;;
    3306)  echo "MySQL/MariaDB exposé|HIGH|bind-address=127.0.0.1"; return ;;
    5432)  echo "PostgreSQL exposé|HIGH|listen_addresses='localhost'"; return ;;
    5900)  echo "VNC — accès graphique non chiffré|HIGH|Désactiver le partage d'écran VNC"; return ;;
    6379)  echo "Redis exposé sans auth|CRITICAL|bind 127.0.0.1 + requirepass"; return ;;
    8080)  echo "HTTP alternatif|LOW|Vérifier HTTPS"; return ;;
    27017) echo "MongoDB exposé|HIGH|bindIp: 127.0.0.1"; return ;;
    *)     echo "Port $p ouvert — vérifier si nécessaire|INFO|"; return ;;
  esac
}

audit_network() {
  local t=0 p=0
  local raw_ports
  raw_ports=$(netstat -antp tcp 2>/dev/null | grep LISTEN || lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null || echo "")

  if [ -z "$raw_ports" ]; then
    ok "NET-000" "network" "Inventaire ports" "netstat/lsof indisponible" "Liste des ports TCP"
    p=$((p+1)); mod_score "network" 1 1; return
  fi

  local seen_ports=""
  while IFS= read -r line; do
    local port_num proc
    # Format lsof : COMMAND PID USER ... TCP *:PORT (LISTEN)
    if echo "$line" | grep -q "TCP.*LISTEN"; then
      port_num=$(echo "$line" | grep -oE ':\d+ \(LISTEN\)' | grep -oE '\d+' | head -1)
      proc=$(echo "$line" | awk '{print $1}')
    else
      # Format netstat
      port_num=$(echo "$line" | awk '{print $4}' | rev | cut -d. -f1 | rev)
      proc=$(echo "$line" | awk '{print $NF}' | grep -oE '[^/]+$')
    fi

    ! echo "$port_num" | grep -qE '^[0-9]+$' && continue
    echo "$seen_ports" | grep -qw "$port_num" && continue
    seen_ports="$seen_ports $port_num"

    local info desc sev rem is_dangerous extra
    info=$(_port_info "$port_num")
    desc=$(echo "$info" | cut -d'|' -f1)
    sev=$(echo "$info" | cut -d'|' -f2)
    rem=$(echo "$info" | cut -d'|' -f3)

    is_dangerous="false"
    for dp in $DANGER_PORTS; do [ "$port_num" = "$dp" ] && is_dangerous="true" && break; done

    extra=""
    [ "$is_dangerous" = "true" ] && extra=" dangerous=\"true\""

    local id; id="NET-$(printf '%04d' "$port_num")"
    t=$((t+1))

    if [ "$sev" = "INFO" ] || [ "$sev" = "LOW" ]; then
      _finding "$id" "network" "$sev" "PASS" \
        "Port $port_num/tcp — $desc" "LISTEN" "LISTEN" "$rem" \
        "Processus: ${proc:-inconnu}" "$extra"
      p=$((p+1))
    else
      _finding "$id" "network" "$sev" "FAIL" \
        "Port $port_num/tcp DANGEREUX — $desc" "LISTEN" "Fermé ou filtré" "$rem" \
        "Processus: ${proc:-inconnu}" "$extra"
    fi
  done <<< "$raw_ports"

  mod_score "network" "$t" "$p"
}

# ── MISES À JOUR ──────────────────────────────────────────────────────────────

audit_updates() {
  local t=0 p=0
  t=$((t+1))
  local upd
  upd=$(softwareupdate -l 2>/dev/null | grep -c "^\s*\*" || echo "0")
  if [ "$upd" = "0" ]; then
    ok "UPD-001" "updates" "Mises à jour macOS" "Système à jour" "État des mises à jour système"; p=$((p+1))
  else
    warn "UPD-001" "updates" "MEDIUM" "Mises à jour macOS disponibles" \
      "$upd mise(s) à jour disponible(s)" "0 (à jour)" \
      "Aller dans Réglages système → Général → Mise à jour logicielle  OU  softwareupdate --install --all" \
      "Exposition aux CVE connues"
  fi
  mod_score "updates" "$t" "$p"
}

# ── COMPTES UTILISATEURS ──────────────────────────────────────────────────────

audit_users() {
  local t=0 p=0

  # Utilisateurs avec accès admin
  t=$((t+1))
  local admins
  admins=$(dscl . -read /Groups/admin GroupMembership 2>/dev/null | sed 's/GroupMembership: //' | tr ' ' ',')
  ok "USR-001" "users" "Administrateurs locaux" "${admins:-aucun}" "Inventaire des comptes administrateurs"; p=$((p+1))

  # Invité
  t=$((t+1))
  local guest_enabled
  guest_enabled=$(defaults read /Library/Preferences/com.apple.loginwindow GuestEnabled 2>/dev/null || echo "0")
  if [ "$guest_enabled" = "0" ]; then
    ok "USR-002" "users" "Compte Invité" "Désactivé" "Connexion invité macOS"; p=$((p+1))
  else
    warn "USR-002" "users" "MEDIUM" "Compte Invité activé" "Activé" "Désactivé" \
      "Préférences Système → Utilisateurs → Désactiver l'accès Invité" \
      "Accès anonyme à l'interface graphique"
  fi

  # Connexion automatique
  t=$((t+1))
  local autologin
  autologin=$(defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser 2>/dev/null || echo "")
  if [ -z "$autologin" ]; then
    ok "USR-003" "users" "Connexion automatique" "Désactivée" "Session auto sans mot de passe"; p=$((p+1))
  else
    warn "USR-003" "users" "HIGH" "Connexion automatique activée" "$autologin" "Désactivée" \
      "Préférences Système → Utilisateurs → Désactiver la connexion automatique" \
      "Démarrage sans authentification"
  fi

  mod_score "users" "$t" "$p"
}

# ── SCORE GLOBAL ──────────────────────────────────────────────────────────────

compute_score() {
  local ded=$(( CRIT*15 + HIGH_C*8 + MED*3 + LOW*1 ))
  SCORE=$(( 100 - ded ))
  [ "$SCORE" -lt 0 ] && SCORE=0
  [ "$SCORE" -gt 100 ] && SCORE=100
  if   [ "$SCORE" -ge 90 ]; then GRADE="A"
  elif [ "$SCORE" -ge 75 ]; then GRADE="B"
  elif [ "$SCORE" -ge 60 ]; then GRADE="C"
  elif [ "$SCORE" -ge 40 ]; then GRADE="D"
  else GRADE="F"; fi
}

# ── GÉNÉRATION XML ────────────────────────────────────────────────────────────

generate_xml() {
  cat > "$OUTFILE" <<XMLEOF
<?xml version="1.0" encoding="UTF-8"?>
<PetrixAuditReport Referential="ANSSI-BP-028" AgentVersion="1.0.0">
  <Metadata>
    <Hostname>$(xml_esc "$HOSTNAME_VAL")</Hostname>
    <OS>$(xml_esc "$OS_NAME")</OS>
    <OSType>macos</OSType>
    <Architecture>$(xml_esc "$ARCH")</Architecture>
    <GenerationDate>$DATE</GenerationDate>
  </Metadata>
  <Scores>
    <GlobalScore>$SCORE</GlobalScore>
    <GlobalGrade>$GRADE</GlobalGrade>
    <TotalChecks>$TOTAL</TotalChecks>
    <PassedChecks>$PASSED</PassedChecks>
    <CriticalCount>$CRIT</CriticalCount>
    <HighCount>$HIGH_C</HighCount>
    <MediumCount>$MED</MediumCount>
    <LowCount>$LOW</LowCount>
    <ModuleScores>
$(printf '%b' "$MODULE_SCORES")
    </ModuleScores>
  </Scores>
  <Findings>$FINDINGS_XML
  </Findings>
</PetrixAuditReport>
XMLEOF
}

# ── UPLOAD ────────────────────────────────────────────────────────────────────

upload_xml() {
  [ -z "$PETRIX_URL" ] && return
  echo ""
  printf "→ Upload vers %s ... " "$PETRIX_URL"
  if curl -sf -X POST "${PETRIX_URL}/api/v1/hardening/import-xml" \
       -H "Accept: application/json" \
       -F "file=@${OUTFILE}" > /dev/null 2>&1; then
    echo "OK"
  else
    echo "ERREUR (vérifier URL et connectivité)"
  fi
}

# ── MAIN ──────────────────────────────────────────────────────────────────────

main() {
  echo "════════════════════════════════════════════════════════════════"
  echo "  Petrix Audit Agent 1.0 — macOS — ANSSI-BP-028"
  echo "  Hôte : $HOSTNAME_VAL"
  echo "  OS   : $OS_NAME ($ARCH)"
  echo "════════════════════════════════════════════════════════════════"

  [ "$(id -u)" -ne 0 ] && { echo "ERREUR : Exécuter en root (sudo bash $0)"; exit 1; }

  echo "[1/8] SSH configuration..."           && audit_ssh
  echo "[2/8] System Integrity Protection..."  && audit_sip
  echo "[3/8] FileVault..."                   && audit_filevault
  echo "[4/8] Pare-feu macOS..."              && audit_firewall
  echo "[5/8] Services de partage..."          && audit_sharing
  echo "[6/8] Ports réseau..."                && audit_network
  echo "[7/8] Mises à jour..."                && audit_updates
  echo "[8/8] Comptes utilisateurs..."         && audit_users

  compute_score
  generate_xml
  # Rendre le fichier accessible à l'utilisateur réel (pas root)
  _REAL_USER="${SUDO_USER:-$(stat -f '%Su' "$(pwd)" 2>/dev/null)}"
  [ -n "$_REAL_USER" ] && [ "$_REAL_USER" != "root" ] && chown "$_REAL_USER" "$OUTFILE" 2>/dev/null || true

  local failed=$((TOTAL - PASSED))
  echo ""
  echo "════════════════════════════════════════════════════════════════"
  printf "  Score : %d/100  Grade : %s\n" "$SCORE" "$GRADE"
  printf "  Checks : %d total | %d OK | %d échecs\n" "$TOTAL" "$PASSED" "$failed"
  printf "  CRITICAL:%d  HIGH:%d  MEDIUM:%d  LOW:%d\n" "$CRIT" "$HIGH_C" "$MED" "$LOW"
  echo "  Rapport : $OUTFILE"
  echo "════════════════════════════════════════════════════════════════"

  upload_xml
}

main
