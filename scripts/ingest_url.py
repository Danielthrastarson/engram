import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup
from core.abstraction_manager import AbstractionManager

logger = logging.getLogger(__name__)

class WebScraper:
    """
    Web scraping integration (Phase 15).
    Fetches URL → extracts content → ingest.
    """
    def __init__(self):
        self.am = AbstractionManager()
        
    def ingest_url(self, url: str) -> Optional[str]:
        """Scrape URL and create abstraction"""
        try:
            logger.info(f"Fetching: {url}")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Engram Memory System)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles, nav
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
                
            # Extract main content
            title = soup.title.string if soup.title else url
            
            # Get paragraphs
            paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
            content = '\n\n'.join(paragraphs)
            
            # Chunk if too long (>2000 chars)
            if len(content) > 2000:
                chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                logger.info(f"Content chunked into {len(chunks)} pieces")
                
                # Create abstraction for each chunk
                ids = []
                for i, chunk in enumerate(chunks):
                    abs_obj, created = self.am.create_abstraction(
                        content=f"{title} (Part {i+1}/{len(chunks)})\n\n{chunk}",
                        metadata={
                            "source": "web",
                            "url": url,
                            "chunk": i + 1,
                            "total_chunks": len(chunks)
                        }
                    )
                    ids.append(abs_obj.id)
                    
                logger.info(f"✅ URL ingested as {len(ids)} chunks")
                return ids[0]  # Return first chunk ID
            else:
                # Single abstraction
                abs_obj, created = self.am.create_abstraction(
                    content=f"{title}\n\n{content}",
                    metadata={
                        "source": "web",
                        "url": url
                    }
                )
                
                logger.info(f"✅ URL ingested: {abs_obj.id[:8]}")
                return abs_obj.id
                
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python web_scraper.py <url>")
        sys.exit(1)
        
    scraper = WebScraper()
    scraper.ingest_url(sys.argv[1])
