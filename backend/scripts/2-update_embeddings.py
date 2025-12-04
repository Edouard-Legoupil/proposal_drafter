import argparse
import asyncio
import concurrent.futures
import os
import sys
import csv
import logging
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.utils.embedding_utils import process_and_store_text
from backend.utils.scraper import scrape_url

def process_reference_safely(ref_id, ref_url, force_rescrape, SessionLocal):
    """
    A self-contained worker function that processes a single reference.
    It manages its own database session and asyncio event loop to ensure isolation.
    """
    logging.info(f"Starting worker for reference {ref_id}...")
    try:
        with SessionLocal() as session:
            with session.begin():
                content = ""
                if force_rescrape:
                    logging.info(f"  - Force re-scraping URL: {ref_url}")
                    content = scrape_url(ref_url)
                else:
                    # Reconstruct content from existing chunks
                    chunks_result = session.execute(
                        text("SELECT text_chunk FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id ORDER BY id"),
                        {"ref_id": ref_id}
                    ).fetchall()
                    if chunks_result:
                        content = "".join([chunk[0] for chunk in chunks_result])
                        logging.info(f"  - Reconstructed content from {len(chunks_result)} chunks.")
                    else:
                        logging.info(f"  - No existing chunks found, scraping URL: {ref_url}")
                        content = scrape_url(ref_url)

                if content:
                    # Each thread gets its own asyncio event loop
                    asyncio.run(process_and_store_text(ref_id, content, session))
                    logging.info(f"  - Successfully processed and stored embeddings for reference {ref_id}")
                else:
                    logging.warning(f"  - No content to process for reference {ref_id}")
        logging.info(f"Worker for reference {ref_id} finished successfully.")
    except Exception as e:
        logging.exception(f"  - Worker for reference {ref_id} failed with error: {e}")
        # The transaction will be rolled back automatically by the `with` statement



def main():
    parser = argparse.ArgumentParser(description="Update embeddings for all knowledge card references.")
    parser.add_argument("--force-rescrape", action="store_true", help="Force re-scraping of all references.")
    parser.add_argument("--test-scrap", action="store_true", help="Test scraping of all reference URLs and log failures.")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum number of concurrent workers.")
    args = parser.parse_args()

    # Configure logging
    log_file = os.path.join(os.path.dirname(__file__), 'update_embeddings.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("Starting embedding update process...")

    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Database connection
    try:
        DATABASE_URL = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("DB_USERNAME").strip('"'),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        logging.critical(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Scrape Test Mode
    with SessionLocal() as session:
        if args.test_scrap:
            logging.info("Starting scrape test...")
            failed_urls = []
            references = session.execute(text("SELECT id, url FROM knowledge_card_references")).fetchall()
            for ref in references:
                try:
                    logging.info(f"  - Testing URL: {ref.url}")
                    scrape_url(ref.url)
                except Exception as e:
                    logging.error(f"  - Failed to scrape URL: {ref.url} with error: {e}")
                    failed_urls.append({'url': ref.url, 'error': str(e)})

            if failed_urls:
                log_dir = 'log'
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_log_file = os.path.join(log_dir, f"scrape_test_failures_{timestamp}.csv")

                with open(csv_log_file, 'w', newline='') as csvfile:
                    fieldnames = ['url', 'error']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(failed_urls)

                logging.error(f"Scrape test finished. Found {len(failed_urls)} failures. See {csv_log_file} for details.")
            else:
                logging.info("Scrape test finished. All URLs were successfully scraped.")

        # Main Embedding Update Logic
        else:
            with session.begin():
                references = session.execute(text("SELECT id, url FROM knowledge_card_references")).fetchall()
                logging.info(f"Found {len(references)} references to process.")

                with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                    future_to_ref = {
                        executor.submit(process_reference_safely, ref.id, ref.url, args.force_rescrape, SessionLocal): ref
                        for ref in references
                    }
                    completed_count = 0
                    for future in concurrent.futures.as_completed(future_to_ref):
                        completed_count += 1
                        ref = future_to_ref[future]
                        try:
                            future.result()  # We call result() to raise any exceptions that occurred
                            logging.info(f"({completed_count}/{len(references)}) COMPLETED processing for reference {ref.id}.")
                        except Exception as exc:
                            logging.error(f"({completed_count}/{len(references)}) FAILED processing for reference {ref.id} ({ref.url}): {exc}")


                logging.info("Embedding update process finished.")

if __name__ == "__main__":
    main()