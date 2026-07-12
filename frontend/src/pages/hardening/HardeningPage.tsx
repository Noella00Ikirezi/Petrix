import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  BookOpen,
  AlertTriangle,
  Terminal,
  Zap,
  FileSearch,
  ChevronRight,
  Lock,
  Flame,
  HardDrive,
  Shield,
  Users,
  Settings,
  RefreshCw,
  Globe,
  LucideIcon,
  FileCode,
  ExternalLink,
  Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { hardeningApi, hardeningCorrelationsApi } from '@/api/client';
import { MODULE_KNOWLEDGE, MODULE_ORDER, type ModuleKnowledge } from '@/data/moduleKnowledge';

const MODULE_ICONS: Record<string, LucideIcon> = {
  lock: Lock, flame: Flame, hardDrive: HardDrive, shield: Shield,
  users: Users, settings: Settings, refreshCw: RefreshCw, globe: Globe,
};

type Target = {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  os_type: string;
  description?: string;
  tags?: string[];
  created_at: string;
};

type Session = {
  id: string;
  target_id: string;
  target_name: string;
  target_host: string;
  status: string;
  current_module?: string;
  progress: number;
  score?: number;
  grade?: string;
  findings_summary?: Record<string, number>;
  total_findings: number;
  total_checks: number;
  passed_checks: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
};

type Finding = {
  id: string;
  check_id: string;
  check_name: string;
  module: string;
  description: string;
  severity: string;
  found: string;
  expected: string;
  remediation?: string;
  status: string;
  cve_ids?: string[];
};

type AuditCheck = {
  id: string;
  anssi: string;
  module: string;
  moduleLabel: string;
  name: string;
  context: string;
  norm: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  os: ('linux' | 'macos' | 'windows')[];
};

const AUDIT_CATALOG: AuditCheck[] = [
  // ── Linux (ANSSI-BP-028) ──────────────────────────────────────────────────
  // SSH
  { id: "SSH-R4-001",  anssi: "R4",  module: "ssh",        moduleLabel: "SSH",               name: "Protocole SSH version 2 uniquement",          severity: "CRITICAL", os: ['linux','macos'], context: "SSHv1 contient des vulnérabilités cryptographiques graves permettant des attaques MITM.", norm: "ANSSI BP-028 R4 — Seul le protocole SSH v2 est acceptable pour les connexions administratives distantes." },
  { id: "SSH-R4-002",  anssi: "R4",  module: "ssh",        moduleLabel: "SSH",               name: "Connexion root SSH désactivée",                severity: "CRITICAL", os: ['linux','macos'], context: "L'accès root direct via SSH élimine la traçabilité des actions administratives.", norm: "ANSSI BP-028 R4 — PermitRootLogin doit être 'no' ou 'prohibit-password'." },
  { id: "SSH-R4-003",  anssi: "R4",  module: "ssh",        moduleLabel: "SSH",               name: "Authentification par mot de passe désactivée",  severity: "HIGH",     os: ['linux','macos'], context: "Les mots de passe sont vulnérables aux attaques de force brute. Les clés SSH sont recommandées.", norm: "ANSSI BP-028 R4 — PasswordAuthentication no dans sshd_config." },
  { id: "SSH-R5-001",  anssi: "R5",  module: "ssh",        moduleLabel: "SSH",               name: "Délai d'authentification SSH limité",           severity: "MEDIUM",   os: ['linux','macos'], context: "Un délai élevé facilite les attaques de force brute et laisse des connexions suspendues.", norm: "ANSSI BP-028 R5 — LoginGraceTime ≤ 60 secondes." },
  { id: "SSH-R5-002",  anssi: "R5",  module: "ssh",        moduleLabel: "SSH",               name: "Nombre de tentatives SSH limité",               severity: "HIGH",     os: ['linux','macos'], context: "Sans limite, un attaquant peut essayer un nombre illimité de mots de passe.", norm: "ANSSI BP-028 R5 — MaxAuthTries ≤ 4 dans sshd_config." },
  // Kernel (Linux only)
  { id: "KERNEL-R8-001", anssi: "R8",  module: "kernel",   moduleLabel: "Noyau",             name: "ASLR activé (randomisation mémoire)",           severity: "HIGH",     os: ['linux'], context: "ASLR rend l'exploitation des débordements de mémoire beaucoup plus difficile.", norm: "ANSSI BP-028 R8 — kernel.randomize_va_space = 2 (randomisation complète)." },
  { id: "KERNEL-R9-001", anssi: "R9",  module: "kernel",   moduleLabel: "Noyau",             name: "Chargement dynamique de modules désactivé",     severity: "MEDIUM",   os: ['linux'], context: "Le chargement de modules à chaud permet à un attaquant root de charger du code noyau malveillant.", norm: "ANSSI BP-028 R9 — kernel.modules_disabled = 1 après le démarrage." },
  { id: "KERNEL-R10-001",anssi: "R10", module: "kernel",   moduleLabel: "Noyau",             name: "Dmesg restreint aux utilisateurs root",         severity: "MEDIUM",   os: ['linux'], context: "Les messages noyau peuvent révéler des adresses mémoire et aider à contourner ASLR.", norm: "ANSSI BP-028 R10 — kernel.dmesg_restrict = 1." },
  { id: "KERNEL-R10-002",anssi: "R10", module: "kernel",   moduleLabel: "Noyau",             name: "Namespaces utilisateur non privilégiés restreints", severity: "HIGH", os: ['linux'], context: "Les namespaces non privilégiés sont exploités pour l'escalade de privilèges via des vulnérabilités noyau.", norm: "ANSSI BP-028 R10 — kernel.unprivileged_userns_clone = 0." },
  { id: "KERNEL-R12-001",anssi: "R12", module: "kernel",   moduleLabel: "Noyau",             name: "Protection SYN cookies activée",                severity: "HIGH",     os: ['linux'], context: "Les SYN cookies protègent contre les attaques SYN flood qui saturent la table de connexions TCP.", norm: "ANSSI BP-028 R12 — net.ipv4.tcp_syncookies = 1." },
  { id: "KERNEL-R12-002",anssi: "R12", module: "kernel",   moduleLabel: "Noyau",             name: "Redirections ICMP refusées",                    severity: "MEDIUM",   os: ['linux'], context: "Les redirections ICMP peuvent être utilisées pour détourner le trafic réseau (MITM).", norm: "ANSSI BP-028 R12 — net.ipv4.conf.all.accept_redirects = 0." },
  { id: "KERNEL-R13-001",anssi: "R13", module: "kernel",   moduleLabel: "Noyau",             name: "Protection ptrace (YAMA)",                      severity: "HIGH",     os: ['linux'], context: "ptrace sans restriction permet à un processus de tracer les processus d'autres utilisateurs.", norm: "ANSSI BP-028 R13 — kernel.yama.ptrace_scope ≥ 1." },
  // Users
  { id: "USERS-R30-001", anssi: "R30", module: "users",    moduleLabel: "Comptes",           name: "Comptes inactifs verrouillés",                  severity: "HIGH",     os: ['linux'], context: "Les comptes inactifs avec shell de connexion sont des vecteurs d'intrusion.", norm: "ANSSI BP-028 R30 — Les comptes non utilisés doivent être verrouillés (usermod -L)." },
  { id: "USERS-R31-001", anssi: "R31", module: "users",    moduleLabel: "Comptes",           name: "Politique d'expiration des mots de passe",      severity: "MEDIUM",   os: ['linux'], context: "Sans expiration, un mot de passe compromis reste utilisable indéfiniment.", norm: "ANSSI BP-028 R31 — PASS_MAX_DAYS ≤ 90, PASS_MIN_DAYS ≥ 1 dans /etc/login.defs." },
  { id: "USERS-R31-002", anssi: "R31", module: "users",    moduleLabel: "Comptes",           name: "Complexité des mots de passe (pam_pwquality)",  severity: "HIGH",     os: ['linux'], context: "Des mots de passe simples sont cassés en quelques secondes par brute force.", norm: "ANSSI BP-028 R31 — pam_pwquality configuré avec minlen ≥ 12, complexité requise." },
  { id: "USERS-R32-001", anssi: "R32", module: "users",    moduleLabel: "Comptes",           name: "Délai d'inactivité de session (TMOUT)",         severity: "MEDIUM",   os: ['linux'], context: "Une session laissée ouverte sans surveillance peut être exploitée.", norm: "ANSSI BP-028 R32 — Variable TMOUT ≤ 900 secondes dans /etc/profile.d/." },
  { id: "USERS-R33-001", anssi: "R33", module: "users",    moduleLabel: "Comptes",           name: "Journalisation sudo (log_input/log_output)",    severity: "HIGH",     os: ['linux'], context: "Sans journalisation sudo, les actions administratives sont indétectables et non auditables.", norm: "ANSSI BP-028 R33 — Defaults log_input, log_output dans /etc/sudoers." },
  { id: "USERS-R34-001", anssi: "R34", module: "users",    moduleLabel: "Comptes",           name: "Comptes de service sans shell de connexion",    severity: "MEDIUM",   os: ['linux'], context: "Les comptes de service avec shell interactif peuvent être utilisés pour des connexions non autorisées.", norm: "ANSSI BP-028 R34 — Les comptes système doivent utiliser /usr/sbin/nologin ou /bin/false." },
  { id: "USERS-R36-001", anssi: "R36", module: "users",    moduleLabel: "Comptes",           name: "UMASK restrictif par défaut",                   severity: "LOW",      os: ['linux'], context: "Un UMASK trop permissif crée des fichiers lisibles par tous.", norm: "ANSSI BP-028 R36 — UMASK 027 ou 077 dans /etc/login.defs." },
  { id: "USERS-R37-001", anssi: "R37", module: "users",    moduleLabel: "Comptes",           name: "Règles NOPASSWD sudo absentes",                 severity: "HIGH",     os: ['linux'], context: "NOPASSWD dans sudo permet d'exécuter des commandes root sans authentification.", norm: "ANSSI BP-028 R37-R44 — Aucune règle NOPASSWD non justifiée dans sudoers." },
  // Filesystem (Linux)
  { id: "FS-R28-001",    anssi: "R28", module: "filesystem",moduleLabel: "Système de fichiers", name: "Options noexec/nosuid/nodev sur /tmp",         severity: "HIGH",     os: ['linux'], context: "/tmp sans noexec permet à un attaquant d'y déposer et exécuter des scripts malveillants.", norm: "ANSSI BP-028 R28 — /tmp, /var/tmp, /dev/shm montés avec nosuid,nodev,noexec." },
  { id: "FS-R29-001",    anssi: "R29", module: "filesystem",moduleLabel: "Système de fichiers", name: "/boot accessible uniquement par root",          severity: "HIGH",     os: ['linux'], context: "Un /boot accessible en écriture permet de modifier le chargeur de démarrage.", norm: "ANSSI BP-028 R29 — /boot : root:root, permissions 700." },
  { id: "FS-R49-001",    anssi: "R49", module: "filesystem",moduleLabel: "Système de fichiers", name: "Permissions de /etc/shadow",                   severity: "CRITICAL", os: ['linux'], context: "/etc/shadow contient les hashes — accès non autorisé = attaque offline.", norm: "ANSSI BP-028 R49 — /etc/shadow : permissions 640, owner root:shadow." },
  { id: "FS-R52-001",    anssi: "R52", module: "filesystem",moduleLabel: "Système de fichiers", name: "Absence de fichiers world-writable",            severity: "HIGH",     os: ['linux'], context: "Des fichiers modifiables par tous peuvent être altérés par n'importe quel utilisateur.", norm: "ANSSI BP-028 R52 — Aucun fichier inscriptible par tous (chmod o-w)." },
  { id: "FS-R54-001",    anssi: "R54", module: "filesystem",moduleLabel: "Système de fichiers", name: "Sticky bit sur répertoires partagés",           severity: "MEDIUM",   os: ['linux'], context: "Sans sticky bit, un utilisateur peut supprimer les fichiers d'autres dans /tmp.", norm: "ANSSI BP-028 R54 — chmod +t sur tous les répertoires world-writable." },
  { id: "FS-R57-001",    anssi: "R57", module: "filesystem",moduleLabel: "Système de fichiers", name: "Binaires setuid root non standard",             severity: "HIGH",     os: ['linux'], context: "Un binaire setuid root vulnérable permet une escalade vers root.", norm: "ANSSI BP-028 R57 — Inventaire et contrôle des exécutables setuid root." },
  // Packages (Linux)
  { id: "PKG-R58-001",   anssi: "R58", module: "packages", moduleLabel: "Paquets",           name: "Absence de paquets inutiles (telnet, rsh…)",    severity: "HIGH",     os: ['linux'], context: "Telnet, rsh transmettent les données en clair et élargissent la surface d'attaque.", norm: "ANSSI BP-028 R58 — N'installer que les paquets strictement nécessaires à la mission." },
  { id: "PKG-R59-001",   anssi: "R59", module: "packages", moduleLabel: "Paquets",           name: "Dépôts APT/YUM officiels uniquement",           severity: "HIGH",     os: ['linux'], context: "Des dépôts tiers peuvent contenir des paquets malveillants ou compromis.", norm: "ANSSI BP-028 R59 — Utiliser uniquement les dépôts officiels de la distribution." },
  { id: "PKG-R61-001",   anssi: "R61", module: "packages", moduleLabel: "Paquets",           name: "Mises à jour de sécurité appliquées",           severity: "CRITICAL", os: ['linux'], context: "Les CVE avec patch disponible représentent le risque le plus immédiat.", norm: "ANSSI BP-028 R61 — Système à jour, unattended-upgrades configuré." },
  // PAM (Linux)
  { id: "PAM-R68-001",   anssi: "R68", module: "pam",      moduleLabel: "PAM",               name: "Verrouillage après tentatives échouées",        severity: "HIGH",     os: ['linux'], context: "Sans verrouillage, un attaquant peut essayer un nombre illimité de mots de passe.", norm: "ANSSI BP-028 R68 — pam_faillock avec deny=5, unlock_time=900 dans /etc/pam.d/." },
  { id: "PAM-R69-001",   anssi: "R69", module: "pam",      moduleLabel: "PAM",               name: "Algorithme de hachage des mots de passe",       severity: "CRITICAL", os: ['linux'], context: "MD5 et DES sont cassés — accès à /etc/shadow = récupération des mots de passe en heures.", norm: "ANSSI BP-028 R69 — ENCRYPT_METHOD SHA512 ou YESCRYPT dans /etc/login.defs." },
  { id: "PAM-R69-003",   anssi: "R69", module: "pam",      moduleLabel: "PAM",               name: "Nombre de rounds de hachage suffisant",         severity: "MEDIUM",   os: ['linux'], context: "Un nombre de rounds trop faible accélère les attaques par dictionnaire sur les hashes.", norm: "ANSSI BP-028 R69 — SHA_CRYPT_MIN_ROUNDS ≥ 100000." },
  { id: "PAM-R70-001",   anssi: "R70", module: "pam",      moduleLabel: "PAM",               name: "Séparation comptes locaux / LDAP",              severity: "HIGH",     os: ['linux'], context: "Une mauvaise configuration NSS peut permettre à des comptes LDAP d'écraser des comptes locaux.", norm: "ANSSI BP-028 R70 — passwd: files ldap (fichiers locaux prioritaires)." },
  // Logging (Linux)
  { id: "LOG-R71-001",   anssi: "R71", module: "logging",  moduleLabel: "Journalisation",    name: "Démon syslog actif (rsyslog/journald)",         severity: "CRITICAL", os: ['linux'], context: "Sans journalisation, aucune trace des événements — intrusion indétectable.", norm: "ANSSI BP-028 R71 — rsyslog ou syslog-ng actif, logs auth/kern/daemon configurés." },
  { id: "LOG-R72-001",   anssi: "R72", module: "logging",  moduleLabel: "Journalisation",    name: "Sous-système d'audit Linux (auditd) actif",     severity: "HIGH",     os: ['linux'], context: "auditd capture les appels système critiques (execve, chmod) pour l'audit forensique.", norm: "ANSSI BP-028 R72 — auditd actif avec règles pour /etc/passwd, /etc/shadow." },
  { id: "LOG-R72-002",   anssi: "R72", module: "logging",  moduleLabel: "Journalisation",    name: "Règles auditd pour fichiers sensibles",         severity: "MEDIUM",   os: ['linux'], context: "Sans règles spécifiques, auditd ne surveille pas les modifications des fichiers critiques.", norm: "ANSSI BP-028 R72 — Règles -w /etc/passwd -w /etc/shadow -w /etc/sudoers." },
  { id: "LOG-R74-001",   anssi: "R74", module: "logging",  moduleLabel: "Journalisation",    name: "Outil de contrôle d'intégrité (AIDE/Tripwire)", severity: "MEDIUM",   os: ['linux'], context: "Sans outil d'intégrité, des modifications de fichiers système par un attaquant passent inaperçues.", norm: "ANSSI BP-028 R74 — AIDE avec base de données initialisée et vérification périodique." },
  // Firewall
  { id: "FW-R67-001",    anssi: "R67", module: "firewall",  moduleLabel: "Pare-feu",         name: "Pare-feu actif (ufw/iptables/nftables)",        severity: "CRITICAL", os: ['linux'], context: "Sans pare-feu, tous les ports ouverts sont accessibles depuis le réseau.", norm: "ANSSI BP-028 R67 — Un pare-feu local doit filtrer les connexions entrantes et sortantes." },
  { id: "FW-R67-002",    anssi: "R67", module: "firewall",  moduleLabel: "Pare-feu",         name: "Politique par défaut DROP",                     severity: "HIGH",     os: ['linux'], context: "Une politique ACCEPT par défaut expose tous les services non explicitement bloqués.", norm: "ANSSI BP-028 R67 — Politique DROP/REJECT par défaut, autoriser uniquement les flux nécessaires." },
  // Services
  { id: "SVC-R62-001",   anssi: "R62", module: "services",  moduleLabel: "Services",         name: "Services inutiles désactivés",                  severity: "MEDIUM",   os: ['linux'], context: "Chaque service actif élargit la surface d'attaque.", norm: "ANSSI BP-028 R62 — Désactiver et supprimer les services non requis." },
  { id: "SVC-R66-001",   anssi: "R66", module: "services",  moduleLabel: "Services",         name: "Services obsolètes absents (FTP, Telnet, NFS)", severity: "HIGH",     os: ['linux'], context: "Telnet, FTP, rsh transmettent les credentials en clair sur le réseau.", norm: "ANSSI BP-028 R66 — Remplacer par des alternatives sécurisées (SSH/SFTP) ou supprimer." },
  // Network
  { id: "NET-R12-001",   anssi: "R12", module: "network",   moduleLabel: "Réseau",           name: "Ports en écoute non nécessaires fermés",        severity: "MEDIUM",   os: ['linux'], context: "Chaque port ouvert est une porte d'entrée potentielle.", norm: "ANSSI BP-028 R12 — Inventaire des ports en écoute, fermeture des services non indispensables." },

  // ── macOS (CIS macOS Benchmark) ───────────────────────────────────────────
  { id: "MAC-SIP-001",   anssi: "CIS 5.1.3",  module: "system",   moduleLabel: "Intégrité",  name: "SIP (System Integrity Protection) actif",      severity: "CRITICAL", os: ['macos'], context: "SIP empêche la modification de /System, /bin, /sbin même en root. Sa désactivation est un signal d'alarme majeur.", norm: "CIS macOS L1 — csrutil status doit retourner 'enabled'." },
  { id: "MAC-FV-001",    anssi: "CIS 2.6.1",  module: "filevault", moduleLabel: "Chiffrement",name: "FileVault activé",                             severity: "HIGH",     os: ['macos'], context: "Sans FileVault, le contenu du disque est lisible en bootant sur un Live USB ou en extrayant le disque.", norm: "CIS macOS L1 — FileVault doit être activé sur tous les Mac (fdesetup status)." },
  { id: "MAC-GK-001",    anssi: "CIS 2.7.1",  module: "system",   moduleLabel: "Intégrité",  name: "Gatekeeper actif",                             severity: "HIGH",     os: ['macos'], context: "Gatekeeper empêche l'exécution d'applications non signées par Apple — protection contre les malwares macOS.", norm: "CIS macOS L1 — spctl --status retourne 'assessments enabled'." },
  { id: "MAC-FW-001",    anssi: "CIS 2.2.2",  module: "firewall", moduleLabel: "Pare-feu",   name: "Pare-feu applicatif macOS activé",             severity: "HIGH",     os: ['macos'], context: "Sans pare-feu, les services actifs sont accessibles sur le réseau local.", norm: "CIS macOS L1 — /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate retourne 'enabled'." },
  { id: "MAC-GUEST-001", anssi: "CIS 5.6",    module: "users",    moduleLabel: "Comptes",    name: "Compte invité macOS désactivé",                severity: "MEDIUM",   os: ['macos'], context: "Le compte invité permet un accès sans authentification à la machine.", norm: "CIS macOS L1 — Le compte Guest doit être désactivé dans System Settings > Users." },
  { id: "MAC-UPD-001",   anssi: "CIS 1.1",    module: "updates",  moduleLabel: "Mises à jour",name: "Mises à jour automatiques macOS activées",    severity: "HIGH",     os: ['macos'], context: "Les mises à jour macOS corrigent des CVE exploités activement (WebKit, kernel, etc.).", norm: "CIS macOS L1 — softwareupdate --schedule on, mises à jour critiques automatiques." },
  { id: "MAC-SSH-001",   anssi: "CIS 2.3.1",  module: "ssh",      moduleLabel: "SSH",        name: "SSH désactivé si non nécessaire",              severity: "MEDIUM",   os: ['macos'], context: "SSH activé élargit la surface d'attaque. La gestion à distance ne doit être active que si requise.", norm: "CIS macOS L1 — Remote Login désactivé dans System Settings > Sharing si SSH non requis." },

  // ── Windows (CIS Windows Benchmark / ANSSI) ───────────────────────────────
  { id: "WIN-FW-001",    anssi: "CIS 9.1",    module: "firewall", moduleLabel: "Pare-feu",   name: "Pare-feu Windows activé (3 profils)",          severity: "CRITICAL", os: ['windows'], context: "Sans pare-feu, tous les services Windows sont exposés sur le réseau (SMB, RDP, WinRM).", norm: "CIS WS2019 L1 9.1-9.3 — Windows Defender Firewall actif sur Domain/Private/Public." },
  { id: "WIN-FW-002",    anssi: "CIS 9.1",    module: "firewall", moduleLabel: "Pare-feu",   name: "Politique entrante par défaut : Block",         severity: "HIGH",     os: ['windows'], context: "DefaultInboundAction=Allow expose tous les ports ouverts sans règle explicite.", norm: "CIS WS2019 L1 — DefaultInboundAction=Block sur les 3 profils." },
  { id: "WIN-SMB-001",   anssi: "CIS 18.3.2", module: "services", moduleLabel: "Services",   name: "SMBv1 désactivé (EternalBlue / WannaCry)",     severity: "CRITICAL", os: ['windows'], context: "MS17-010 (EternalBlue) exploite SMBv1 pour une exécution de code à distance sans authentification — WannaCry infecté 200 000 machines en 24h.", norm: "CIS WS2019 L1 — Get-SmbServerConfiguration | EnableSMB1Protocol doit être False." },
  { id: "WIN-USR-001",   anssi: "CIS 2.3.1",  module: "users",    moduleLabel: "Comptes",    name: "Compte Administrator intégré désactivé",       severity: "HIGH",     os: ['windows'], context: "Le compte Administrator intégré est ciblé en premier par les attaques (SID S-1-5-21-*-500). Renommer ou désactiver.", norm: "CIS WS2019 L1 2.3.1.1 — Disable-LocalUser Administrator OU renommer." },
  { id: "WIN-USR-002",   anssi: "CIS 2.3.1",  module: "users",    moduleLabel: "Comptes",    name: "Compte Guest désactivé",                       severity: "HIGH",     os: ['windows'], context: "Le compte Guest permet un accès sans mot de passe au système — désactiver systématiquement.", norm: "CIS WS2019 L1 — Disable-LocalUser Guest." },
  { id: "WIN-USR-003",   anssi: "CIS 1.1.4",  module: "users",    moduleLabel: "Comptes",    name: "Longueur minimale mot de passe ≥ 12 caractères", severity: "HIGH",   os: ['windows'], context: "Les mots de passe courts sont cassés en quelques secondes avec des GPU modernes (hashcat).", norm: "CIS WS2019 L1 1.1.4 — net accounts /minpwlen:12." },
  { id: "WIN-UAC-001",   anssi: "CIS 2.3.17", module: "winpolicies",moduleLabel: "Stratégies", name: "UAC activé (EnableLUA=1)",                   severity: "CRITICAL", os: ['windows'], context: "UAC désactivé = tout processus lancé par l'utilisateur obtient directement les droits SYSTEM.", norm: "CIS WS2019 L1 2.3.17.1 — EnableLUA=1, ConsentPromptBehaviorAdmin≥2." },
  { id: "WIN-PS-001",    anssi: "CIS 18.9.95",module: "winpolicies",moduleLabel: "Stratégies", name: "ExecutionPolicy PowerShell restrictive",      severity: "HIGH",     os: ['windows'], context: "ExecutionPolicy Unrestricted = n'importe quel script PS s'exécute — vecteur principal des attaques fileless.", norm: "CIS WS2019 L1 — ExecutionPolicy: RemoteSigned ou AllSigned sur LocalMachine." },
  { id: "WIN-LOCK-001",  anssi: "CIS 2.3.7",  module: "winpolicies",moduleLabel: "Stratégies", name: "Verrouillage de session automatique (≤ 15 min)", severity: "MEDIUM", os: ['windows'], context: "Un poste sans verrouillage automatique est accessible physiquement à quiconque passe à proximité.", norm: "CIS WS2019 L1 — ScreenSaverIsSecure=1, ScreenSaveTimeOut≤900." },
  { id: "WIN-DEF-001",   anssi: "CIS 18.9.45",module: "system",   moduleLabel: "Intégrité",  name: "Windows Defender protection temps réel activée", severity: "HIGH",   os: ['windows'], context: "Sans antivirus temps réel, les malwares s'exécutent sans entrave sur le système.", norm: "CIS WS2019 L1 — RealTimeProtectionEnabled=True, signatures < 7 jours." },
  { id: "WIN-BL-001",    anssi: "CIS 18.9.11",module: "filevault", moduleLabel: "Chiffrement", name: "BitLocker activé sur C:",                    severity: "HIGH",     os: ['windows'], context: "Un disque non chiffré est lisible en bootant sur une clé USB externe ou en l'extrayant.", norm: "CIS WS2019 L1 — Get-BitLockerVolume C: : VolumeStatus=FullyEncrypted, ProtectionStatus=On." },
  { id: "WIN-UPD-001",   anssi: "CIS 18.9.108",module: "updates",  moduleLabel: "Mises à jour", name: "Windows Update activé et à jour",           severity: "CRITICAL", os: ['windows'], context: "Les CVE Windows critiques (RDP, SMB, Print Spooler) sont exploités activement en quelques jours.", norm: "CIS WS2019 L1 — Mises à jour auto activées, pas de KB critiques manquants > 30 jours." },
  { id: "WIN-LOG-001",   anssi: "CIS 17.1",   module: "winlogging",moduleLabel: "Journalisation", name: "Journal Security Windows activé (≥ 200 Mo)", severity: "HIGH",  os: ['windows'], context: "Sans journal Security, les connexions, élévations et modifications de comptes sont invisibles.", norm: "CIS WS2019 L1 17.1 — Journal Security: IsEnabled=True, MaxSize≥196 Mo." },
  { id: "WIN-LOG-002",   anssi: "CIS 17.2",   module: "winlogging",moduleLabel: "Journalisation", name: "Politique d'audit complète (Logon/Account Mgmt)", severity: "HIGH", os: ['windows'], context: "Sans audit des connexions et des comptes, les attaques (pass-the-hash, kerberoasting) sont indétectables.", norm: "CIS WS2019 L1 17.x — auditpol: Account Logon, Account Management: Success and Failure." },
  { id: "WIN-NET-001",   anssi: "CIS 18.5",   module: "network",  moduleLabel: "Réseau",     name: "NetBIOS et LLMNR désactivés",                  severity: "HIGH",     os: ['windows'], context: "NetBIOS/LLMNR actifs permettent des attaques Responder pour capturer des hashes NTLM sur le LAN.", norm: "CIS WS2019 L1 — TcpipNetbiosOptions=2, HKLM EnableMulticast=0." },
];

const MODULE_COLORS: Record<string, string> = {
  ssh:        'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  kernel:     'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  users:      'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
  filesystem: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  packages:   'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  pam:        'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
  logging:    'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  firewall:   'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  services:   'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  network:    'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300',
};

const OS_FILTER_LABELS: Record<string, { label: string; cls: string; activeCls: string }> = {
  all:     { label: 'Tous', cls: 'text-gray-500 border-transparent', activeCls: 'border-primary-600 text-primary-700 dark:text-primary-400' },
  linux:   { label: 'Linux', cls: 'text-orange-600 border-transparent', activeCls: 'border-orange-500 text-orange-700 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/10' },
  macos:   { label: 'macOS', cls: 'text-gray-600 border-transparent', activeCls: 'border-gray-500 text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800' },
  windows: { label: 'Windows', cls: 'text-blue-600 border-transparent', activeCls: 'border-blue-500 text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10' },
};

const OS_BADGE_INLINE: Record<string, string> = {
  linux:   'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  macos:   'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
  windows: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
};

const REF_NORM_LABELS: Record<string, string> = {
  linux:   'ANSSI-BP-028',
  macos:   'CIS macOS',
  windows: 'CIS WS2019',
};

function ReferentielTab() {
  const [osFilter, setOsFilter] = useState<'all' | 'linux' | 'macos' | 'windows'>('linux');
  const [moduleFilter, setModuleFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const osCounts = { linux: 0, macos: 0, windows: 0 };
  AUDIT_CATALOG.forEach(c => c.os.forEach(o => { osCounts[o] = (osCounts[o] || 0) + 1; }));

  const byOs = osFilter === 'all'
    ? AUDIT_CATALOG
    : AUDIT_CATALOG.filter(c => c.os.includes(osFilter));

  const modules = [...new Set(byOs.map(c => c.module))];
  const filtered = byOs.filter(c =>
    (!moduleFilter || c.module === moduleFilter) &&
    (!severityFilter || c.severity === severityFilter)
  );

  const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const sorted = [...filtered].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  return (
    <div className="space-y-4">
      {/* Banner */}
      <div className="rounded-lg border p-4" style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}>
        <div className="flex items-start gap-3">
          <BookOpen className="mt-0.5 h-5 w-5 shrink-0 text-primary-600 dark:text-primary-400" />
          <div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Référentiel multi-OS — ANSSI-BP-028 · CIS macOS · CIS Windows Server 2019
            </p>
            <p className="mt-1 text-xs" style={{ color: 'var(--faint)' }}>
              {AUDIT_CATALOG.length} contrôles couvrant Linux ({osCounts.linux}), macOS ({osCounts.macos}) et Windows ({osCounts.windows}).
              Chaque contrôle est associé à sa norme officielle et à son contexte de risque.
            </p>
          </div>
        </div>
      </div>

      {/* OS tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: 'var(--line)' }}>
        {(['all', 'linux', 'macos', 'windows'] as const).map(os => {
          const o = OS_FILTER_LABELS[os];
          const isActive = osFilter === os;
          const count = os === 'all' ? AUDIT_CATALOG.length : osCounts[os];
          return (
            <button
              key={os}
              onClick={() => { setOsFilter(os); setModuleFilter(''); }}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 -mb-px transition-colors ${isActive ? o.activeCls : o.cls + ' hover:text-gray-700 dark:hover:text-gray-300'}`}
            >
              {o.label}
              <span className="rounded-full bg-current/10 px-1.5 py-0.5 font-mono text-xs opacity-70">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" style={{ color: 'var(--faint)' }} />
          <select className="input py-1.5 text-sm" value={moduleFilter} onChange={e => setModuleFilter(e.target.value)}>
            <option value="">Tous les modules</option>
            {modules.map(m => (
              <option key={m} value={m}>{byOs.find(c => c.module === m)?.moduleLabel ?? m}</option>
            ))}
          </select>
        </div>
        <select className="input py-1.5 text-sm" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
          <option value="">Toutes les sévérités</option>
          <option value="CRITICAL">Critique</option>
          <option value="HIGH">Élevé</option>
          <option value="MEDIUM">Moyen</option>
          <option value="LOW">Faible</option>
        </select>
        <span className="ml-auto self-center text-xs" style={{ color: 'var(--faint)' }}>{sorted.length} contrôle(s)</span>
      </div>

      {/* Checks list */}
      <div className="space-y-2">
        {sorted.map(check => (
          <div key={check.id} className="rounded-lg border" style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}>
            <button
              className="flex w-full items-start gap-3 p-4 text-left"
              onClick={() => setExpanded(e => e === check.id ? null : check.id)}
            >
              <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-bold ${SEVERITY_COLORS[check.severity]}`}>
                {check.severity === 'CRITICAL' ? 'CRITIQUE' : check.severity === 'HIGH' ? 'ÉLEVÉ' : check.severity === 'MEDIUM' ? 'MOYEN' : 'FAIBLE'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${MODULE_COLORS[check.module] ?? 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'}`}>
                    {check.moduleLabel}
                  </span>
                  {check.os.map(o => (
                    <span key={o} className={`rounded-full px-1.5 py-0.5 text-xs font-medium ${OS_BADGE_INLINE[o]}`}>
                      {o === 'linux' ? 'Linux' : o === 'macos' ? 'macOS' : 'Windows'}
                    </span>
                  ))}
                  <span className="font-mono text-xs font-semibold text-primary-600 dark:text-primary-400">
                    {check.anssi}
                  </span>
                  <span className="text-xs font-mono" style={{ color: 'var(--faint)' }}>{check.id}</span>
                </div>
                <p className="mt-1 text-sm font-medium" style={{ color: 'var(--text)' }}>{check.name}</p>
              </div>
              <span className="shrink-0" style={{ color: 'var(--faint)' }}>
                {expanded === check.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </span>
            </button>
            {expanded === check.id && (
              <div className="border-t px-4 pb-4 pt-3 space-y-3" style={{ borderColor: 'var(--line)' }}>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--faint)' }}>Contexte de risque</p>
                  <p className="mt-1 text-sm" style={{ color: 'var(--dim)' }}>{check.context}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--faint)' }}>
                    Exigence — {check.os.map(o => REF_NORM_LABELS[o]).join(' / ')}
                  </p>
                  <p className="mt-1 text-sm font-medium text-primary-700 dark:text-primary-300">{check.norm}</p>
                </div>
              </div>
            )}
          </div>
        ))}
        {sorted.length === 0 && (
          <div className="py-12 text-center text-sm" style={{ color: 'var(--faint)' }}>
            Aucun contrôle pour cette combinaison de filtres.
          </div>
        )}
      </div>
    </div>
  );
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  HIGH: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  INFO: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

// ─── Composant Fiche Module (style PingCastle) ──────────────────────────────

const ATK_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', border: 'border-red-300 dark:border-red-700' },
  HIGH:     { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-300 dark:border-orange-700' },
  MEDIUM:   { bg: 'bg-yellow-50 dark:bg-yellow-900/20', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-300 dark:border-yellow-700' },
  LOW:      { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-300 dark:border-blue-700' },
};

const OS_BADGE: Record<string, { label: string; cls: string }> = {
  linux:   { label: 'Linux', cls: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' },
  macos:   { label: 'macOS', cls: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  windows: { label: 'Windows', cls: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
  all:     { label: 'Tous', cls: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
};

const SOURCE_COLORS: Record<string, string> = {
  ANSSI:  'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  CIS:    'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  NIST:   'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  CVE:    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  MITRE:  'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  RFC:    'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

function RiskBar({ score }: { score: number }) {
  const color = score >= 80 ? 'bg-red-500' : score >= 60 ? 'bg-orange-400' : score >= 40 ? 'bg-yellow-400' : 'bg-green-500';
  const label = score >= 80 ? 'Risque critique' : score >= 60 ? 'Risque élevé' : score >= 40 ? 'Risque modéré' : 'Risque faible';
  const textColor = score >= 80 ? 'text-red-600 dark:text-red-400' : score >= 60 ? 'text-orange-600 dark:text-orange-400' : score >= 40 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400';
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700">
        <div className={`h-1.5 rounded-full ${color} transition-all duration-700`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-semibold ${textColor} shrink-0`}>{label}</span>
    </div>
  );
}

function FicheModule({ mod, sessions }: { mod: ModuleKnowledge; sessions: Session[] }) {
  const [section, setSection] = useState<'attacks' | 'audit' | 'fix' | 'sources' | null>('attacks');
  const [osFilter, setOsFilter] = useState<'linux' | 'macos' | 'windows' | 'all'>('linux');
  const ModIcon = MODULE_ICONS[mod.icon] ?? Shield;

  const hasFindings = sessions.some(s => s.status === 'completed' && s.total_findings > 0);
  const auditCmds = mod.auditCommands.filter(c => c.os === osFilter || c.os === 'all');
  const fixCmds   = mod.remediationSteps.filter(c => c.os === osFilter || c.os === 'all');

  return (
    <div className="bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="p-5 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center shrink-0">
            <ModIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">{mod.label}</h3>
              {mod.anssiRefs.map(r => (
                <span key={r} className="rounded-full border border-primary-200 bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700 dark:border-primary-700 dark:bg-primary-900/20 dark:text-primary-300">
                  {r}
                </span>
              ))}
            </div>
            <RiskBar score={mod.riskScore} />
          </div>
        </div>
        <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{mod.description}</p>

        {/* Quick facts */}
        <div className="mt-3 space-y-1.5">
          {mod.quickFacts.map((f, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span className="shrink-0 mt-0.5 h-3.5 w-3.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                <Zap className="h-2.5 w-2.5 text-yellow-600 dark:text-yellow-400" />
              </span>
              <span>{f}</span>
            </div>
          ))}
        </div>

        {/* Corrélation avec audits */}
        {hasFindings && (
          <div className="mt-3 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 px-3 py-2 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0" />
            <span className="text-xs text-orange-700 dark:text-orange-400 font-medium">
              Des findings ont été détectés dans vos audits — consultez la page Rapport d'audit.
            </span>
          </div>
        )}
      </div>

      {/* Section tabs */}
      <div className="flex border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 px-2 pt-1.5">
        {[
          { key: 'attacks', label: 'Attaques', icon: AlertTriangle },
          { key: 'audit',   label: 'Audit', icon: FileSearch },
          { key: 'fix',     label: 'Remédiation', icon: Terminal },
          { key: 'sources', label: 'Sources', icon: BookOpen },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setSection(prev => prev === t.key ? null : t.key as typeof section)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
              section === t.key
                ? 'border-primary-600 text-primary-700 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <t.icon className="h-3.5 w-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {/* Section content */}
      {section && (
        <div className="p-5">

          {/* Attacks */}
          {section === 'attacks' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed font-medium">{mod.whyItMatters}</p>
              <div className="space-y-2">
                {mod.attackTypes.map((atk, i) => {
                  const c = ATK_COLORS[atk.severity] ?? ATK_COLORS.LOW;
                  return (
                    <div key={i} className={`rounded-lg border ${c.border} ${c.bg} p-4`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${SEVERITY_COLORS[atk.severity] ?? ''}`}>
                          {atk.severity === 'CRITICAL' ? 'CRITIQUE' : atk.severity === 'HIGH' ? 'ÉLEVÉ' : atk.severity === 'MEDIUM' ? 'MODÉRÉ' : 'FAIBLE'}
                        </span>
                        <span className={`text-sm font-semibold ${c.text}`}>{atk.name}</span>
                        <span className="ml-auto text-xs font-mono text-gray-400">{atk.technique}</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{atk.description}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        <strong>Impact :</strong> {atk.impact}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Audit commands */}
          {section === 'audit' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Système :</span>
                {(['linux', 'macos', 'windows'] as const).map(os => (
                  <button
                    key={os}
                    onClick={() => setOsFilter(os)}
                    className={`text-xs px-2 py-1 rounded-full font-medium transition-colors ${
                      osFilter === os ? OS_BADGE[os].cls + ' ring-1 ring-current' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {OS_BADGE[os].label}
                  </button>
                ))}
              </div>
              {auditCmds.length === 0
                ? <p className="text-sm text-gray-400 py-4 text-center">Pas de commande pour {OS_BADGE[osFilter].label}</p>
                : auditCmds.map((cmd, i) => (
                  <div key={i} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-hidden">
                    <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                      <span className={`text-xs px-1.5 py-0.5 rounded ${OS_BADGE[cmd.os].cls}`}>{OS_BADGE[cmd.os].label}</span>
                      <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">{cmd.label}</span>
                    </div>
                    <pre className="px-4 py-3 text-xs font-mono text-green-700 dark:text-green-400 whitespace-pre-wrap overflow-x-auto">{cmd.command}</pre>
                    <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 space-y-1">
                      <p className="text-xs text-gray-500">{cmd.explanation}</p>
                      <p className="text-xs text-green-600 dark:text-green-400"><strong>Résultat attendu :</strong> {cmd.expectedGood}</p>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {/* Remediation */}
          {section === 'fix' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Système :</span>
                {(['linux', 'macos', 'windows'] as const).map(os => (
                  <button
                    key={os}
                    onClick={() => setOsFilter(os)}
                    className={`text-xs px-2 py-1 rounded-full font-medium transition-colors ${
                      osFilter === os ? OS_BADGE[os].cls + ' ring-1 ring-current' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {OS_BADGE[os].label}
                  </button>
                ))}
              </div>
              {fixCmds.length === 0
                ? <p className="text-sm text-gray-400 py-4 text-center">Pas de remédiation pour {OS_BADGE[osFilter].label}</p>
                : fixCmds.map((step, i) => (
                  <div key={i} className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/10 overflow-hidden">
                    <div className="px-4 py-2 border-b border-blue-200 dark:border-blue-800 flex items-center gap-2">
                      <Terminal className="h-3.5 w-3.5 text-blue-600" />
                      <span className={`text-xs px-1.5 py-0.5 rounded ${OS_BADGE[step.os].cls}`}>{OS_BADGE[step.os].label}</span>
                      <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">{step.label}</span>
                    </div>
                    <pre className="px-4 py-3 text-xs font-mono text-blue-900 dark:text-blue-200 whitespace-pre-wrap overflow-x-auto">{step.command}</pre>
                    <div className="px-4 py-2 border-t border-blue-200 dark:border-blue-800">
                      <p className="text-xs text-blue-700 dark:text-blue-400">{step.explanation}</p>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {/* Sources */}
          {section === 'sources' && (
            <div className="space-y-2">
              {mod.sources.map((src, i) => (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-3 hover:border-primary-300 hover:shadow-sm transition-all"
                >
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold ${SOURCE_COLORS[src.type] ?? ''}`}>{src.type}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-mono font-semibold text-gray-700 dark:text-gray-300">{src.ref}</p>
                    <p className="text-xs text-gray-500 truncate">{src.label}</p>
                  </div>
                  <ExternalLink className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FichesTab({ sessions }: { sessions: Session[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-4">
        <div className="flex items-start gap-3">
          <BookOpen className="mt-0.5 h-5 w-5 shrink-0 text-primary-600 dark:text-primary-400" />
          <div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Base de connaissance — {MODULE_ORDER.length} modules · Linux / macOS / Windows
            </p>
            <p className="mt-1 text-xs" style={{ color: 'var(--faint)' }}>
              Vecteurs d'attaque, commandes d'audit par OS, remédiation et sources officielles (ANSSI-BP-028, CIS, NIST, MITRE ATT&amp;CK).
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {MODULE_ORDER.map(modId => {
          const mod = MODULE_KNOWLEDGE[modId];
          if (!mod) return null;
          const isOpen = expanded === modId;
          const ModIcon = MODULE_ICONS[mod.icon] ?? Shield;

          return (
            <div key={modId} className="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setExpanded(isOpen ? null : modId)}
                className="w-full flex items-center gap-4 px-5 py-3.5 text-left bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors"
              >
                <div className="h-8 w-8 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center shrink-0">
                  <ModIcon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-semibold text-sm text-gray-900 dark:text-white">{mod.label}</span>
                    {mod.anssiRefs.slice(0, 4).map(r => (
                      <span key={r} className="rounded-full border border-primary-200 bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700 dark:border-primary-700 dark:bg-primary-900/20 dark:text-primary-300">
                        {r}
                      </span>
                    ))}
                  </div>
                  <RiskBar score={mod.riskScore} />
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className="text-xs text-gray-400 hidden sm:block">{mod.attackTypes.length} vecteurs</span>
                  {isOpen
                    ? <ChevronUp className="h-4 w-4 text-gray-400" />
                    : <ChevronRight className="h-4 w-4 text-gray-400" />
                  }
                </div>
              </button>
              {isOpen && (
                <div className="border-t border-gray-100 dark:border-gray-700">
                  <FicheModule mod={mod} sessions={sessions} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600 dark:text-green-400',
  B: 'text-lime-600 dark:text-lime-400',
  C: 'text-yellow-600 dark:text-yellow-400',
  D: 'text-orange-600 dark:text-orange-400',
  F: 'text-red-600 dark:text-red-400',
};

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { icon: React.ReactNode; cls: string }> = {
    pending: { icon: <Clock className="h-3 w-3" />, cls: 'text-gray-500' },
    connecting: { icon: <Loader2 className="h-3 w-3 animate-spin" />, cls: 'text-blue-500' },
    auditing: { icon: <Loader2 className="h-3 w-3 animate-spin" />, cls: 'text-blue-500' },
    completed: { icon: <CheckCircle className="h-3 w-3" />, cls: 'text-green-500' },
    failed: { icon: <XCircle className="h-3 w-3" />, cls: 'text-red-500' },
  };
  const { icon, cls } = map[status] ?? { icon: null, cls: '' };
  return (
    <span className={`flex items-center gap-1 text-xs font-medium capitalize ${cls}`}>
      {icon}
      {status}
    </span>
  );
}

/** Modal d'import XML — remplace l'ancien workflow SSH. */
function ImportXmlModal({ onClose, onImported }: { onClose: () => void; onImported: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: (file: File) => hardeningApi.importXml(file),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['hardening-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['hardening-targets'] });
      toast.success(`Rapport importé — score ${data.score ?? '?'}/100`);
      onImported();
      onClose();
    },
    onError: () => toast.error("Erreur lors de l'import du rapport XML"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-1 text-lg font-bold dark:text-white">Importer un rapport d'audit</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-5">
          Généré par l'agent Petrix sur le système cible.
        </p>

        {/* Steps */}
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">1</div>
            <div>
              <p className="text-sm font-semibold dark:text-white mb-1">Télécharger l'agent</p>
              <p className="text-xs text-gray-500 mb-2">Depuis la page <strong>Systèmes</strong>, cliquez sur "Auditer" pour télécharger l'agent de votre OS.</p>
              <Link to="/assets" onClick={onClose}
                className="inline-flex items-center gap-1.5 text-xs text-primary-600 hover:underline">
                <ExternalLink className="h-3 w-3" /> Aller sur la page Systèmes
              </Link>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">2</div>
            <div className="flex-1">
              <p className="text-sm font-semibold dark:text-white mb-2">Importer le fichier XML</p>
              <input ref={fileInputRef} type="file" accept=".xml" className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) importMutation.mutate(f); e.target.value = ''; }} />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={importMutation.isPending}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 transition-colors disabled:opacity-50">
                {importMutation.isPending
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <FileCode className="h-4 w-4 text-primary-600" />}
                Sélectionner le fichier .xml
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>Fermer</button>
        </div>
      </div>
    </div>
  );
}

// TargetModal et SessionModal supprimés — les systèmes sont gérés via /assets et les audits via agent local + import XML.

function SessionCard({ session }: { session: Session }) {
  const [expanded, setExpanded] = useState(false);
  const [showCorr, setShowCorr] = useState(false);

  const { data: findings } = useQuery<Finding[]>({
    queryKey: ['hardening-findings', session.id],
    queryFn: () => hardeningApi.getFindings(session.id),
    enabled: expanded && session.status === 'completed',
  });

  const { data: corrData, isLoading: corrLoading } = useQuery({
    queryKey: ['hardening-correlations', session.id],
    queryFn: () => hardeningCorrelationsApi.sessionCorrelations(session.id),
    enabled: showCorr && session.status === 'completed',
    staleTime: 5 * 60 * 1000,
  });
  const correlations: any[] = corrData?.correlations ?? [];

  const summary = session.findings_summary ?? {};

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-medium dark:text-white">{session.target_name}</span>
            <StatusBadge status={session.status} />
            {session.grade && (
              <span className={`text-xl font-bold ${GRADE_COLORS[session.grade] ?? ''}`}>
                {session.grade}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">{session.target_host}</p>
          {session.status === 'auditing' && (
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs text-gray-500">
                <span>{session.current_module ?? 'running…'}</span>
                <span>{session.progress}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-1.5 rounded-full bg-primary-500 transition-all"
                  style={{ width: `${session.progress}%` }}
                />
              </div>
            </div>
          )}
          {session.status === 'completed' && (
            <div className="mt-2 flex flex-wrap gap-2">
              {session.score !== undefined && (
                <span className="text-sm font-medium dark:text-gray-300">
                  Score: <strong>{session.score}/100</strong>
                </span>
              )}
              {Object.entries(summary).map(([sev, count]) =>
                count > 0 ? (
                  <span key={sev} className={`rounded px-2 py-0.5 text-xs font-medium ${SEVERITY_COLORS[sev] ?? ''}`}>
                    {count} {sev}
                  </span>
                ) : null
              )}
              <span className="text-xs text-gray-400">
                {session.passed_checks}/{session.total_checks} checks passed
              </span>
            </div>
          )}
          {session.status === 'failed' && session.error_message && (
            <p className="mt-1 text-xs text-red-500">{session.error_message}</p>
          )}
        </div>
        {session.status === 'completed' && (
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={() => setExpanded(e => !e)}
              className="flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400"
            >
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              Findings
            </button>
            <button
              onClick={() => setShowCorr(e => !e)}
              className="flex items-center gap-1 text-xs text-orange-600 hover:underline dark:text-orange-400"
            >
              {showCorr ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              CERT-FR
            </button>
          </div>
        )}
      </div>

      {expanded && findings && findings.length > 0 && (
        <div className="mt-4 space-y-2 border-t border-gray-100 pt-4 dark:border-gray-700">
          {findings.map(f => (
            <div key={f.id} className="rounded-md border border-gray-100 p-3 dark:border-gray-700">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${SEVERITY_COLORS[f.severity] ?? ''}`}>
                      {f.severity}
                    </span>
                    <span className="text-xs font-mono text-gray-500">{f.check_id}</span>
                    <span className="text-xs font-medium dark:text-gray-300">{f.check_name}</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{f.description}</p>
                  <p className="text-xs text-gray-500">
                    Found: <code className="rounded bg-gray-100 px-1 dark:bg-gray-700">{f.found}</code>
                    {' → '}Expected: <code className="rounded bg-gray-100 px-1 dark:bg-gray-700">{f.expected}</code>
                  </p>
                  {f.cve_ids && f.cve_ids.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {f.cve_ids.map(cve => (
                        <a
                          key={cve}
                          href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-0.5 rounded border border-orange-300 bg-orange-50 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-orange-700 hover:bg-orange-100 dark:border-orange-700 dark:bg-orange-950/40 dark:text-orange-400 dark:hover:bg-orange-900/50"
                        >
                          {cve}
                          <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                        </a>
                      ))}
                    </div>
                  )}
                  {f.remediation && (
                    <details className="mt-1">
                      <summary className="cursor-pointer text-xs text-primary-600 dark:text-primary-400">
                        Remediation
                      </summary>
                      <pre className="mt-1 overflow-auto rounded bg-gray-50 p-2 text-xs dark:bg-gray-900">{f.remediation}</pre>
                    </details>
                  )}
                </div>
                <span className="shrink-0 rounded px-1.5 py-0.5 text-xs text-gray-400 dark:bg-gray-700">
                  {f.module}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      {expanded && findings && findings.length === 0 && (
        <div className="mt-4 flex items-center gap-2 border-t border-gray-100 pt-4 text-sm text-green-600 dark:border-gray-700 dark:text-green-400">
          <CheckCircle className="h-4 w-4" />
          No findings — all checks passed!
        </div>
      )}

      {/* ── Corrélations CERT-FR ── */}
      {showCorr && (
        <div className="mt-4 border-t border-orange-100 pt-4 dark:border-orange-900/30">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-orange-600 dark:text-orange-400">
            Corrélations CERT-FR · alertes liées aux findings FAIL
          </p>
          {corrLoading && (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <div className="h-3 w-3 animate-spin rounded-full border-2 border-orange-200 border-t-orange-500" />
              Interrogation du CERT-FR…
            </div>
          )}
          {!corrLoading && correlations.length === 0 && (
            <p className="text-xs text-gray-400">
              Aucune alerte CERT-FR ne correspond aux findings de cet audit (par mots-clés).
            </p>
          )}
          {!corrLoading && correlations.length > 0 && (
            <div className="space-y-3">
              {correlations.map((corr: any) => (
                <div key={corr.finding_id}
                  className="rounded-md border border-orange-100 bg-orange-50/50 p-3 dark:border-orange-900/20 dark:bg-orange-950/10">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs font-mono text-gray-500">{corr.check_id}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${
                      ({ CRITICAL:'bg-red-100 text-red-700', HIGH:'bg-orange-100 text-orange-700',
                        MEDIUM:'bg-yellow-100 text-yellow-700', LOW:'bg-blue-100 text-blue-700' } as Record<string,string>)[corr.severity] ?? 'bg-gray-100 text-gray-600'
                    }`}>{corr.severity}</span>
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{corr.check_name}</span>
                  </div>
                  <div className="space-y-1.5">
                    {corr.cert_alerts.map((alert: any) => (
                      <div key={alert.cert_id} className="flex items-start gap-2">
                        <span className="shrink-0 mt-0.5 font-mono text-xs font-bold text-orange-600 dark:text-orange-400">
                          {alert.cert_id}
                        </span>
                        <span className="text-xs text-gray-600 dark:text-gray-400 leading-snug flex-1">
                          {alert.title}
                        </span>
                        {alert.link && (
                          <a href={alert.link} target="_blank" rel="noreferrer"
                            className="shrink-0 text-gray-400 hover:text-primary-600">
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function HardeningPage() {
  const [tab, setTab] = useState<'fiches' | 'referentiel' | 'sessions'>('fiches');
  const [showImportModal, setShowImportModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: targets = [] } = useQuery<Target[]>({
    queryKey: ['hardening-targets'],
    queryFn: hardeningApi.listTargets,
  });

  const { data: sessions = [], isLoading: loadingSessions } = useQuery<Session[]>({
    queryKey: ['hardening-sessions'],
    queryFn: hardeningApi.listSessions,
    refetchInterval: (query) => {
      const data = query.state.data as Session[] | undefined;
      const hasActive = data?.some(s => ['pending', 'connecting', 'auditing'].includes(s.status));
      return hasActive ? 3000 : false;
    },
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['hardening-targets'] });
    queryClient.invalidateQueries({ queryKey: ['hardening-sessions'] });
  };

  const completedSessions = sessions.filter(s => s.status === 'completed');
  const avgScore =
    completedSessions.length > 0
      ? Math.round(completedSessions.reduce((acc, s) => acc + (s.score ?? 0), 0) / completedSessions.length)
      : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Hardening (HCO)
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Référentiel ANSSI-BP-028 · Audit par agent local
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowImportModal(true)} className="btn btn-primary btn-md">
            <FileCode className="mr-2 h-4 w-4" />
            Importer un rapport XML
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Systèmes</p>
          <p className="text-2xl font-bold dark:text-white">{targets.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Audits terminés</p>
          <p className="text-2xl font-bold dark:text-white">{completedSessions.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Score moyen</p>
          <p className="text-2xl font-bold dark:text-white">{avgScore !== null ? `${avgScore}/100` : '—'}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Total findings</p>
          <p className="text-2xl font-bold dark:text-white">
            {sessions.reduce((acc, s) => acc + s.total_findings, 0)}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        {([
          { id: 'fiches',      label: 'Fiches modules' },
          { id: 'referentiel', label: 'Référentiel ANSSI' },
          { id: 'sessions',    label: `Historique (${completedSessions.length})` },
        ] as const).map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`pb-3 text-sm font-medium whitespace-nowrap transition-colors ${
              tab === t.id
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Fiches Tab */}
      {tab === 'fiches' && <FichesTab sessions={sessions} />}

      {/* Référentiel Tab */}
      {tab === 'referentiel' && <ReferentielTab />}

      {/* Sessions Tab */}
      {tab === 'sessions' && (
        <div className="space-y-3">
          {loadingSessions ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
              <ShieldCheck className="h-12 w-12 opacity-30" />
              <p className="text-center">
                Aucun audit pour le moment.<br />
                <span className="text-sm">Téléchargez l'agent depuis la page <Link to="/assets" className="text-primary-600 hover:underline">Systèmes</Link> et importez le rapport XML.</span>
              </p>
              <button onClick={() => setShowImportModal(true)} className="btn btn-primary btn-sm">
                <FileCode className="mr-1.5 h-3.5 w-3.5" /> Importer un rapport
              </button>
            </div>
          ) : (
            sessions.map(s => <SessionCard key={s.id} session={s} />)
          )}
        </div>
      )}

      {showImportModal && (
        <ImportXmlModal onClose={() => setShowImportModal(false)} onImported={refresh} />
      )}
    </div>
  );
}
