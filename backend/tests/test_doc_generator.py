"""
Tests for modules/doc_generator.py
All Ollama HTTP calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock
from modules.ollama_client import OllamaClient, OllamaResponse
from modules.doc_generator import DocumentGenerator, DocumentRequest
from config.settings import DOC_CLASSIFICATION, ORGANIZATION


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
# DocumentRequest dataclass tests
# ---------------------------------------------------------------------------

class TestDocumentRequest:
    """Tests for the DocumentRequest dataclass."""

    def test_create_document_request(self):
        req = DocumentRequest(
            ref_iso="A.9.1.1",
            measure_name="Politique de controle d'acces",
            doc_type="POL",
        )
        assert req.ref_iso == "A.9.1.1"
        assert req.measure_name == "Politique de controle d'acces"
        assert req.doc_type == "POL"

    def test_default_classification(self):
        req = DocumentRequest(
            ref_iso="A.5.1",
            measure_name="Politique de securite",
            doc_type="POL",
        )
        assert req.classification == "internal"

    def test_default_additional_context(self):
        req = DocumentRequest(
            ref_iso="A.5.1",
            measure_name="Politique",
            doc_type="POL",
        )
        assert req.additional_context == ""

    def test_default_frameworks_is_none(self):
        req = DocumentRequest(
            ref_iso="A.5.1",
            measure_name="Politique",
            doc_type="POL",
        )
        assert req.frameworks is None

    def test_custom_values(self):
        req = DocumentRequest(
            ref_iso="A.9.2.1",
            measure_name="Enregistrement utilisateurs",
            doc_type="PRO",
            classification="confidential",
            additional_context="Active Directory environment",
            frameworks=["ISO 27001:2022", "RGPD"],
        )
        assert req.doc_type == "PRO"
        assert req.classification == "confidential"
        assert req.additional_context == "Active Directory environment"
        assert len(req.frameworks) == 2


# ---------------------------------------------------------------------------
# DocumentGenerator initialization tests
# ---------------------------------------------------------------------------

class TestDocumentGeneratorInit:
    """Tests for DocumentGenerator initialization."""

    def test_init_with_provided_client(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        assert generator.client is client

    def test_templates_contain_expected_keys(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        assert "POL" in generator.templates
        assert "PRO" in generator.templates
        assert "CHK" in generator.templates


# ---------------------------------------------------------------------------
# _build_system_prompt() tests
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    """Tests for _build_system_prompt()."""

    def test_returns_string(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        prompt = generator._build_system_prompt()
        assert isinstance(prompt, str)

    def test_contains_organization_name(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        prompt = generator._build_system_prompt()
        assert ORGANIZATION["name"] in prompt

    def test_contains_sector(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        prompt = generator._build_system_prompt()
        assert ORGANIZATION["sector"] in prompt

    def test_custom_frameworks(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        prompt = generator._build_system_prompt(frameworks=["PCI-DSS", "SOC2"])
        assert "PCI-DSS" in prompt
        assert "SOC2" in prompt

    def test_default_frameworks_from_organization(self):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        prompt = generator._build_system_prompt()
        # Should contain at least one of the default frameworks
        assert "ISO 27001" in prompt


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------

class TestGenerate:
    """Tests for the generate() method with mocked LLM calls."""

    def test_generate_policy_success(self):
        llm_response = OllamaResponse(
            content="# Politique de Controle d'Acces\n\n## 1. Objet\n...",
            model="mistral",
            eval_count=500,
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate("A.9.1.1", "Politique de controle d'acces", doc_type="POL")

        assert isinstance(result, str)
        assert "Politique" in result
        client.generate.assert_called_once()

    def test_generate_procedure_success(self):
        llm_response = OllamaResponse(
            content="# Procedure d'Enregistrement\n\n## 1. Objet\n...",
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate("A.9.2.1", "Enregistrement utilisateurs", doc_type="PRO")

        assert isinstance(result, str)
        assert "Procedure" in result

    def test_generate_checklist_success(self):
        llm_response = OllamaResponse(
            content="# Checklist Controle d'Acces\n\n| # | Point |",
            model="mistral",
            success=True,
        )
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate("A.9.1.1", "Controle d'acces", doc_type="CHK")

        assert isinstance(result, str)
        assert "Checklist" in result

    def test_generate_error_returns_error_message(self):
        llm_response = OllamaResponse(
            content="",
            model="mistral",
            success=False,
            error="Model not loaded",
        )
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate("A.5.1", "Politique de securite")

        assert isinstance(result, str)
        assert "Erreur" in result
        assert "Model not loaded" in result

    def test_generate_uses_documentation_task_type(self):
        llm_response = OllamaResponse(content="ok", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        generator.generate("A.5.1", "Politique")

        call_kwargs = client.generate.call_args
        assert call_kwargs.kwargs.get("task_type") == "documentation"

    def test_generate_passes_system_prompt(self):
        llm_response = OllamaResponse(content="ok", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        generator.generate("A.5.1", "Politique")

        call_kwargs = client.generate.call_args
        system = call_kwargs.kwargs.get("system")
        assert system is not None
        assert len(system) > 0

    def test_generate_prompt_contains_ref_iso(self):
        llm_response = OllamaResponse(content="ok", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        generator.generate("A.12.4.1", "Journalisation")

        call_kwargs = client.generate.call_args
        prompt = call_kwargs.kwargs.get("prompt")
        assert "A.12.4.1" in prompt

    def test_generate_prompt_contains_measure_name(self):
        llm_response = OllamaResponse(content="ok", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        generator.generate("A.9.1.1", "Politique de controle d'acces")

        call_kwargs = client.generate.call_args
        prompt = call_kwargs.kwargs.get("prompt")
        assert "Politique de controle d'acces" in prompt

    def test_generate_unknown_doc_type_falls_back_to_policy(self):
        """Unknown doc_type should fall back to the POLICY_TEMPLATE."""
        llm_response = OllamaResponse(content="ok", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        # "XYZ" is not in templates, should use POLICY_TEMPLATE
        generator.generate("A.5.1", "Politique", doc_type="XYZ")

        call_kwargs = client.generate.call_args
        prompt = call_kwargs.kwargs.get("prompt")
        # Policy template contains "POLITIQUE"
        assert "POLITIQUE" in prompt


# ---------------------------------------------------------------------------
# Shortcut methods tests
# ---------------------------------------------------------------------------

class TestShortcutMethods:
    """Tests for generate_policy, generate_procedure, generate_checklist."""

    def test_generate_policy_shortcut(self):
        llm_response = OllamaResponse(content="Politique generee", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate_policy("A.5.1", "Politique de securite")
        assert "Politique generee" in result

    def test_generate_procedure_shortcut(self):
        llm_response = OllamaResponse(content="Procedure generee", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate_procedure("A.9.2.1", "Enregistrement")
        assert "Procedure generee" in result

    def test_generate_checklist_shortcut(self):
        llm_response = OllamaResponse(content="Checklist generee", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        result = generator.generate_checklist("A.9.1.1", "Controle d'acces")
        assert "Checklist generee" in result


# ---------------------------------------------------------------------------
# save_document() tests
# ---------------------------------------------------------------------------

class TestSaveDocument:
    """Tests for save_document()."""

    def test_save_document_creates_file(self, tmp_path):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)

        filepath = generator.save_document(
            content="# Test Policy\n\nContent here.",
            reference="POL-SEC-001",
            output_dir=tmp_path,
        )

        assert filepath.exists()
        assert filepath.suffix == ".md"
        assert "POL-SEC-001" in filepath.name

    def test_save_document_content_written(self, tmp_path):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        content = "# Politique de Securite\n\n## 1. Objet"

        filepath = generator.save_document(
            content=content,
            reference="POL-SEC-002",
            output_dir=tmp_path,
        )

        saved_content = filepath.read_text(encoding="utf-8")
        assert saved_content == content

    def test_save_document_creates_directory(self, tmp_path):
        client = _make_mock_client()
        generator = DocumentGenerator(client=client)
        nested_dir = tmp_path / "sub" / "dir"

        filepath = generator.save_document(
            content="content",
            reference="PRO-SEC-001",
            output_dir=nested_dir,
        )

        assert nested_dir.exists()
        assert filepath.exists()


# ---------------------------------------------------------------------------
# batch_generate() tests
# ---------------------------------------------------------------------------

class TestBatchGenerate:
    """Tests for batch_generate()."""

    def test_batch_generate_creates_multiple_files(self, tmp_path):
        llm_response = OllamaResponse(content="Generated doc", model="mistral", success=True)
        client = _make_mock_client(generate_response=llm_response)
        generator = DocumentGenerator(client=client)

        # Monkeypatch save_document to use tmp_path
        original_save = generator.save_document
        generator.save_document = lambda content, reference: original_save(content, reference, output_dir=tmp_path)

        measures = [
            {"ref": "A.5.1", "name": "Politique de securite"},
            {"ref": "A.9.1.1", "name": "Controle d'acces"},
        ]

        created = generator.batch_generate(measures, doc_type="POL")

        assert len(created) == 2
        assert client.generate.call_count == 2
