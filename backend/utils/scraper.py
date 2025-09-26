import requests
from bs4 import BeautifulSoup
import logging
import io
from urllib.parse import urlparse
from PyPDF2 import PdfReader
import os
import time
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def scrape_url(url: str) -> str:
    """
    Scrapes the main text content from a given URL.
    Supports both HTML pages and PDF files.
    """
    logger.info(f"Starting scrape for URL: {url}")

    try:
        headers = {}
        parsed_url = urlparse(url)
        if parsed_url.netloc == "www.unhcr.org":
            logger.info("UNHCR URL detected, adding authentication headers and delay.")
            time.sleep(10)  # Add a 10-second delay
            client_id = os.getenv("CF-Access-Client-Id")
            client_secret = os.getenv("CF-Access-Client-Secret")
            if client_id and client_secret:
                auth_token = f"{client_id}:{client_secret}"
                headers["Authorization"] = f"Bearer {auth_token}"
            else:
                logger.warning("Cloudflare credentials not found in environment variables.")

        logger.info("Sending GET request...")
        response = requests.get(url, timeout=20, headers=headers)
        logger.info(f"Received response with status code: {response.status_code}")
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        logger.info(f"Detected Content-Type: {content_type}")

        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            logger.info("Processing PDF content...")
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)

            text_chunks = []
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    logger.info(f"Extracted {len(text)} characters from page {i+1}.")
                    text_chunks.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i+1}: {e}")

            main_content = "\n".join(text_chunks).strip()
            if main_content:
                logger.info(f"PDF scraping completed. Extracted {len(main_content)} characters total.")
            else:
                logger.warning("PDF parsing completed but no text extracted.")
            return main_content or None

        else:
            logger.info("Processing HTML content with BeautifulSoup...")
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info("Successfully parsed HTML.")

            paragraphs = soup.find_all('p')
            logger.info(f"Found {len(paragraphs)} <p> tags.")

            main_content = "\n".join([p.get_text(strip=True) for p in paragraphs])

            if main_content.strip():
                logger.info("Extracted text content from paragraph tags.")
            else:
                logger.warning("No paragraph content found. Falling back to extracting all text.")
                main_content = soup.get_text(separator='\n', strip=True)

            logger.info(f"HTML scraping completed. Extracted {len(main_content)} characters.")
            return main_content

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out while scraping {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while scraping {url}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error while scraping {url}: {e}")
        return None
