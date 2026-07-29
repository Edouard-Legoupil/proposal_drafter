import concurrent.futures
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest
from crewai.llms.providers.azure.completion import AzureCompletion

from backend.core import llm as llm_module


@pytest.fixture(autouse=True)
def clear_embedding_client_cache():
    llm_module.reset_embedding_client()
    yield
    llm_module.reset_embedding_client()


def test_chat_llm_uses_crewai_native_azure_provider():
    assert llm_module.AzureCompletion is AzureCompletion
    assert isinstance(llm_module.llm, AzureCompletion)
    assert llm_module.llm.model == "test-deployment"
    assert llm_module.llm.api_key == "test-key"
    assert llm_module.llm.api_version == "2023-07-01-preview"
    assert llm_module.llm.timeout == 30
    assert llm_module.llm.endpoint == ("https://test.openai.azure.com/openai/deployments/test-deployment")


def test_aliased_azure_deployment_supports_function_calling_and_tools():
    tool = {
        "type": "function",
        "function": {
            "name": "lookup_reference",
            "description": "Look up a reference",
            "parameters": {"type": "object", "properties": {}},
        },
    }

    params = llm_module.llm._prepare_completion_params(
        messages=[{"role": "user", "content": "Find a reference"}],
        tools=[tool],
    )

    assert llm_module.llm.supports_function_calling() is True
    assert len(params["tools"]) == 1
    assert params["tool_choice"] == "auto"


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

        def close(self):
            pass

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


def test_embedding_config_requires_dedicated_endpoint_and_key(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT_EMBED", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY_EMBED", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://chat.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "chat-key")

    for operation in (
        llm_module.get_embedder_config,
        lambda: llm_module.create_embedding("content"),
    ):
        with pytest.raises(ValueError) as exc_info:
            operation()

        assert str(exc_info.value) == (
            "Missing required environment variables for embeddings: "
            "AZURE_OPENAI_ENDPOINT_EMBED, AZURE_OPENAI_API_KEY_EMBED"
        )
        assert "chat-key" not in str(exc_info.value)
        assert "chat.openai.azure.com" not in str(exc_info.value)


def test_embedding_config_preserves_legacy_defaults(monkeypatch):
    clients = []

    class FakeEmbeddings:
        def create(self, **kwargs):
            assert kwargs == {
                "model": "text-embedding-ada-002",
                "input": ["content"],
            }
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.5])])

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            clients.append(kwargs)
            self.embeddings = FakeEmbeddings()

        def close(self):
            pass

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT_EMBED", "https://embed.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_EMBED", "embed-key")
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION_EMBED", raising=False)
    monkeypatch.delenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", raising=False)
    monkeypatch.setattr(llm_module, "AzureOpenAI", FakeAzureOpenAI)

    assert llm_module.create_embedding("content") == [0.5]
    assert clients[0]["api_version"] == "2023-05-15"
    assert llm_module.get_embedder_config()["config"] == {
        "model": "text-embedding-ada-002",
        "deployment_id": "text-embedding-ada-002",
        "api_key": "embed-key",
        "api_base": "https://embed.openai.azure.com/",
        "api_version": "2023-05-15",
    }


def test_embedding_calls_reuse_one_synchronous_client(monkeypatch):
    client_count = 0
    create_inputs = []

    class FakeEmbeddings:
        def create(self, **kwargs):
            create_inputs.append(kwargs["input"])
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0])])

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            nonlocal client_count
            client_count += 1
            self.embeddings = FakeEmbeddings()

        def close(self):
            pass

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT_EMBED", "https://embed.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_EMBED", "embed-key")
    monkeypatch.setattr(llm_module, "AzureOpenAI", FakeAzureOpenAI)

    llm_module.create_embedding("first")
    llm_module.create_embedding("second")

    assert client_count == 1
    assert create_inputs == [["first"], ["second"]]


def test_embedding_client_cold_start_is_single_flight(monkeypatch):
    worker_count = 5
    start_barrier = threading.Barrier(worker_count)
    constructor_condition = threading.Condition()
    release_constructor = threading.Event()
    construction_count = 0

    class FakeEmbeddings:
        def create(self, **kwargs):
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0])])

    class DelayedAzureOpenAI:
        def __init__(self, **kwargs):
            nonlocal construction_count
            with constructor_condition:
                construction_count += 1
                constructor_condition.notify_all()
            assert release_constructor.wait(timeout=3)
            self.embeddings = FakeEmbeddings()

        def close(self):
            pass

    def create_from_worker(index):
        start_barrier.wait(timeout=3)
        return llm_module.create_embedding(f"content-{index}")

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT_EMBED", "https://embed.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_EMBED", "embed-key")
    monkeypatch.setattr(llm_module, "AzureOpenAI", DelayedAzureOpenAI)

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(create_from_worker, index) for index in range(worker_count)]
        with constructor_condition:
            constructor_condition.wait_for(
                lambda: construction_count == worker_count,
                timeout=1,
            )
        release_constructor.set()
        results = [future.result(timeout=3) for future in futures]

    assert construction_count == 1
    assert results == [[1.0]] * worker_count


def test_reset_embedding_client_closes_once_and_allows_recreation(monkeypatch):
    clients = []

    class FakeEmbeddings:
        def create(self, **kwargs):
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0])])

    class ClosableAzureOpenAI:
        def __init__(self, **kwargs):
            self.close_count = 0
            self.embeddings = FakeEmbeddings()
            clients.append(self)

        def close(self):
            self.close_count += 1

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT_EMBED", "https://embed.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_EMBED", "embed-key")
    monkeypatch.setattr(llm_module, "AzureOpenAI", ClosableAzureOpenAI)

    llm_module.create_embedding("first")
    llm_module.reset_embedding_client()
    llm_module.reset_embedding_client()
    llm_module.create_embedding("second")
    llm_module.reset_embedding_client()

    assert len(clients) == 2
    assert [client.close_count for client in clients] == [1, 1]


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
