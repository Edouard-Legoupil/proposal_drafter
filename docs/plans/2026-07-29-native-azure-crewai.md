# Native Azure CrewAI Connection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove LiteLLM and route CrewAI chat and application embeddings directly through supported Azure SDKs.

**Architecture:** Construct CrewAI's native `AzureCompletion` provider explicitly for agent chat and centralize embeddings behind an `AzureOpenAI` helper. Preserve existing API-key configuration and add a policy test preventing LiteLLM from returning.

**Tech Stack:** Python, CrewAI native Azure provider, Azure AI Inference SDK, OpenAI Azure SDK, pytest, Ruff, mypy, pip-audit.

---

### Task 1: Specify the native-provider contract

**Files:**
- Create: `backend/tests/test_native_azure_llm.py`
- Modify: `backend/tests/test_dependency_scanning.py`

**Steps:**

1. Add tests that reload `backend.core.llm` with test environment values and assert `llm` is an `AzureCompletion` with the expected deployment, endpoint, API version, timeout, and API key.
2. Add a test with a fake `AzureOpenAI` client asserting the embedding helper calls `embeddings.create(model=<deployment>, input=[<text>])` and returns the vector.
3. Add a repository policy test asserting `litellm` is absent from `backend/requirements.txt` and backend runtime Python imports.
4. Run `pytest -q backend/tests/test_native_azure_llm.py backend/tests/test_dependency_scanning.py` and confirm failures identify the current generic provider, missing helper, and LiteLLM references.

### Task 2: Switch chat completion to CrewAI's native Azure provider

**Files:**
- Modify: `backend/core/llm.py`
- Modify: `backend/requirements.txt`

**Steps:**

1. Replace `from crewai import LLM` with `AzureCompletion` from CrewAI's native Azure provider.
2. Instantiate `AzureCompletion` explicitly with the existing deployment, endpoint, key, API version, and timeout values.
3. Constrain CrewAI to a native-provider-capable release and retain the `azure-ai-inference` extra.
4. Run the provider tests and confirm the chat-provider assertions pass while embedding and LiteLLM-removal assertions remain red.
5. Commit the native chat-provider migration.

### Task 3: Replace LiteLLM embeddings with the Azure OpenAI SDK

**Files:**
- Modify: `backend/core/llm.py`
- Modify: `backend/utils/embedding_utils.py`
- Modify: `backend/utils/crew_knowledge.py`
- Test: `backend/tests/test_native_azure_llm.py`

**Steps:**

1. Add a cached `AzureOpenAI` embedding client factory and `create_embedding(text)` helper in `backend/core/llm.py`.
2. Validate the embedding endpoint, key, version, and deployment variables without logging values.
3. Replace both `litellm.embedding` call paths with the shared helper, preserving chunk parallelism and vector formatting.
4. Run the focused tests and confirm all provider and embedding tests pass.
5. Commit the direct embedding migration.

### Task 4: Remove LiteLLM and enforce absence

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/scripts/generate_card_content.py`
- Modify: `backend/scripts/4-find-references.py`
- Test: `backend/tests/test_dependency_scanning.py`

**Steps:**

1. Remove the LiteLLM requirement and stale logger configuration.
2. Search backend runtime code and dependency declarations for case-insensitive `litellm` references.
3. Run the policy test and focused provider tests to green.
4. Resolve `backend/requirements.txt` with `pip --dry-run` and run `pip-audit` with the documented no-fix ChromaDB exception.
5. Commit the dependency and policy cleanup.

### Task 5: Regression and acceptance verification

**Files:**
- Modify only if verification exposes a tested regression.

**Steps:**

1. Run pre-commit against every changed Python, requirements, and documentation file.
2. Run `pytest -q backend/tests`.
3. Run Bandit at high severity and the Python dependency audit.
4. Run `git diff --check` and verify `rg -n -i 'litellm' backend` returns only an intentional policy-test string, if any.
5. Record that a live Azure completion is not invoked locally because it would consume external credentials; rely on SDK-boundary contract tests and deployment smoke testing.
