import argparse
import asyncio
import os
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.utils.embedding_utils import process_and_store_text
from backend.utils.scraper import scrape_url

def main():
    parser = argparse.ArgumentParser(description="Update embeddings for all knowledge card references.")
    parser.add_argument("--force-rescrape", action="store_true", help="Force re-scraping of all references.")
    args = parser.parse_args()

    print("Starting embedding update process...")

    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Database connection
    db_username = os.getenv("DB_USERNAME").strip('"')
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    DATABASE_URL = f"postgresql+psycopg2://{db_username}:{db_password}@localhost:5432/{db_name}"

    if not all([db_username, db_password, db_name]):
        print("Error: Database credentials not found in .env file.")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
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