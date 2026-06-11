"""
Tests for config/settings.py
Validates the configuration constants used across the SMSI project.
"""
import pytest
from config.settings import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    MODELS,
    LLM_PARAMS,
    DOC_TYPES,
    PRIORITIES,
    MATURITY_LEVELS,
    ORGANIZATION,
    DOC_CLASSIFICATION,
    BASE_DIR,
    TEMPLATES_DIR,
    KNOWLEDGE_BASE_DIR,
    OUTPUTS_DIR,
    DOCUMENTS_DIR,
    AUDITS_DIR,
    ANALYSES_DIR,
)


class TestOllamaHost:
    """Tests for OLLAMA_HOST configuration."""

    def test_ollama_host_is_string(self):
        assert isinstance(OLLAMA_HOST, str)

    def test_ollama_host_is_valid_url(self):
        assert OLLAMA_HOST.startswith("http://") or OLLAMA_HOST.startswith("https://")

    def test_ollama_host_default_contains_port(self):
        # Default host should include a port number
        assert ":" in OLLAMA_HOST.split("//")[1]

    def test_ollama_model_is_string(self):
        assert isinstance(OLLAMA_MODEL, str)
        assert len(OLLAMA_MODEL) > 0

    def test_ollama_timeout_is_positive_int(self):
        assert isinstance(OLLAMA_TIMEOUT, int)
        assert OLLAMA_TIMEOUT > 0


class TestModels:
    """Tests for MODELS dict mapping task types to model names."""

    def test_models_is_dict(self):
        assert isinstance(MODELS, dict)

    def test_models_is_non_empty(self):
        assert len(MODELS) > 0

    def test_models_has_expected_keys(self):
        expected_keys = {"documentation", "analysis", "assistant", "audit"}
        assert expected_keys.issubset(set(MODELS.keys()))

    def test_models_values_are_strings(self):
        for key, value in MODELS.items():
            assert isinstance(value, str), f"MODELS['{key}'] should be a string, got {type(value)}"

    def test_models_values_are_non_empty(self):
        for key, value in MODELS.items():
            assert len(value) > 0, f"MODELS['{key}'] should not be empty"


class TestLLMParams:
    """Tests for LLM_PARAMS configuration."""

    def test_llm_params_is_dict(self):
        assert isinstance(LLM_PARAMS, dict)

    def test_llm_params_is_non_empty(self):
        assert len(LLM_PARAMS) > 0

    def test_llm_params_has_expected_keys(self):
        expected_keys = {"documentation", "analysis", "assistant", "audit"}
        assert expected_keys.issubset(set(LLM_PARAMS.keys()))

    def test_temperature_values_in_valid_range(self):
        for task_type, params in LLM_PARAMS.items():
            temp = params.get("temperature")
            assert temp is not None, f"Missing temperature for '{task_type}'"
            assert 0 <= temp <= 1, f"Temperature for '{task_type}' is {temp}, should be between 0 and 1"

    def test_top_p_values_in_valid_range(self):
        for task_type, params in LLM_PARAMS.items():
            top_p = params.get("top_p")
            assert top_p is not None, f"Missing top_p for '{task_type}'"
            assert 0 < top_p <= 1, f"top_p for '{task_type}' is {top_p}, should be between 0 and 1"

    def test_num_predict_values_are_positive(self):
        for task_type, params in LLM_PARAMS.items():
            num_predict = params.get("num_predict")
            assert num_predict is not None, f"Missing num_predict for '{task_type}'"
            assert num_predict > 0, f"num_predict for '{task_type}' should be positive"

    def test_analysis_has_lower_temperature_than_assistant(self):
        """Analysis tasks should use lower temperature for more deterministic output."""
        assert LLM_PARAMS["analysis"]["temperature"] < LLM_PARAMS["assistant"]["temperature"]


class TestDocTypes:
    """Tests for DOC_TYPES configuration."""

    def test_doc_types_is_dict(self):
        assert isinstance(DOC_TYPES, dict)

    def test_doc_types_is_non_empty(self):
        assert len(DOC_TYPES) > 0

    def test_doc_types_has_seven_types(self):
        assert len(DOC_TYPES) == 7

    def test_doc_types_has_expected_keys(self):
        expected_keys = {"POL", "PRO", "GUI", "REG", "CHK", "FOR", "RAP"}
        assert set(DOC_TYPES.keys()) == expected_keys

    def test_doc_types_keys_are_strings(self):
        for key in DOC_TYPES:
            assert isinstance(key, str)

    def test_doc_types_values_are_strings(self):
        for key, value in DOC_TYPES.items():
            assert isinstance(value, str), f"DOC_TYPES['{key}'] should be a string"
            assert len(value) > 0, f"DOC_TYPES['{key}'] should not be empty"


class TestPriorities:
    """Tests for PRIORITIES configuration."""

    def test_priorities_is_dict(self):
        assert isinstance(PRIORITIES, dict)

    def test_priorities_has_four_levels(self):
        assert len(PRIORITIES) == 4

    def test_priorities_has_expected_keys(self):
        expected_keys = {"critical", "high", "medium", "low"}
        assert set(PRIORITIES.keys()) == expected_keys

    def test_priorities_have_label_and_days(self):
        for level, data in PRIORITIES.items():
            assert "label" in data, f"Priority '{level}' missing 'label'"
            assert "days" in data, f"Priority '{level}' missing 'days'"

    def test_priorities_days_are_positive(self):
        for level, data in PRIORITIES.items():
            assert data["days"] > 0, f"Priority '{level}' days should be positive"

    def test_priorities_days_ordering(self):
        """Critical priority should have fewer days than low priority."""
        assert PRIORITIES["critical"]["days"] < PRIORITIES["high"]["days"]
        assert PRIORITIES["high"]["days"] < PRIORITIES["medium"]["days"]
        assert PRIORITIES["medium"]["days"] < PRIORITIES["low"]["days"]


class TestMaturityLevels:
    """Tests for MATURITY_LEVELS configuration."""

    def test_maturity_levels_is_dict(self):
        assert isinstance(MATURITY_LEVELS, dict)

    def test_maturity_levels_has_six_levels(self):
        assert len(MATURITY_LEVELS) == 6

    def test_maturity_levels_range_0_to_5(self):
        assert set(MATURITY_LEVELS.keys()) == {0, 1, 2, 3, 4, 5}

    def test_maturity_levels_have_name_and_description(self):
        for level, data in MATURITY_LEVELS.items():
            assert "name" in data, f"Maturity level {level} missing 'name'"
            assert "description" in data, f"Maturity level {level} missing 'description'"

    def test_maturity_levels_names_are_non_empty(self):
        for level, data in MATURITY_LEVELS.items():
            assert len(data["name"]) > 0, f"Maturity level {level} has empty name"
            assert len(data["description"]) > 0, f"Maturity level {level} has empty description"

    def test_maturity_level_0_is_inexistant(self):
        assert MATURITY_LEVELS[0]["name"] == "Inexistant"

    def test_maturity_level_5_is_optimise(self):
        assert MATURITY_LEVELS[5]["name"] == "Optimisé"


class TestOrganization:
    """Tests for ORGANIZATION configuration."""

    def test_organization_is_dict(self):
        assert isinstance(ORGANIZATION, dict)

    def test_organization_has_required_keys(self):
        required_keys = {"name", "sector", "size", "scope", "frameworks"}
        assert required_keys.issubset(set(ORGANIZATION.keys()))

    def test_organization_frameworks_is_list(self):
        assert isinstance(ORGANIZATION["frameworks"], list)
        assert len(ORGANIZATION["frameworks"]) > 0


class TestDocClassification:
    """Tests for DOC_CLASSIFICATION configuration."""

    def test_doc_classification_is_dict(self):
        assert isinstance(DOC_CLASSIFICATION, dict)

    def test_doc_classification_has_expected_keys(self):
        expected_keys = {"public", "internal", "confidential", "secret"}
        assert set(DOC_CLASSIFICATION.keys()) == expected_keys


class TestPaths:
    """Tests for path configurations."""

    def test_base_dir_is_path(self):
        from pathlib import Path
        assert isinstance(BASE_DIR, Path)

    def test_subdirectories_are_under_base_dir(self):
        for subdir in [TEMPLATES_DIR, KNOWLEDGE_BASE_DIR, OUTPUTS_DIR]:
            assert str(subdir).startswith(str(BASE_DIR))

    def test_documents_dir_under_outputs(self):
        assert str(DOCUMENTS_DIR).startswith(str(OUTPUTS_DIR))

    def test_audits_dir_under_outputs(self):
        assert str(AUDITS_DIR).startswith(str(OUTPUTS_DIR))

    def test_analyses_dir_under_outputs(self):
        assert str(ANALYSES_DIR).startswith(str(OUTPUTS_DIR))
