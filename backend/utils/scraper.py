import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def scrape_url(url: str) -> str:
    """
    Scrapes the main text content from a given URL.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # A simple approach to get the main content:
        # join the text of all paragraph tags.
        # This can be improved with more sophisticated methods.
        paragraphs = soup.find_all('p')
        main_content = "\n".join([p.get_text() for p in paragraphs])

        if not main_content:
            # Fallback to getting all text if no paragraphs are found
            main_content = soup.get_text(separator='\n', strip=True)

        return main_content

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping {url}: {e}")
        return None
