"""Seed test data for development and testing environments."""
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_password_hash
from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.database.models import (
    Base,
    User,
    UserRole,
    Asset,
    AssetType,
    AssetStatus,
    Vulnerability,
    Severity,
    VulnStatus,
    Scan,
    ScanType,
    ScanStatus,
)


def create_users(db: Session) -> dict[str, User]:
    """Create test users with different roles."""
    users = {}

    user_data = [
        ("admin@grc-platform.local", "Admin", "User", UserRole.ADMIN, "GrcAdmin@2024!Secure"),
        ("auditor@grc-platform.local", "Alice", "Auditor", UserRole.AUDITOR, "Auditor@2024!"),
        ("analyst@grc-platform.local", "Bob", "Analyst", UserRole.ANALYST, "Analyst@2024!"),
        ("viewer@grc-platform.local", "Charlie", "Viewer", UserRole.VIEWER, "Viewer@2024!"),
    ]

    for email, first_name, last_name, role, password in user_data:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users[role.value] = existing
            continue

        user = User(
            id=uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=get_password_hash(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        users[role.value] = user

    db.commit()
    print(f"✓ Created {len(users)} users")
    return users


def create_assets(db: Session, admin_user: User) -> list[Asset]:
    """Create sample assets."""
    assets = []

    # Map criticality string to Severity enum
    criticality_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
    }

    asset_data = [
        # Servers
        ("srv-web-01", AssetType.SERVER, "192.168.1.10", "Production Web Server", "critical"),
        ("srv-web-02", AssetType.SERVER, "192.168.1.11", "Production Web Server Backup", "high"),
        ("srv-db-01", AssetType.DATABASE, "192.168.1.20", "Primary Database Server", "critical"),
        ("srv-db-02", AssetType.DATABASE, "192.168.1.21", "Replica Database Server", "high"),
        ("srv-app-01", AssetType.SERVER, "192.168.1.30", "Application Server", "high"),
        ("srv-mail-01", AssetType.SERVER, "192.168.1.40", "Mail Server", "medium"),
        ("srv-file-01", AssetType.SERVER, "192.168.1.50", "File Server", "medium"),

        # Workstations
        ("ws-dev-01", AssetType.WORKSTATION, "192.168.2.10", "Developer Workstation", "low"),
        ("ws-dev-02", AssetType.WORKSTATION, "192.168.2.11", "Developer Workstation", "low"),
        ("ws-admin-01", AssetType.WORKSTATION, "192.168.2.100", "Admin Workstation", "high"),

        # Network devices
        ("fw-main-01", AssetType.NETWORK, "192.168.0.1", "Main Firewall", "critical"),
        ("sw-core-01", AssetType.NETWORK, "192.168.0.10", "Core Switch", "high"),
        ("sw-access-01", AssetType.NETWORK, "192.168.0.20", "Access Switch Floor 1", "medium"),
        ("router-01", AssetType.NETWORK, "192.168.0.2", "Main Router", "critical"),

        # Cloud
        ("aws-ec2-prod", AssetType.CLOUD_INSTANCE, "aws:ec2:i-abc123", "AWS Production Instance", "critical"),
        ("aws-rds-prod", AssetType.CLOUD_INSTANCE, "aws:rds:db-xyz789", "AWS RDS Database", "critical"),
        ("azure-vm-dev", AssetType.CLOUD_INSTANCE, "azure:vm:dev-001", "Azure Dev VM", "low"),

        # Containers
        ("k8s-api-pod", AssetType.CONTAINER, "k8s:default:api-7f8d9", "API Pod", "high"),
        ("k8s-worker-pod", AssetType.CONTAINER, "k8s:default:worker-3a2b1", "Worker Pod", "medium"),

        # Applications
        ("app-crm", AssetType.APPLICATION, "https://crm.company.local", "CRM Application", "high"),
        ("app-erp", AssetType.APPLICATION, "https://erp.company.local", "ERP System", "critical"),
    ]

    for name, asset_type, ip, notes, criticality in asset_data:
        existing = db.query(Asset).filter(Asset.name == name).first()
        if existing:
            assets.append(existing)
            continue

        asset = Asset(
            id=uuid4(),
            name=name,
            hostname=name,
            ip_address=ip,
            asset_type=asset_type,
            status=random.choice([AssetStatus.ACTIVE, AssetStatus.ACTIVE, AssetStatus.ACTIVE, AssetStatus.MAINTENANCE]),
            os=random.choice(["Ubuntu 22.04", "Windows Server 2022", "CentOS 8", "Debian 12", "RHEL 9"]) if asset_type in [AssetType.SERVER, AssetType.WORKSTATION] else None,
            notes=notes,
            criticality=criticality_map[criticality],
            tags=[asset_type.value, criticality],
        )
        db.add(asset)
        assets.append(asset)

    db.commit()
    print(f"✓ Created {len(assets)} assets")
    return assets


def create_vulnerabilities(db: Session, assets: list[Asset], admin_user: User) -> list[Vulnerability]:
    """Create sample vulnerabilities."""
    vulns = []

    vuln_templates = [
        # Critical
        ("CVE-2024-0001", "Remote Code Execution in OpenSSL", Severity.CRITICAL, 9.8,
         "A critical vulnerability allows remote code execution via crafted TLS packets.",
         "Update OpenSSL to version 3.1.5 or later."),
        ("CVE-2024-0002", "SQL Injection in Web Application", Severity.CRITICAL, 9.5,
         "SQL injection vulnerability allows authentication bypass and data exfiltration.",
         "Apply parameterized queries and input validation."),
        ("CVE-2024-0003", "Privilege Escalation in Kernel", Severity.CRITICAL, 9.0,
         "Local privilege escalation to root via kernel vulnerability.",
         "Update kernel to latest patched version."),

        # High
        ("CVE-2024-1001", "Cross-Site Scripting (XSS)", Severity.HIGH, 7.5,
         "Stored XSS vulnerability in user profile page.",
         "Implement proper output encoding."),
        ("CVE-2024-1002", "Insecure Direct Object Reference", Severity.HIGH, 7.2,
         "IDOR allows access to other users' documents.",
         "Implement proper authorization checks."),
        ("CVE-2024-1003", "Weak SSH Configuration", Severity.HIGH, 7.0,
         "SSH server allows weak ciphers and key exchange algorithms.",
         "Update SSH configuration to use strong ciphers only."),
        ("CVE-2024-1004", "Outdated TLS Version", Severity.HIGH, 7.4,
         "Server supports TLS 1.0 and 1.1 which are deprecated.",
         "Disable TLS 1.0/1.1, enable TLS 1.2+ only."),

        # Medium
        ("CVE-2024-2001", "Information Disclosure", Severity.MEDIUM, 5.3,
         "Server version disclosed in HTTP headers.",
         "Remove server version from response headers."),
        ("CVE-2024-2002", "Missing Security Headers", Severity.MEDIUM, 5.0,
         "Missing Content-Security-Policy and X-Frame-Options headers.",
         "Add appropriate security headers."),
        ("CVE-2024-2003", "Session Timeout Too Long", Severity.MEDIUM, 4.8,
         "User sessions do not expire for 24 hours.",
         "Reduce session timeout to 30 minutes."),
        ("CVE-2024-2004", "Verbose Error Messages", Severity.MEDIUM, 4.5,
         "Application exposes stack traces in error responses.",
         "Implement custom error pages without technical details."),

        # Low
        ("CVE-2024-3001", "Cookie Without Secure Flag", Severity.LOW, 3.1,
         "Session cookie missing Secure flag.",
         "Add Secure flag to all cookies."),
        ("CVE-2024-3002", "Missing HSTS Header", Severity.LOW, 2.5,
         "HTTP Strict Transport Security header not implemented.",
         "Add HSTS header with appropriate max-age."),
        ("CVE-2024-3003", "Default Credentials", Severity.LOW, 3.5,
         "Test account with default credentials still active.",
         "Remove or disable test accounts."),

        # Info
        ("INFO-2024-001", "Outdated Software Version", Severity.INFO, 0.0,
         "Software version is 2 minor versions behind latest.",
         "Consider upgrading to latest stable version."),
    ]

    # Map Severity to criticality level for comparison
    severity_to_level = {
        Severity.CRITICAL: 4,
        Severity.HIGH: 3,
        Severity.MEDIUM: 2,
        Severity.LOW: 1,
        Severity.INFO: 0,
    }

    # Distribute vulnerabilities across assets
    for i, asset in enumerate(assets):
        # Critical assets get more vulns
        asset_level = severity_to_level.get(asset.criticality, 2)
        num_vulns = random.randint(1, 4) if asset_level >= 3 else random.randint(0, 2)

        selected_vulns = random.sample(vuln_templates, min(num_vulns, len(vuln_templates)))

        for cve, title, severity, cvss, desc, remediation in selected_vulns:
            # Check if this vuln already exists for this asset
            existing = db.query(Vulnerability).filter(
                Vulnerability.cve_ids.contains([cve]),
                Vulnerability.asset_id == asset.id
            ).first()
            if existing:
                vulns.append(existing)
                continue

            vuln = Vulnerability(
                id=uuid4(),
                title=title,
                description=desc,
                severity=severity,
                cvss_score=cvss,
                cve_ids=[cve],
                asset_id=asset.id,
                status=random.choices(
                    [VulnStatus.OPEN, VulnStatus.IN_PROGRESS, VulnStatus.RESOLVED, VulnStatus.ACCEPTED],
                    weights=[50, 20, 20, 10]
                )[0],
                remediation=remediation,
                discovered_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            )
            db.add(vuln)
            vulns.append(vuln)

    db.commit()
    print(f"✓ Created {len(vulns)} vulnerabilities")
    return vulns


def create_scans(db: Session, assets: list[Asset], admin_user: User) -> list[Scan]:
    """Create sample scans with results."""
    scans = []

    scan_configs = [
        ("Full Infrastructure Scan Q4", ScanType.FULL, 85.5, "A"),
        ("Vulnerability Assessment", ScanType.VULNERABILITY, 72.0, "B"),
        ("Discovery Scan", ScanType.DISCOVERY, 68.5, "C"),
        ("Compliance Check - CIS", ScanType.COMPLIANCE, 78.0, "B"),
        ("Quick Discovery", ScanType.DISCOVERY, 90.2, "A"),
        ("Monthly Routine Scan", ScanType.FULL, 82.0, "B"),
        ("Post-Patch Verification", ScanType.VULNERABILITY, 95.0, "A"),
        ("Full Security Audit", ScanType.FULL, 65.0, "C"),
    ]

    for i, (name, scan_type, score, grade) in enumerate(scan_configs):
        # Vary the dates
        days_ago = (len(scan_configs) - i) * 7 + random.randint(0, 5)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        status = ScanStatus.COMPLETED if i < len(scan_configs) - 1 else random.choice([ScanStatus.PENDING, ScanStatus.RUNNING])

        findings_summary = {
            "critical": random.randint(0, 3) if status == ScanStatus.COMPLETED else 0,
            "high": random.randint(1, 8) if status == ScanStatus.COMPLETED else 0,
            "medium": random.randint(3, 15) if status == ScanStatus.COMPLETED else 0,
            "low": random.randint(5, 20) if status == ScanStatus.COMPLETED else 0,
            "info": random.randint(0, 10) if status == ScanStatus.COMPLETED else 0,
        }

        scan = Scan(
            id=uuid4(),
            name=name,
            scan_type=scan_type,
            status=status,
            targets=[{"ip": a.ip_address, "name": a.name} for a in random.sample(assets, min(5, len(assets)))],
            progress=100 if status == ScanStatus.COMPLETED else random.randint(0, 80),
            score=score if status == ScanStatus.COMPLETED else None,
            grade=grade if status == ScanStatus.COMPLETED else None,
            findings_summary=findings_summary,
            created_at=created_at,
            started_at=created_at + timedelta(minutes=5) if status != ScanStatus.PENDING else None,
            completed_at=created_at + timedelta(hours=random.randint(1, 4)) if status == ScanStatus.COMPLETED else None,
            created_by_id=admin_user.id,
        )
        db.add(scan)
        scans.append(scan)

    db.commit()
    print(f"✓ Created {len(scans)} scans")
    return scans


def seed_database():
    """Main seed function."""
    print("\n🌱 Seeding test database...\n")

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Create test data
        users = create_users(db)
        admin_user = users.get("admin")

        assets = create_assets(db, admin_user)
        vulns = create_vulnerabilities(db, assets, admin_user)
        scans = create_scans(db, assets, admin_user)

        print("\n✅ Database seeded successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Users: {len(users)}")
        print(f"   - Assets: {len(assets)}")
        print(f"   - Vulnerabilities: {len(vulns)}")
        print(f"   - Scans: {len(scans)}")
        print("\n🔑 Test Credentials:")
        print("   Admin:   admin@grc-platform.local / GrcAdmin@2024!Secure")
        print("   Auditor: auditor@grc-platform.local / Auditor@2024!")
        print("   Analyst: analyst@grc-platform.local / Analyst@2024!")
        print("   Viewer:  viewer@grc-platform.local / Viewer@2024!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
