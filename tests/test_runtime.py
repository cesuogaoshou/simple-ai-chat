from ai_chat.runtime import RuntimeInfo, detect_runtime


def test_detect_runtime_defaults_to_local(monkeypatch):
    clear_runtime_env(monkeypatch)

    runtime = detect_runtime()

    assert runtime == RuntimeInfo(name="local", label="Runtime: local")


def test_detect_runtime_reports_streamlit_cloud(monkeypatch):
    clear_runtime_env(monkeypatch)
    monkeypatch.setenv("STREAMLIT_CLOUD", "1")

    runtime = detect_runtime()

    assert runtime == RuntimeInfo(name="streamlit-cloud", label="Runtime: streamlit-cloud")


def test_runtime_label_does_not_include_secret_values(monkeypatch):
    clear_runtime_env(monkeypatch)
    monkeypatch.setenv("STREAMLIT_CLOUD", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key")

    runtime = detect_runtime()

    assert "super-secret-key" not in runtime.label


def clear_runtime_env(monkeypatch):
    for key in ["STREAMLIT_CLOUD", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
