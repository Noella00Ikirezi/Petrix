#!/usr/bin/env bash
# ==============================================================================
# Petrix Audit Agent — Linux (ANSSI-BP-028 v2.0)
# 14 modules — ~110 checks
#
# Usage :
#   sudo bash petrix_agent_linux.sh
#   sudo bash petrix_agent_linux.sh http://PETRIX_URL
#   sudo OUTFILE=/tmp/mon_audit.xml bash petrix_agent_linux.sh
# ==============================================================================
set -u

PETRIX_URL="${1:-}"
HOSTNAME_VAL=$(hostname -f 2>/dev/null || hostname)
OS_NAME=$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s)
ARCH=$(uname -m)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

_FNAME="petrix_audit_${HOSTNAME_VAL}_$(date +%Y%m%d_%H%M%S).xml"
OUTFILE="${OUTFILE:-$(pwd)/${_FNAME}}"

TOTAL=0; PASSED=0; CRIT=0; HIGH_C=0; MED=0; LOW=0
FINDINGS_XML=""; MODULE_SCORES=""

# ── Helpers ───────────────────────────────────────────────────────────────────

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

ok()   { _finding "$1" "$2" "INFO"  "PASS" "$3" "$4" "$4"  ""   "$5" ""; }
warn() { _finding "$1" "$2" "$3" "FAIL" "$4" "$5" "$6" "$7" "$8" ""; }

sshd_val() {
  local d="$1" def="${2:-}"
  local v
  v=$(sshd -T 2>/dev/null | grep -i "^${d,,} " | awk '{print $2}' | head -1)
  [ -z "$v" ] && v=$(grep -iE "^[[:space:]]*${d}[[:space:]]" /etc/ssh/sshd_config 2>/dev/null | tail -1 | awk '{print $2}')
  echo "${v:-$def}"
}

sysctl_val() { sysctl -n "$1" 2>/dev/null || echo ""; }

mod_score() {
  local name="$1" t="$2" p="$3"
  local sc=0; [ "$t" -gt 0 ] && sc=$(( p * 100 / t ))
  MODULE_SCORES="${MODULE_SCORES}      <Module name=\"$(xml_esc "$name")\" score=\"$sc\" />\n"
}

logindef_val() {
  grep -E "^${1}[[:space:]]" /etc/login.defs 2>/dev/null | awk '{print $2}' | tail -1
}

fperm()  { stat -c '%a' "$1" 2>/dev/null || echo ""; }
fowner() { stat -c '%U' "$1" 2>/dev/null || echo ""; }

# ── [1] SSH ───────────────────────────────────────────────────────────────────

audit_ssh() {
  local t=0 p=0

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

  ssh_chk "SSH-001" "PermitRootLogin"         "no"  "HIGH"     "Connexion root SSH directe"               "echo 'PermitRootLogin no' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-002" "PasswordAuthentication"  "no"  "HIGH"     "Auth par mot de passe SSH"                "echo 'PasswordAuthentication no' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-003" "PermitEmptyPasswords"    "no"  "CRITICAL" "Mots de passe vides SSH autorisés"        "echo 'PermitEmptyPasswords no' >> /etc/ssh/sshd_config && systemctl restart sshd" "no"
  ssh_chk "SSH-004" "X11Forwarding"           "no"  "MEDIUM"   "X11 Forwarding activé"                   "echo 'X11Forwarding no' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-005" "AllowAgentForwarding"    "no"  "MEDIUM"   "Agent forwarding SSH"                    "echo 'AllowAgentForwarding no' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-006" "AllowTcpForwarding"      "no"  "MEDIUM"   "TCP forwarding — tunneling non contrôlé" "echo 'AllowTcpForwarding no' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-007" "UsePAM"                  "yes" "MEDIUM"   "PAM désactivé pour SSH"                  "echo 'UsePAM yes' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-009" "StrictModes"             "yes" "MEDIUM"   "StrictModes désactivé"                   "echo 'StrictModes yes' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-012" "IgnoreRhosts"            "yes" "HIGH"     "Auth rhosts activée"                     "echo 'IgnoreRhosts yes' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"
  ssh_chk "SSH-013" "HostbasedAuthentication" "no"  "HIGH"     "Auth basée sur l'hôte"                   "echo 'HostbasedAuthentication no' >> /etc/ssh/sshd_config && systemctl restart sshd" "no"
  ssh_chk "SSH-018" "PermitUserEnvironment"   "no"  "MEDIUM"   "Variables env user via SSH"              "echo 'PermitUserEnvironment no' >> /etc/ssh/sshd_config && systemctl restart sshd" "no"
  ssh_chk "SSH-019" "PrintLastLog"            "yes" "LOW"      "Dernier login non affiché"               "echo 'PrintLastLog yes' >> /etc/ssh/sshd_config && systemctl restart sshd" "yes"

  # MaxAuthTries
  t=$((t+1))
  local mt; mt=$(sshd_val "MaxAuthTries" "6")
  if [ "${mt:-6}" -le 4 ] 2>/dev/null; then
    ok "SSH-015" "ssh" "MaxAuthTries" "$mt" "Limite tentatives SSH"; p=$((p+1))
  else
    warn "SSH-015" "ssh" "MEDIUM" "MaxAuthTries" "${mt:-6}" "<= 4" \
      "sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 4/' /etc/ssh/sshd_config && systemctl restart sshd" \
      "Trop de tentatives d'auth autorisées"
  fi

  # LoginGraceTime
  t=$((t+1))
  local lgt; lgt=$(sshd_val "LoginGraceTime" "120")
  if [ "${lgt:-120}" -le 60 ] 2>/dev/null; then
    ok "SSH-008" "ssh" "LoginGraceTime" "${lgt}s" "Délai d'auth SSH"; p=$((p+1))
  else
    warn "SSH-008" "ssh" "MEDIUM" "LoginGraceTime" "${lgt:-120}s" "<= 60s" \
      "echo 'LoginGraceTime 60' >> /etc/ssh/sshd_config && systemctl restart sshd" \
      "Délai d'auth trop long — exposition aux attaques"
  fi

  # ClientAliveInterval
  t=$((t+1))
  local ci; ci=$(sshd_val "ClientAliveInterval" "0")
  if [ "${ci:-0}" -gt 0 ] && [ "${ci:-0}" -le 300 ] 2>/dev/null; then
    ok "SSH-016" "ssh" "ClientAliveInterval" "${ci}s" "Timeout session SSH"; p=$((p+1))
  else
    warn "SSH-016" "ssh" "MEDIUM" "ClientAliveInterval" "${ci:-0} (désactivé)" "<= 300s" \
      "echo 'ClientAliveInterval 300' >> /etc/ssh/sshd_config && systemctl restart sshd" \
      "Sessions inactives non terminées"
  fi

  # ClientAliveCountMax
  t=$((t+1))
  local cc; cc=$(sshd_val "ClientAliveCountMax" "3")
  if [ "${cc:-3}" -le 3 ] 2>/dev/null; then
    ok "SSH-017" "ssh" "ClientAliveCountMax" "$cc" "Keep-alive SSH max"; p=$((p+1))
  else
    warn "SSH-017" "ssh" "LOW" "ClientAliveCountMax" "${cc:-3}" "<= 3" \
      "echo 'ClientAliveCountMax 3' >> /etc/ssh/sshd_config && systemctl restart sshd" \
      "Déconnexion tardive des sessions mortes"
  fi

  # Banner
  t=$((t+1))
  local banner; banner=$(sshd_val "Banner" "none")
  if [ -n "$banner" ] && [ "$banner" != "none" ] && [ -f "$banner" ] 2>/dev/null; then
    ok "SSH-011" "ssh" "Banner SSH" "$banner" "Bannière légale d'avertissement"; p=$((p+1))
  else
    warn "SSH-011" "ssh" "LOW" "Banner SSH" "${banner:-non configurée}" "/etc/issue.net" \
      "echo 'Acces reserve aux utilisateurs autorises' > /etc/issue.net && echo 'Banner /etc/issue.net' >> /etc/ssh/sshd_config && systemctl restart sshd" \
      "Pas de bannière d'avertissement légale"
  fi

  # Version OpenSSH
  t=$((t+1))
  local sshver; sshver=$(ssh -V 2>&1 | head -1)
  ok "SSH-023" "ssh" "OpenSSH version" "$sshver" "Version OpenSSH installée"; p=$((p+1))

  mod_score "ssh" "$t" "$p"
}

# ── [2] KERNEL ────────────────────────────────────────────────────────────────

audit_kernel() {
  local t=0 p=0

  kchk() {
    local id="$1" param="$2" exp="$3" sev="$4" desc="$5"
    local val; val=$(sysctl_val "$param")
    t=$((t+1))
    if [ "$val" = "$exp" ]; then
      ok "$id" "kernel" "$param" "$val" "$desc"; p=$((p+1))
    else
      warn "$id" "kernel" "$sev" "$param" "${val:-non défini}" "$exp" \
        "sysctl -w $param=$exp && echo '$param = $exp' >> /etc/sysctl.d/99-petrix.conf" "$desc"
    fi
  }

  kchk "KRN-001" "kernel.randomize_va_space"                 "2" "HIGH"   "ASLR — protection ret2libc"
  kchk "KRN-002" "net.ipv4.tcp_syncookies"                    "1" "HIGH"   "SYN cookies — anti-SYN flood"
  kchk "KRN-003" "net.ipv4.ip_forward"                        "0" "HIGH"   "IP forwarding — routage non désiré"
  kchk "KRN-004" "net.ipv4.conf.all.send_redirects"           "0" "MEDIUM" "Envoi redirections ICMP (all)"
  kchk "KRN-005" "net.ipv4.conf.all.accept_redirects"         "0" "MEDIUM" "Acceptation redirections ICMP (all)"
  kchk "KRN-006" "net.ipv4.conf.all.accept_source_route"      "0" "MEDIUM" "Source routing (all)"
  kchk "KRN-007" "net.ipv4.conf.all.log_martians"             "1" "LOW"    "Paquets martians non loggés"
  kchk "KRN-008" "kernel.dmesg_restrict"                      "1" "MEDIUM" "dmesg accessible aux non-root"
  kchk "KRN-009" "kernel.kptr_restrict"                       "2" "MEDIUM" "Adresses noyau exposées"
  kchk "KRN-010" "fs.suid_dumpable"                           "0" "MEDIUM" "Core dumps SUID autorisés"
  kchk "KRN-011" "net.ipv6.conf.all.accept_ra"                "0" "LOW"    "Router Advertisements IPv6"
  kchk "KRN-012" "kernel.yama.ptrace_scope"                   "1" "MEDIUM" "ptrace non restreint"
  kchk "KRN-013" "net.ipv4.conf.default.accept_redirects"     "0" "MEDIUM" "Acceptation redirections ICMP (default)"
  kchk "KRN-014" "net.ipv4.conf.default.send_redirects"       "0" "MEDIUM" "Envoi redirections ICMP (default)"
  kchk "KRN-015" "net.ipv6.conf.all.forwarding"               "0" "LOW"    "IPv6 forwarding"
  kchk "KRN-016" "net.ipv4.conf.all.rp_filter"                "1" "MEDIUM" "Reverse Path Filtering désactivé"
  kchk "KRN-017" "net.ipv4.icmp_echo_ignore_broadcasts"       "1" "LOW"    "Réponse broadcasts ICMP (Smurf)"
  kchk "KRN-018" "net.ipv4.icmp_ignore_bogus_error_responses" "1" "LOW"    "Réponses ICMP bogus"
  kchk "KRN-019" "kernel.sysrq"                               "0" "MEDIUM" "Magic SysRq — commandes noyau directes"
  kchk "KRN-020" "kernel.core_uses_pid"                       "1" "LOW"    "Nom des core dumps sans PID"

  mod_score "kernel" "$t" "$p"
}

# ── [3] USERS ─────────────────────────────────────────────────────────────────

audit_users() {
  local t=0 p=0

  t=$((t+1))
  local uid0; uid0=$(awk -F: '($3==0 && $1!="root"){print $1}' /etc/passwd 2>/dev/null | tr '\n' ',' | sed 's/,$//')
  if [ -z "$uid0" ]; then
    ok "USR-001" "users" "Comptes UID 0" "root uniquement" "Comptes avec privilèges root"; p=$((p+1))
  else
    warn "USR-001" "users" "CRITICAL" "Comptes UID 0 non-root" "$uid0" "root uniquement" \
      "Corriger les UID dupliqués dans /etc/passwd" "Comptes root supplémentaires"
  fi

  t=$((t+1))
  local epw; epw=$(awk -F: '($2=="" || $2=="!!" || $2=="!"){print $1}' /etc/shadow 2>/dev/null | tr '\n' ',' | sed 's/,$//')
  if [ -z "$epw" ]; then
    ok "USR-002" "users" "Mots de passe vides" "Aucun" "Comptes sans mot de passe"; p=$((p+1))
  else
    warn "USR-002" "users" "CRITICAL" "Comptes sans mot de passe" "$epw" "Aucun" \
      "passwd <utilisateur> pour chaque compte" "Comptes sans authentification"
  fi

  t=$((t+1))
  local nopw; nopw=$(grep -rh "NOPASSWD" /etc/sudoers /etc/sudoers.d/ 2>/dev/null | grep -v "^#" | head -3 | tr '\n' ';')
  if [ -z "$nopw" ]; then
    ok "USR-003" "users" "NOPASSWD sudo" "Aucune règle" "Sudo sans mot de passe"; p=$((p+1))
  else
    warn "USR-003" "users" "HIGH" "Sudo NOPASSWD" "$nopw" "Aucune règle NOPASSWD" \
      "Éditer /etc/sudoers et supprimer les règles NOPASSWD" "Élévation sans authentification"
  fi

  t=$((t+1))
  local shellac; shellac=$(awk -F: '($7!="/sbin/nologin"&&$7!="/bin/false"&&$7!=""&&$3>=1000){print $1}' /etc/passwd 2>/dev/null | tr '\n' ',' | sed 's/,$//')
  ok "USR-004" "users" "Comptes avec shell" "${shellac:-aucun}" "Inventaire comptes accès shell"; p=$((p+1))

  # PASS_MAX_DAYS
  t=$((t+1))
  local pmax; pmax=$(logindef_val "PASS_MAX_DAYS")
  if [ -n "$pmax" ] && [ "$pmax" -le 90 ] 2>/dev/null; then
    ok "USR-005" "users" "PASS_MAX_DAYS" "$pmax jours" "Expiration max des mots de passe"; p=$((p+1))
  else
    warn "USR-005" "users" "MEDIUM" "PASS_MAX_DAYS" "${pmax:-non défini}" "<= 90 jours" \
      "sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/' /etc/login.defs" \
      "Mots de passe sans expiration — ANSSI: 90 jours max"
  fi

  # PASS_MIN_DAYS
  t=$((t+1))
  local pmin; pmin=$(logindef_val "PASS_MIN_DAYS")
  if [ -n "$pmin" ] && [ "$pmin" -ge 1 ] 2>/dev/null; then
    ok "USR-006" "users" "PASS_MIN_DAYS" "$pmin jour(s)" "Durée min avant changement mdp"; p=$((p+1))
  else
    warn "USR-006" "users" "MEDIUM" "PASS_MIN_DAYS" "${pmin:-0}" ">= 1 jour" \
      "sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS\t1/' /etc/login.defs" \
      "Changement immédiat possible — contournement historique"
  fi

  # PASS_WARN_AGE
  t=$((t+1))
  local pwarn; pwarn=$(logindef_val "PASS_WARN_AGE")
  if [ -n "$pwarn" ] && [ "$pwarn" -ge 7 ] 2>/dev/null; then
    ok "USR-007" "users" "PASS_WARN_AGE" "$pwarn jours" "Avertissement expiration mdp"; p=$((p+1))
  else
    warn "USR-007" "users" "LOW" "PASS_WARN_AGE" "${pwarn:-0}" ">= 7 jours" \
      "sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE\t7/' /etc/login.defs" \
      "Utilisateurs non avertis de l'expiration"
  fi

  # UMASK
  t=$((t+1))
  local umask_val; umask_val=$(grep -E "^UMASK" /etc/login.defs 2>/dev/null | awk '{print $2}' | head -1)
  if [ "$umask_val" = "027" ] || [ "$umask_val" = "077" ]; then
    ok "USR-009" "users" "UMASK système" "$umask_val" "Masque de création de fichiers restrictif"; p=$((p+1))
  else
    warn "USR-009" "users" "MEDIUM" "UMASK système" "${umask_val:-022}" "027 ou 077" \
      "sed -i 's/^UMASK.*/UMASK\t\t027/' /etc/login.defs" \
      "Fichiers créés trop permissifs par défaut"
  fi

  # PATH root sans "."
  t=$((t+1))
  local root_path_check; root_path_check=$(grep -hE "^PATH=|^export PATH=" /root/.bashrc /root/.bash_profile /etc/profile 2>/dev/null | head -3)
  if echo "${root_path_check}${PATH:-}" | tr ':' '\n' | grep -qx '\.'; then
    warn "USR-010" "users" "HIGH" "PATH root contient '.'" ".(point) présent" "Pas de '.' dans PATH" \
      "Supprimer '.' du PATH dans /root/.bashrc et /etc/profile" \
      "Exécution d'un binaire malveillant dans le dossier courant possible"
  else
    ok "USR-010" "users" "PATH root" "Sans '.'" "PATH root sans répertoire courant"; p=$((p+1))
  fi

  # /etc/cron.allow
  t=$((t+1))
  if [ -f /etc/cron.allow ]; then
    ok "USR-011" "users" "/etc/cron.allow" "Présent" "Restriction d'accès à cron"; p=$((p+1))
  else
    warn "USR-011" "users" "MEDIUM" "/etc/cron.allow" "Absent" "Présent" \
      "touch /etc/cron.allow && chmod 640 /etc/cron.allow" \
      "Tout utilisateur peut planifier des tâches cron"
  fi

  # /etc/at.allow
  t=$((t+1))
  if [ -f /etc/at.allow ]; then
    ok "USR-012" "users" "/etc/at.allow" "Présent" "Restriction d'accès à at"; p=$((p+1))
  else
    warn "USR-012" "users" "LOW" "/etc/at.allow" "Absent" "Présent" \
      "touch /etc/at.allow && chmod 640 /etc/at.allow" \
      "Tout utilisateur peut planifier des tâches via at"
  fi

  mod_score "users" "$t" "$p"
}

# ── [4] PAM ───────────────────────────────────────────────────────────────────

audit_pam() {
  local t=0 p=0
  local pwq_conf="/etc/security/pwquality.conf"
  local pam_pass_files="/etc/pam.d/common-password /etc/pam.d/password-auth /etc/pam.d/system-auth"
  local pam_auth_files="/etc/pam.d/common-auth /etc/pam.d/password-auth /etc/pam.d/system-auth"

  # pam_pwquality présent
  t=$((t+1))
  if grep -qE "pam_pwquality|pam_cracklib" $pam_pass_files 2>/dev/null; then
    ok "PAM-001" "pam" "pam_pwquality" "Configuré" "Politique de complexité des mots de passe"; p=$((p+1))
  else
    warn "PAM-001" "pam" "HIGH" "pam_pwquality" "Non configuré" "Dans /etc/pam.d/common-password" \
      "apt-get install -y libpam-pwquality  OU  dnf install -y libpwquality" \
      "Aucune politique de complexité de mot de passe"
  fi

  # minlen >= 12
  t=$((t+1))
  local minlen; minlen=$(grep -E "^minlen" "$pwq_conf" 2>/dev/null | grep -oE "[0-9]+" | head -1)
  if [ -n "$minlen" ] && [ "$minlen" -ge 12 ] 2>/dev/null; then
    ok "PAM-002" "pam" "minlen" "$minlen caractères" "Longueur minimum des mots de passe"; p=$((p+1))
  else
    warn "PAM-002" "pam" "HIGH" "minlen" "${minlen:-non défini}" ">= 12 caractères" \
      "echo 'minlen = 12' >> /etc/security/pwquality.conf" \
      "Mots de passe trop courts autorisés"
  fi

  # dcredit — au moins 1 chiffre requis
  t=$((t+1))
  local dcred; dcred=$(grep -E "^dcredit" "$pwq_conf" 2>/dev/null | grep -oE "\-?[0-9]+" | head -1)
  if [ -n "$dcred" ] && [ "$dcred" -le -1 ] 2>/dev/null; then
    ok "PAM-003" "pam" "dcredit" "$dcred (chiffre requis)" "Exigence de chiffre dans le mdp"; p=$((p+1))
  else
    warn "PAM-003" "pam" "MEDIUM" "dcredit (chiffres)" "${dcred:-non défini}" "<= -1 (au moins 1 chiffre)" \
      "echo 'dcredit = -1' >> /etc/security/pwquality.conf" \
      "Pas de chiffre requis dans les mots de passe"
  fi

  # Historique mots de passe
  t=$((t+1))
  local remember; remember=$(grep -hE "remember=" $pam_pass_files 2>/dev/null | grep -oE "remember=[0-9]+" | cut -d= -f2 | tail -1)
  if [ -n "$remember" ] && [ "$remember" -ge 5 ] 2>/dev/null; then
    ok "PAM-004" "pam" "Historique mdp" "$remember anciens" "Prévention réutilisation de mots de passe"; p=$((p+1))
  else
    warn "PAM-004" "pam" "MEDIUM" "Historique mdp (remember)" "${remember:-0}" ">= 5 anciens" \
      "Ajouter 'remember=5' à pam_pwhistory dans /etc/pam.d/common-password" \
      "Réutilisation des anciens mots de passe possible"
  fi

  # pam_faillock / pam_tally2 — verrouillage compte
  t=$((t+1))
  if grep -qE "pam_faillock|pam_tally2" $pam_auth_files 2>/dev/null; then
    ok "PAM-005" "pam" "pam_faillock" "Configuré" "Verrouillage après échecs d'auth"; p=$((p+1))
  else
    warn "PAM-005" "pam" "HIGH" "pam_faillock" "Non configuré" "Dans /etc/pam.d/common-auth" \
      "Configurer pam_faillock deny=5 unlock_time=900 dans /etc/pam.d/common-auth" \
      "Pas de protection contre la force brute locale"
  fi

  # unlock_time >= 900s
  t=$((t+1))
  local unlock_time; unlock_time=$(grep -hE "unlock_time=" /etc/security/faillock.conf $pam_auth_files 2>/dev/null | grep -oE "unlock_time=[0-9]+" | cut -d= -f2 | tail -1)
  if [ -n "$unlock_time" ] && [ "$unlock_time" -ge 900 ] 2>/dev/null; then
    ok "PAM-006" "pam" "unlock_time" "${unlock_time}s" "Durée de verrouillage après échecs"; p=$((p+1))
  else
    warn "PAM-006" "pam" "MEDIUM" "unlock_time" "${unlock_time:-non défini}" ">= 900s (15 min)" \
      "echo 'unlock_time = 900' >> /etc/security/faillock.conf" \
      "Verrouillage trop court — force brute locale possible"
  fi

  mod_score "pam" "$t" "$p"
}

# ── [5] MONTAGE DES PARTITIONS ────────────────────────────────────────────────

audit_mounts() {
  local t=0 p=0

  mnt_chk() {
    local id="$1" mpoint="$2" opt="$3" sev="$4" desc="$5"
    t=$((t+1))
    local found_opts; found_opts=$(grep -E "^[^ ]+ ${mpoint} " /proc/mounts 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -z "$found_opts" ]; then
      warn "$id" "mounts" "LOW" "$mpoint" "Pas de partition dédiée" "Partition dédiée avec $opt" \
        "Ajouter dans /etc/fstab : tmpfs $mpoint tmpfs defaults,$opt 0 0" "$desc"
      return
    fi
    if echo ",$found_opts," | grep -q ",$opt,"; then
      ok "$id" "mounts" "$mpoint ($opt)" "Présent" "$desc"; p=$((p+1))
    else
      warn "$id" "mounts" "$sev" "$mpoint — $opt manquant" "Option absente" "Présente" \
        "Ajouter $opt dans /etc/fstab pour $mpoint puis : mount -o remount,$opt $mpoint" "$desc"
    fi
  }

  mnt_chk "MNT-001" "/tmp"     "nodev"   "MEDIUM" "/tmp sans nodev — montage de périphériques possible"
  mnt_chk "MNT-002" "/tmp"     "nosuid"  "MEDIUM" "/tmp sans nosuid — binaires setuid exécutables"
  mnt_chk "MNT-003" "/tmp"     "noexec"  "MEDIUM" "/tmp sans noexec — scripts exécutables dans /tmp"
  mnt_chk "MNT-004" "/dev/shm" "nodev"   "HIGH"   "/dev/shm sans nodev"
  mnt_chk "MNT-005" "/dev/shm" "nosuid"  "HIGH"   "/dev/shm sans nosuid"
  mnt_chk "MNT-006" "/dev/shm" "noexec"  "HIGH"   "/dev/shm sans noexec — exécution en mémoire partagée"
  mnt_chk "MNT-007" "/home"    "nodev"   "LOW"    "/home sans nodev"
  mnt_chk "MNT-008" "/var/tmp" "nodev"   "MEDIUM" "/var/tmp sans nodev"
  mnt_chk "MNT-009" "/var/tmp" "nosuid"  "MEDIUM" "/var/tmp sans nosuid"

  mod_score "mounts" "$t" "$p"
}

# ── [6] PERMISSIONS FICHIERS SENSIBLES ───────────────────────────────────────

audit_perms() {
  local t=0 p=0

  pchk() {
    local id="$1" fpath="$2" exp_perm="$3" exp_owner="$4" sev="$5" desc="$6" rem="$7"
    t=$((t+1))
    [ ! -e "$fpath" ] && { ok "$id" "perms" "$fpath" "Absent (non applicable)" "$desc"; p=$((p+1)); return; }
    local perm owner
    perm=$(fperm "$fpath"); owner=$(fowner "$fpath")
    if [ "$perm" = "$exp_perm" ] && [ "$owner" = "$exp_owner" ]; then
      ok "$id" "perms" "$fpath" "$perm ($owner)" "$desc"; p=$((p+1))
    else
      warn "$id" "perms" "$sev" "$fpath" "$perm ($owner)" "$exp_perm ($exp_owner)" "$rem" "$desc"
    fi
  }

  # /etc/shadow — accepte 640 ou 000 (RHEL), propriétaire root
  shadow_chk() {
    local id="$1" fpath="$2" sev="$3" desc="$4" rem="$5"
    t=$((t+1))
    [ ! -e "$fpath" ] && { ok "$id" "perms" "$fpath" "Absent (non applicable)" "$desc"; p=$((p+1)); return; }
    local perm owner
    perm=$(fperm "$fpath"); owner=$(fowner "$fpath")
    local other; other=$(echo "${perm:-777}" | rev | cut -c1)
    if [ "$other" = "0" ] && [ "$owner" = "root" ]; then
      ok "$id" "perms" "$fpath" "$perm ($owner)" "$desc"; p=$((p+1))
    else
      warn "$id" "perms" "$sev" "$fpath" "$perm ($owner)" "max 640, owner root" "$rem" "$desc"
    fi
  }

  pchk    "PERM-001" "/etc/passwd"           "644" "root" "HIGH"   "Permissions /etc/passwd"             "chmod 644 /etc/passwd && chown root:root /etc/passwd"
  shadow_chk "PERM-002" "/etc/shadow"                    "HIGH"   "Permissions /etc/shadow (hashs mdp)" "chmod 640 /etc/shadow && chown root:shadow /etc/shadow"
  shadow_chk "PERM-003" "/etc/gshadow"                   "HIGH"   "Permissions /etc/gshadow"            "chmod 640 /etc/gshadow && chown root:shadow /etc/gshadow"
  pchk    "PERM-004" "/etc/group"            "644" "root" "MEDIUM" "Permissions /etc/group"              "chmod 644 /etc/group && chown root:root /etc/group"
  pchk    "PERM-005" "/etc/sudoers"          "440" "root" "HIGH"   "Permissions /etc/sudoers"            "chmod 440 /etc/sudoers && chown root:root /etc/sudoers"
  pchk    "PERM-007" "/etc/crontab"          "600" "root" "MEDIUM" "Permissions /etc/crontab"            "chmod 600 /etc/crontab && chown root:root /etc/crontab"
  pchk    "PERM-008" "/etc/ssh/sshd_config"  "600" "root" "MEDIUM" "Permissions sshd_config"             "chmod 600 /etc/ssh/sshd_config && chown root:root /etc/ssh/sshd_config"
  pchk    "PERM-009" "/root"                 "700" "root" "HIGH"   "Permissions répertoire /root"        "chmod 700 /root && chown root:root /root"

  # SSH host private keys
  t=$((t+1))
  local bad_keys=""
  for keyfile in /etc/ssh/ssh_host_*_key; do
    [ -f "$keyfile" ] || continue
    local kperm; kperm=$(fperm "$keyfile")
    [ "$kperm" != "600" ] && bad_keys="$bad_keys $keyfile($kperm)"
  done
  if [ -z "$bad_keys" ]; then
    ok "PERM-006" "perms" "Clés SSH host privées" "600 (correct)" "Permissions des clés SSH du serveur"; p=$((p+1))
  else
    warn "PERM-006" "perms" "HIGH" "Clés SSH host privées" "$bad_keys" "600" \
      "chmod 600 /etc/ssh/ssh_host_*_key" "Clés privées SSH lisibles par des non-root"
  fi

  # Fichiers .rhosts / .netrc
  t=$((t+1))
  local rhosts; rhosts=$(find /home /root -name ".rhosts" -o -name ".netrc" 2>/dev/null | head -5 | tr '\n' ';')
  if [ -z "$rhosts" ]; then
    ok "PERM-010" "perms" "Fichiers .rhosts/.netrc" "Aucun" "Absence d'auth faible"; p=$((p+1))
  else
    warn "PERM-010" "perms" "HIGH" "Fichiers .rhosts/.netrc présents" "$rhosts" "Aucun" \
      "rm -f \$(find /home /root -name '.rhosts' -o -name '.netrc')" \
      "Fichiers d'authentification faible détectés"
  fi

  mod_score "perms" "$t" "$p"
}

# ── [7] MAC (AppArmor / SELinux) ──────────────────────────────────────────────

audit_mac() {
  local t=2 p=0

  if command -v aa-status &>/dev/null; then
    local enforce_c; enforce_c=$(aa-status 2>/dev/null | grep "profiles are in enforce mode" | grep -oE "^[0-9]+")
    if [ -n "$enforce_c" ] && [ "$enforce_c" -gt 0 ] 2>/dev/null; then
      ok "MAC-001" "mac" "AppArmor" "$enforce_c profiles enforce" "Contrôle d'accès obligatoire actif"; p=$((p+1))
      ok "MAC-002" "mac" "AppArmor mode" "enforce" "Profiles AppArmor en mode enforce"; p=$((p+1))
    else
      warn "MAC-001" "mac" "HIGH" "AppArmor" "0 profiles enforce" "AppArmor actif avec profiles" \
        "aa-enforce /etc/apparmor.d/*" "Aucun profil AppArmor en mode enforce"
      warn "MAC-002" "mac" "MEDIUM" "AppArmor mode" "complain ou vide" "enforce" \
        "aa-enforce /etc/apparmor.d/*" "Profils non en enforce"
    fi
  elif command -v getenforce &>/dev/null; then
    local selval; selval=$(getenforce 2>/dev/null)
    if [ "${selval,,}" = "enforcing" ]; then
      ok "MAC-001" "mac" "SELinux" "enforcing" "Contrôle d'accès obligatoire actif"; p=$((p+1))
      ok "MAC-002" "mac" "SELinux mode" "enforcing" "SELinux en mode enforcing"; p=$((p+1))
    else
      warn "MAC-001" "mac" "HIGH" "SELinux" "${selval:-désactivé}" "enforcing" \
        "setenforce 1 && sed -i 's/SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config" \
        "SELinux non en mode enforcing"
      warn "MAC-002" "mac" "MEDIUM" "SELinux mode" "${selval:-disabled}" "enforcing" \
        "setenforce 1" "SELinux non enforcing"
    fi
  else
    warn "MAC-001" "mac" "HIGH" "AppArmor/SELinux" "Non détecté" "AppArmor ou SELinux" \
      "apt-get install -y apparmor apparmor-profiles  OU  dnf install -y selinux-policy" \
      "Aucun module MAC détecté"
    warn "MAC-002" "mac" "MEDIUM" "MAC mode" "N/A" "enforce" \
      "Installer et activer AppArmor ou SELinux" "Aucun profil de confinement"
  fi

  mod_score "mac" "$t" "$p"
}

# ── [8] NTP ───────────────────────────────────────────────────────────────────

audit_ntp() {
  local t=0 p=0
  local ntp_svc="aucun"

  t=$((t+1))
  if systemctl is-active --quiet chronyd 2>/dev/null; then
    ntp_svc="chronyd"
  elif systemctl is-active --quiet systemd-timesyncd 2>/dev/null; then
    ntp_svc="systemd-timesyncd"
  elif systemctl is-active --quiet ntpd 2>/dev/null; then
    ntp_svc="ntpd"
  fi

  if [ "$ntp_svc" != "aucun" ]; then
    ok "NTP-001" "ntp" "Service NTP" "$ntp_svc (actif)" "Synchronisation de l'heure — intégrité des logs"; p=$((p+1))
  else
    warn "NTP-001" "ntp" "MEDIUM" "Service NTP" "Aucun actif" "chronyd ou systemd-timesyncd" \
      "dnf install -y chrony && systemctl enable --now chronyd  OU  systemctl enable --now systemd-timesyncd" \
      "Horloge non synchronisée — timestamps logs non fiables"
  fi

  t=$((t+1))
  local ntp_servers=""
  case "$ntp_svc" in
    chronyd)           ntp_servers=$(grep -E "^(server|pool)" /etc/chrony.conf 2>/dev/null | head -2 | tr '\n' ' ') ;;
    systemd-timesyncd) ntp_servers=$(grep "^NTP=" /etc/systemd/timesyncd.conf 2>/dev/null | cut -d= -f2) ;;
    ntpd)              ntp_servers=$(grep "^server" /etc/ntp.conf 2>/dev/null | head -2 | tr '\n' ' ') ;;
  esac
  if [ -n "$ntp_servers" ]; then
    ok "NTP-002" "ntp" "Serveurs NTP" "$ntp_servers" "Serveurs NTP configurés"; p=$((p+1))
  else
    warn "NTP-002" "ntp" "LOW" "Serveurs NTP" "Non configurés" "Au moins 1 serveur" \
      "Ajouter 'server pool.ntp.org iburst' dans /etc/chrony.conf" \
      "Aucun serveur NTP de référence"
  fi

  mod_score "ntp" "$t" "$p"
}

# ── [9] FIREWALL ──────────────────────────────────────────────────────────────

audit_firewall() {
  local t=0 p=0
  t=$((t+1))
  if systemctl is-active --quiet firewalld 2>/dev/null; then
    ok "FW-001" "firewall" "Pare-feu" "firewalld (actif)" "Présence d'un pare-feu"; p=$((p+1))
    t=$((t+1))
    local zones; zones=$(firewall-cmd --get-active-zones 2>/dev/null | grep -v "interfaces" | tr '\n' ',')
    ok "FW-002" "firewall" "Zones firewalld" "${zones:-aucune}" "Configuration par zones"; p=$((p+1))
  elif systemctl is-active --quiet ufw 2>/dev/null; then
    ok "FW-001" "firewall" "Pare-feu" "ufw (actif)" "Présence d'un pare-feu"; p=$((p+1))
    t=$((t+1))
    ok "FW-002" "firewall" "UFW status" "$(ufw status 2>/dev/null | head -1)" "État UFW"; p=$((p+1))
  elif iptables -nL 2>/dev/null | grep -q "Chain"; then
    ok "FW-001" "firewall" "Pare-feu" "iptables (actif)" "Présence d'un pare-feu"; p=$((p+1))
  else
    warn "FW-001" "firewall" "HIGH" "Pare-feu" "Aucun détecté" "firewalld ou ufw actif" \
      "dnf install -y firewalld && systemctl enable --now firewalld" "Aucun pare-feu actif"
  fi
  mod_score "firewall" "$t" "$p"
}

# ── [10] SERVICES DANGEREUX ───────────────────────────────────────────────────

audit_services() {
  local t=0 p=0
  dsvc() {
    local id="$1" svc="$2" desc="$3"
    t=$((t+1))
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
      warn "$id" "services" "HIGH" "Service $svc" "actif" "désactivé/absent" \
        "systemctl stop $svc && systemctl disable $svc" "$desc"
    else
      ok "$id" "services" "Service $svc" "inactif/absent" "$desc"; p=$((p+1))
    fi
  }
  dsvc "SVC-001" "telnet"       "Telnet — protocole non chiffré"
  dsvc "SVC-002" "rsh"          "rsh — authentification faible"
  dsvc "SVC-003" "rlogin"       "rlogin — authentification faible"
  dsvc "SVC-004" "rexec"        "rexec — authentification faible"
  dsvc "SVC-005" "tftp"         "TFTP — pas d'authentification"
  dsvc "SVC-006" "vsftpd"       "FTP en clair (vsftpd)"
  dsvc "SVC-007" "finger"       "finger — exposition d'infos utilisateurs"
  dsvc "SVC-008" "avahi-daemon" "mDNS/Avahi — découverte réseau inutile en prod"
  dsvc "SVC-009" "cups"         "CUPS — serveur d'impression inutile en serveur"
  dsvc "SVC-010" "bluetooth"    "Bluetooth — surface d'attaque inutile en serveur"
  dsvc "SVC-011" "nfs-server"   "NFS — partage réseau non chiffré"
  dsvc "SVC-012" "ypbind"       "NIS/YP — annuaire réseau obsolète et non sécurisé"
  mod_score "services" "$t" "$p"
}

# ── [11] PORTS RÉSEAU ─────────────────────────────────────────────────────────

DANGER_PORTS="21 23 69 110 135 137 138 139 143 389 445 512 513 514 1433 1521 3306 5432 5900 6379 27017"

_port_info() {
  case "$1" in
    21)    echo "FTP — protocole non chiffré|HIGH|systemctl disable vsftpd" ;;
    22)    echo "SSH — port standard|INFO|" ;;
    23)    echo "Telnet — remplacé par SSH|CRITICAL|systemctl stop telnet && systemctl disable telnet" ;;
    25)    echo "SMTP — vérifier exposition externe|MEDIUM|Restreindre aux interfaces internes" ;;
    69)    echo "TFTP — pas d'authentification|HIGH|Désactiver TFTP" ;;
    80)    echo "HTTP — trafic non chiffré|LOW|Configurer HTTPS" ;;
    110)   echo "POP3 — auth en clair|HIGH|Utiliser POP3S (995)" ;;
    135)   echo "RPC Endpoint Mapper|HIGH|Bloquer ou désactiver" ;;
    137|138|139) echo "NetBIOS — vecteur propagation|HIGH|Désactiver si inutile" ;;
    143)   echo "IMAP — auth en clair|HIGH|Utiliser IMAPS (993)" ;;
    389)   echo "LDAP non chiffré|HIGH|Utiliser LDAPS (636)" ;;
    443)   echo "HTTPS — chiffré|INFO|" ;;
    445)   echo "SMB/CIFS — vecteur propagation|HIGH|Bloquer si inutile" ;;
    512)   echo "rexec — auth faible|CRITICAL|Désactiver rexec" ;;
    513)   echo "rlogin — auth faible|CRITICAL|Désactiver rlogin" ;;
    514)   echo "rsh — auth faible|CRITICAL|Désactiver rsh" ;;
    1433)  echo "MSSQL Server exposé|HIGH|Lier à 127.0.0.1" ;;
    1521)  echo "Oracle DB exposé|HIGH|Restreindre accès réseau" ;;
    3306)  echo "MySQL/MariaDB exposé|HIGH|bind-address=127.0.0.1 dans my.cnf" ;;
    5432)  echo "PostgreSQL exposé|HIGH|listen_addresses='localhost'" ;;
    5900)  echo "VNC non chiffré|HIGH|Utiliser un tunnel SSH" ;;
    6379)  echo "Redis exposé sans auth|CRITICAL|bind 127.0.0.1 + requirepass" ;;
    8080)  echo "HTTP alternatif|LOW|Vérifier HTTPS disponible" ;;
    27017) echo "MongoDB exposé|HIGH|bindIp: 127.0.0.1 dans mongod.conf" ;;
    *)     echo "Port $1 ouvert — vérifier si nécessaire|INFO|" ;;
  esac
}

audit_network() {
  local t=0 p=0
  local raw_ports
  raw_ports=$(ss -tlnH 2>/dev/null || netstat -tlnH 2>/dev/null || echo "")

  if [ -z "$raw_ports" ]; then
    ok "NET-000" "network" "Inventaire ports" "ss/netstat indisponible" "Ports TCP en écoute"
    p=$((p+1)); mod_score "network" "$t" "$p"; return
  fi

  local seen_ports=""
  while IFS= read -r line; do
    local addr port_num proc
    addr=$(echo "$line" | awk '{print $4}')
    port_num=$(echo "$addr" | rev | cut -d: -f1 | rev)
    proc=$(echo "$line" | awk '{print $NF}' | sed 's/users:(("\([^"]*\)".*/\1/')
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
    extra=""; [ "$is_dangerous" = "true" ] && extra=" dangerous=\"true\""
    local id; id="NET-$(printf '%04d' "$port_num")"
    t=$((t+1))
    if [ "$sev" = "INFO" ] || [ "$sev" = "LOW" ]; then
      _finding "$id" "network" "$sev" "PASS" "Port $port_num/tcp — $desc" "LISTEN" "LISTEN" "$rem" "Processus: ${proc:-inconnu}" "$extra"
      p=$((p+1))
    else
      _finding "$id" "network" "$sev" "FAIL" "Port $port_num/tcp DANGEREUX — $desc" "LISTEN" "Fermé ou filtré" "$rem" "Processus: ${proc:-inconnu}" "$extra"
    fi
  done <<< "$raw_ports"

  mod_score "network" "$t" "$p"
}

# ── [12] SYSTÈME DE FICHIERS ──────────────────────────────────────────────────

audit_filesystem() {
  local t=0 p=0

  # Fichiers setuid/setgid
  t=$((t+1))
  local suid_c; suid_c=$(find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "${suid_c:-0}" -le 25 ]; then
    ok "FS-001" "filesystem" "Fichiers setuid/setgid" "$suid_c fichiers" "Binaires avec élévation de privilèges"; p=$((p+1))
  else
    warn "FS-001" "filesystem" "MEDIUM" "Fichiers setuid/setgid" "$suid_c fichiers" "<= 25" \
      "find / -xdev -perm -4000 -type f -exec ls -la {} \\;" "Nombre élevé de binaires setuid"
  fi

  # /tmp sticky bit
  t=$((t+1))
  if stat -c '%a' /tmp 2>/dev/null | grep -qE '^[0-9]{3}[1-9]$' || ls -lad /tmp 2>/dev/null | grep -q "^d.*.t"; then
    ok "FS-002" "filesystem" "/tmp sticky bit" "Activé" "Protection suppression inter-utilisateurs"; p=$((p+1))
  else
    warn "FS-002" "filesystem" "MEDIUM" "/tmp sticky bit" "Absent" "Activé" "chmod +t /tmp" \
      "Suppression de fichiers /tmp inter-utilisateurs possible"
  fi

  # Répertoires world-writable hors /tmp /var/tmp
  t=$((t+1))
  local ww; ww=$(find / -xdev -type d -perm -0002 ! -path "/tmp" ! -path "/var/tmp" \
    ! -path "/proc/*" ! -path "/sys/*" 2>/dev/null | head -5 | tr '\n' ';')
  if [ -z "$ww" ]; then
    ok "FS-003" "filesystem" "Répertoires world-writable" "Aucun hors /tmp" "Permissions des répertoires"; p=$((p+1))
  else
    warn "FS-003" "filesystem" "MEDIUM" "Répertoires world-writable" "$ww" "Aucun hors /tmp /var/tmp" \
      "chmod o-w sur chaque répertoire listé" "Répertoires accessibles en écriture par tous"
  fi

  # Fichiers sans propriétaire
  t=$((t+1))
  local noown; noown=$(find / -xdev \( -nouser -o -nogroup \) ! -path "/proc/*" 2>/dev/null | head -5 | tr '\n' ';')
  if [ -z "$noown" ]; then
    ok "FS-006" "filesystem" "Fichiers sans propriétaire" "Aucun" "Fichiers orphelins"; p=$((p+1))
  else
    warn "FS-006" "filesystem" "MEDIUM" "Fichiers sans propriétaire" "$noown" "Aucun" \
      "Assigner un propriétaire valide ou supprimer ces fichiers" "Fichiers orphelins — risque d'élévation de privilèges"
  fi

  mod_score "filesystem" "$t" "$p"
}

# ── [13] PAQUETS ──────────────────────────────────────────────────────────────

audit_packages() {
  local t=0 p=0
  t=$((t+1))
  local updates="?"
  if command -v dnf &>/dev/null; then
    updates=$(dnf check-update -q 2>/dev/null | grep -cE "^[a-zA-Z]" || echo "0")
  elif command -v apt-get &>/dev/null; then
    apt-get -qq update 2>/dev/null; updates=$(apt-get -s upgrade 2>/dev/null | grep -c "^Inst" || echo "0")
  elif command -v yum &>/dev/null; then
    updates=$(yum check-update -q 2>/dev/null | grep -cE "^[a-zA-Z]" || echo "0")
  fi

  if [ "$updates" = "0" ]; then
    ok "PKG-001" "packages" "Mises à jour" "Système à jour" "État des paquets"; p=$((p+1))
  elif [ "$updates" = "?" ]; then
    ok "PKG-001" "packages" "Mises à jour" "Gestionnaire non détecté" "État des paquets"; p=$((p+1))
  else
    warn "PKG-001" "packages" "MEDIUM" "Mises à jour disponibles" "$updates paquet(s)" "0 (à jour)" \
      "dnf update -y  OU  apt-get upgrade -y" "Paquets non à jour — exposition aux CVE"
  fi

  for pkg in telnet rsh-client rlogin xinetd nis; do
    t=$((t+1))
    if rpm -q "$pkg" &>/dev/null || dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
      warn "PKG-$(echo "$pkg" | tr '[:lower:]' '[:upper:]')" "packages" "MEDIUM" \
        "Paquet $pkg installé" "installé" "supprimé" \
        "dnf remove -y $pkg  OU  apt-get remove -y $pkg" "Paquet inutile en production"
    else
      ok "PKG-$(echo "$pkg" | tr '[:lower:]' '[:upper:]')" "packages" "Paquet $pkg" \
        "non installé" "Absence de paquet inutile"; p=$((p+1))
    fi
  done

  mod_score "packages" "$t" "$p"
}

# ── [14] JOURNALISATION ───────────────────────────────────────────────────────

audit_logging() {
  local t=0 p=0

  t=$((t+1))
  if systemctl is-active --quiet rsyslog 2>/dev/null || systemctl is-active --quiet syslog 2>/dev/null; then
    ok "LOG-001" "logging" "Syslog" "actif (rsyslog)" "Journalisation système"; p=$((p+1))
  else
    warn "LOG-001" "logging" "HIGH" "Syslog" "inactif" "rsyslog ou syslog actif" \
      "dnf install -y rsyslog && systemctl enable --now rsyslog" "Journalisation système absente"
  fi

  t=$((t+1))
  if systemctl is-active --quiet auditd 2>/dev/null; then
    ok "LOG-002" "logging" "Auditd" "actif" "Framework d'audit Linux"; p=$((p+1))
  else
    warn "LOG-002" "logging" "MEDIUM" "Auditd" "inactif" "actif" \
      "dnf install -y audit && systemctl enable --now auditd" "Audit syscall désactivé"
  fi

  # Persistance journald
  t=$((t+1))
  local storage; storage=$(grep -E "^Storage=" /etc/systemd/journald.conf 2>/dev/null | cut -d= -f2)
  if [ "${storage:-}" = "persistent" ]; then
    ok "LOG-003" "logging" "Journald persistant" "persistent" "Logs conservés après redémarrage"; p=$((p+1))
  else
    warn "LOG-003" "logging" "LOW" "Journald Storage" "${storage:-auto}" "persistent" \
      "sed -i 's/^#*Storage=.*/Storage=persistent/' /etc/systemd/journald.conf && systemctl restart systemd-journald" \
      "Logs perdus au redémarrage"
  fi

  # Règles auditd sur /etc/passwd et /etc/shadow
  t=$((t+1))
  if auditctl -l 2>/dev/null | grep -qE "/etc/passwd|/etc/shadow"; then
    ok "LOG-004" "logging" "Règles auditd" "Surveillance /etc/passwd+shadow" "Traçabilité des modifications de comptes"; p=$((p+1))
  else
    warn "LOG-004" "logging" "MEDIUM" "Règles auditd" "Pas de surveillance /etc/passwd ou /etc/shadow" "Règles configurées" \
      "auditctl -w /etc/passwd -p wa -k identity && auditctl -w /etc/shadow -p wa -k identity" \
      "Modifications des comptes non tracées"
  fi

  mod_score "logging" "$t" "$p"
}

# ── SCORE ─────────────────────────────────────────────────────────────────────

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

# ── XML ───────────────────────────────────────────────────────────────────────

generate_xml() {
  cat > "$OUTFILE" <<XMLEOF
<?xml version="1.0" encoding="UTF-8"?>
<PetrixAuditReport Referential="ANSSI-BP-028" AgentVersion="2.0.0">
  <Metadata>
    <Hostname>$(xml_esc "$HOSTNAME_VAL")</Hostname>
    <OS>$(xml_esc "$OS_NAME")</OS>
    <OSType>linux</OSType>
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
  echo "  Petrix Audit Agent 2.0 — Linux — ANSSI-BP-028 v2.0"
  echo "  Hôte : $HOSTNAME_VAL"
  echo "  OS   : $OS_NAME ($ARCH)"
  echo "════════════════════════════════════════════════════════════════"

  [ "$(id -u)" -ne 0 ] && { echo "ERREUR : Exécuter en root (sudo bash $0)"; exit 1; }

  echo "[ 1/14] SSH configuration..."              && audit_ssh
  echo "[ 2/14] Paramètres noyau..."               && audit_kernel
  echo "[ 3/14] Comptes utilisateurs..."            && audit_users
  echo "[ 4/14] Politique PAM..."                   && audit_pam
  echo "[ 5/14] Montage des partitions..."          && audit_mounts
  echo "[ 6/14] Permissions fichiers sensibles..."  && audit_perms
  echo "[ 7/14] Contrôle d'accès MAC..."            && audit_mac
  echo "[ 8/14] NTP / Synchronisation horloge..."  && audit_ntp
  echo "[ 9/14] Pare-feu..."                        && audit_firewall
  echo "[10/14] Services dangereux..."              && audit_services
  echo "[11/14] Ports réseau..."                    && audit_network
  echo "[12/14] Système de fichiers..."             && audit_filesystem
  echo "[13/14] Paquets..."                         && audit_packages
  echo "[14/14] Journalisation..."                  && audit_logging

  compute_score
  generate_xml
  _REAL_USER="${SUDO_USER:-$(stat -c '%U' "$(pwd)" 2>/dev/null)}"
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
