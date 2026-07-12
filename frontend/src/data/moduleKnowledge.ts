// Base de connaissance des modules de durcissement Petrix
// Inspiré du niveau de détail PingCastle — ANSSI-BP-028 v2.0

export interface AttackType {
  name: string;
  technique: string; // MITRE ATT&CK ID
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  impact: string;
}

export interface AuditCommand {
  os: 'linux' | 'macos' | 'windows' | 'all';
  label: string;
  command: string;
  explanation: string;
  expectedGood: string;
}

export interface RemediationStep {
  os: 'linux' | 'macos' | 'windows' | 'all';
  label: string;
  command: string;
  explanation: string;
}

export interface KnowledgeSource {
  type: 'ANSSI' | 'CIS' | 'NIST' | 'CVE' | 'MITRE' | 'RFC';
  ref: string;
  label: string;
  url: string;
}

export interface ModuleKnowledge {
  id: string;
  label: string;
  icon: string;
  description: string;
  whyItMatters: string;
  riskScore: number;
  anssiRefs: string[];
  attackTypes: AttackType[];
  auditCommands: AuditCommand[];
  remediationSteps: RemediationStep[];
  sources: KnowledgeSource[];
  quickFacts: string[];
}

export const MODULE_KNOWLEDGE: Record<string, ModuleKnowledge> = {

  // ─── SSH ────────────────────────────────────────────────────────────────────
  ssh: {
    id: 'ssh',
    label: 'Configuration SSH',
    icon: "lock",
    description: 'Secure Shell (SSH) est le protocole d\'administration à distance le plus répandu. Une configuration incorrecte est l\'une des premières choses qu\'un attaquant exploite pour prendre le contrôle d\'un serveur.',
    whyItMatters: 'SSH est la porte d\'entrée principale des serveurs Linux/macOS. Un seul paramètre mal configuré (root login autorisé, authentification par mot de passe) suffit pour permettre une compromission complète en quelques minutes.',
    riskScore: 95,
    anssiRefs: ['R4', 'R5', 'R21', 'R22'],
    attackTypes: [
      {
        name: 'Attaque par force brute',
        technique: 'T1110.001',
        description: 'Un attaquant tente automatiquement des milliers de combinaisons de mots de passe (dictionnaire, bruteforce) pour se connecter en SSH.',
        severity: 'CRITICAL',
        impact: 'Accès initial au serveur, mouvement latéral sur le réseau interne.',
      },
      {
        name: 'Connexion root directe',
        technique: 'T1078.003',
        description: 'Si PermitRootLogin est activé, un attaquant ayant le mot de passe root (ou une clé volée) obtient directement un accès total sans traçabilité.',
        severity: 'CRITICAL',
        impact: 'Compromission totale du système, pas d\'audit trail.',
      },
      {
        name: 'Attaque MITM / Downgrade SSH',
        technique: 'T1557.001',
        description: 'Si SSHv1 est activé, un attaquant en position Man-in-the-Middle peut intercepter et déchiffrer les communications (vulnérabilité CVE-2008-5161).',
        severity: 'HIGH',
        impact: 'Capture de credentials, écoute des commandes administratives.',
      },
      {
        name: 'Vol de clé privée',
        technique: 'T1552.004',
        description: 'Si l\'authentification par mot de passe est activée, une clé SSH volée sur une machine compromise permet de rebondir sur tous les serveurs configurés.',
        severity: 'HIGH',
        impact: 'Mouvement latéral, persistance sur le réseau.',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Vérifier la configuration sshd',
        command: 'sudo grep -E "^(Protocol|PermitRootLogin|PasswordAuthentication|MaxAuthTries|LoginGraceTime|PubkeyAuthentication)" /etc/ssh/sshd_config',
        explanation: 'Affiche les paramètres de sécurité critiques du démon SSH.',
        expectedGood: 'Protocol 2, PermitRootLogin no, PasswordAuthentication no, MaxAuthTries 4',
      },
      {
        os: 'linux',
        label: 'Tester la force des algorithmes cryptographiques',
        command: 'ssh -vvv -o BatchMode=yes localhost 2>&1 | grep -E "kex|cipher|mac"',
        explanation: 'Affiche les algorithmes d\'échange de clés, chiffrement et MAC négociés.',
        expectedGood: 'Algorithmes curve25519, aes256-gcm, hmac-sha2-512 uniquement.',
      },
      {
        os: 'macos',
        label: 'Vérifier SSH sur macOS',
        command: 'sudo grep -E "^(PermitRootLogin|PasswordAuthentication|MaxAuthTries)" /etc/ssh/sshd_config 2>/dev/null || echo "SSH désactivé"',
        explanation: 'Vérifie si SSH est actif et ses paramètres de sécurité.',
        expectedGood: 'SSH désactivé OU PermitRootLogin no, PasswordAuthentication no',
      },
      {
        os: 'linux',
        label: 'Vérifier les connexions SSH actives',
        command: 'ss -tnp | grep ":22" && last | grep "still logged in" | head -10',
        explanation: 'Liste les connexions SSH actuelles et les sessions actives.',
        expectedGood: 'Seules les connexions attendues depuis des IP connues.',
      },
      {
        os: 'windows',
        label: 'Vérifier si OpenSSH Server est installé',
        command: 'Get-WindowsCapability -Online | Where-Object Name -like "OpenSSH.Server*" | Select-Object Name, State',
        explanation: 'Vérifie si le serveur OpenSSH Windows est installé. Doit être absent si non nécessaire.',
        expectedGood: 'State: NotPresent — ou State: Installed avec configuration durcie',
      },
      {
        os: 'windows',
        label: 'Vérifier la configuration sshd Windows (si installé)',
        command: 'if (Test-Path "$env:ProgramData\\ssh\\sshd_config") { Get-Content "$env:ProgramData\\ssh\\sshd_config" | Select-String "PermitRootLogin|PasswordAuthentication|MaxAuthTries" } else { Write-Host "OpenSSH Server non installe" }',
        explanation: 'Analyse la config SSH Windows — mêmes règles que Linux.',
        expectedGood: 'PermitRootLogin no, PasswordAuthentication no, MaxAuthTries 4',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Désactiver l\'accès root et les mots de passe SSH',
        command: `sudo sed -i 's/^#\\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\\?MaxAuthTries.*/MaxAuthTries 4/' /etc/ssh/sshd_config
sudo sed -i 's/^#\\?LoginGraceTime.*/LoginGraceTime 60/' /etc/ssh/sshd_config
sudo systemctl restart sshd`,
        explanation: 'Durcissement de la configuration SSH : forcer l\'authentification par clé, bloquer root.',
      },
      {
        os: 'linux',
        label: 'Restreindre les algorithmes cryptographiques',
        command: `sudo bash -c 'cat >> /etc/ssh/sshd_config << EOF

# Durcissement ANSSI R5 — Algorithmes forts uniquement
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512,hmac-sha2-256
EOF'
sudo systemctl restart sshd`,
        explanation: 'Limite SSH aux algorithmes cryptographiques approuvés par l\'ANSSI.',
      },
      {
        os: 'macos',
        label: 'Désactiver SSH sur macOS si non nécessaire',
        command: 'sudo systemsetup -setremotelogin off\nsudo launchctl disable system/com.openssh.sshd',
        explanation: 'Désactive complètement SSH si la gestion à distance n\'est pas requise (recommandé).',
      },
      {
        os: 'windows',
        label: 'Désactiver OpenSSH Server Windows si non nécessaire',
        command: 'Stop-Service sshd -Force -ErrorAction SilentlyContinue\nSet-Service sshd -StartupType Disabled -ErrorAction SilentlyContinue\nRemove-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0',
        explanation: 'Supprime le serveur SSH Windows si la gestion distante n\'est pas requise.',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R4', label: 'ANSSI BP-028 — Configuration SSH', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
      { type: 'CIS', ref: 'CIS SSH L1', label: 'CIS Benchmark SSH Level 1', url: 'https://www.cisecurity.org/benchmark/debian_linux' },
      { type: 'MITRE', ref: 'T1110.001', label: 'MITRE ATT&CK — Brute Force: Password Guessing', url: 'https://attack.mitre.org/techniques/T1110/001/' },
      { type: 'CVE', ref: 'CVE-2023-38408', label: 'OpenSSH agent hijacking (2023)', url: 'https://www.cvedetails.com/cve/CVE-2023-38408/' },
    ],
    quickFacts: [
      'En 2023, 22% des serveurs exposés en ligne ont un accès SSH avec authentification par mot de passe (Shodan)',
      'Un serveur SSH exposé sur Internet reçoit en moyenne 3000 tentatives de brute force par jour',
      'CVE-2023-38408 permettait l\'exécution de code via ssh-agent sur les clients OpenSSH < 9.3p2',
    ],
  },

  // ─── Firewall ───────────────────────────────────────────────────────────────
  firewall: {
    id: 'firewall',
    label: 'Pare-feu local',
    icon: "flame",
    description: 'Le pare-feu local filtre les connexions réseau entrantes et sortantes. C\'est la première ligne de défense contre les tentatives d\'accès non autorisées aux services du système.',
    whyItMatters: 'Sans pare-feu, chaque service actif sur le serveur est accessible depuis le réseau. Une application web, une base de données mal configurée, ou un service de debugging peuvent exposer des points d\'entrée non intentionnels.',
    riskScore: 90,
    anssiRefs: ['R67', 'R68'],
    attackTypes: [
      {
        name: 'Reconnaissance réseau / Port scanning',
        technique: 'T1046',
        description: 'Un attaquant utilise nmap ou masscan pour cartographier les ports ouverts et identifier les services exposés.',
        severity: 'MEDIUM',
        impact: 'Identification de la surface d\'attaque, planification d\'une attaque ciblée.',
      },
      {
        name: 'Exploitation de services non protégés',
        technique: 'T1190',
        description: 'Sans pare-feu, des services non destinés à être exposés (Redis, bases de données, interfaces d\'administration) sont accessibles depuis Internet.',
        severity: 'CRITICAL',
        impact: 'Accès initial, exécution de code à distance, compromission de données.',
      },
      {
        name: 'Mouvement latéral inter-serveurs',
        technique: 'T1021',
        description: 'Sans règles de filtrage sortant, un système compromis peut initier des connexions vers d\'autres systèmes internes.',
        severity: 'HIGH',
        impact: 'Propagation de l\'attaque sur le réseau interne.',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Vérifier le statut du pare-feu (ufw)',
        command: 'sudo ufw status verbose',
        explanation: 'Affiche le statut et les règles du pare-feu ufw (Ubuntu/Debian).',
        expectedGood: 'Status: active, Default: deny (incoming), allow (outgoing)',
      },
      {
        os: 'linux',
        label: 'Vérifier avec iptables/nftables',
        command: 'sudo iptables -L -n -v --line-numbers 2>/dev/null || sudo nft list ruleset 2>/dev/null',
        explanation: 'Liste toutes les règles de filtrage actives.',
        expectedGood: 'Politique INPUT DROP, règles explicites pour SSH et services légitimes.',
      },
      {
        os: 'linux',
        label: 'Vérifier firewalld (RHEL/CentOS/Fedora)',
        command: 'sudo firewall-cmd --state && sudo firewall-cmd --list-all',
        explanation: 'Affiche le statut et la configuration de firewalld.',
        expectedGood: 'running, zone=public, services limités (ssh uniquement si serveur dédié)',
      },
      {
        os: 'macos',
        label: 'Vérifier le pare-feu Application macOS',
        command: 'sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate && sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps',
        explanation: 'Vérifie le statut du pare-feu applicatif macOS.',
        expectedGood: 'Firewall enabled, Stealth mode ON',
      },
      {
        os: 'windows',
        label: 'Vérifier le pare-feu Windows (3 profils)',
        command: 'Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction | Format-Table -AutoSize',
        explanation: 'Contrôle les profils Domain, Private et Public du pare-feu Windows Defender.',
        expectedGood: 'Enabled=True, DefaultInboundAction=Block pour les 3 profils',
      },
      {
        os: 'windows',
        label: 'Lister les règles entrantes autorisées',
        command: 'Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True | Select-Object DisplayName, Profile, @{N="Port";E={($_ | Get-NetFirewallPortFilter).LocalPort}} | Sort-Object Port | Format-Table -AutoSize',
        explanation: 'Inventaire des règles autorisant du trafic entrant — chaque règle doit être justifiée.',
        expectedGood: 'Seules les règles explicitement requises (RDP si admin distant, HTTPS pour serveur web)',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Activer et configurer ufw (Ubuntu/Debian)',
        command: `sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw --force enable
sudo ufw status verbose`,
        explanation: 'Configure un pare-feu strict : deny-all entrant sauf SSH, allow-all sortant.',
      },
      {
        os: 'linux',
        label: 'Configuration iptables sécurisée',
        command: `# Vider les règles existantes
sudo iptables -F && sudo iptables -X
# Politiques par défaut
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT
# Autoriser loopback
sudo iptables -A INPUT -i lo -j ACCEPT
# Autoriser connexions établies
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Autoriser SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Sauvegarder
sudo iptables-save > /etc/iptables/rules.v4`,
        explanation: 'Mise en place d\'un filtrage strict DROP-by-default via iptables.',
      },
      {
        os: 'macos',
        label: 'Activer le pare-feu macOS et le mode furtif',
        command: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on`,
        explanation: 'Active le pare-feu macOS avec mode furtif (pas de réponse aux pings) et blocage total.',
      },
      {
        os: 'windows',
        label: 'Activer le pare-feu Windows sur tous les profils',
        command: 'Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True\nSet-NetFirewallProfile -Profile Domain,Private,Public -DefaultInboundAction Block\nSet-NetFirewallProfile -Profile Domain,Private,Public -DefaultOutboundAction Allow\n# Vérifier :\nGet-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction',
        explanation: 'Active Windows Defender Firewall avec politique deny-all entrant sur les 3 profils (CIS L1).',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R67', label: 'ANSSI BP-028 — Pare-feu local', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
      { type: 'CIS', ref: 'CIS L1 3.5', label: 'CIS Benchmark — Firewall Configuration', url: 'https://www.cisecurity.org/' },
      { type: 'MITRE', ref: 'T1046', label: 'MITRE ATT&CK — Network Service Discovery', url: 'https://attack.mitre.org/techniques/T1046/' },
    ],
    quickFacts: [
      '75% des violations de données impliquent des services non intentionnellement exposés (Verizon DBIR)',
      'Un serveur Redis sans authentification exposé sur Internet est compromis en moins de 3 heures en moyenne',
      'La règle de base : "ce qui n\'est pas explicitement autorisé est interdit"',
    ],
  },

  // ─── Chiffrement ────────────────────────────────────────────────────────────
  filevault: {
    id: 'filevault',
    label: 'Chiffrement du disque',
    icon: "hardDrive",
    description: 'Le chiffrement de disque complet (FileVault sur macOS, LUKS sur Linux, BitLocker sur Windows) protège les données au repos. En cas de vol physique, les données restent inaccessibles sans la clé de déchiffrement.',
    whyItMatters: 'Un ordinateur portable volé sans chiffrement de disque donne accès à 100% des données en quelques minutes, même si Windows/macOS est protégé par un mot de passe (boot sur Live USB, extraction du disque).',
    riskScore: 85,
    anssiRefs: ['R56', 'R57'],
    attackTypes: [
      {
        name: 'Vol physique et extraction de disque',
        technique: 'T1200',
        description: 'Un attaquant ayant accès physique au matériel peut extraire le disque dur et le lire sur une autre machine, contournant tout contrôle d\'accès OS.',
        severity: 'CRITICAL',
        impact: 'Accès à toutes les données : mots de passe, clés SSH, données personnelles, documents confidentiels.',
      },
      {
        name: 'Attaque Evil Maid',
        technique: 'T1542.001',
        description: 'Un attaquant ayant un accès physique temporaire installe un keylogger matériel ou modifie le bootloader pour capturer la phrase de passe de déchiffrement.',
        severity: 'HIGH',
        impact: 'Capture de la clé de chiffrement, compromission silencieuse.',
      },
      {
        name: 'Attaque Cold Boot',
        technique: 'T1006',
        description: 'Sur certains systèmes, la clé de déchiffrement reste en mémoire RAM après hibernation. Un attaquant peut freezer la RAM et lire le contenu.',
        severity: 'MEDIUM',
        impact: 'Extraction de la clé de chiffrement depuis la mémoire vive.',
      },
    ],
    auditCommands: [
      {
        os: 'macos',
        label: 'Vérifier le statut FileVault',
        command: 'fdesetup status && diskutil apfs list | grep "FileVault"',
        explanation: 'Vérifie si FileVault est activé et l\'état de chiffrement des volumes.',
        expectedGood: 'FileVault is On. Chiffrement: Yes',
      },
      {
        os: 'linux',
        label: 'Vérifier le chiffrement LUKS',
        command: 'lsblk -f | grep -E "crypto_LUKS|dm-crypt" && sudo dmsetup status 2>/dev/null',
        explanation: 'Identifie les partitions chiffrées avec LUKS (Linux Unified Key Setup).',
        expectedGood: 'Partitions système chiffrées avec LUKS2, algorithme aes-xts-plain64',
      },
      {
        os: 'linux',
        label: 'Vérifier la force du chiffrement LUKS',
        command: 'sudo cryptsetup luksDump /dev/sda3 2>/dev/null | grep -E "Version|Cipher|Hash"',
        explanation: 'Affiche les paramètres cryptographiques du volume LUKS.',
        expectedGood: 'LUKS2, Cipher: aes-xts-plain64, Hash: sha512',
      },
      {
        os: 'windows',
        label: 'Vérifier le statut BitLocker',
        command: 'Get-BitLockerVolume | Select-Object MountPoint, EncryptionMethod, VolumeStatus, ProtectionStatus | Format-Table -AutoSize',
        explanation: 'Vérifie si BitLocker chiffre les volumes Windows. Requiert Windows Pro/Enterprise.',
        expectedGood: 'VolumeStatus=FullyEncrypted, ProtectionStatus=On sur C: (et D: si applicable)',
      },
      {
        os: 'windows',
        label: 'Vérifier TPM et SecureBoot (prérequis BitLocker)',
        command: '(Get-Tpm).TpmReady\nConfirm-SecureBootUEFI 2>&1',
        explanation: 'BitLocker sans TPM est moins sécurisé (pas de mesure d\'intégrité au démarrage).',
        expectedGood: 'TpmReady=True, SecureBoot=True',
      },
    ],
    remediationSteps: [
      {
        os: 'macos',
        label: 'Activer FileVault sur macOS',
        command: 'sudo fdesetup enable -user $(whoami)\n# Sauvegarder la clé de récupération affichée dans un endroit sécurisé',
        explanation: 'Active FileVault. La clé de récupération doit être stockée OFFLINE dans un coffre-fort ou sur un compte iCloud d\'entreprise.',
      },
      {
        os: 'windows',
        label: 'Activer BitLocker sur C: (TPM requis)',
        command: '# Activer BitLocker avec AES-XTS 256 bits\nEnable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -TpmProtector\n# Sauvegarder la clé de récupération\n$vol = Get-BitLockerVolume C:\n$kp = $vol.KeyProtector | Where-Object KeyProtectorType -eq "RecoveryPassword"\nBackup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId $kp.KeyProtectorId',
        explanation: 'Active BitLocker AES-XTS 256 bits avec protection TPM. La clé de récupération doit être stockée hors ligne (AD, coffre-fort).',
      },
      {
        os: 'linux',
        label: 'Chiffrer une partition avec LUKS (Ubuntu — lors de l\'installation)',
        command: `# À l'installation Ubuntu : cocher "Encrypt the new Ubuntu installation"
# Sur un système existant (DANGER : destructif) :
sudo apt install cryptsetup
# Créer une nouvelle partition chiffrée :
sudo cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 --hash sha512 --key-size 512 /dev/sdXY`,
        explanation: 'LUKS2 avec AES-XTS 512 bits est le standard recommandé par l\'ANSSI.',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R56', label: 'ANSSI BP-028 — Chiffrement des données', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
      { type: 'NIST', ref: 'SP 800-111', label: 'NIST Guide to Storage Encryption Technologies', url: 'https://csrc.nist.gov/publications/detail/sp/800-111/final' },
      { type: 'MITRE', ref: 'T1200', label: 'MITRE ATT&CK — Hardware Additions', url: 'https://attack.mitre.org/techniques/T1200/' },
    ],
    quickFacts: [
      '43% des violations de données impliquent des actifs physiques perdus ou volés (IBM Cost of a Data Breach)',
      'FileVault sur Apple Silicon (M1/M2) chiffre le disque au niveau hardware — performance quasi nulle',
      'Une partition LUKS peut contenir plusieurs clés — permettre la récupération par l\'administrateur système',
    ],
  },

  // ─── Intégrité Système ──────────────────────────────────────────────────────
  system: {
    id: 'system',
    label: 'Intégrité du système',
    icon: "shield",
    description: 'Les mécanismes d\'intégrité système (SIP sur macOS, AppArmor/SELinux sur Linux) limitent les capacités d\'un attaquant même après une compromission initiale. Ils empêchent les modifications des fichiers système critiques.',
    whyItMatters: 'Après compromission initiale, un attaquant cherche à persister et escalader ses privilèges. SIP et SELinux/AppArmor rendent cette étape extrêmement difficile, même avec les droits root.',
    riskScore: 85,
    anssiRefs: ['R51', 'R52', 'R53'],
    attackTypes: [
      {
        name: 'Installation de rootkit',
        technique: 'T1014',
        description: 'Un attaquant avec root peut modifier des binaires système (/bin/ls, /bin/ps) pour masquer sa présence. SIP empêche cette modification même en root.',
        severity: 'CRITICAL',
        impact: 'Persistance indétectable, masquage de l\'attaque, backdoor permanente.',
      },
      {
        name: 'Escalade de privilèges via module kernel',
        technique: 'T1215',
        description: 'Un attaquant peut charger un module noyau malveillant pour obtenir les droits kernel. SIP/SecureBoot l\'empêche sur macOS et UEFI SecureBoot sur Linux.',
        severity: 'CRITICAL',
        impact: 'Contrôle total du noyau, contournement de tous les mécanismes de sécurité.',
      },
      {
        name: 'Exploitation de processus sans confinement',
        technique: 'T1055',
        description: 'Sans AppArmor/SELinux, un processus compromis (nginx, apache) peut accéder à n\'importe quel fichier sur le système.',
        severity: 'HIGH',
        impact: 'Accès aux clés SSH, bases de données, fichiers de configuration sensibles.',
      },
    ],
    auditCommands: [
      {
        os: 'macos',
        label: 'Vérifier SIP (System Integrity Protection)',
        command: 'csrutil status',
        explanation: 'SIP protège les répertoires système (/System, /bin, /sbin, /usr) même en root.',
        expectedGood: 'System Integrity Protection status: enabled.',
      },
      {
        os: 'macos',
        label: 'Vérifier Gatekeeper et XProtect',
        command: 'spctl --status && spctl --list 2>/dev/null | head -5',
        explanation: 'Gatekeeper empêche l\'exécution d\'applications non signées/non notariées.',
        expectedGood: 'assessments enabled',
      },
      {
        os: 'linux',
        label: 'Vérifier le statut SELinux',
        command: 'getenforce 2>/dev/null || sestatus 2>/dev/null | head -3',
        explanation: 'SELinux en mode Enforcing confine les processus selon des politiques strictes.',
        expectedGood: 'Enforcing',
      },
      {
        os: 'linux',
        label: 'Vérifier AppArmor (Ubuntu/Debian)',
        command: 'sudo apparmor_status 2>/dev/null | head -10 || sudo aa-status 2>/dev/null | head -10',
        explanation: 'AppArmor confine les applications avec des profils de sécurité.',
        expectedGood: 'apparmor module is loaded, N profiles in enforce mode',
      },
      {
        os: 'linux',
        label: 'Vérifier l\'intégrité des binaires système',
        command: 'sudo debsums -c 2>/dev/null | head -20 || sudo rpm -Va 2>/dev/null | grep "^..5" | head -20',
        explanation: 'Vérifie l\'intégrité des fichiers installés par les packages.',
        expectedGood: 'Aucun binaire modifié en dehors des mises à jour normales.',
      },
      {
        os: 'windows',
        label: 'Vérifier Windows Defender (protection temps réel)',
        command: 'Get-MpComputerStatus | Select-Object AMServiceEnabled, AntispywareEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, NISSignatureLastUpdated | Format-List',
        explanation: 'Contrôle que Windows Defender est actif et ses signatures à jour (< 7 jours).',
        expectedGood: 'AMServiceEnabled=True, RealTimeProtectionEnabled=True, signatures < 7 jours',
      },
      {
        os: 'windows',
        label: 'Vérifier SecureBoot et TPM',
        command: 'Write-Host "SecureBoot:"; Confirm-SecureBootUEFI 2>&1\nWrite-Host "TPM Ready:"; (Get-Tpm).TpmReady\nWrite-Host "TPM Activated:"; (Get-Tpm).TpmActivated',
        explanation: 'SecureBoot empêche le chargement de bootloaders non signés. TPM sécurise BitLocker et les mesures d\'intégrité.',
        expectedGood: 'SecureBoot=True, TpmReady=True, TpmActivated=True',
      },
    ],
    remediationSteps: [
      {
        os: 'macos',
        label: 'Réactiver SIP (si désactivé)',
        command: `# Nécessite le mode Recovery (redémarrage + maintien Cmd+R)
# Dans Terminal Recovery :
csrutil enable
# Redémarrer normalement
reboot`,
        explanation: 'SIP ne peut être (ré)activé que depuis le mode Recovery. Sa désactivation est un signal d\'alarme majeur.',
      },
      {
        os: 'linux',
        label: 'Activer SELinux en mode Enforcing',
        command: `sudo sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
sudo setenforce 1
# Vérifier les alertes
sudo ausearch -m AVC -ts recent | head -20`,
        explanation: 'SELinux enforcing est la configuration cible. Si des denials légitimes apparaissent, créer des modules de politique plutôt que de désactiver.',
      },
      {
        os: 'windows',
        label: 'Réactiver Windows Defender et mettre à jour les signatures',
        command: 'Set-MpPreference -DisableRealtimeMonitoring $false\nSet-MpPreference -DisableBehaviorMonitoring $false\nSet-MpPreference -DisableIOAVProtection $false\nUpdate-MpSignature\nStart-MpScan -ScanType QuickScan',
        explanation: 'Réactive la protection temps réel Defender, met à jour les signatures et lance un scan rapide.',
      },
      {
        os: 'linux',
        label: 'Installer AIDE (Advanced Intrusion Detection Environment)',
        command: `sudo apt install aide -y   # Debian/Ubuntu
# OU
sudo dnf install aide -y  # RHEL/Fedora
# Initialiser la base de référence
sudo aide --init
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz
# Programmer la vérification quotidienne
echo "0 3 * * * root /usr/bin/aide --check 2>&1 | mail -s 'AIDE Check' admin@domain.fr" | sudo tee /etc/cron.d/aide`,
        explanation: 'AIDE détecte toute modification non autorisée des fichiers système en comparant avec une base de référence cryptographique.',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R51', label: 'ANSSI BP-028 — Intégrité du système', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
      { type: 'MITRE', ref: 'T1014', label: 'MITRE ATT&CK — Rootkit', url: 'https://attack.mitre.org/techniques/T1014/' },
      { type: 'NIST', ref: 'SP 800-155', label: 'NIST BIOS Integrity Measurement', url: 'https://csrc.nist.gov/publications/detail/sp/800-155/draft' },
    ],
    quickFacts: [
      'SIP sur macOS protège /System, /bin, /sbin, /usr (sauf /usr/local) même avec sudo',
      'SELinux en mode enforcing réduit la surface d\'exploitation de 90% selon NSA',
      'AIDE peut détecter une modification de fichier en quelques octets, y compris les timestamps',
    ],
  },

  // ─── Comptes Utilisateurs ───────────────────────────────────────────────────
  users: {
    id: 'users',
    label: 'Comptes utilisateurs',
    icon: "users",
    description: 'La gestion des comptes utilisateurs, des droits sudo et des politiques de mots de passe est critique. Les comptes mal configurés ou abandonnés sont des vecteurs d\'attaque privilégiés.',
    whyItMatters: 'Un compte avec NOPASSWD dans sudo est équivalent à un compte root. Un compte inactif avec mot de passe faible est une porte dérobée. La règle du moindre privilège est le fondement de la sécurité.',
    riskScore: 88,
    anssiRefs: ['R30', 'R31', 'R32', 'R33', 'R34', 'R36', 'R37'],
    attackTypes: [
      {
        name: 'Escalade de privilèges via sudo NOPASSWD',
        technique: 'T1548.003',
        description: 'Une règle NOPASSWD dans sudoers permet à un attaquant ayant compromis un compte utilisateur d\'exécuter des commandes root sans mot de passe.',
        severity: 'CRITICAL',
        impact: 'Élévation immédiate vers root, compromission totale du système.',
      },
      {
        name: 'Comptes de service avec shell interactif',
        technique: 'T1078.003',
        description: 'Les comptes de service (www-data, mysql, postgres) avec /bin/bash comme shell peuvent être utilisés pour se connecter si compromis.',
        severity: 'HIGH',
        impact: 'Accès initial via compte de service, mouvement latéral.',
      },
      {
        name: 'Exploitation de comptes inactifs',
        technique: 'T1078.003',
        description: 'Les comptes non utilisés depuis plusieurs mois sont des cibles : leurs mots de passe ne changent pas, les utilisateurs ne surveillent pas les alertes.',
        severity: 'HIGH',
        impact: 'Accès persistant non détecté pendant des semaines/mois.',
      },
      {
        name: 'Attaque par dictionnaire sur mots de passe locaux',
        technique: 'T1110.002',
        description: 'Un attaquant ayant accès à /etc/shadow peut tenter de casser les mots de passe hachés hors ligne avec hashcat/john.',
        severity: 'MEDIUM',
        impact: 'Récupération de mots de passe, réutilisation sur d\'autres systèmes.',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Lister les utilisateurs avec shell de connexion',
        command: 'awk -F: \'($7!~/false|nologin/) && $3>=1000 {print $1, "UID="$3, "Shell="$7}\' /etc/passwd',
        explanation: 'Identifie tous les comptes qui peuvent se connecter interactivement.',
        expectedGood: 'Seuls les utilisateurs humains légitimes avec un shell interactif.',
      },
      {
        os: 'linux',
        label: 'Vérifier les règles sudo NOPASSWD',
        command: 'sudo grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ 2>/dev/null',
        explanation: 'NOPASSWD dans sudoers est un risque de sécurité majeur.',
        expectedGood: 'Aucun résultat, ou seulement des exceptions documentées et justifiées.',
      },
      {
        os: 'linux',
        label: 'Vérifier la politique d\'expiration des mots de passe',
        command: 'sudo grep -E "^PASS_(MAX|MIN|WARN)_DAYS" /etc/login.defs && sudo chage -l root',
        explanation: 'Vérifie les paramètres d\'expiration des mots de passe.',
        expectedGood: 'PASS_MAX_DAYS 90, PASS_MIN_DAYS 1, PASS_WARN_AGE 14',
      },
      {
        os: 'linux',
        label: 'Identifier les comptes UID 0 (root) cachés',
        command: 'awk -F: \'$3==0 {print "UID0:", $1}\' /etc/passwd',
        explanation: 'Tout compte avec UID 0 a les mêmes droits que root — il ne devrait y en avoir qu\'un seul.',
        expectedGood: 'Seul root a UID 0.',
      },
      {
        os: 'macos',
        label: 'Vérifier le compte invité et les comptes admin',
        command: 'dscl . -list /Users UniqueID | awk \'$2>=500\' && sudo dscl . -read /Users/Guest UserShell',
        explanation: 'Liste les comptes utilisateurs macOS et vérifie le statut du compte invité.',
        expectedGood: 'Compte invité désactivé (UserShell: /usr/bin/false)',
      },
      {
        os: 'windows',
        label: 'Lister les comptes locaux Windows',
        command: 'Get-LocalUser | Select-Object Name, Enabled, PasswordExpires, LastLogon, PasswordLastSet | Format-Table -AutoSize',
        explanation: 'Inventaire des comptes locaux — Administrator intégré doit être désactivé ou renommé.',
        expectedGood: 'Administrator: Enabled=False (ou renommé), Guest: Enabled=False',
      },
      {
        os: 'windows',
        label: 'Vérifier les membres du groupe Administrateurs',
        command: 'Get-LocalGroupMember -Group "Administrators" | Select-Object Name, PrincipalSource, ObjectClass | Format-Table -AutoSize',
        explanation: 'Seuls les comptes nominatifs et justifiés doivent être dans le groupe Administrators.',
        expectedGood: 'Pas de comptes de service, pas de compte Administrator générique activé',
      },
      {
        os: 'windows',
        label: 'Vérifier la politique de mots de passe Windows',
        command: 'net accounts',
        explanation: 'Affiche longueur minimale, durée d\'expiration, historique des mots de passe.',
        expectedGood: 'Minimum password length: 12+, Maximum password age: 90 jours, Password history: 5+',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Verrouiller les comptes inactifs',
        command: `# Verrouiller un compte spécifique
sudo usermod -L username
# Retirer le shell des comptes de service
sudo usermod -s /usr/sbin/nologin service_user
# Lister les comptes sans date d'expiration
sudo chage -l username`,
        explanation: 'Verrouille les comptes non utilisés et retire le shell interactif des comptes de service.',
      },
      {
        os: 'linux',
        label: 'Configurer la politique de mots de passe',
        command: `sudo apt install libpam-pwquality -y  # Debian/Ubuntu
# Configurer /etc/pam.d/common-password :
sudo sed -i 's/pam_pwquality.so.*/pam_pwquality.so retry=3 minlen=12 dcredit=-1 ucredit=-1 ocredit=-1 lcredit=-1/' /etc/pam.d/common-password
# Configurer l'expiration
sudo sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS 90/' /etc/login.defs
sudo sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS 1/' /etc/login.defs`,
        explanation: 'Impose des mots de passe d\'au moins 12 caractères avec complexité, expiration à 90 jours.',
      },
      {
        os: 'windows',
        label: 'Désactiver le compte Administrator intégré',
        command: 'Disable-LocalUser -Name "Administrator"\nDisable-LocalUser -Name "Guest"\n# Créer un compte admin nommé si nécessaire :\n# New-LocalUser "AdminNom" -Password (Read-Host -AsSecureString) | Add-LocalGroupMember -Group "Administrators"',
        explanation: 'Le compte Administrator intégré est ciblé en premier par les attaques. Utiliser un compte nominatif à la place.',
      },
      {
        os: 'windows',
        label: 'Renforcer la politique de mots de passe',
        command: 'net accounts /minpwlen:12 /maxpwage:90 /minpwage:1 /uniquepw:5\n# Vérifier :\nnet accounts',
        explanation: 'Impose : longueur min 12, expiration 90 jours, délai min 1 jour, historique 5 mots de passe.',
      },
      {
        os: 'linux',
        label: 'Configurer la journalisation sudo',
        command: `sudo bash -c 'cat >> /etc/sudoers.d/security << EOF
Defaults log_input
Defaults log_output
Defaults logfile="/var/log/sudo.log"
EOF'
sudo chmod 440 /etc/sudoers.d/security`,
        explanation: 'Enregistre toutes les commandes exécutées via sudo (ANSSI R33).',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R30', label: 'ANSSI BP-028 — Gestion des comptes', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
      { type: 'CIS', ref: 'CIS L1 5.x', label: 'CIS Benchmark — Access Control', url: 'https://www.cisecurity.org/' },
      { type: 'MITRE', ref: 'T1548.003', label: 'MITRE ATT&CK — Sudo and Sudo Caching', url: 'https://attack.mitre.org/techniques/T1548/003/' },
    ],
    quickFacts: [
      'Le principe du moindre privilège : donner uniquement les droits nécessaires à la mission',
      '81% des violations de données impliquent des credentials volés ou faibles (Verizon DBIR 2023)',
      'NOPASSWD dans sudoers devrait déclencher une alerte immédiate en monitoring',
    ],
  },

  // ─── Services ───────────────────────────────────────────────────────────────
  services: {
    id: 'services',
    label: 'Services et démons',
    icon: "settings",
    description: 'Chaque service actif sur un système est un vecteur d\'attaque potentiel. Les services inutiles, obsolètes (Telnet, FTP, rsh) ou mal configurés élargissent significativement la surface d\'attaque.',
    whyItMatters: 'La règle est simple : ce qui ne tourne pas ne peut pas être compromis. Désactiver les services inutiles réduit mécaniquement le risque. Les protocoles anciens (Telnet, rsh) n\'ont aucune justification en 2025.',
    riskScore: 78,
    anssiRefs: ['R62', 'R63', 'R64', 'R65', 'R66'],
    attackTypes: [
      {
        name: 'Exploitation de services obsolètes',
        technique: 'T1190',
        description: 'Telnet, FTP, rsh et rlogin transmettent les credentials en clair. Un attaquant en position MITM capture immédiatement les mots de passe.',
        severity: 'CRITICAL',
        impact: 'Capture de credentials, accès initial.',
      },
      {
        name: 'Exploitation de vulnérabilités CVE',
        technique: 'T1190',
        description: 'Un service non mis à jour avec une vulnérabilité CVE connue est une cible privilégiée des botnets qui scannent en permanence Internet.',
        severity: 'HIGH',
        impact: 'Exécution de code à distance, ransomware, cryptomining.',
      },
      {
        name: 'Service mal configuré comme point d\'entrée',
        technique: 'T1021',
        description: 'Bluetooth, mDNS, Apple Remote Desktop, ou partages de fichiers activés par défaut sont exploités pour du mouvement latéral.',
        severity: 'MEDIUM',
        impact: 'Accès au réseau local, énumération de ressources.',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Lister les services actifs',
        command: 'systemctl list-units --type=service --state=running --no-legend | awk \'{print $1, $3, $4}\'',
        explanation: 'Identifie tous les services en cours d\'exécution pour revue.',
        expectedGood: 'Seuls les services nécessaires à la mission du serveur.',
      },
      {
        os: 'linux',
        label: 'Détecter les services dangereux',
        command: 'for s in telnet ftp vsftpd rsh rlogin rexec tftp xinetd; do systemctl is-active $s 2>/dev/null && echo "DANGER: $s est actif"; done',
        explanation: 'Vérifie la présence de services legacy dangereux.',
        expectedGood: 'Aucun de ces services ne doit être actif.',
      },
      {
        os: 'macos',
        label: 'Lister les services macOS actifs (LaunchDaemons)',
        command: 'sudo launchctl list | grep -v "^-" | awk \'NR>1 && $3!~/apple/ {print $3}\' | head -20',
        explanation: 'Liste les services tiers actifs sur macOS.',
        expectedGood: 'Seuls les services tiers justifiés et à jour.',
      },
      {
        os: 'macos',
        label: 'Vérifier les services de partage macOS',
        command: 'sudo systemsetup -getremotelogin -getremoteappleevents && sharing -l',
        explanation: 'Vérifie les services de partage macOS (SSH, Remote Events, Screen Sharing).',
        expectedGood: 'Remote Login: Off, Remote Apple Events: Off',
      },
      {
        os: 'windows',
        label: 'Vérifier SMBv1 (vecteur WannaCry / EternalBlue)',
        command: 'Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol | Select-Object FeatureName, State\n# Vérifier aussi côté serveur :\nGet-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol',
        explanation: 'SMBv1 est vulnérable à MS17-010 (EternalBlue), utilisé par WannaCry et NotPetya.',
        expectedGood: 'SMB1Protocol: Disabled, SMB2Protocol: True',
      },
      {
        os: 'windows',
        label: 'Vérifier les services Windows dangereux',
        command: '@("TlntSvr","FTPSVC","WinRM","RemoteRegistry","Browser","SNMP","W3SVC") | ForEach-Object { $s = Get-Service $_ -EA 0; if($s){ [PSCustomObject]@{Service=$_; Status=$s.Status; StartType=$s.StartType} } } | Format-Table -AutoSize',
        explanation: 'Vérifie la présence de services potentiellement dangereux (Telnet, FTP, WinRM, Remote Registry).',
        expectedGood: 'TlntSvr/FTPSVC: Stopped/Disabled. WinRM: Stopped si administration locale seulement.',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Désactiver et supprimer les services dangereux',
        command: `for s in telnet ftp vsftpd rsh rshd rlogin rexec tftp xinetd; do
    sudo systemctl stop $s 2>/dev/null
    sudo systemctl disable $s 2>/dev/null
    sudo apt purge -y $s 2>/dev/null || sudo dnf remove -y $s 2>/dev/null
done`,
        explanation: 'Arrête, désactive et supprime les services legacy dangereux.',
      },
      {
        os: 'macos',
        label: 'Désactiver les services de partage macOS',
        command: `sudo systemsetup -setremotelogin off
sudo systemsetup -setremoteappleevents off
sudo launchctl disable system/com.apple.screensharing
sudo launchctl disable system/com.apple.smbd`,
        explanation: 'Désactive les services de partage réseau non nécessaires sur macOS.',
      },
      {
        os: 'windows',
        label: 'Désactiver SMBv1 (CRITIQUE — EternalBlue)',
        command: 'Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force\nDisable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart\n# Vérifier :\nGet-SmbServerConfiguration | Select-Object EnableSMB1Protocol',
        explanation: 'SMBv1 DOIT être désactivé sur toutes les machines Windows sans exception (CVE-2017-0144).',
      },
      {
        os: 'windows',
        label: 'Désactiver les services Windows non nécessaires',
        command: '# Telnet (jamais nécessaire)\nStop-Service TlntSvr -Force -EA 0; Set-Service TlntSvr -StartupType Disabled -EA 0\n# Remote Registry (dangereux)\nStop-Service RemoteRegistry -Force -EA 0; Set-Service RemoteRegistry -StartupType Disabled -EA 0\n# Computer Browser (protocole legacy)\nStop-Service Browser -Force -EA 0; Set-Service Browser -StartupType Disabled -EA 0',
        explanation: 'Désactive les services Windows legacy inutiles et dangereux (ANSSI CIS L1).',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R62', label: 'ANSSI BP-028 — Services réseaux', url: 'https://www.ssi.gouv.fr/' },
      { type: 'CIS', ref: 'CIS L1 2.x', label: 'CIS Benchmark — Services', url: 'https://www.cisecurity.org/' },
      { type: 'MITRE', ref: 'T1190', label: 'MITRE ATT&CK — Exploit Public-Facing Application', url: 'https://attack.mitre.org/techniques/T1190/' },
    ],
    quickFacts: [
      'Telnet en 2025 = envoi du mot de passe en clair sur le réseau',
      'BlueKeep (CVE-2019-0708) RDP a infecté 800 000 machines en quelques jours — update immédiat requis',
      'La réduction de la surface d\'attaque est le principe le plus efficace en sécurité défensive',
    ],
  },

  // ─── Mises à jour ───────────────────────────────────────────────────────────
  updates: {
    id: 'updates',
    label: 'Gestion des mises à jour',
    icon: "refreshCw",
    description: 'Les mises à jour de sécurité corrigent des vulnérabilités connues (CVE). Un système non mis à jour est une cible prioritaire pour les attaquants qui disposent d\'exploits publics.',
    whyItMatters: 'La majorité des compromissions exploitent des vulnérabilités connues avec des patches disponibles depuis plusieurs semaines. La fenêtre entre publication d\'un CVE et son exploitation passe en dessous de 48h pour les vulnérabilités critiques.',
    riskScore: 92,
    anssiRefs: ['R58', 'R59', 'R61'],
    attackTypes: [
      {
        name: 'Exploitation de CVE avec PoC public',
        technique: 'T1190',
        description: 'Des outils comme Metasploit incluent des exploits pour les CVE publiés. Un système non patché est exploitable par n\'importe quel script kiddie.',
        severity: 'CRITICAL',
        impact: 'Exécution de code à distance, déni de service, escalade de privilèges.',
      },
      {
        name: 'Exploitation zero-day (0day)',
        technique: 'T1190',
        description: 'Les vulnérabilités zero-day sont sans patch disponible. Les mises à jour préventives limitent la fenêtre d\'exposition.',
        severity: 'HIGH',
        impact: 'Compromission avant qu\'un patch soit disponible.',
      },
      {
        name: 'Supply chain attack via paquets malveillants',
        technique: 'T1195.002',
        description: 'Utiliser des dépôts tiers non officiels expose à l\'installation de paquets compromis (typosquatting, dépôts pirates).',
        severity: 'HIGH',
        impact: 'Installation de backdoors, exfiltration de données, cryptomining.',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Lister les mises à jour de sécurité disponibles (Debian/Ubuntu)',
        command: 'sudo apt list --upgradable 2>/dev/null | grep -i security | head -20',
        explanation: 'Affiche les paquets avec des mises à jour de sécurité en attente.',
        expectedGood: 'Aucune mise à jour de sécurité en attente.',
      },
      {
        os: 'linux',
        label: 'Vérifier la date de la dernière mise à jour',
        command: 'grep " install " /var/log/dpkg.log 2>/dev/null | tail -5 || rpm -qa --last | head -5',
        explanation: 'Vérifie quand les dernières mises à jour ont été installées.',
        expectedGood: 'Mises à jour installées dans les 30 derniers jours.',
      },
      {
        os: 'linux',
        label: 'Vérifier unattended-upgrades',
        command: 'sudo systemctl is-active unattended-upgrades && cat /etc/apt/apt.conf.d/50unattended-upgrades | grep -E "^\\s*\\"" | head -10',
        explanation: 'Vérifie si les mises à jour automatiques de sécurité sont configurées.',
        expectedGood: 'active, mises à jour de sécurité automatiques activées',
      },
      {
        os: 'macos',
        label: 'Vérifier les mises à jour macOS disponibles',
        command: 'softwareupdate --list 2>&1 | head -20',
        explanation: 'Liste les mises à jour disponibles pour macOS et les applications système.',
        expectedGood: 'No updates are available.',
      },
      {
        os: 'windows',
        label: 'Vérifier les derniers patches installés',
        command: 'Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 | Format-Table HotFixID, Description, InstalledOn -AutoSize',
        explanation: 'Affiche les 10 derniers KB installés. La date du plus récent ne doit pas dépasser 30 jours.',
        expectedGood: 'Patches installés dans les 30 derniers jours, pas de KB critiques manquants',
      },
      {
        os: 'windows',
        label: 'Lister les mises à jour Windows en attente',
        command: '$s = New-Object -ComObject Microsoft.Update.Session\n$r = $s.CreateUpdateSearcher().Search("IsInstalled=0 and Type=\'Software\' and IsHidden=0")\nWrite-Host "Mises a jour en attente: $($r.Updates.Count)"\n$r.Updates | Select-Object Title | Format-Table -AutoSize',
        explanation: 'Identifie les mises à jour disponibles non encore installées (Windows Update Agent COM).',
        expectedGood: '0 mise à jour en attente — ou uniquement des mises à jour optionnelles',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Appliquer toutes les mises à jour de sécurité',
        command: `sudo apt update && sudo apt upgrade -y
# Ou pour RHEL/CentOS :
sudo dnf update --security -y`,
        explanation: 'Met à jour tous les paquets avec des correctifs de sécurité disponibles.',
      },
      {
        os: 'linux',
        label: 'Activer les mises à jour automatiques',
        command: `sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
# Configurer les mises à jour de sécurité uniquement :
sudo bash -c 'cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF'`,
        explanation: 'Configure les mises à jour automatiques de sécurité quotidiennes (ANSSI R61).',
      },
      {
        os: 'windows',
        label: 'Installer les mises à jour Windows en attente',
        command: '# Via PSWindowsUpdate (recommandé) :\nInstall-Module PSWindowsUpdate -Force -Scope CurrentUser\nGet-WindowsUpdate -Install -AcceptAll -IgnoreReboot\n# Ou déclencher manuellement :\nStart-Process ms-settings:windowsupdate',
        explanation: 'Installe toutes les mises à jour disponibles. Un redémarrage peut être nécessaire.',
      },
      {
        os: 'windows',
        label: 'Activer les mises à jour automatiques Windows',
        command: '$key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU"\nNew-Item -Path $key -Force | Out-Null\nSet-ItemProperty -Path $key -Name "AUOptions" -Value 4  # Telecharger et installer auto\nSet-ItemProperty -Path $key -Name "NoAutoUpdate" -Value 0\nRestart-Service wuauserv',
        explanation: 'Configure Windows Update en mode automatique via registre (AUOptions=4 = télécharger et installer).',
      },
      {
        os: 'macos',
        label: 'Activer les mises à jour automatiques macOS',
        command: `sudo softwareupdate --schedule on
# Via System Preferences/Settings > Software Update > Activate "Automatic updates"
defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true
defaults write com.apple.SoftwareUpdate AutomaticDownload -bool true
defaults write com.apple.SoftwareUpdate CriticalUpdateInstall -bool true`,
        explanation: 'Active les mises à jour automatiques macOS pour les correctifs de sécurité critiques.',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R61', label: 'ANSSI BP-028 — Gestion des mises à jour', url: 'https://www.ssi.gouv.fr/' },
      { type: 'NIST', ref: 'SP 800-40', label: 'NIST Guide to Enterprise Patch Management', url: 'https://csrc.nist.gov/publications/detail/sp/800-40/rev-4/final' },
      { type: 'MITRE', ref: 'T1190', label: 'MITRE ATT&CK — Exploit Public-Facing App', url: 'https://attack.mitre.org/techniques/T1190/' },
      { type: 'CVE', ref: 'CVE-2021-44228', label: 'Log4Shell — CVE critique non patché (exemple)', url: 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-44228' },
    ],
    quickFacts: [
      'La fenêtre moyenne entre publication CVE critique et premier exploit : 4,3 jours (Rapid7, 2023)',
      'Log4Shell (2021) : 72h entre la divulgation et l\'exploitation massive mondiale',
      'Les mises à jour automatiques de sécurité réduisent le risque de 85% selon CISA',
    ],
  },

  // ─── Réseau ─────────────────────────────────────────────────────────────────
  network: {
    id: 'network',
    label: 'Exposition réseau',
    icon: "globe",
    description: 'La surface réseau expose les services aux attaquants. Des ports ouverts inutiles, le forwarding IP activé ou des paramètres sysctl permissifs élargissent la surface d\'attaque.',
    whyItMatters: 'Chaque port ouvert est une opportunité pour un attaquant. Les paramètres réseau du noyau Linux contrôlent des comportements critiques (réponse aux pings, SYN cookies, redirections IP) qui peuvent être exploités pour des attaques de réseau.',
    riskScore: 75,
    anssiRefs: ['R12', 'R65', 'R66'],
    attackTypes: [
      {
        name: 'Attaque SYN Flood (DDoS)',
        technique: 'T1498.001',
        description: 'Un attaquant envoie des milliers de paquets SYN pour saturer la table de connexions TCP, rendant le serveur inaccessible.',
        severity: 'HIGH',
        impact: 'Déni de service, indisponibilité du serveur.',
      },
      {
        name: 'Reconnaissance réseau (fingerprinting)',
        technique: 'T1018',
        description: 'Les réponses aux pings ICMP et les bannières de services permettent d\'identifier le système d\'exploitation, la version et les services.',
        severity: 'LOW',
        impact: 'Cartographie de la cible, planification d\'une attaque ciblée.',
      },
      {
        name: 'IP Forwarding — pivot réseau',
        technique: 'T1599',
        description: 'Si IP Forwarding est activé, un système compromis peut servir de routeur pour atteindre des segments réseau normalement inaccessibles.',
        severity: 'HIGH',
        impact: 'Mouvement latéral, compromission de réseaux internes isolés.',
      },
      {
        name: 'Attaque ARP / ICMP redirect',
        technique: 'T1557.002',
        description: 'Des redirections ICMP malveillantes modifient la table de routage et redirigent le trafic vers un attaquant.',
        severity: 'MEDIUM',
        impact: 'Interception du trafic (MITM).',
      },
    ],
    auditCommands: [
      {
        os: 'linux',
        label: 'Lister les ports en écoute',
        command: 'ss -tlnp | sort -k5 -t: -n | awk \'NR>1 {print $1, $4, $6}\'',
        explanation: 'Identifie tous les services réseau en écoute avec leurs processus.',
        expectedGood: 'Seuls les services nécessaires en écoute, sur des interfaces spécifiques.',
      },
      {
        os: 'linux',
        label: 'Vérifier les paramètres sysctl réseau',
        command: 'sysctl net.ipv4.ip_forward net.ipv4.tcp_syncookies net.ipv4.conf.all.accept_redirects net.ipv4.conf.all.send_redirects net.ipv4.conf.all.accept_source_route',
        explanation: 'Vérifie les paramètres noyau critiques pour la sécurité réseau.',
        expectedGood: 'ip_forward=0, syncookies=1, accept_redirects=0, send_redirects=0, accept_source_route=0',
      },
      {
        os: 'macos',
        label: 'Lister les ports en écoute sur macOS',
        command: 'sudo lsof -i -P -n | grep LISTEN',
        explanation: 'Affiche tous les services réseau en écoute sur macOS.',
        expectedGood: 'Seuls les services connus et nécessaires.',
      },
      {
        os: 'windows',
        label: 'Lister les ports en écoute Windows avec processus',
        command: 'Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess | Sort-Object LocalPort | ForEach-Object { $proc = Get-Process -Id $_.OwningProcess -EA 0; [PSCustomObject]@{ Port=$_.LocalPort; IP=$_.LocalAddress; Process=$proc.Name } } | Format-Table -AutoSize',
        explanation: 'Identifie chaque port ouvert avec le processus responsable.',
        expectedGood: 'Pas de port 23 (Telnet), 21 (FTP), 5900 (VNC) sans tunnel. RDP (3389) restreint par IP.',
      },
      {
        os: 'windows',
        label: 'Vérifier NetBIOS et LLMNR (vecteurs Responder)',
        command: '# NetBIOS :\nGet-WmiObject Win32_NetworkAdapterConfiguration | Where-Object IPEnabled | Select-Object Description, TcpipNetbiosOptions\n# LLMNR :\n$v = (Get-ItemProperty "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" -Name EnableMulticast -EA 0).EnableMulticast\nif($v -eq 0){ "LLMNR: Desactive (OK)" } else { "LLMNR: Actif (RISQUE - Responder)" }',
        explanation: 'NetBIOS/LLMNR actifs permettent des attaques Responder pour capturer des hashes NTLM.',
        expectedGood: 'TcpipNetbiosOptions=2 (Disabled), LLMNR=Disabled (EnableMulticast=0)',
      },
    ],
    remediationSteps: [
      {
        os: 'linux',
        label: 'Durcissement des paramètres réseau sysctl',
        command: `sudo bash -c 'cat >> /etc/sysctl.d/99-security.conf << EOF
# ANSSI R12 — Durcissement réseau
net.ipv4.ip_forward = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv6.conf.all.accept_redirects = 0
EOF'
sudo sysctl -p /etc/sysctl.d/99-security.conf`,
        explanation: 'Applique le durcissement réseau recommandé par l\'ANSSI. Persistant après redémarrage.',
      },
      {
        os: 'windows',
        label: 'Désactiver NetBIOS over TCP/IP',
        command: 'Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" | ForEach-Object { $_.SetTcpipNetbios(2) }\n# 0=DefaultViaDHCP 1=Enabled 2=Disabled',
        explanation: 'NetBIOS over TCP/IP permet des attaques NBNS poisoning. À désactiver sauf si Active Directory l\'exige.',
      },
      {
        os: 'windows',
        label: 'Désactiver LLMNR (Link-Local Multicast Name Resolution)',
        command: '$key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient"\nNew-Item -Path $key -Force | Out-Null\nSet-ItemProperty -Path $key -Name "EnableMulticast" -Value 0\n# Vérifier :\n(Get-ItemProperty $key).EnableMulticast',
        explanation: 'LLMNR est exploité par Responder pour capturer des hashes NTLM sur le réseau local (T1557.001).',
      },
    ],
    sources: [
      { type: 'ANSSI', ref: 'R12', label: 'ANSSI BP-028 — Paramètres réseau noyau', url: 'https://www.ssi.gouv.fr/' },
      { type: 'CIS', ref: 'CIS L1 3.2', label: 'CIS Benchmark — Network Parameters', url: 'https://www.cisecurity.org/' },
      { type: 'MITRE', ref: 'T1498.001', label: 'MITRE ATT&CK — Network DoS: Direct Network Flood', url: 'https://attack.mitre.org/techniques/T1498/001/' },
    ],
    quickFacts: [
      'IP Forwarding activé transforme votre serveur en routeur — dangereux dans 99% des cas',
      'Les SYN cookies protègent efficacement contre les attaques SYN flood avec un coût CPU minimal',
      'Répondre aux pings ICMP externes révèle qu\'un serveur est actif — désactiver en prod',
    ],
  },
  // ─── Stratégies Windows (UAC / GP) ─────────────────────────────────────────
  winpolicies: {
    id: 'winpolicies',
    label: 'Stratégies Windows (UAC / GP)',
    icon: 'settings',
    description: 'UAC, ExecutionPolicy PowerShell, verrouillage de session et les stratégies de groupe (GPO) constituent la colonne vertébrale de la sécurité Windows. Leur mauvaise configuration est exploitée dans 70% des compromissions Windows.',
    whyItMatters: 'UAC désactivé = un malware lancé par l\'utilisateur obtient directement les droits SYSTEM. ExecutionPolicy unrestricted = n\'importe quel script PowerShell s\'exécute sans contrôle. Ce sont les premiers contrôles vérifiés lors d\'un pentest Windows.',
    riskScore: 88,
    anssiRefs: ['CIS WS 2019 L1', 'ANSSI-BP-028'],
    attackTypes: [
      {
        name: 'Bypass UAC',
        technique: 'T1548.002',
        description: 'Même avec UAC activé, de nombreuses techniques de contournement existent (fodhelper.exe, eventvwr, DLL hijacking). Sans UAC du tout, l\'escalade est immédiate.',
        severity: 'CRITICAL',
        impact: 'Élévation vers SYSTEM sans invite utilisateur.',
      },
      {
        name: 'Exécution de scripts PowerShell malveillants',
        technique: 'T1059.001',
        description: 'ExecutionPolicy Unrestricted ou Bypass permet d\'exécuter n\'importe quel script PS1 — les malwares modernes utilisent massivement PowerShell pour éviter la détection.',
        severity: 'HIGH',
        impact: 'Exécution de code malveillant, téléchargement de payload, mouvement latéral.',
      },
      {
        name: 'Session laissée déverrouillée (piggybacking)',
        technique: 'T1078',
        description: 'Une session Windows sans verrouillage automatique laissée sans surveillance est accessible physiquement à tout employé passant à proximité.',
        severity: 'MEDIUM',
        impact: 'Accès non autorisé à la session utilisateur, vol de données, exécution de code.',
      },
    ],
    auditCommands: [
      {
        os: 'windows',
        label: 'Vérifier le statut UAC',
        command: '$uac = (Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System").EnableLUA\nif($uac -eq 1){ "UAC: Actif (OK)" } else { "UAC: DESACTIVE (CRITIQUE)" }\n# Niveau UAC :\n$lvl = (Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System").ConsentPromptBehaviorAdmin\nWrite-Host "ConsentPromptBehaviorAdmin: $lvl (2=toujours, 5=par defaut, 0=JAMAIS)"',
        explanation: 'UAC (EnableLUA=1) est une protection fondamentale. ConsentPromptBehaviorAdmin=2 est le niveau le plus sûr.',
        expectedGood: 'EnableLUA=1, ConsentPromptBehaviorAdmin=2 (invite pour toutes les élévations)',
      },
      {
        os: 'windows',
        label: 'Vérifier l\'ExecutionPolicy PowerShell',
        command: 'Get-ExecutionPolicy -List | Format-Table -AutoSize',
        explanation: 'Liste la politique d\'exécution PS par scope (MachinePolicy, UserPolicy, Process, CurrentUser, LocalMachine).',
        expectedGood: 'MachinePolicy ou LocalMachine: RemoteSigned ou AllSigned. Jamais Unrestricted ou Bypass en permanence.',
      },
      {
        os: 'windows',
        label: 'Vérifier le verrouillage de session automatique',
        command: '$lock = (Get-ItemProperty "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop" -EA 0).ScreenSaverIsSecure\n$timeout = (Get-ItemProperty "HKCU:\\Control Panel\\Desktop" -EA 0).ScreenSaveTimeOut\nWrite-Host "Screensaver protege: $lock (doit etre 1)"\nWrite-Host "Timeout: $timeout secondes (doit etre <= 900)"',
        explanation: 'Le verrouillage automatique empêche l\'accès physique non autorisé à une session laissée sans surveillance.',
        expectedGood: 'ScreenSaverIsSecure=1, ScreenSaveTimeOut<=900 (15 minutes maximum)',
      },
    ],
    remediationSteps: [
      {
        os: 'windows',
        label: 'Activer UAC au niveau maximum',
        command: '$key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"\nSet-ItemProperty -Path $key -Name "EnableLUA" -Value 1\nSet-ItemProperty -Path $key -Name "ConsentPromptBehaviorAdmin" -Value 2\nSet-ItemProperty -Path $key -Name "ConsentPromptBehaviorUser" -Value 3\n# Redémarrage requis pour appliquer',
        explanation: 'Active UAC avec invite pour toutes les élévations (ConsentPromptBehaviorAdmin=2 = le plus sécurisé).',
      },
      {
        os: 'windows',
        label: 'Configurer ExecutionPolicy RemoteSigned',
        command: 'Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force\n# Vérifier :\nGet-ExecutionPolicy -List',
        explanation: 'RemoteSigned autorise les scripts locaux et les scripts distants signés — bon équilibre sécurité/fonctionnalité.',
      },
      {
        os: 'windows',
        label: 'Activer le verrouillage de session automatique (15 min)',
        command: '# Via Group Policy (persistant) :\n$key = "HKCU:\\Control Panel\\Desktop"\nSet-ItemProperty -Path $key -Name "ScreenSaveActive" -Value "1"\nSet-ItemProperty -Path $key -Name "ScreenSaveTimeOut" -Value "900"\nSet-ItemProperty -Path $key -Name "ScreenSaverIsSecure" -Value "1"\n# Appliquer immédiatement :\nrundll32.exe user32.dll,UpdatePerUserSystemParameters',
        explanation: 'Verrouille automatiquement la session après 15 minutes d\'inactivité (ANSSI / CIS L1).',
      },
    ],
    sources: [
      { type: 'CIS', ref: 'CIS WS2019 L1 2.3.x', label: 'CIS Benchmark Windows Server 2019 — Security Options', url: 'https://www.cisecurity.org/benchmark/microsoft_windows_server_2019' },
      { type: 'MITRE', ref: 'T1548.002', label: 'MITRE ATT&CK — Bypass User Account Control', url: 'https://attack.mitre.org/techniques/T1548/002/' },
      { type: 'MITRE', ref: 'T1059.001', label: 'MITRE ATT&CK — PowerShell', url: 'https://attack.mitre.org/techniques/T1059/001/' },
    ],
    quickFacts: [
      'Plus de 60 techniques de bypass UAC documentées sur MITRE — UAC ≠ barrière absolue mais reste essentiel',
      'PowerShell est utilisé dans 89% des attaques fileless (Symantec 2023) — ExecutionPolicy est la première ligne de défense',
      'La fenêtre d\'opportunité physique : un poste déverrouillé 30 secondes suffit pour installer un keylogger USB',
    ],
  },

  // ─── Journalisation Windows ─────────────────────────────────────────────────
  winlogging: {
    id: 'winlogging',
    label: 'Journalisation Windows',
    icon: 'refreshCw',
    description: 'Les journaux Windows (Security, System, Application) et la politique d\'audit enregistrent toutes les actions critiques : connexions, élévations de privilèges, modifications de comptes. Sans ces traces, une intrusion est indétectable et toute investigation forensique est impossible.',
    whyItMatters: 'Un attaquant qui sait que les logs sont insuffisants agit librement. Les journaux Windows permettent de détecter des connexions suspectes, des tentatives d\'escalade, des modifications de comptes et des exécutions de processus anormaux.',
    riskScore: 80,
    anssiRefs: ['CIS WS 2019 L1 17.x', 'ANSSI-BP-028 R71'],
    attackTypes: [
      {
        name: 'Effacement des journaux (Log Tampering)',
        technique: 'T1070.001',
        description: 'Un attaquant ayant des droits admin vide les journaux Windows pour effacer ses traces. Si la taille maximale est trop petite, les vieux événements sont automatiquement écrasés.',
        severity: 'HIGH',
        impact: 'Impossibilité de tracer l\'intrusion, investigation forensique compromise.',
      },
      {
        name: 'Attaques non détectées faute de politique d\'audit',
        technique: 'T1562.002',
        description: 'Sans audit des connexions, des modifications de comptes et des élévations, les attaques passent inaperçues dans les journaux.',
        severity: 'HIGH',
        impact: 'Détection tardive ou nulle d\'une intrusion, perte de preuves légales.',
      },
    ],
    auditCommands: [
      {
        os: 'windows',
        label: 'Vérifier la taille et l\'état des journaux Windows',
        command: 'Get-WinEvent -ListLog "Security","System","Application" | Select-Object LogName, MaximumSizeInBytes, RecordCount, IsEnabled | Format-Table -AutoSize',
        explanation: 'Le journal Security doit avoir une taille minimum de 196 Mo (CIS L1) pour conserver un historique suffisant.',
        expectedGood: 'Security: IsEnabled=True, MaximumSizeInBytes>=200000000 (200 Mo)',
      },
      {
        os: 'windows',
        label: 'Vérifier la politique d\'audit Windows',
        command: 'auditpol /get /category:*',
        explanation: 'Affiche tous les paramètres d\'audit : connexions, gestion de comptes, exécution de processus, accès objets.',
        expectedGood: 'Account Logon: Success and Failure, Account Management: Success and Failure, Logon/Logoff: Success and Failure',
      },
      {
        os: 'windows',
        label: 'Vérifier les derniers événements de connexion (4624/4625)',
        command: 'Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4624,4625; StartTime=(Get-Date).AddDays(-1)} -MaxEvents 20 -EA 0 | Select-Object TimeCreated, Id, @{N="User";E={$_.Properties[5].Value}}, @{N="IP";E={$_.Properties[18].Value}} | Format-Table -AutoSize',
        explanation: '4624=Connexion réussie, 4625=Connexion échouée. Un grand nombre de 4625 indique une attaque brute force.',
        expectedGood: 'Peu d\'échecs (4625), IP sources connues pour les 4624',
      },
    ],
    remediationSteps: [
      {
        os: 'windows',
        label: 'Augmenter la taille des journaux Windows',
        command: 'wevtutil sl Security /ms:209715200   # 200 Mo\nwevtutil sl System /ms:104857600     # 100 Mo\nwevtutil sl Application /ms:52428800  # 50 Mo\n# Vérifier :\nGet-WinEvent -ListLog Security | Select-Object MaximumSizeInBytes',
        explanation: 'Augmente la taille des journaux pour conserver plus d\'historique (recommandation CIS L1 = 196 Mo minimum pour Security).',
      },
      {
        os: 'windows',
        label: 'Activer la politique d\'audit complète',
        command: '# Connexions\nauditpol /set /subcategory:"Logon" /success:enable /failure:enable\nauditpol /set /subcategory:"Logoff" /success:enable\n# Gestion des comptes\nauditpol /set /subcategory:"User Account Management" /success:enable /failure:enable\nauditpol /set /subcategory:"Security Group Management" /success:enable\n# Elévation de privilèges\nauditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable\n# Exécution de processus\nauditpol /set /subcategory:"Process Creation" /success:enable',
        explanation: 'Configure l\'audit complet des événements critiques : connexions, comptes, privilèges, processus.',
      },
      {
        os: 'windows',
        label: 'Activer la journalisation PowerShell (Module + ScriptBlock)',
        command: '$key = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell"\nNew-Item -Path "$key\\ModuleLogging" -Force | Out-Null\nSet-ItemProperty -Path "$key\\ModuleLogging" -Name "EnableModuleLogging" -Value 1\nNew-Item -Path "$key\\ScriptBlockLogging" -Force | Out-Null\nSet-ItemProperty -Path "$key\\ScriptBlockLogging" -Name "EnableScriptBlockLogging" -Value 1',
        explanation: 'Journalise tous les scripts PowerShell exécutés — essentiel pour détecter les attaques fileless (T1059.001).',
      },
    ],
    sources: [
      { type: 'CIS', ref: 'CIS WS2019 L1 17.x', label: 'CIS Benchmark Windows — Audit Policy', url: 'https://www.cisecurity.org/benchmark/microsoft_windows_server_2019' },
      { type: 'MITRE', ref: 'T1070.001', label: 'MITRE ATT&CK — Clear Windows Event Logs', url: 'https://attack.mitre.org/techniques/T1070/001/' },
      { type: 'NIST', ref: 'SP 800-92', label: 'NIST Guide to Computer Security Log Management', url: 'https://csrc.nist.gov/publications/detail/sp/800-92/final' },
    ],
    quickFacts: [
      'Sans audit PowerShell activé, les attaques fileless (80% des APT) sont invisibles dans les logs',
      'Le journal Security Windows écrase les anciens événements par défaut — augmenter à 200 Mo minimum',
      'Event ID 4625 (échec de connexion) > 10/minute = probable brute force en cours',
    ],
  },
};

export const MODULE_ORDER = ['ssh', 'firewall', 'filevault', 'system', 'users', 'services', 'updates', 'network', 'winpolicies', 'winlogging'];
