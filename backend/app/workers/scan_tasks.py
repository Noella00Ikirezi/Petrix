"""Celery tasks for network scan execution."""

from datetime import datetime, timezone

from loguru import logger

from app.workers.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.database.models import Scan, ScanStatus, ScanType


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _update_scan(db, scan: Scan, **kwargs):
    for k, v in kwargs.items():
        setattr(scan, k, v)
    db.commit()


def _calculate_score(findings: dict) -> tuple[float, str, str]:
    """Return (score 0-100, grade A-F, risk_level)."""
    critical = findings.get("critical", 0)
    high = findings.get("high", 0)
    medium = findings.get("medium", 0)
    low = findings.get("low", 0)

    penalty = critical * 25 + high * 10 + medium * 4 + low * 1
    score = max(0.0, 100.0 - penalty)

    if score >= 90:
        grade, risk = "A", "low"
    elif score >= 75:
        grade, risk = "B", "low"
    elif score >= 60:
        grade, risk = "C", "medium"
    elif score >= 40:
        grade, risk = "D", "high"
    else:
        grade, risk = "F", "critical"

    return round(score, 1), grade, risk


def _classify_port_finding(port: int, service_name: str) -> str:
    """Classify a finding severity based on port/service."""
    critical_ports = {21, 23, 69, 135, 139, 445, 512, 513, 514, 1099, 1521, 3389, 5900}
    high_ports = {22, 80, 443, 3306, 5432, 6379, 8080, 8443, 27017}

    service_lower = service_name.lower() if service_name else ""
    if any(s in service_lower for s in ("telnet", "ftp", "rsh", "rlogin", "vnc", "rdp")):
        return "critical"
    if port in critical_ports:
        return "critical"
    if port in high_ports:
        return "high"
    return "medium"


@celery_app.task(bind=True, name="scans.execute_scan", soft_time_limit=1800, time_limit=3600)
def execute_scan(self, scan_id: str) -> dict:
    """
    Execute a network scan:
    1. Host discovery (Scapy ARP/ICMP or nmap ping)
    2. Port scan per host (nmap)
    3. Score calculation + findings summary
    """
    db = SessionLocal()

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"error": f"Scan {scan_id} not found"}

        log = lambda msg: logger.info(f"[scan:{scan_id[:8]}] {msg}")  # noqa

        # ── Phase 1: Discovery ────────────────────────────────────────────
        _update_scan(db, scan, current_phase="discovery", progress=5)

        from app.scanners.network_discovery import discover_network

        all_discovered: list = []
        for t in scan.targets or []:
            target_value = t.get("value", "")
            if not target_value:
                continue
            log(f"Discovering {target_value}...")
            result = discover_network(target_value, callback=log)
            all_discovered.extend(result.hosts)

        if not all_discovered:
            _update_scan(
                db, scan,
                status=ScanStatus.COMPLETED,
                progress=100,
                current_phase=None,
                phases_completed=["discovery"],
                completed_at=_utcnow(),
                duration_seconds=(
                    (_utcnow() - scan.started_at).total_seconds()
                    if scan.started_at else 0
                ),
                findings_summary={"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                score=100.0,
                grade="A",
                risk_level="low",
                error_message="No live hosts found",
            )
            return {"status": "completed", "hosts_found": 0}

        log(f"Discovery done: {len(all_discovered)} host(s) found")
        _update_scan(db, scan, progress=30, phases_completed=["discovery"])

        # ── Phase 2: Port scan (skip for DISCOVERY type) ──────────────────
        all_findings: list[dict] = []
        host_results: list[dict] = []

        if scan.scan_type != ScanType.DISCOVERY:
            _update_scan(db, scan, current_phase="port_scan", progress=35)

            try:
                from app.pentest.scanners.nmap_scanner import NmapScanner
                nmap_scanner = NmapScanner()
            except Exception as e:
                log(f"Nmap init failed: {e}")
                nmap_scanner = None

            config = scan.config or {}
            ports = config.get("ports", "1-1000")
            aggressive = scan.scan_type == ScanType.FULL

            step = 30 / max(len(all_discovered), 1)

            for idx, discovered in enumerate(all_discovered):
                ip = discovered.ip
                log(f"Port scan on {ip} ({idx+1}/{len(all_discovered)})...")

                host_entry: dict = {
                    "ip": ip,
                    "mac": discovered.mac,
                    "hostname": discovered.hostname,
                    "open_ports": [],
                }

                if nmap_scanner:
                    try:
                        host = nmap_scanner.scan_host(
                            ip, ports=ports, aggressive=aggressive, callback=log
                        )
                        host_entry["hostname"] = host.hostname or discovered.hostname
                        host_entry["os"] = host.os

                        for port in host.ports:
                            from app.pentest.scanners.models import PortState
                            if port.state != PortState.OPEN:
                                continue

                            service_name = port.service.name if port.service else ""
                            severity = _classify_port_finding(port.number, service_name)

                            port_info = {
                                "port": port.number,
                                "protocol": port.protocol.value,
                                "service": service_name,
                                "product": port.service.product if port.service else None,
                                "version": port.service.version if port.service else None,
                                "severity": severity,
                            }
                            host_entry["open_ports"].append(port_info)
                            all_findings.append({
                                "host": ip,
                                "severity": severity,
                                "title": f"Open port {port.number}/{port.protocol.value} ({service_name})",
                                "description": (
                                    f"Service: {port.service.product or service_name} "
                                    f"{port.service.version or ''}".strip()
                                    if port.service else ""
                                ),
                            })
                    except Exception as e:
                        log(f"Port scan failed on {ip}: {e}")

                host_results.append(host_entry)
                progress = 35 + int(step * (idx + 1))
                _update_scan(db, scan, progress=progress)

            _update_scan(db, scan, phases_completed=["discovery", "port_scan"])

        else:
            # Discovery only — add info findings for each found host
            for discovered in all_discovered:
                host_results.append({"ip": discovered.ip, "mac": discovered.mac, "open_ports": []})
                all_findings.append({
                    "host": discovered.ip,
                    "severity": "info",
                    "title": f"Host discovered: {discovered.ip}",
                    "description": f"Method: {discovered.method}" + (
                        f", MAC: {discovered.mac}" if discovered.mac else ""
                    ),
                })

        # ── Phase 3: Vulnerability check (VULNERABILITY / FULL) ───────────
        vuln_findings: list[dict] = []
        if scan.scan_type in (ScanType.VULNERABILITY, ScanType.FULL) and scan.config.get("vuln_scan"):
            _update_scan(db, scan, current_phase="vuln_check", progress=70)
            log("Running vulnerability checks via nmap scripts...")
            try:
                from app.pentest.scanners.vuln_scanner import VulnScanner
                vuln_scanner = VulnScanner()
                for hresult in host_results:
                    ip = hresult["ip"]
                    open_ports = [str(p["port"]) for p in hresult.get("open_ports", [])]
                    if not open_ports:
                        continue
                    results = vuln_scanner.scan(ip, ports=",".join(open_ports), callback=log)
                    for v in results:
                        vuln_findings.append({
                            "host": ip,
                            "severity": v.get("severity", "medium"),
                            "title": v.get("title", "Vulnerability found"),
                            "description": v.get("description", ""),
                            "cve": v.get("cve"),
                        })
                all_findings.extend(vuln_findings)
            except Exception as e:
                log(f"Vuln check failed: {e}")

        # ── Phase 4: Score & finalize ─────────────────────────────────────
        _update_scan(db, scan, current_phase="scoring", progress=90)

        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in all_findings:
            sev = f.get("severity", "info")
            if sev in summary:
                summary[sev] += 1

        score, grade, risk = _calculate_score(summary)

        phases = ["discovery"]
        if scan.scan_type != ScanType.DISCOVERY:
            phases.append("port_scan")
        if scan.scan_type in (ScanType.VULNERABILITY, ScanType.FULL):
            phases.append("vuln_check")
        phases.append("scoring")

        completed_at = _utcnow()
        duration = (
            (completed_at - scan.started_at).total_seconds()
            if scan.started_at else 0
        )

        # Store detailed results in config so /findings endpoint can serve them
        updated_config = dict(scan.config or {})
        updated_config["_results"] = {
            "hosts": host_results,
            "findings": all_findings,
        }

        _update_scan(
            db, scan,
            status=ScanStatus.COMPLETED,
            progress=100,
            current_phase=None,
            phases_completed=phases,
            completed_at=completed_at,
            duration_seconds=duration,
            findings_summary=summary,
            config=updated_config,
            score=score,
            grade=grade,
            risk_level=risk,
        )

        log(f"Scan complete — {len(all_discovered)} host(s), {len(all_findings)} finding(s), grade {grade}")
        return {
            "status": "completed",
            "hosts_found": len(all_discovered),
            "findings": len(all_findings),
            "grade": grade,
            "score": score,
        }

    except Exception as exc:
        logger.exception(f"Scan {scan_id} failed: {exc}")
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                _update_scan(
                    db, scan,
                    status=ScanStatus.FAILED,
                    error_message=str(exc)[:500],
                    completed_at=_utcnow(),
                )
        except Exception:
            pass
        return {"error": str(exc)}

    finally:
        db.close()
