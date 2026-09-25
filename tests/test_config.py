from document_reader.config.settings import Settings


def test_settings_reads_openai_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = Settings()

    assert settings.openai_api_key == "test-key"


def test_settings_uses_default_model(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = Settings()

    assert settings.openai_model == "gpt-5.6-mini"


def test_settings_reads_custom_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")

    settings = Settings()

    assert settings.openai_model == "custom-model"