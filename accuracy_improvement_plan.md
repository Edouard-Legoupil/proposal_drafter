# CrewAI-Enhanced RAG Optimisation Framework for Proposal Drafting

This document outlines an integrated optimisation framework for a **CrewAI-powered humanitarian proposal drafting solution**, focused on improving factual consistency, contextual grounding, and system scalability.

The system relies on **two hierarchical context layers**:

1. **Level 1 – Knowledge Card Construction:**  
   Retrieve, chunk, and synthesise relevant information from the RAG database into structured, reusable **Knowledge Cards**.  

2. **Level 2 – Proposal Drafting:**  
   Use these Knowledge Cards as the authoritative context for the **CrewAI proposal drafting agent**, ensuring factual grounding, narrative consistency, and alignment with donor or organisational requirements.

To achieve optimal results, three dimensions of optimisation are applied:

1. **Prompt Optimisation**  
2. **Context Optimisation (RAG Layer)**  
3. **Model Optimisation**

---

## 1. Prompt Optimisation

Prompt engineering defines how the CrewAI agents interact with retrieved knowledge and how proposals are progressively composed from factual building blocks.

### 1.1 Multi-Agent Prompt Framework

Each agent in the CrewAI pipeline (e.g., *Retriever*, *Knowledge Curator*, *Proposal Writer*, *Evaluator*) must have its own role-specific prompt templates that follow a **consistent instruction hierarchy**:

| Agent | Role | Example Prompt Focus |
|--------|------|----------------------|
| Retriever | Extracts relevant chunks from RAG | "Retrieve documents relevant to the thematic and geographic scope of this query." |
| Curator | Synthesises chunks into Knowledge Cards | "Summarise the retrieved evidence into structured knowledge cards with clear references." |
| Writer | Generates proposal sections | "Draft a coherent section using the provided knowledge card content as factual basis. Do not add unsupported claims." |
| Evaluator | Validates coherence and consistency | "Check if the proposal aligns with the evidence base and organisational templates." |

### 1.2 Prompt Design Principles

* **Instruction Clarity:** Explicitly separate *source material* (Knowledge Card) from *generation tasks* (writing, summarising, evaluating).  
* **Context Anchoring:** Embed the Knowledge Card text in the system prompt before proposal generation.  
* **Hierarchical Consistency:** Ensure every agent passes clean, structured outputs downstream — for example, the *Curator* agent outputs JSON-formatted Knowledge Cards that the *Writer* agent can parse directly.  
* **Adaptive Framing:** Adjust prompts dynamically based on donor type, project scope, or language preference.  

### 1.3 Evaluation

* Conduct A/B testing of prompts for **faithfulness**, **style coherence**, and **information density**.  
* Use a *proposal validation script* comparing outputs across CrewAI runs with identical inputs but different prompt templates.

---

## 2. Context Optimisation (RAG Layer)

The context layer underpins Level 1 (Knowledge Card generation) and determines how effectively the system retrieves, filters, and synthesises relevant material from the document corpus.

### 2.1 Level 1 – Knowledge Card Generation

**Goal:** Transform raw retrieved chunks into structured, reusable **Knowledge Cards** that encapsulate facts, data, and verified references.



**RAG Retrieval Process:**
1. **Chunk Documents:** Apply one of the strategies below (Semantic, Agentic, or Content-Aware).  
2. **Embed and Store:** Vectorise each chunk using the selected embedding model.  
3. **Query Expansion:** Optionally use **HyDE** to create a hypothetical “ideal” summary before retrieval.  
4. **Curate:** Synthesize retrieved chunks into concise, verified Knowledge Cards.


### 2.2 Chunking Strategies

#### a. Semantic Chunking
Semantic chunking splits text based on meaning, using NLP libraries to identify sentence or paragraph boundaries. This approach aims to keep related concepts within the same chunk, improving contextual relevance. Ideal for narrative and report-like content (e.g., needs assessments, evaluations).

**Pros:**
*   **Higher Relevance:** Chunks are more likely to contain complete thoughts or ideas, leading to better search results.
*   **Improved Context:** Overlap is less critical since chunks are already semantically coherent.

**Cons:**
*   **Complexity:** Requires NLP libraries (e.g., NLTK, spaCy), adding dependencies and processing overhead.
*   **Variable Chunk Size:** Chunks will have inconsistent lengths, which may be suboptimal for some embedding models.
 

#### b. Agentic Chunking

Agentic chunking uses a language model to analyze the text and decide on the most logical split points. This is the most advanced and flexible approach, as the LLM can make nuanced decisions based on the content's meaning and structure. Can adapt to different document types (e.g., PDFs, Excel tables, markdown reports).

**Pros:**
*   **Highest Accuracy:** The LLM can theoretically produce the most semantically coherent chunks possible.
*   **Adaptable:** Can be fine-tuned with specific instructions to handle different content types.

**Cons:**
*   **Cost and Latency:** Requires calls to a powerful LLM, which can be expensive and slow.
*   **Implementation Complexity:** The logic for interacting with the LLM and processing its output is more complex.

#### c. Content-Aware Chunking
Content-aware chunking adapts the splitting strategy based on the document's structure. For example, it could use Markdown headers, code blocks, or HTML tags to define chunk boundaries.Best for structured data (project logframes, budget tables, ToC diagrams).

**Pros:**
*   **Structured Data:** Works exceptionally well for structured documents like Markdown, code, or technical manuals.
*   **Preserves Formatting:** Can keep important structural elements within the same chunk.

**Cons:**
*   **Less Effective for Unstructured Text:** Offers little advantage for plain text documents without clear structural cues.
*   **Requires Custom Logic:** Different logic is needed to handle each content type (e.g., a Markdown parser, an HTML parser).


### 2.3 Complementary Technique: HyDE Retrieval

It is important to note that chunking is only one part of the retrieval process. Another powerful technique that can be used in conjunction with any of the above chunking strategies is **HyDE (Hypothetical Document Embeddings)**.

HyDE is a retrieval technique, not a chunking one. It works as follows:

1.  **Generate a Hypothetical Document:** When a user submits a query, a language model is first used to generate a detailed, hypothetical answer to that query.
2.  **Embed the Hypothetical Document:** This generated document is then embedded into a vector.
3.  **Retrieve Real Documents:** The vector of the hypothetical document is used to perform a similarity search against the vector database of real, chunked documents.

**Pros:**
*   **Improved Relevance:** The generated document is often more semantically aligned with the *ideal* answer than the original, brief query. This can lead to retrieving more relevant and useful chunks.
*   **Handles Ambiguity:** If a user's query is short or ambiguous, the generated document can add the necessary context to find better results.

**Cons:**
*   **Increased Latency and Cost:** It requires an extra call to a language model for every query, which adds to both the time and cost of retrieval.
*   **Risk of Hallucination:** If the initial hypothetical document is completely wrong or "hallucinates" incorrect facts, it can lead the retrieval system to fetch irrelevant documents.

**Implementation:**
HyDE can be implemented as a layer on top of our existing retrieval system. It would not replace the need for a good chunking strategy but would instead enhance the process of finding the best chunks for a given query.


### 2.4 Level 2 – Proposal Generation from Knowledge Cards

At this stage, the **CrewAI Proposal Writer** agent uses the Knowledge Cards as the factual anchor for drafting coherent and consistent proposal narratives.

**Mechanism:**
1. Retrieve Knowledge Cards relevant to the current proposal section.  
2. Pass them into the CrewAI prompt as structured input.  
3. Generate text grounded strictly on these cards.  
4. The **Evaluator Agent** then validates consistency.

This two-level design ensures:
* All generated text remains **traceable** to a factual evidence base.  
* Proposal narratives maintain **semantic consistency** across multiple sections.  
* Knowledge Cards can be **reused** across different proposals or donors.



### 2.5 Evaluating RAG and Knowledge Card Quality

We employ a **RAG evaluation pipeline** with a *Judge LLM* and metrics inspired by **RAGAs**.

**Key Metrics:**
* **Faithfulness:** Does each Knowledge Card accurately represent its sources?  
* **Context Precision:** Are retrieved chunks relevant to the query?  
* **Proposal Consistency:** Does the proposal text align with the Knowledge Card content?  

**Pipeline Steps:**
1. Log all RAG retrievals and outputs in `rag_evaluation_logs`.  
2. Periodically sample records for evaluation.  
3. Submit `(query, retrieved_context, knowledge_card, generated_answer)` to a judge LLM.  
4. Compute automated scores and store results.  

---

## 3. Model Optimisation

Model optimisation enhances both retrieval and generation efficiency while maintaining contextual accuracy across CrewAI agents.

### 3.1 Embedding Model Optimisation

* Use **domain-tuned embeddings** (e.g., `text-embedding-3-large` or `bge-m3`) fine-tuned on humanitarian texts.  
* Apply **semantic clustering** in Redis or Postgres pgvector to group thematically related knowledge chunks.  
* Optimise query speed with FAISS or HNSW indexing.  
* Employ **hybrid retrieval** (vector + BM25) for keyword-rich technical documents.  

### 3.2 Generation Model and Instruction Optimisation

* Fine-tune the **Proposal Writer** agent using **LoRA adapters** on a corpus of approved proposals.  
* Adjust temperature and `top_p` values to maintain factual precision over creative variability.  
* Include **Knowledge Card verification layers** before final text output (the Evaluator agent can reject ungrounded statements).  
* Maintain deterministic “style adapters” for specific donors (e.g., ECHO, USAID, UN OCHA).  

### 3.3 System-Level Optimisations

* **Caching:** Cache embeddings and generated Knowledge Cards to minimise recomputation.  
* **Batch Inference:** Embed multiple documents or queries concurrently.  
* **Async Retrieval:** Run parallel searches across RAG sources.  
* **Feedback Loop:** Store proposal sections and validation results for iterative fine-tuning of both retrieval and generation layers.  

---

## Implementation Roadmap

| Phase | Focus | Outputs |
|-------|--------|----------|
| **Phase 1** | Baseline Upgrade | Implement **Semantic Chunking** and **Knowledge Card creation** pipeline with RAG logging |
| **Phase 2** | Context Maturity | Integrate **HyDE retrieval**, **Content-Aware chunking**, and automated **RAG evaluation** |
| **Phase 3** | Adaptive Optimisation | Add **Agentic Chunking** and continuous **evaluation-driven tuning** |

---

## Conclusion

By combining **Prompt**, **Context**, and **Model Optimisation**, this CrewAI-enhanced RAG system enables proposal teams to move from *document retrieval* to *knowledge synthesis and narrative generation*.

The **two-level context management**—Knowledge Cards (Level 1) feeding grounded proposal drafts (Level 2)—ensures:
* **Traceability** of all facts used in proposal writing  
* **Consistency** across proposal sections and iterations  
* **Scalability** across multiple donors and response contexts  

This framework represents a foundational step toward **AI-assisted, evidence-grounded humanitarian proposal generation** that balances automation with control and transparency.

