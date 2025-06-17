import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin
import json
import feedparser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# More realistic browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'DNT': '1'
}

def safe_request(url, timeout=30, max_retries=3):
    """Make a request with retries and error handling"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting request to {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Successfully fetched {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All attempts failed for {url}")
                raise
            time.sleep(random.uniform(2, 4))
    return None

def get_articles_oilprice():
    """Get articles from OilPrice.com"""
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        response = safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Find all article containers
        for article in soup.find_all('div', class_='categoryArticle'):
            try:
                title_elem = article.find('h2', class_='categoryArticleTitle')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                link = title_elem.find('a')['href']
                
                # Get date
                date_elem = article.find('span', class_='article_byline')
                date_str = date_elem.get_text(strip=True) if date_elem else None
                date = None
                if date_str:
                    try:
                        # Try to parse the date string
                        date = datetime.strptime(date_str, '%b %d, %Y')
                    except:
                        try:
                            # Try alternative format
                            date = datetime.strptime(date_str, '%B %d, %Y')
                        except:
                            date = None
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'OilPrice',
                    'date': date
                })
            except Exception as e:
                logger.error(f"Error parsing OilPrice article: {str(e)}")
                continue
                
        logger.info(f"Found {len(articles)} articles from OilPrice")
        return articles
    except Exception as e:
        logger.error(f"Error fetching from OilPrice: {str(e)}")
        return []

def get_articles_reuters():
    """Get articles from Reuters Energy News"""
    try:
        url = "https://www.reuters.com/business/energy/"
        response = safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Find all article containers
        for article in soup.find_all(['article', 'div'], class_=['media-story-card', 'story-card']):
            try:
                title_elem = article.find(['h3', 'h2'], class_=['media-story-card__heading__eqhp9', 'story-card__heading'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                link = article.find('a')['href']
                if not link.startswith('http'):
                    link = urljoin(url, link)
                
                # Get date
                date_elem = article.find(['time', 'span'], class_=['media-story-card__timestamp__1j5qf', 'story-card__timestamp'])
                date_str = date_elem.get_text(strip=True) if date_elem else None
                date = None
                if date_str:
                    try:
                        # Try to parse the date string
                        date = datetime.strptime(date_str, '%b %d, %Y')
                    except:
                        try:
                            # Try alternative format
                            date = datetime.strptime(date_str, '%B %d, %Y')
                        except:
                            date = None
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Reuters',
                    'date': date
                })
            except Exception as e:
                logger.error(f"Error parsing Reuters article: {str(e)}")
                continue
                
        logger.info(f"Found {len(articles)} articles from Reuters")
        return articles
    except Exception as e:
        logger.error(f"Error fetching from Reuters: {str(e)}")
        return []

def get_articles_bloomberg():
    """Get articles from Bloomberg Energy News"""
    try:
        url = "https://www.bloomberg.com/markets/commodities"
        response = safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Find all article containers
        for article in soup.find_all(['article', 'div'], class_=['story-list-story', 'story-package-module__story']):
            try:
                title_elem = article.find(['h3', 'h2'], class_=['headline__text', 'story-package-module__headline'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                link = article.find('a')['href']
                if not link.startswith('http'):
                    link = urljoin(url, link)
                
                # Get date
                date_elem = article.find(['time', 'span'], class_=['timestamp', 'story-package-module__timestamp'])
                date_str = date_elem.get_text(strip=True) if date_elem else None
                date = None
                if date_str:
                    try:
                        # Try to parse the date string
                        date = datetime.strptime(date_str, '%b %d, %Y')
                    except:
                        try:
                            # Try alternative format
                            date = datetime.strptime(date_str, '%B %d, %Y')
                        except:
                            date = None
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Bloomberg',
                    'date': date
                })
            except Exception as e:
                logger.error(f"Error parsing Bloomberg article: {str(e)}")
                continue
                
        logger.info(f"Found {len(articles)} articles from Bloomberg")
        return articles
    except Exception as e:
        logger.error(f"Error fetching from Bloomberg: {str(e)}")
        return []

def test_source(source_func):
    """Test a single source and return the results"""
    try:
        logger.info(f"Testing source: {source_func.__name__}")
        articles = source_func()
        if articles:
            logger.info(f"✅ {source_func.__name__} succeeded with {len(articles)} articles")
            return True, len(articles)
        else:
            logger.warning(f"⚠️ {source_func.__name__} returned no articles")
            return False, 0
    except Exception as e:
        logger.error(f"❌ {source_func.__name__} failed: {str(e)}")
        return False, 0

def fetch_all_articles():
    """Fetch articles from all sources"""
    all_articles = []
    
    # Fetch from each source
    sources = [
        get_articles_oilprice,
        get_articles_reuters,
        get_articles_bloomberg
    ]
    
    for source_func in sources:
        try:
            articles = source_func()
            if articles:
                all_articles.extend(articles)
            time.sleep(2)  # Delay between requests
        except Exception as e:
            logger.error(f"Error fetching from source: {str(e)}")
            continue
    
    # Sort articles by date if available, otherwise by source
    all_articles.sort(key=lambda x: (x.get('date', datetime.min), x['source']), reverse=True)
    
    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles

