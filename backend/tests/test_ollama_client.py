"""
Tests for modules/ollama_client.py
All HTTP calls to the Ollama API are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock
from modules.ollama_client import OllamaClient, OllamaResponse


# ---------------------------------------------------------------------------
# OllamaResponse dataclass tests
# ---------------------------------------------------------------------------

class TestOllamaResponse:
    """Tests for the OllamaResponse dataclass."""

    def test_create_successful_response(self):
        response = OllamaResponse(
            content="ISO 27001 is an information security standard.",
            model="mistral",
            total_duration=1500000,
            eval_count=42,
            success=True,
            error=None,
        )
        assert response.content == "ISO 27001 is an information security standard."
        assert response.model == "mistral"
        assert response.total_duration == 1500000
        assert response.eval_count == 42
        assert response.success is True
        assert response.error is None

    def test_create_error_response(self):
        response = OllamaResponse(
            content="",
            model="mistral",
            success=False,
            error="Connection refused",
        )
        assert response.content == ""
        assert response.success is False
        assert response.error == "Connection refused"

    def test_default_optional_fields(self):
        response = OllamaResponse(content="test", model="mistral")
        assert response.total_duration is None
        assert response.eval_count is None
        assert response.success is True
        assert response.error is None

    def test_fields_are_accessible(self):
        response = OllamaResponse(content="hello", model="qwen2.5-coder:7b")
        assert hasattr(response, "content")
        assert hasattr(response, "model")
        assert hasattr(response, "total_duration")
        assert hasattr(response, "eval_count")
        assert hasattr(response, "success")
        assert hasattr(response, "error")


# ---------------------------------------------------------------------------
# OllamaClient initialization tests
# ---------------------------------------------------------------------------

class TestOllamaClientInit:
    """Tests for OllamaClient initialization."""

    @patch("modules.ollama_client.requests.get")
    def test_init_with_default_host(self, mock_get):
        """Client should use default OLLAMA_HOST when none is provided."""
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient()
        assert "localhost" in client.host or "127.0.0.1" in client.host or client.host.startswith("http")

    @patch("modules.ollama_client.requests.get")
    def test_init_with_custom_host(self, mock_get):
        """Client should use the custom host when provided."""
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient(host="http://192.168.1.100:11434")
        assert client.host == "http://192.168.1.100:11434"

    @patch("modules.ollama_client.requests.get")
    def test_init_strips_trailing_slash(self, mock_get):
        """Trailing slash should be stripped from the host URL."""
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient(host="http://localhost:11434/")
        assert not client.host.endswith("/")

    @patch("modules.ollama_client.requests.get")
    def test_init_with_custom_model(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient(default_model="llama3")
        assert client.default_model == "llama3"

    @patch("modules.ollama_client.requests.get")
    def test_init_default_model_from_settings(self, mock_get):
        """Without explicit model the default should come from MODELS settings."""
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient()
        assert isinstance(client.default_model, str)
        assert len(client.default_model) > 0


# ---------------------------------------------------------------------------
# _check_connection tests
# ---------------------------------------------------------------------------

class TestCheckConnection:
    """Tests for _check_connection method."""

    @patch("modules.ollama_client.requests.get")
    def test_check_connection_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        client = OllamaClient()
        result = client._check_connection()
        assert result is True

    @patch("modules.ollama_client.requests.get")
    def test_check_connection_failure(self, mock_get):
        import requests as req
        # First call succeeds (constructor), second call fails
        mock_get.side_effect = [
            MagicMock(status_code=200),
            req.exceptions.ConnectionError("Connection refused"),
        ]
        client = OllamaClient()
        result = client._check_connection()
        assert result is False

    @patch("modules.ollama_client.requests.get")
    def test_check_connection_non_200_status(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        client = OllamaClient()
        result = client._check_connection()
        assert result is False


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------

class TestGenerate:
    """Tests for the generate() method with mocked HTTP calls."""

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_successful(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "response": "L'ISO 27001 est une norme de securite.",
                "total_duration": 2000000,
                "eval_count": 15,
            }),
        )

        client = OllamaClient()
        response = client.generate("Explique l'ISO 27001", task_type="assistant")

        assert isinstance(response, OllamaResponse)
        assert response.success is True
        assert "ISO 27001" in response.content
        assert response.total_duration == 2000000
        assert response.eval_count == 15

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_payload_structure(self, mock_post, mock_get):
        """Verify the JSON payload sent to the Ollama API."""
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": "ok"}),
        )

        client = OllamaClient()
        client.generate("test prompt", task_type="documentation", system="system prompt")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        assert "model" in payload
        assert payload["prompt"] == "test prompt"
        assert payload["stream"] is False
        assert "options" in payload
        assert "temperature" in payload["options"]
        assert "top_p" in payload["options"]
        assert "num_predict" in payload["options"]
        assert payload["system"] == "system prompt"

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_without_system_prompt(self, mock_post, mock_get):
        """When no system prompt is given, it should not be in the payload."""
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": "ok"}),
        )

        client = OllamaClient()
        client.generate("test prompt")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "system" not in payload

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_http_error(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=500,
            text="Internal Server Error",
        )

        client = OllamaClient()
        response = client.generate("test")

        assert response.success is False
        assert response.error is not None
        assert "500" in response.error

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_timeout(self, mock_post, mock_get):
        import requests as req
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.side_effect = req.exceptions.Timeout("Request timed out")

        client = OllamaClient()
        response = client.generate("test")

        assert response.success is False
        assert response.error is not None
        assert "Timeout" in response.error

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_connection_error(self, mock_post, mock_get):
        import requests as req
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.side_effect = req.exceptions.ConnectionError("Connection refused")

        client = OllamaClient()
        response = client.generate("test")

        assert response.success is False
        assert response.error is not None

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_with_custom_model(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": "ok"}),
        )

        client = OllamaClient()
        client.generate("test", model="llama3")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["model"] == "llama3"

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_generate_uses_task_type_params(self, mock_post, mock_get):
        """Verify that LLM_PARAMS for the task type are applied."""
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"response": "ok"}),
        )

        client = OllamaClient()
        client.generate("test", task_type="analysis")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        # Analysis should have temperature 0.1 from settings
        assert payload["options"]["temperature"] == 0.1


# ---------------------------------------------------------------------------
# chat() tests
# ---------------------------------------------------------------------------

class TestChat:
    """Tests for the chat() method."""

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_chat_successful(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "message": {"content": "Reponse du chat"},
                "total_duration": 1000000,
                "eval_count": 10,
            }),
        )

        client = OllamaClient()
        messages = [{"role": "user", "content": "Bonjour"}]
        response = client.chat(messages)

        assert isinstance(response, OllamaResponse)
        assert response.success is True
        assert response.content == "Reponse du chat"

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_chat_payload_contains_messages(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"message": {"content": "ok"}}),
        )

        client = OllamaClient()
        messages = [
            {"role": "system", "content": "Tu es un expert SMSI"},
            {"role": "user", "content": "Bonjour"},
        ]
        client.chat(messages)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "messages" in payload
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_chat_http_error(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(status_code=503, text="Service Unavailable")

        client = OllamaClient()
        response = client.chat([{"role": "user", "content": "test"}])

        assert response.success is False
        assert "503" in response.error

    @patch("modules.ollama_client.requests.get")
    @patch("modules.ollama_client.requests.post")
    def test_chat_exception(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.side_effect = Exception("Unexpected error")

        client = OllamaClient()
        response = client.chat([{"role": "user", "content": "test"}])

        assert response.success is False
        assert "Unexpected error" in response.error


# ---------------------------------------------------------------------------
# list_models() tests
# ---------------------------------------------------------------------------

class TestListModels:
    """Tests for the list_models() method."""

    @patch("modules.ollama_client.requests.get")
    def test_list_models_success(self, mock_get):
        mock_get.side_effect = [
            # First call: _check_connection in __init__
            MagicMock(status_code=200),
            # Second call: list_models
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "models": [
                        {"name": "mistral:latest"},
                        {"name": "llama3:latest"},
                        {"name": "qwen2.5-coder:7b"},
                    ]
                }),
            ),
        ]

        client = OllamaClient()
        models = client.list_models()

        assert isinstance(models, list)
        assert len(models) == 3
        assert "mistral:latest" in models
        assert "llama3:latest" in models

    @patch("modules.ollama_client.requests.get")
    def test_list_models_empty(self, mock_get):
        mock_get.side_effect = [
            MagicMock(status_code=200),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={"models": []}),
            ),
        ]

        client = OllamaClient()
        models = client.list_models()

        assert isinstance(models, list)
        assert len(models) == 0

    @patch("modules.ollama_client.requests.get")
    def test_list_models_api_error(self, mock_get):
        mock_get.side_effect = [
            MagicMock(status_code=200),
            MagicMock(status_code=500),
        ]

        client = OllamaClient()
        models = client.list_models()

        assert isinstance(models, list)
        assert len(models) == 0

    @patch("modules.ollama_client.requests.get")
    def test_list_models_connection_error(self, mock_get):
        import requests as req
        mock_get.side_effect = [
            MagicMock(status_code=200),
            req.exceptions.ConnectionError("Connection refused"),
        ]

        client = OllamaClient()
        models = client.list_models()

        assert isinstance(models, list)
        assert len(models) == 0
