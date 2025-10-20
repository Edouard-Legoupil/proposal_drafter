import concurrent.futures
import logging
from sqlalchemy import text
from langchain.text_splitter import RecursiveCharacterTextSplitter
import litellm

from backend.core.llm import get_embedder_config

logger = logging.getLogger(__name__)

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

async def process_and_store_text(reference_id, text_content, connection):
    """
    Chunks text, creates embeddings, and stores them for a given reference.
    """
    try:
        # For now, we will clear old vectors before adding new ones
        connection.execute(
            text("DELETE FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id"),
            {"ref_id": reference_id}
        )

        # Chunk the text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content.replace('\x00', ''))
        logger.info(f"Content chunked into {len(chunks)} chunks.")

        if not chunks:
            logger.warning("No chunks generated from text content")
            return

        # Get the embedding configuration
        embedder_config = get_embedder_config()["config"]
        model = f"azure/{embedder_config.pop('deployment_id')}"
        # The 'model' key in the config is just the deployment name, which is not needed anymore.
        embedder_config.pop('model', None)

        # Generate and store embeddings in parallel with error handling
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # Limit workers
            futures = [executor.submit(get_embedding, chunk, model, embedder_config) for chunk in chunks]
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    chunk, embedding = future.result()
                    completed += 1
                    logger.info(f"Embedding for chunk {completed}/{len(chunks)} completed.")

                    connection.execute(
                        text("""
                            INSERT INTO knowledge_card_reference_vectors (reference_id, text_chunk, embedding)
                            VALUES (:ref_id, :chunk, :embedding)
                        """),
                        {"ref_id": reference_id, "chunk": chunk, "embedding": str(embedding)}
                    )
                except Exception as e:
                    logger.error(f"[CHUNK PROCESSING ERROR] Failed to process chunk: {e}")
                    continue  # Continue with other chunks even if one fails

        # Update scraped_at timestamp
        connection.execute(
            text("UPDATE knowledge_card_references SET scraped_at = CURRENT_TIMESTAMP, scraping_error = FALSE WHERE id = :id"),
            {"id": reference_id}
        )

    except Exception as e:
        logger.error(f"[PROCESS AND STORE TEXT ERROR] {e}", exc_info=True)
        # Mark as error in database
        connection.execute(
            text("UPDATE knowledge_card_references SET scraping_error = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": reference_id}
        )
        raise