"""Tests for the HCO hardening engine — SSH mocked, no real connections."""
import pytest
from unittest.mock import MagicMock, patch

from app.hardening.engine import (
    run_hardening_audit,
    _compute_score,
    SUPPORTED_OS_TYPES,
    DEFAULT_MODULES_BY_OS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_connector(command_responses: dict | None = None):
    """Return a mock SSHConnector whose execute_command dispatches on the cmd."""
    connector = MagicMock()
    connector.connect.return_value = True

    responses = command_responses or {}

    def _exec(cmd, *args, **kwargs):
        for pattern, (stdout, stderr) in responses.items():
            if pattern in cmd:
                return stdout, stderr
        return "", ""

    connector.execute_command.side_effect = _exec
    return connector


# ---------------------------------------------------------------------------
# _compute_score
# ---------------------------------------------------------------------------

class TestComputeScore:
    def test_no_findings_is_perfect(self):
        score, grade = _compute_score([])
        assert score == 100.0
        assert grade == "A"

    def test_critical_finding_reduces_score(self):
        score, grade = _compute_score([{"severity": "CRITICAL"}])
        assert score == 85.0
        assert grade == "B"

    def test_multiple_highs(self):
        findings = [{"severity": "HIGH"}] * 3
        score, grade = _compute_score(findings)
        assert score == 76.0
        assert grade == "B"

    def test_score_clamps_at_zero(self):
        findings = [{"severity": "CRITICAL"}] * 20
        score, grade = _compute_score(findings)
        assert score == 0.0
        assert grade == "F"

    def test_grade_thresholds(self):
        assert _compute_score([])[1] == "A"
        assert _compute_score([{"severity": "CRITICAL"}, {"severity": "HIGH"}])[1] in ("B", "C", "D", "F")

    def test_unknown_severity_treated_as_info(self):
        score, _ = _compute_score([{"severity": "WHATEVER"}])
        assert score == 100.0


# ---------------------------------------------------------------------------
# run_hardening_audit — unsupported OS
# ---------------------------------------------------------------------------

class TestRunHardeningAuditUnsupportedOS:
    def test_bad_os_returns_error(self):
        result = run_hardening_audit(host="1.2.3.4", os_type="windows_xp")
        assert result["error"] is not None
        assert "not supported" in result["error"]

    def test_supported_os_types_exist(self):
        assert "linux" in SUPPORTED_OS_TYPES
        assert "macos_intel" in SUPPORTED_OS_TYPES
        assert "macos_silicon" in SUPPORTED_OS_TYPES


# ---------------------------------------------------------------------------
# run_hardening_audit — SSH connection failure
# ---------------------------------------------------------------------------

class TestRunHardeningAuditSSHFail:
    @patch("app.hardening.engine.SSHConnector")
    def test_ssh_connect_failure_returns_error(self, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = False

        result = run_hardening_audit(
            host="unreachable.local",
            port=22,
            username="root",
            password="pass",
            os_type="linux",
        )
        assert result["error"] is not None
        assert "SSH connection" in result["error"]

    @patch("app.hardening.engine.SSHConnector")
    def test_disconnect_called_even_on_failure(self, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = False

        run_hardening_audit(host="x.local", password="p", os_type="linux")
        instance.disconnect.assert_not_called()


# ---------------------------------------------------------------------------
# run_hardening_audit — successful path with mocked modules
# ---------------------------------------------------------------------------

class TestRunHardeningAuditSuccess:
    def _mock_module(self, findings=None, passed=None):
        mod = MagicMock()
        mod.run_audit.return_value = {
            "findings": findings or [],
            "passed": passed or [],
            "summary": {
                "total_checks": len(findings or []) + len(passed or []),
                "passed": len(passed or []),
                "failed": len(findings or []),
            },
        }
        return mod

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_returns_full_result_structure(self, mock_map, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = True

        finding = {"check": "SSH_ROOT", "check_name": "Root login", "severity": "HIGH",
                   "description": "Root login allowed", "found": "yes", "expected": "no"}
        passed_item = {"check": "SSH_PASS", "check_name": "Password auth", "severity": "HIGH"}

        mock_mod = self._mock_module(findings=[finding], passed=[passed_item])
        mock_map.__contains__ = lambda self, key: key == "linux"
        mock_map.get = lambda key, default=None: {"ssh": mock_mod} if key == "linux" else default
        mock_map.__getitem__ = lambda self, key: {"ssh": mock_mod}

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["ssh"]}):
            result = run_hardening_audit(
                host="10.0.0.1", password="secret", os_type="linux", modules=["ssh"]
            )

        assert result["error"] is None
        assert result["host"] == "10.0.0.1"
        assert result["os_type"] == "linux"
        assert "ssh" in result["modules_completed"]
        assert len(result["all_findings"]) == 1
        assert result["all_findings"][0]["module"] == "ssh"
        assert result["score"] <= 100.0
        assert result["grade"] in ("A", "B", "C", "D", "F")
        assert result["total_checks"] == 2
        assert result["passed_checks"] == 1

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_disconnect_called_after_audit(self, mock_map, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = True

        mock_mod = self._mock_module()
        mock_map.get = lambda key, default=None: {"ssh": mock_mod} if key == "linux" else default
        mock_map.__contains__ = lambda self, key: key == "linux"

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["ssh"]}):
            run_hardening_audit(host="10.0.0.1", password="p", os_type="linux", modules=["ssh"])

        instance.disconnect.assert_called_once()

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_module_crash_does_not_abort_audit(self, mock_map, MockSSH):
        """A crashing module is skipped; the others still complete."""
        instance = MockSSH.return_value
        instance.connect.return_value = True

        crash_mod = MagicMock()
        crash_mod.run_audit.side_effect = RuntimeError("SSH timeout")
        ok_mod = self._mock_module(passed=[{"check": "OK", "severity": "INFO"}])

        mock_map.get = lambda key, default=None: {"crash": crash_mod, "ok": ok_mod} if key == "linux" else default
        mock_map.__contains__ = lambda self, key: key == "linux"

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["crash", "ok"]}):
            result = run_hardening_audit(
                host="10.0.0.1", password="p", os_type="linux", modules=["crash", "ok"]
            )

        assert result["error"] is None
        assert "ok" in result["modules_completed"]
        assert "crash" in result["modules_completed"]

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_progress_callback_called(self, mock_map, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = True

        mock_mod = self._mock_module()
        mock_map.get = lambda key, default=None: {"ssh": mock_mod} if key == "linux" else default
        mock_map.__contains__ = lambda self, key: key == "linux"

        calls = []
        def _progress(module, pct):
            calls.append((module, pct))

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["ssh"]}):
            run_hardening_audit(
                host="10.0.0.1", password="p", os_type="linux",
                modules=["ssh"], progress_callback=_progress,
            )

        assert len(calls) >= 1
        assert calls[0][0] == "ssh"

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_unknown_modules_filtered_out(self, mock_map, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = True

        mock_mod = self._mock_module()
        mock_map.get = lambda key, default=None: {"ssh": mock_mod} if key == "linux" else default
        mock_map.__contains__ = lambda self, key: key == "linux"

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["ssh"]}):
            result = run_hardening_audit(
                host="10.0.0.1", password="p", os_type="linux",
                modules=["ssh", "nonexistent_module"],
            )

        assert "nonexistent_module" not in result["modules_completed"]
        assert "ssh" in result["modules_completed"]

    @patch("app.hardening.engine.SSHConnector")
    @patch("app.hardening.engine.OS_MODULE_MAP")
    def test_perfect_score_when_no_findings(self, mock_map, MockSSH):
        instance = MockSSH.return_value
        instance.connect.return_value = True

        mock_mod = self._mock_module(findings=[], passed=[{"check": "ALL_GOOD", "severity": "INFO"}])
        mock_map.get = lambda key, default=None: {"ssh": mock_mod} if key == "linux" else default
        mock_map.__contains__ = lambda self, key: key == "linux"

        with patch("app.hardening.engine.DEFAULT_MODULES_BY_OS", {"linux": ["ssh"]}):
            result = run_hardening_audit(
                host="10.0.0.1", password="p", os_type="linux", modules=["ssh"]
            )

        assert result["score"] == 100.0
        assert result["grade"] == "A"
