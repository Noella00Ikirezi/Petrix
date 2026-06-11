"""
Tests for modules/compliance_analyzer.py
All Ollama HTTP calls are mocked.
"""
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from modules.ollama_client import OllamaClient, OllamaResponse
from modules.compliance_analyzer import (
    ComplianceAnalyzer,
    ComplianceGap,
    ComplianceReport,
)


# ---------------------------------------------------------------------------
# Helper: create a mocked OllamaClient
# ---------------------------------------------------------------------------

def _make_mock_client(generate_response=None):
    """Build an OllamaClient with mocked HTTP (bypasses _check_connection)."""
    with patch("modules.ollama_client.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient()
    if generate_response is not None:
        client.generate = MagicMock(return_value=generate_response)
    return client


# ---------------------------------------------------------------------------
# REQUIREMENTS_DB tests
# ---------------------------------------------------------------------------

class TestRequirementsDB:
    """Tests for ComplianceAnalyzer.REQUIREMENTS_DB."""

    def test_requirements_db_is_non_empty(self):
        assert len(ComplianceAnalyzer.REQUIREMENTS_DB) > 0

    def test_requirements_db_has_eight_controls(self):
        assert len(ComplianceAnalyzer.REQUIREMENTS_DB) == 8

    def test_requirements_db_keys_start_with_a(self):
        for key in ComplianceAnalyzer.REQUIREMENTS_DB:
            assert key.startswith("A."), f"Key '{key}' does not start with 'A.'"

    def test_requirements_db_entries_have_expected_fields(self):
        for ref, data in ComplianceAnalyzer.REQUIREMENTS_DB.items():
            assert "title" in data, f"{ref} missing 'title'"
            assert "text" in data, f"{ref} missing 'text'"
            assert "controls" in data, f"{ref} missing 'controls'"
            assert isinstance(data["controls"], list), f"{ref} 'controls' should be a list"
            assert len(data["controls"]) > 0, f"{ref} should have at least one control"

    def test_known_requirements_are_present(self):
        expected = {"A.5.1", "A.5.2", "A.9.1.1", "A.9.2.1", "A.9.2.3", "A.9.4.2", "A.12.4.1", "A.8.2.1"}
        assert set(ComplianceAnalyzer.REQUIREMENTS_DB.keys()) == expected


# ---------------------------------------------------------------------------
# _get_requirements_text() tests
# ---------------------------------------------------------------------------

class TestGetRequirementsText:
    """Tests for _get_requirements_text()."""

    def test_returns_string(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.9.1.1"])
        assert isinstance(text, str)

    def test_contains_requirement_reference(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.9.1.1"])
        assert "A.9.1.1" in text

    def test_contains_requirement_title(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.5.1"])
        assert "Politiques de sécurité" in text

    def test_multiple_requirements(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.9.1.1", "A.9.2.1"])
        assert "A.9.1.1" in text
        assert "A.9.2.1" in text

    def test_unknown_requirement_handled_gracefully(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.99.99.99"])
        assert "A.99.99.99" in text

    def test_contains_controls(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        text = analyzer._get_requirements_text(["A.9.4.2"])
        # A.9.4.2 has control "MFA"
        assert "MFA" in text


# ---------------------------------------------------------------------------
# ComplianceGap dataclass tests
# ---------------------------------------------------------------------------

class TestComplianceGap:
    """Tests for the ComplianceGap dataclass."""

    def test_create_compliance_gap(self):
        gap = ComplianceGap(
            requirement_ref="A.9.1.1",
            requirement_text="Politique de controle d'acces",
            expected="Politique documentee",
            found="Aucune politique",
            score=1,
            gap_type="major_nc",
            recommendation="Rediger une politique",
            priority="critical",
            effort="high",
        )
        assert gap.requirement_ref == "A.9.1.1"
        assert gap.score == 1
        assert gap.gap_type == "major_nc"
        assert gap.priority == "critical"

    def test_gap_fields_accessible(self):
        gap = ComplianceGap(
            requirement_ref="A.5.1",
            requirement_text="test",
            expected="expected",
            found="found",
            score=3,
            gap_type="minor_nc",
            recommendation="rec",
            priority="high",
            effort="medium",
        )
        assert hasattr(gap, "requirement_ref")
        assert hasattr(gap, "requirement_text")
        assert hasattr(gap, "expected")
        assert hasattr(gap, "found")
        assert hasattr(gap, "score")
        assert hasattr(gap, "gap_type")
        assert hasattr(gap, "recommendation")
        assert hasattr(gap, "priority")
        assert hasattr(gap, "effort")


# ---------------------------------------------------------------------------
# ComplianceReport dataclass tests
# ---------------------------------------------------------------------------

class TestComplianceReport:
    """Tests for the ComplianceReport dataclass."""

    def test_create_compliance_report(self):
        report = ComplianceReport(
            document_name="test.md",
            analysis_date="2024-01-15T10:00:00",
            requirements_analyzed=["A.9.1.1"],
            overall_score=3.5,
            risk_level="Modere",
            gaps=[],
            summary="Test summary",
            action_plan=[],
        )
        assert report.document_name == "test.md"
        assert report.overall_score == 3.5
        assert report.risk_level == "Modere"
        assert isinstance(report.gaps, list)
        assert isinstance(report.action_plan, list)

    def test_report_with_gaps(self):
        gap = ComplianceGap(
            requirement_ref="A.9.1.1",
            requirement_text="Politique",
            expected="Documentee",
            found="Absente",
            score=0,
            gap_type="major_nc",
            recommendation="Creer",
            priority="critical",
            effort="high",
        )
        report = ComplianceReport(
            document_name="doc.md",
            analysis_date="2024-01-15",
            requirements_analyzed=["A.9.1.1"],
            overall_score=0,
            risk_level="Critique",
            gaps=[gap],
            summary="Non conforme",
            action_plan=[{"priority": 1, "action": "Creer politique"}],
        )
        assert len(report.gaps) == 1
        assert report.gaps[0].gap_type == "major_nc"
        assert len(report.action_plan) == 1


# ---------------------------------------------------------------------------
# _create_error_report() tests
# ---------------------------------------------------------------------------

class TestCreateErrorReport:
    """Tests for _create_error_report()."""

    def test_returns_compliance_report(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Some error")
        assert isinstance(report, ComplianceReport)

    def test_error_report_has_zero_score(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Error")
        assert report.overall_score == 0

    def test_error_report_risk_level(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Error")
        assert report.risk_level == "Non évalué"

    def test_error_report_has_empty_gaps(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Error")
        assert report.gaps == []
        assert report.action_plan == []

    def test_error_report_summary_contains_error(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Connection refused")
        assert "Connection refused" in report.summary

    def test_error_report_preserves_document_name(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("my_policy.md", ["A.5.1"], "Err")
        assert report.document_name == "my_policy.md"

    def test_error_report_preserves_requirements(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        reqs = ["A.9.1.1", "A.9.2.1"]
        report = analyzer._create_error_report("doc.md", reqs, "Err")
        assert report.requirements_analyzed == reqs

    def test_error_report_has_valid_date(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = analyzer._create_error_report("doc.md", ["A.9.1.1"], "Err")
        # Should be a valid ISO date string
        assert isinstance(report.analysis_date, str)
        datetime.fromisoformat(report.analysis_date)


# ---------------------------------------------------------------------------
# analyze_file() tests
# ---------------------------------------------------------------------------

class TestAnalyzeFile:
    """Tests for analyze_file()."""

    def test_analyze_file_nonexistent_raises(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file("/tmp/nonexistent_smsi_doc_xyz123.md", ["A.9.1.1"])

    def test_analyze_file_reads_and_delegates(self, tmp_path):
        """analyze_file should read the file and call analyze_document."""
        # Create a temporary file
        test_file = tmp_path / "policy.md"
        test_file.write_text("# Politique de test\nContenu du document.", encoding="utf-8")

        # Build a mock client that returns a successful analysis
        llm_response = OllamaResponse(
            content=json.dumps({
                "overall_score": 3.0,
                "risk_level": "Modéré",
                "summary": "Analyse OK",
                "gaps": [],
                "action_plan": [],
            }),
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        analyzer = ComplianceAnalyzer(client=client)

        report = analyzer.analyze_file(str(test_file), ["A.5.1"])

        assert isinstance(report, ComplianceReport)
        assert report.document_name == "policy.md"
        client.generate.assert_called_once()


# ---------------------------------------------------------------------------
# analyze_document() tests
# ---------------------------------------------------------------------------

class TestAnalyzeDocument:
    """Tests for analyze_document() with mocked Ollama client."""

    def test_successful_analysis(self):
        llm_json = {
            "overall_score": 3.5,
            "risk_level": "Modéré",
            "summary": "Le document couvre partiellement les exigences.",
            "gaps": [
                {
                    "requirement_ref": "A.9.1.1",
                    "requirement_text": "Politique de controle d'acces",
                    "expected": "Politique documentee",
                    "found": "Politique partielle",
                    "score": 3,
                    "gap_type": "minor_nc",
                    "recommendation": "Completer la politique",
                    "priority": "high",
                    "effort": "medium",
                }
            ],
            "action_plan": [
                {
                    "priority": 1,
                    "action": "Completer la politique",
                    "responsible": "RSSI",
                    "deadline": "3 mois",
                    "deliverable": "Politique v2",
                }
            ],
        }
        llm_response = OllamaResponse(
            content=json.dumps(llm_json),
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        analyzer = ComplianceAnalyzer(client=client)

        report = analyzer.analyze_document(
            document_content="# Politique de test",
            requirements=["A.9.1.1"],
            document_name="test_policy.md",
        )

        assert isinstance(report, ComplianceReport)
        assert report.overall_score == 3.5
        assert report.risk_level == "Modéré"
        assert len(report.gaps) == 1
        assert report.gaps[0].requirement_ref == "A.9.1.1"
        assert report.gaps[0].gap_type == "minor_nc"
        assert len(report.action_plan) == 1

    def test_analysis_with_llm_error(self):
        llm_response = OllamaResponse(
            content="",
            model="mistral",
            success=False,
            error="Model not found",
        )
        client = _make_mock_client(generate_response=llm_response)
        analyzer = ComplianceAnalyzer(client=client)

        report = analyzer.analyze_document(
            document_content="# Document",
            requirements=["A.9.1.1"],
            document_name="doc.md",
        )

        assert isinstance(report, ComplianceReport)
        assert report.overall_score == 0
        assert "Model not found" in report.summary

    def test_analysis_with_invalid_json_response(self):
        llm_response = OllamaResponse(
            content="This is not valid JSON at all",
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        analyzer = ComplianceAnalyzer(client=client)

        report = analyzer.analyze_document(
            document_content="# Document",
            requirements=["A.9.1.1"],
            document_name="doc.md",
        )

        # Should return an error report when JSON parsing fails
        assert isinstance(report, ComplianceReport)
        assert report.overall_score == 0

    def test_analysis_calls_generate_with_analysis_task_type(self):
        llm_response = OllamaResponse(
            content=json.dumps({
                "overall_score": 4.0,
                "risk_level": "Faible",
                "summary": "OK",
                "gaps": [],
                "action_plan": [],
            }),
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        analyzer = ComplianceAnalyzer(client=client)

        analyzer.analyze_document("content", ["A.5.1"], "doc.md")

        call_kwargs = client.generate.call_args
        assert call_kwargs.kwargs.get("task_type") == "analysis" or (
            len(call_kwargs.args) == 0 and call_kwargs[1].get("task_type") == "analysis"
        )


# ---------------------------------------------------------------------------
# format_report_markdown() tests
# ---------------------------------------------------------------------------

class TestFormatReportMarkdown:
    """Tests for format_report_markdown()."""

    def _make_sample_report(self):
        gap = ComplianceGap(
            requirement_ref="A.9.1.1",
            requirement_text="Politique de controle d'acces",
            expected="Politique documentee",
            found="Absente",
            score=0,
            gap_type="major_nc",
            recommendation="Creer la politique",
            priority="critical",
            effort="high",
        )
        return ComplianceReport(
            document_name="policy.md",
            analysis_date="2024-01-15T10:00:00",
            requirements_analyzed=["A.9.1.1"],
            overall_score=1.5,
            risk_level="Critique",
            gaps=[gap],
            summary="Document non conforme.",
            action_plan=[{
                "priority": 1,
                "action": "Creer politique",
                "responsible": "RSSI",
                "deadline": "1 mois",
                "deliverable": "Politique v1",
            }],
        )

    def test_returns_string(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert isinstance(md, str)

    def test_contains_main_title(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "# Rapport d'Analyse de Conformité" in md

    def test_contains_general_info_section(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "## Informations générales" in md

    def test_contains_document_name(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "policy.md" in md

    def test_contains_overall_score(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "1.5/5" in md

    def test_contains_synthesis_section(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "## Synthèse" in md

    def test_contains_gap_details_section(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "## Détail des écarts" in md

    def test_contains_statistics(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "### Statistiques" in md

    def test_contains_gap_requirement_ref(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "A.9.1.1" in md

    def test_contains_action_plan(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "## Plan d'action recommandé" in md

    def test_empty_report_no_action_plan_section(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = ComplianceReport(
            document_name="empty.md",
            analysis_date="2024-01-15",
            requirements_analyzed=[],
            overall_score=0,
            risk_level="Non évalué",
            gaps=[],
            summary="Aucune analyse",
            action_plan=[],
        )
        md = analyzer.format_report_markdown(report)
        # With empty action_plan, the action plan section should not be rendered
        assert "## Plan d'action recommandé" not in md

    def test_contains_footer(self):
        client = _make_mock_client()
        analyzer = ComplianceAnalyzer(client=client)
        report = self._make_sample_report()
        md = analyzer.format_report_markdown(report)
        assert "Rapport généré automatiquement" in md
