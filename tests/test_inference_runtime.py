import pytest

from inference import load_runtime_config


def test_load_runtime_config_reads_required_environment_variables(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("MODEL_NAME", "gpt-test")
    monkeypatch.setenv("HF_TOKEN", "hf_test_token")

    config = load_runtime_config()

    assert config.api_base_url == "https://api.example.com"
    assert config.model_name == "gpt-test"
    assert config.hf_token == "hf_test_token"


def test_load_runtime_config_requires_all_environment_variables(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        load_runtime_config()
