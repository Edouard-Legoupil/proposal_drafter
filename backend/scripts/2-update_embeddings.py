import argparse
import asyncio
import os
import sys
import csv
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.utils.embedding_utils import process_and_store_text
from backend.utils.scraper import scrape_url

def main():
    parser = argparse.ArgumentParser(description="Update embeddings for all knowledge card references.")
    parser.add_argument("--force-rescrape", action="store_true", help="Force re-scraping of all references.")
    parser.add_argument("--test-scrap", action="store_true", help="Test scraping of all reference URLs and log failures.")
    args = parser.parse_args()

    print("Starting embedding update process...")

    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Database connection
    db_username = os.getenv("DB_USERNAME", "").strip().strip('"')
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "").strip()

    if not all([db_username, db_password, db_name]):
        print("Error: Database credentials not found in .env file.")
        sys.exit(1)

    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=db_username,
        password=db_password,
        host="localhost",
        port="5432",
        database=db_name
    )
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
        if args.test_scrap:
            print("Starting scrape test...")
            failed_urls = []
            references = session.execute(text("SELECT id, url FROM knowledge_card_references")).fetchall()
            for ref in references:
                try:
                    print(f"  - Testing URL: {ref.url}")
                    scrape_url(ref.url)
                except Exception as e:
                    print(f"  - Failed to scrape URL: {ref.url} with error: {e}")
                    failed_urls.append({'url': ref.url, 'error': str(e)})

            if failed_urls:
                log_dir = 'log'
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = os.path.join(log_dir, f"scrape_test_failures_{timestamp}.csv")

                with open(log_file, 'w', newline='') as csvfile:
                    fieldnames = ['url', 'error']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(failed_urls)

                print(f"Scrape test finished. Found {len(failed_urls)} failures. See {log_file} for details.")
            else:
                print("Scrape test finished. All URLs were successfully scraped.")

        else:
            with session.begin():
                references = session.execute(text("SELECT id, url FROM knowledge_card_references")).fetchall()
                print(f"Found {len(references)} references to process.")

                for ref in references:
                    print(f"Processing reference {ref.id} from URL: {ref.url}")
                    try:
                        content = ""
                        if args.force_rescrape:
                            print(f"  - Force re-scraping URL: {ref.url}")
                            content = scrape_url(ref.url)
                        else:
                            # Reconstruct content from existing chunks
                            chunks_result = session.execute(
                                text("SELECT text_chunk FROM knowledge_card_reference_vectors WHERE reference_id = :ref_id ORDER BY id"),
                                {"ref_id": ref.id}
                            ).fetchall()
                            if chunks_result:
                                content = "".join([chunk[0] for chunk in chunks_result])
                                print(f"  - Reconstructed content from {len(chunks_result)} chunks.")
                            else:
                                print(f"  - No existing chunks found, scraping URL: {ref.url}")
                                content = scrape_url(ref.url)

                        if content:
                            asyncio.run(process_and_store_text(ref.id, content, session))
                            print(f"  - Successfully processed and stored embeddings for reference {ref.id}")
                        else:
                            print(f"  - No content to process for reference {ref.id}")

                    except Exception as e:
                        print(f"  - Error processing reference {ref.id}: {e}")

                print("Embedding update process finished.")

if __name__ == "__main__":
    main()