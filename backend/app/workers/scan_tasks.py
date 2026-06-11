"""Celery tasks for network scan execution."""

import subprocess
from datetime import datetime, timezone

from loguru import logger

from app.workers.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.database.models import Scan, ScanStatus, ScanType


def _get_blackbox_targets() -> list[dict]:
    """
    Determine targets for blackbox scan:
    1. Server's own public IP (what it exposes to internet)
    2. Curated free public test targets (legal to scan)
    """
    from app.scanners.rich_scan import get_server_public_ip, PUBLIC_TEST_TARGETS
    targets = []

    public_ip = get_server_public_ip()
    if public_ip:
        targets.append({"type": "ip", "value": public_ip, "label": f"Serveur (IP publique: {public_ip})"})

    for t in PUBLIC_TEST_TARGETS:
        targets.append({"type": "hostname", "value": t["value"], "label": t["label"]})

    return targets


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

        # Blackbox mode: no targets → scan server's public IP + free test targets
        targets = scan.targets or []
        if not targets or all(not t.get("value") for t in targets):
            blackbox_targets = _get_blackbox_targets()
            log(f"Blackbox mode — targets: {[t['value'] for t in blackbox_targets]}")
            targets = blackbox_targets
            updated_config = dict(scan.config or {})
            updated_config["blackbox_targets"] = [t["value"] for t in targets]
            _update_scan(db, scan, targets=targets, config=updated_config)

        all_discovered: list = []
        for t in targets:
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

        # ── Phase 2: Rich deep scan (skip for DISCOVERY type) ────────────
        all_findings: list[dict] = []
        host_results: list[dict] = []

        if scan.scan_type != ScanType.DISCOVERY:
            _update_scan(db, scan, current_phase="port_scan", progress=35)

            from app.scanners.rich_scan import rich_scan_host, RICH_PORTS
            from app.pentest.scanners.vuln_scanner import get_hardening_hint

            step = 55 / max(len(all_discovered), 1)

            for idx, discovered in enumerate(all_discovered):
                ip = discovered.ip
                log(f"Rich scan on {ip} ({idx+1}/{len(all_discovered)})...")

                try:
                    rich = rich_scan_host(ip, callback=log)
                except Exception as e:
                    log(f"Rich scan failed on {ip}: {e}")
                    rich = {"ip": ip, "hostname": None, "os": None, "open_ports": []}

                host_entry: dict = {
                    "ip": ip,
                    "mac": discovered.mac,
                    "hostname": rich.get("hostname") or discovered.hostname,
                    "os": rich.get("os"),
                    "open_ports": [],
                }

                for p in rich.get("open_ports", []):
                    svc = p.get("service", "")
                    port_num = p.get("port", 0)
                    severity = _classify_port_finding(port_num, svc)
                    hardening = get_hardening_hint(port_num, svc)

                    # Build rich description
                    parts = [p.get("product", "")]
                    if p.get("banner"):
                        parts.append(f"Banner: {p['banner']}")
                    if p.get("http_title"):
                        parts.append(f"Page: {p['http_title']}")
                    if p.get("ssl_subject"):
                        parts.append(f"SSL: {p['ssl_subject']}")
                    if p.get("extra"):
                        parts.extend(p["extra"])
                    description = " | ".join(filter(None, parts))

                    port_info = {
                        "port": port_num,
                        "protocol": p.get("protocol", "tcp"),
                        "service": svc,
                        "product": p.get("product"),
                        "banner": p.get("banner"),
                        "http_title": p.get("http_title"),
                        "http_headers": p.get("http_headers", {}),
                        "ssl_subject": p.get("ssl_subject"),
                        "ssl_expiry": p.get("ssl_expiry"),
                        "ssh_keys": p.get("ssh_keys", []),
                        "extra": p.get("extra", []),
                        "severity": severity,
                    }
                    host_entry["open_ports"].append(port_info)
                    all_findings.append({
                        "host": ip,
                        "severity": severity,
                        "title": f"Port {port_num}/{p.get('protocol','tcp')} — {svc} {p.get('product','')!s}".strip(" —"),
                        "description": description,
                        "hardening": hardening,
                    })

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
