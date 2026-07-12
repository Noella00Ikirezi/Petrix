"""Static mapping: hardening check_id → list of relevant CVE IDs.

CVEs are referenced from known security advisories and vulnerability databases.
Each CVE is directly exploitable when the corresponding check fails.
"""

# check_id → list of CVE IDs (most severe / most relevant first)
CHECK_CVE_MAP: dict[str, list[str]] = {

    # ─── SSH ──────────────────────────────────────────────────────────────────
    # SSH-001: PermitRootLogin — root brute-force, lateral movement
    "SSH-001": ["CVE-2023-38408", "CVE-2016-0777", "CVE-2016-0778"],
    # SSH-002: PasswordAuthentication — credential spraying, brute force
    "SSH-002": ["CVE-2023-38408", "CVE-2018-15473"],
    # SSH-003: PermitEmptyPasswords — trivial authentication bypass
    "SSH-003": ["CVE-2008-5161", "CVE-2015-5600"],
    # SSH-004: X11Forwarding — X11 hijacking, session injection
    "SSH-004": ["CVE-2008-1483"],
    # SSH-005: AllowAgentForwarding — SSH agent hijacking
    "SSH-005": ["CVE-2023-38408"],
    # SSH-006: AllowTcpForwarding — unauthorized tunneling
    "SSH-006": [],
    # SSH-007: UsePAM — authentication bypass if PAM disabled
    "SSH-007": [],
    # SSH-008: LoginGraceTime — DoS via connection exhaustion
    "SSH-008": ["CVE-2024-6387"],
    # SSH-009: StrictModes — config file permission exploits
    "SSH-009": [],
    # SSH-011: Banner — missing legal warning (compliance)
    "SSH-011": [],
    # SSH-012: IgnoreRhosts — rhosts-based auth bypass
    "SSH-012": ["CVE-2015-5600"],
    # SSH-013: HostbasedAuthentication — host spoofing
    "SSH-013": [],
    # SSH-015: MaxAuthTries — brute-force resistance
    "SSH-015": ["CVE-2024-6387", "CVE-2018-15473"],
    # SSH-016: ClientAliveInterval — zombie session resource exhaustion
    "SSH-016": [],
    # SSH-017: ClientAliveCountMax
    "SSH-017": [],
    # SSH-018: PermitUserEnvironment — env injection via SSH
    "SSH-018": [],
    # SSH-019: PrintLastLog — audit trail
    "SSH-019": [],
    # SSH-023: OpenSSH version — Terrapin attack, regreSSHion
    "SSH-023": ["CVE-2023-48795", "CVE-2024-6387", "CVE-2023-38408"],

    # ─── FIREWALL ─────────────────────────────────────────────────────────────
    "FW-001": [],
    "FW-002": [],

    # ─── KERNEL / SYSCTL ──────────────────────────────────────────────────────
    # KRN-001: ASLR disabled → return-to-libc, heap/stack spray
    "KRN-001": ["CVE-2021-4034", "CVE-2016-5195"],
    # KRN-002: SYN cookies — SYN flood DoS
    "KRN-002": ["CVE-1999-0116"],
    # KRN-003: IP forwarding — man-in-the-middle, routing attacks
    "KRN-003": [],
    # KRN-004/005/006: ICMP redirects / source routing — MITM
    "KRN-004": [],
    "KRN-005": [],
    "KRN-006": [],
    "KRN-007": [],
    # KRN-008: dmesg_restrict — kernel address disclosure
    "KRN-008": ["CVE-2021-4034"],
    # KRN-009: kptr_restrict — kernel pointer leaks → exploit primitives
    "KRN-009": ["CVE-2021-4034", "CVE-2021-3156"],
    # KRN-010: suid_dumpable — credential leak via core dump
    "KRN-010": [],
    "KRN-011": [],
    # KRN-012: ptrace_scope — process injection, credential theft
    "KRN-012": ["CVE-2019-13272"],
    "KRN-013": [],
    "KRN-014": [],
    "KRN-015": [],
    "KRN-016": [],
    # KRN-017: Smurf amplification
    "KRN-017": ["CVE-1998-0107"],
    "KRN-018": [],
    # KRN-019: SysRq — direct kernel commands
    "KRN-019": [],
    "KRN-020": [],

    # ─── USERS / ACCOUNTS ─────────────────────────────────────────────────────
    # USR-001: Extra UID-0 accounts — trivial privilege escalation
    "USR-001": [],
    # USR-002: Empty passwords — unauthenticated access
    "USR-002": [],
    # USR-003: Sudo NOPASSWD — instant root via sudo
    "USR-003": ["CVE-2021-3156", "CVE-2019-14287", "CVE-2021-4034"],
    # USR-004: Shell accounts inventory
    "USR-004": [],
    # USR-005/006/007: Password policy — credential aging
    "USR-005": [],
    "USR-006": [],
    "USR-007": [],
    # USR-009: UMASK — world-readable file creation
    "USR-009": [],
    # USR-010: dot in root PATH — path hijacking
    "USR-010": [],
    "USR-011": [],
    "USR-012": [],

    # ─── PAM ──────────────────────────────────────────────────────────────────
    # PAM-001/002: Weak passwords → credential stuffing
    "PAM-001": [],
    "PAM-002": [],
    "PAM-003": [],
    # PAM-004: Password history — reuse attack
    "PAM-004": [],
    # PAM-005/006: Account lockout — brute force
    "PAM-005": ["CVE-2024-6387"],
    "PAM-006": [],

    # ─── SERVICES ─────────────────────────────────────────────────────────────
    # SVC-001: Telnet — cleartext credentials
    "SVC-001": ["CVE-2011-4862"],
    # SVC-002/003/004: rsh/rlogin/rexec — trust-based auth bypass
    "SVC-002": [],
    "SVC-003": [],
    "SVC-004": [],
    # SVC-005: TFTP — unauthenticated file read/write
    "SVC-005": [],
    # SVC-006: FTP cleartext
    "SVC-006": ["CVE-2015-3306"],
    # SVC-007: finger — user enumeration
    "SVC-007": [],
    "SVC-008": [],
    "SVC-009": [],
    "SVC-010": [],
    # SVC-011: NFS — unauthenticated export
    "SVC-011": ["CVE-2017-0144"],
    # SVC-012: NIS/YP — insecure directory service
    "SVC-012": [],

    # ─── FILESYSTEM ───────────────────────────────────────────────────────────
    # FS-001: Excessive setuid binaries → local privilege escalation
    "FS-001": ["CVE-2021-4034", "CVE-2021-3156"],
    # FS-002: /tmp sticky bit — symlink attacks, TOCTOU
    "FS-002": ["CVE-2017-8295"],
    # FS-003: World-writable directories — arbitrary write
    "FS-003": [],
    "FS-006": [],

    # ─── LOGGING ──────────────────────────────────────────────────────────────
    "LOG-001": [],
    "LOG-002": [],
    "LOG-003": [],
    "LOG-004": [],

    # ─── PERMISSIONS ──────────────────────────────────────────────────────────
    # PERM-001/002/003: /etc/passwd+shadow+gshadow permissions → hash theft
    "PERM-001": [],
    "PERM-002": ["CVE-2002-0824"],
    "PERM-003": [],
    "PERM-004": [],
    # PERM-005: /etc/sudoers writable → instant root
    "PERM-005": ["CVE-2021-3156"],
    "PERM-006": [],
    "PERM-007": [],
    "PERM-008": [],
    # PERM-009: /root world-accessible → sensitive file exposure
    "PERM-009": [],
    # PERM-010: .rhosts/.netrc — trust-based auth bypass
    "PERM-010": ["CVE-2015-5600"],

    # ─── MOUNTS ───────────────────────────────────────────────────────────────
    "MNT-001": [],
    # MNT-002: /tmp nosuid — setuid execution in /tmp
    "MNT-002": ["CVE-2021-4034"],
    # MNT-003: /tmp noexec — script execution in /tmp
    "MNT-003": [],
    "MNT-004": [],
    # MNT-005/006: /dev/shm nosuid/noexec — in-memory payload execution
    "MNT-005": ["CVE-2021-4034"],
    "MNT-006": ["CVE-2021-4034"],
    "MNT-007": [],
    "MNT-008": [],
    "MNT-009": [],

    # ─── NTP ──────────────────────────────────────────────────────────────────
    "NTP-001": [],
    "NTP-002": [],

    # ─── NETWORK ──────────────────────────────────────────────────────────────
    "NET-000": [],

    # ─── PACKAGES ─────────────────────────────────────────────────────────────
    # PKG-001: Unpatched packages — all unpatched CVEs apply
    "PKG-001": ["CVE-2021-44228", "CVE-2021-4034", "CVE-2021-3156", "CVE-2023-38408"],

    # ─── macOS SPECIFIC ───────────────────────────────────────────────────────
    # SIP-001: SIP disabled — rootkit, kernel extension attacks
    "SIP-001": ["CVE-2021-30892", "CVE-2021-30883"],
    # SIP-002: Gatekeeper disabled — unsigned malware execution
    "SIP-002": ["CVE-2021-30657", "CVE-2022-22616"],
    # FV-001: FileVault disabled — offline disk decryption
    "FV-001": [],
    # SHR-001: Screen sharing — remote access without additional auth
    "SHR-001": [],
    # SHR-002: SMB file sharing
    "SHR-002": ["CVE-2017-0144", "CVE-2019-0703"],
    "SHR-003": [],
    # SHR-004: FTP
    "SHR-004": ["CVE-2015-3306"],
    # SHR-005: Remote Desktop
    "SHR-005": ["CVE-2019-0708", "CVE-2019-1181", "CVE-2019-1182"],
    "SHR-006": [],
    # UPD-001 (macOS): unpatched system
    "UPD-001": ["CVE-2021-30892", "CVE-2022-22616", "CVE-2021-44228"],

    # ─── WINDOWS SPECIFIC ─────────────────────────────────────────────────────
    # SEC-001: Windows Defender disabled
    "SEC-001": [],
    # SEC-002: Outdated AV signatures
    "SEC-002": [],
    # SEC-003: BitLocker disabled
    "SEC-003": [],
    # SVC-001 (Windows): Telnet
    # (already mapped above)
    # SVC-002: Remote Registry — remote registry modification
    # (already mapped above)
    # POL-001: UAC disabled — privilege escalation
    "POL-001": ["CVE-2021-36934", "CVE-2021-1732"],
    # POL-002: No screen lock
    "POL-002": [],
    # POL-003: PowerShell unrestricted execution
    "POL-003": ["CVE-2020-0601"],
    # USR-003 (Windows): auto-logon
    # USR-004 (Windows): guest account
    "USR-004": [],
    # LOG-001/002 (Windows): audit logging
    # (already mapped above)
}


def get_cves_for_check(check_id: str) -> list[str]:
    """Return the CVE list for a given check_id, or [] if unknown."""
    return CHECK_CVE_MAP.get(check_id, [])
