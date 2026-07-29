from pathlib import Path
from types import SimpleNamespace

from crewai.llms.providers.azure.completion import AzureCompletion

from backend.core import llm as llm_module


def test_chat_llm_uses_crewai_native_azure_provider():
    assert llm_module.AzureCompletion is AzureCompletion
    assert isinstance(llm_module.llm, AzureCompletion)
    assert llm_module.llm.model == "test-deployment"
    assert llm_module.llm.api_key == "test-key"
    assert llm_module.llm.api_version == "2023-07-01-preview"
    assert llm_module.llm.timeout == 30
    assert llm_module.llm.endpoint == ("https://test.openai.azure.com/openai/deployments/test-deployment")


def test_create_embedding_uses_official_azure_openai_client(monkeypatch):
    create_calls = []
    client_kwargs = {}

    class FakeEmbeddings:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.25, 0.75])])

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            client_kwargs.update(kwargs)
            self.embeddings = FakeEmbeddings()

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT_EMBED", "https://embed.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_EMBED", "embed-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION_EMBED", "2024-02-01")
    monkeypatch.setenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "embed-deployment")
    monkeypatch.setattr(llm_module, "AzureOpenAI", FakeAzureOpenAI)

    result = llm_module.create_embedding("content to embed")

    assert result == [0.25, 0.75]
    assert client_kwargs == {
        "azure_endpoint": "https://embed.openai.azure.com/",
        "api_key": "embed-key",
        "api_version": "2024-02-01",
        "timeout": 30,
        "max_retries": 3,
    }
    assert create_calls == [{"model": "embed-deployment", "input": ["content to embed"]}]


def test_runtime_has_no_litellm_dependency_or_references():
    backend_root = Path(__file__).resolve().parents[1]
    runtime_files = [path for path in backend_root.rglob("*.py") if "tests" not in path.relative_to(backend_root).parts]
    offenders = [
        str(path.relative_to(backend_root.parent))
        for path in runtime_files
        if "litellm" in path.read_text(encoding="utf-8").lower()
    ]

    requirements = (backend_root / "requirements.txt").read_text(encoding="utf-8")

    assert offenders == []
    assert "litellm" not in requirements.lower()
