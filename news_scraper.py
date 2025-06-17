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

def safe_request(url, max_retries=3):
    """Make a request with retries and proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to fetch {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully fetched {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

def get_articles_oilprice():
    """Get articles from OilPrice.com"""
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        logger.info(f"Starting to fetch from OilPrice: {url}")
        
        response = safe_request(url)
        if not response:
            logger.error("Failed to get response from OilPrice")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Try multiple selectors for article containers
        selectors = [
            'div.categoryArticle',
            'article.categoryArticle',
            'div.article-list-item',
            'div.article-item',
            'div.article',
            'div.article-content',
            'div.article-wrapper'
        ]
        
        for selector in selectors:
            logger.info(f"Trying selector: {selector}")
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector {selector}")
            
            for article in elements:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h2 a', 'h3 a', 'a.title', 'a.headline', 'h2', 'h3', 'a']
                    for title_selector in title_selectors:
                        title = article.select_one(title_selector)
                        if title:
                            title_text = title.text.strip()
                            if not title_text:
                                continue
                                
                            # Get link from title or parent
                            link = title.get('href', '')
                            if not link and title.parent:
                                link = title.parent.get('href', '')
                                
                            if not link.startswith('http'):
                                link = urljoin('https://oilprice.com', link)
                            
                            # Get date
                            date_elem = article.find(['span', 'time'], class_=['article_byline', 'date', 'timestamp'])
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
                                'title': title_text,
                                'url': link,
                                'source': 'OilPrice',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text}")
                            break
                except Exception as e:
                    logger.error(f"Error parsing OilPrice article: {str(e)}")
                    continue
        
        logger.info(f"Total articles found from OilPrice: {len(articles)}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching from OilPrice: {str(e)}")
        return []

def get_articles_reuters():
    """Get articles from Reuters Energy News"""
    try:
        url = "https://www.reuters.com/business/energy/"
        logger.info(f"Starting to fetch from Reuters: {url}")
        
        response = safe_request(url)
        if not response:
            logger.error("Failed to get response from Reuters")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Try multiple selectors for article containers
        selectors = [
            'div[data-testid="MediaStoryCard"]',
            'div[data-testid="StoryCard"]',
            'article.story-card',
            'div.story-card',
            'div.article-item',
            'article.article-item'
        ]
        
        for selector in selectors:
            logger.info(f"Trying selector: {selector}")
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector {selector}")
            
            for article in elements:
                try:
                    # Try multiple title selectors
                    title_selectors = [
                        'h3', 'h2', 'a[data-testid="Headline"]',
                        'a.headline', 'a.title', 'h3 a', 'h2 a'
                    ]
                    for title_selector in title_selectors:
                        title = article.select_one(title_selector)
                        if title:
                            title_text = title.text.strip()
                            if not title_text:
                                continue
                                
                            # Get link from title or parent
                            link = title.get('href', '')
                            if not link and title.parent:
                                link = title.parent.get('href', '')
                                
                            if not link.startswith('http'):
                                link = urljoin('https://www.reuters.com', link)
                            
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
                                'title': title_text,
                                'url': link,
                                'source': 'Reuters',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text}")
                            break
                except Exception as e:
                    logger.error(f"Error parsing Reuters article: {str(e)}")
                    continue
        
        logger.info(f"Total articles found from Reuters: {len(articles)}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching from Reuters: {str(e)}")
        return []

def get_articles_bloomberg():
    """Get articles from Bloomberg Energy News"""
    try:
        url = "https://www.bloomberg.com/markets/commodities"
        logger.info(f"Starting to fetch from Bloomberg: {url}")
        
        response = safe_request(url)
        if not response:
            logger.error("Failed to get response from Bloomberg")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Try multiple selectors for article containers
        selectors = [
            'div.story-list-story',
            'article.story-list-story',
            'div.story',
            'article.story',
            'div[data-type="article"]',
            'article[data-type="article"]',
            'div.headline-list__item'
        ]
        
        for selector in selectors:
            logger.info(f"Trying selector: {selector}")
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector {selector}")
            
            for article in elements:
                try:
                    # Try multiple title selectors
                    title_selectors = [
                        'h3 a', 'h2 a', 'a.headline', 'a.title',
                        'h3', 'h2', 'a[data-type="headline"]',
                        'div.headline__text'
                    ]
                    for title_selector in title_selectors:
                        title = article.select_one(title_selector)
                        if title:
                            title_text = title.text.strip()
                            if not title_text:
                                continue
                                
                            # Get link from title or parent
                            link = title.get('href', '')
                            if not link and title.parent:
                                link = title.parent.get('href', '')
                                
                            if not link.startswith('http'):
                                link = urljoin('https://www.bloomberg.com', link)
                            
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
                                'title': title_text,
                                'url': link,
                                'source': 'Bloomberg',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text}")
                            break
                except Exception as e:
                    logger.error(f"Error parsing Bloomberg article: {str(e)}")
                    continue
        
        logger.info(f"Total articles found from Bloomberg: {len(articles)}")
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
            logger.info(f"Starting to fetch from {source_func.__name__}")
            articles = source_func()
            if articles:
                all_articles.extend(articles)
                logger.info(f"Successfully fetched {len(articles)} articles from {source_func.__name__}")
            else:
                logger.warning(f"No articles found from {source_func.__name__}")
            time.sleep(2)  # Delay between requests
        except Exception as e:
            logger.error(f"Error fetching from {source_func.__name__}: {str(e)}")
            continue
    
    # Sort articles by date if available, otherwise by source
    all_articles.sort(key=lambda x: (x.get('date', datetime.min), x['source']), reverse=True)
    
    logger.info(f"Total articles fetched across all sources: {len(all_articles)}")
    return all_articles

