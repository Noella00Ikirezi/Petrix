"""Tests for the HCO Hardening API — targets, sessions, findings endpoints."""
import uuid
import pytest
from unittest.mock import patch

from app.core.security import create_access_token
from app.infrastructure.database.models import User
from app.core.permissions import UserRole
from app.infrastructure.database.hardening_models import (
    HardeningTarget,
    HardeningSession,
    HardeningSessionStatus,
    HardeningFinding,
)

BASE = "/api/v1/hardening"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="admin@petrix.local",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
        full_name="Admin Test",
        mfa_enabled=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(admin_user):
    token = create_access_token({"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_target(db_session, admin_user):
    target = HardeningTarget(
        id=uuid.uuid4(),
        created_by_id=admin_user.id,
        name="Test Server",
        host="192.168.1.10",
        port=22,
        username="root",
        os_type="linux",
        description="Unit test target",
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


@pytest.fixture
def sample_session(db_session, admin_user, sample_target):
    session = HardeningSession(
        id=uuid.uuid4(),
        target_id=sample_target.id,
        created_by_id=admin_user.id,
        status=HardeningSessionStatus.COMPLETED,
        modules_requested=["ssh", "users"],
        modules_completed=["ssh", "users"],
        progress=100,
        score=72.5,
        grade="B",
        total_findings=2,
        total_checks=10,
        passed_checks=8,
        findings_summary={"CRITICAL": 0, "HIGH": 1, "MEDIUM": 1, "LOW": 0, "INFO": 0},
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


# ---------------------------------------------------------------------------
# /modules — public-ish endpoint (still requires auth)
# ---------------------------------------------------------------------------

class TestModulesEndpoint:
    def test_list_modules_returns_200(self, client, auth_headers):
        r = client.get(f"{BASE}/modules", headers=auth_headers)
        assert r.status_code == 200

    def test_modules_has_linux_key(self, client, auth_headers):
        data = client.get(f"{BASE}/modules", headers=auth_headers).json()
        assert "modules_by_os" in data
        assert "linux" in data["modules_by_os"]

    def test_linux_has_7_modules(self, client, auth_headers):
        data = client.get(f"{BASE}/modules", headers=auth_headers).json()
        assert len(data["modules_by_os"]["linux"]) == 7

    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{BASE}/modules")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Targets — CRUD
# ---------------------------------------------------------------------------

class TestTargetCreate:
    def test_create_minimal_target(self, client, auth_headers):
        r = client.post(f"{BASE}/targets", json={
            "name": "Prod-01",
            "host": "10.0.0.1",
            "password": "secret",
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["host"] == "10.0.0.1"
        assert data["port"] == 22
        assert data["os_type"] == "linux"
        assert "id" in data

    def test_create_target_with_all_fields(self, client, auth_headers):
        r = client.post(f"{BASE}/targets", json={
            "name": "Full Target",
            "host": "172.16.0.5",
            "port": 2222,
            "username": "ubuntu",
            "os_type": "linux",
            "description": "Full test",
            "password": "pass123",
            "tags": ["prod", "web"],
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["port"] == 2222
        assert data["username"] == "ubuntu"

    def test_unauthenticated_create_returns_401(self, client):
        r = client.post(f"{BASE}/targets", json={"name": "X", "host": "1.2.3.4"})
        assert r.status_code == 401


class TestTargetList:
    def test_empty_list(self, client, auth_headers):
        r = client.get(f"{BASE}/targets", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_existing_targets(self, client, auth_headers, sample_target):
        r = client.get(f"{BASE}/targets", headers=auth_headers)
        assert r.status_code == 200
        ids = [t["id"] for t in r.json()]
        assert str(sample_target.id) in ids


class TestTargetGet:
    def test_get_existing_target(self, client, auth_headers, sample_target):
        r = client.get(f"{BASE}/targets/{sample_target.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Test Server"

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        r = client.get(f"{BASE}/targets/{uuid.uuid4()}", headers=auth_headers)
        assert r.status_code == 404


class TestTargetDelete:
    def test_delete_existing_target(self, client, auth_headers, sample_target):
        r = client.delete(f"{BASE}/targets/{sample_target.id}", headers=auth_headers)
        assert r.status_code == 204

    def test_delete_removes_from_list(self, client, auth_headers, sample_target):
        client.delete(f"{BASE}/targets/{sample_target.id}", headers=auth_headers)
        r = client.get(f"{BASE}/targets", headers=auth_headers)
        ids = [t["id"] for t in r.json()]
        assert str(sample_target.id) not in ids

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete(f"{BASE}/targets/{uuid.uuid4()}", headers=auth_headers)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class TestSessionCreate:
    def test_create_session_dispatches_celery(self, client, auth_headers, sample_target):
        with patch("app.api.v1.hardening.run_hardening_session") as mock_task:
            mock_task.delay.return_value = None
            r = client.post(f"{BASE}/sessions", json={
                "target_id": str(sample_target.id),
            }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "pending"
        assert data["target_id"] == str(sample_target.id)
        mock_task.delay.assert_called_once()

    def test_create_session_with_specific_modules(self, client, auth_headers, sample_target):
        with patch("app.api.v1.hardening.run_hardening_session") as mock_task:
            mock_task.delay.return_value = None
            r = client.post(f"{BASE}/sessions", json={
                "target_id": str(sample_target.id),
                "modules": ["ssh", "firewall"],
            }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert "ssh" in data["modules_requested"]
        assert "firewall" in data["modules_requested"]

    def test_create_session_unknown_target_returns_404(self, client, auth_headers):
        r = client.post(f"{BASE}/sessions", json={
            "target_id": str(uuid.uuid4()),
        }, headers=auth_headers)
        assert r.status_code == 404


class TestSessionList:
    def test_list_sessions_empty(self, client, auth_headers):
        r = client.get(f"{BASE}/sessions", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_sessions_includes_existing(self, client, auth_headers, sample_session):
        r = client.get(f"{BASE}/sessions", headers=auth_headers)
        ids = [s["id"] for s in r.json()]
        assert str(sample_session.id) in ids


class TestSessionGet:
    def test_get_existing_session(self, client, auth_headers, sample_session):
        r = client.get(f"{BASE}/sessions/{sample_session.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "completed"
        assert data["score"] == 72.5
        assert data["grade"] == "B"

    def test_get_nonexistent_session_returns_404(self, client, auth_headers):
        r = client.get(f"{BASE}/sessions/{uuid.uuid4()}", headers=auth_headers)
        assert r.status_code == 404


class TestSessionFindings:
    @pytest.fixture
    def session_with_findings(self, db_session, sample_session):
        for sev in ["HIGH", "MEDIUM"]:
            finding = HardeningFinding(
                id=uuid.uuid4(),
                session_id=sample_session.id,
                check_id=f"SSH_{sev}",
                check_name=f"Check {sev}",
                module="ssh",
                description=f"A {sev} severity finding",
                severity=sev,
                found="yes",
                expected="no",
                status="FAIL",
            )
            db_session.add(finding)
        db_session.commit()
        return sample_session

    def test_get_findings_returns_list(self, client, auth_headers, session_with_findings):
        r = client.get(f"{BASE}/sessions/{session_with_findings.id}/findings", headers=auth_headers)
        assert r.status_code == 200
        findings = r.json()
        assert len(findings) == 2

    def test_finding_has_expected_fields(self, client, auth_headers, session_with_findings):
        findings = client.get(
            f"{BASE}/sessions/{session_with_findings.id}/findings", headers=auth_headers
        ).json()
        f = findings[0]
        assert "check_id" in f
        assert "severity" in f
        assert "module" in f
        assert f["status"] == "FAIL"

    def test_findings_for_empty_session(self, client, auth_headers, sample_session):
        r = client.get(f"{BASE}/sessions/{sample_session.id}/findings", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_findings_nonexistent_session_returns_404(self, client, auth_headers):
        r = client.get(f"{BASE}/sessions/{uuid.uuid4()}/findings", headers=auth_headers)
        assert r.status_code == 404
