import requests
from bs4 import BeautifulSoup
import logging
import io
from urllib.parse import urlparse, parse_qs
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
    Handles UNHCR PDF.js viewer by extracting and downloading the actual PDF.
    """
    logger.info(f"Starting scrape for URL: {url}")

    try:
        headers = {}
        parsed_url = urlparse(url)
        
        # Check if this is a UNHCR PDF.js viewer URL
        is_unhcr_pdfjs = (parsed_url.netloc == "www.unhcr.org" and 
                          "/media/" in parsed_url.path)
        
        if parsed_url.netloc == "www.unhcr.org" or is_unhcr_pdfjs:
            logger.info("UNHCR URL detected, adding authentication headers and delay.")
            time.sleep(10)  # Add a 10-second delay
            client_id = os.getenv("cfAccessClientId")
            client_secret = os.getenv("cfAccessClientSecret")
            if client_id and client_secret:
                auth_token = f"{client_id}:{client_secret}"
                headers["Authorization"] = f"Bearer {auth_token}"
                headers["CF-Access-Client-Id"] = f"{client_id}"
            else:
                logger.warning("Cloudflare credentials not found in environment variables.")

        # Handle PDF.js viewer URLs - extract the actual PDF URL
        if is_unhcr_pdfjs:
            logger.info("UNHCR PDF.js viewer detected, extracting actual PDF URL.")
            # Extract the file parameter from query string
            query_params = parse_qs(parsed_url.query)
            file_param = query_params.get('file', [None])[0]
            
            if file_param:
                # Construct the actual PDF URL
                if file_param.startswith('/'):
                    # Absolute path
                    pdf_url = f"https://www.unhcr.org{file_param}"
                else:
                    # Relative path - construct based on current path
                    base_path = parsed_url.path.rsplit('/pdf.js/web/viewer.html', 1)[0]
                    pdf_url = f"https://www.unhcr.org{base_path}/{file_param}"
                
                logger.info(f"Extracted PDF URL: {pdf_url}")
                url = pdf_url  # Replace URL with the actual PDF URL

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

            # Additional check for PDF.js viewer in HTML content
            if "pdf.js" in soup.text.lower() or "viewer.html" in url:
                logger.info("PDF.js viewer detected in HTML, looking for PDF links...")
                # Look for PDF links in the page
                pdf_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.lower().endswith('.pdf'):
                        pdf_links.append(href)
                
                if pdf_links:
                    # Use the first PDF link found
                    pdf_url = pdf_links[0]
                    if not pdf_url.startswith('http'):
                        # Convert relative URL to absolute
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        pdf_url = base_url + pdf_url
                    
                    logger.info(f"Found PDF link, scraping: {pdf_url}")
                    return scrape_url(pdf_url)  # Recursively scrape the PDF

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