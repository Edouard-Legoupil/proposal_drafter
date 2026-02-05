import concurrent.futures
import logging
from sqlalchemy import text
import litellm
import nltk
from nltk.tokenize import sent_tokenize
import os

from backend.core.llm import get_embedder_config

logger = logging.getLogger(__name__)

# --- NLTK setup: use predownloaded path if available, otherwise download ---
NLTK_DATA_PATH = os.environ.get("NLTK_DATA", "/app/nltk_data")
if NLTK_DATA_PATH not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_PATH)

try:
    # Test if punkt tokenizer is available
    nltk.data.find("tokenizers/punkt")
except LookupError:
    logger.info("NLTK punkt tokenizer not found, downloading...")
    nltk.download("punkt", download_dir=NLTK_DATA_PATH)

# --- Embedding helper ---
def get_embedding(chunk, model, embedder_config):
    """Get embedding for a text chunk with error handling"""
    try:
        response = litellm.embedding(
            model=model,
            input=[chunk],
            max_retries=3,
            **embedder_config
        )
        return chunk, response.data[0]['embedding']
    except Exception as e:
        logger.error(f"[EMBEDDING ERROR] Failed to get embedding for chunk: {e}")
        raise

# --- Main processing function ---
async def process_and_store_text(reference_id, text_content, connection):
    """
    Chunks text, creates embeddings, and stores them for a given reference.
    """
    try:
        logger.info(f"Starting to process and store text for reference_id: {reference_id}")

        # Clear old vectors
        logger.info(f"Deleting existing vectors for reference_id: {reference_id}")
        connection.execute(
            text("DELETE FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id"),
            {"ref_id": reference_id}
        )

        # Chunk the text
        sentences = sent_tokenize(text_content.replace('\x00', ''))

        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= 1000:
                current_chunk += " " + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"Content for reference_id: {reference_id} chunked into {len(chunks)} chunks.")
        if not chunks:
            logger.warning(f"No chunks generated for reference_id: {reference_id}")
            return

        # Embedding configuration
        embedder_config = get_embedder_config()["config"]
        model = f"azure/{embedder_config.pop('deployment_id')}"
        embedder_config.pop('model', None)

        # Generate embeddings in parallel
        logger.info(f"Starting parallel embedding generation for {len(chunks)} chunks...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_embedding, chunk, model, embedder_config) for chunk in chunks]
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    chunk, embedding = future.result()
                    completed += 1

                    # Insert chunk and embedding into database
                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_reference_vectors (reference_id, text_chunk, embedding)
                            VALUES (:ref_id, :chunk, :embedding)
                        """),
                        {"ref_id": reference_id, "chunk": chunk, "embedding": str(embedding)}
                    )

                except Exception as e:
                    logger.error(f"[CHUNK PROCESSING ERROR] Failed for reference_id {reference_id}: {e}")
                    continue

        # Update scraped_at timestamp
        connection.execute(
            text("UPDATE knowledge_card_references SET scraped_at = CURRENT_TIMESTAMP, scraping_error = FALSE WHERE id = :id"),
            {"id": reference_id}
        )

    except Exception as e:
        logger.error(f"[PROCESS AND STORE TEXT ERROR] {e}", exc_info=True)
        # Mark as error
        connection.execute(
            text("UPDATE knowledge_card_references SET scraping_error = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": reference_id}
        )
        raise
