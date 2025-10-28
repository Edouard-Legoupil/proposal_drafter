# Chunking Strategy Proposals

This document outlines three alternative chunking strategies to improve the relevance and accuracy of our RAG system.

### 1. Semantic Chunking

Semantic chunking splits text based on meaning, using NLP libraries to identify sentence or paragraph boundaries. This approach aims to keep related concepts within the same chunk, improving contextual relevance.

**Pros:**
*   **Higher Relevance:** Chunks are more likely to contain complete thoughts or ideas, leading to better search results.
*   **Improved Context:** Overlap is less critical since chunks are already semantically coherent.

**Cons:**
*   **Complexity:** Requires NLP libraries (e.g., NLTK, spaCy), adding dependencies and processing overhead.
*   **Variable Chunk Size:** Chunks will have inconsistent lengths, which may be suboptimal for some embedding models.

### 2. Agentic Chunking

Agentic chunking uses a language model to analyze the text and decide on the most logical split points. This is the most advanced and flexible approach, as the LLM can make nuanced decisions based on the content's meaning and structure.

**Pros:**
*   **Highest Accuracy:** The LLM can theoretically produce the most semantically coherent chunks possible.
*   **Adaptable:** Can be fine-tuned with specific instructions to handle different content types.

**Cons:**
*   **Cost and Latency:** Requires calls to a powerful LLM, which can be expensive and slow.
*   **Implementation Complexity:** The logic for interacting with the LLM and processing its output is more complex.

### 3. Content-Aware Chunking

Content-aware chunking adapts the splitting strategy based on the document's structure. For example, it could use Markdown headers, code blocks, or HTML tags to define chunk boundaries.

**Pros:**
*   **Structured Data:** Works exceptionally well for structured documents like Markdown, code, or technical manuals.
*   **Preserves Formatting:** Can keep important structural elements within the same chunk.

**Cons:**
*   **Less Effective for Unstructured Text:** Offers little advantage for plain text documents without clear structural cues.
*   **Requires Custom Logic:** Different logic is needed to handle each content type (e.g., a Markdown parser, an HTML parser).

---

My recommendation is to start with **Semantic Chunking** as it offers a significant improvement over the current fixed-size approach with manageable complexity.

### Complementary Strategy: HyDE Retrieval

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

---

### Measuring RAG Accuracy

To systematically improve the accuracy of our RAG system, we need a robust evaluation framework. This allows us to benchmark changes and ensure that new strategies (like different chunking methods or HyDE retrieval) are having a positive impact.

#### Evaluation Approach: LLM as a Judge

A powerful and scalable method for RAG evaluation is the "LLM as a Judge" pattern. In this approach, we use a powerful language model to assess the quality of the RAG system's output based on several key metrics.

**Key Metrics:**
*   **Faithfulness:** Does the generated answer stay true to the retrieved context? (i.e., no hallucinations)
*   **Answer Relevancy:** Is the answer relevant to the user's original query?
*   **Context Precision:** Are the retrieved chunks relevant to the query?
*   **Context Recall:** Were all the necessary chunks retrieved to answer the query completely?

**Pros:**
*   **Scalability:** Can be automated to evaluate hundreds or thousands of query-response pairs without human intervention.
*   **Nuanced Evaluation:** The LLM judge can provide qualitative feedback and reasoning, not just a simple score.
*   **Cost-Effective:** Cheaper than manual evaluation by human experts, especially at scale.

**Cons:**
*   **Judge Bias:** The judge LLM can have its own biases or may favor certain styles of answers.
*   **Setup Complexity:** Requires a well-defined evaluation dataset and carefully crafted prompts for the judge LLM.
*   **Cost:** While cheaper than human evaluation, it still incurs costs for the LLM judge's API calls.

#### Build the Evaluation Pipeline

The `_run` method of the `VectorSearchTool` in `backend/utils/crew_knowledge.py` must be modified. After retrieving the context, it should insert a new record into the `rag_evaluation_logs` table and pass the `id` of this new record forward.

With the logging in place - implemented through the function log_rag_output to the rag_evaluation_logs table, an external script can now be created to:
 *   Query the `rag_evaluation_logs` table.
 *   For each record, send the `query`, `retrieved_context`, and `generated_answer` to a judge LLM.
 *   Use a framework like **RAGAs** to score the results on metrics like Faithfulness and Relevancy.
 *   Store these scores to benchmark the performance of the RAG system over time.
