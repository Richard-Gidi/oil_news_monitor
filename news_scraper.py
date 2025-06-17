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
    """Fetch articles from OilPrice.com"""
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        logger.info(f"Starting to fetch from OilPrice: {url}")
        
        res = safe_request(url)
        if not res:
            logger.error("Failed to get response from OilPrice")
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
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
                            
                        articles.append({
                            'title': title_text,
                            'url': link,
                            'source': 'OilPrice'
                        })
                        logger.info(f"Found article: {title_text}")
                        break
        
        logger.info(f"Total articles found from OilPrice: {len(articles)}")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching OilPrice: {str(e)}")
        return []

def get_articles_reuters():
    """Fetch articles from Reuters using RSS feed"""
    try:
        url = "https://www.reutersagency.com/feed/?best-topics=energy&post_type=best"
        logger.info(f"Starting to fetch from Reuters RSS: {url}")
        
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link
            
            if title and link:
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Reuters'
                })
                logger.info(f"Found article: {title}")
        
        logger.info(f"Total articles found from Reuters: {len(articles)}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching Reuters: {str(e)}")
        return []

def get_articles_bloomberg():
    """Fetch articles from Bloomberg Energy"""
    try:
        url = "https://www.bloomberg.com/energy"
        logger.info(f"Starting to fetch from Bloomberg: {url}")
        
        res = safe_request(url)
        if not res:
            logger.error("Failed to get response from Bloomberg")
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'article.story-list-story',
            'div.story-list-story',
            'article.story',
            'div.story',
            'div[data-type="article"]',
            'article[data-type="article"]'
        ]
        
        for selector in selectors:
            logger.info(f"Trying selector: {selector}")
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector {selector}")
            
            for article in elements:
                # Try multiple title selectors
                title_selectors = [
                    'h3 a', 'h2 a', 'a.headline', 'a.title',
                    'h3', 'h2', 'a[data-type="headline"]'
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
                            
                        articles.append({
                            'title': title_text,
                            'url': link,
                            'source': 'Bloomberg'
                        })
                        logger.info(f"Found article: {title_text}")
                        break
        
        logger.info(f"Total articles found from Bloomberg: {len(articles)}")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Bloomberg: {str(e)}")
        return []

def get_articles_offshore_energy():
    """Fetch articles from Offshore-Energy.biz using RSS feed"""
    try:
        url = "https://www.offshore-energy.biz/feed/"
        logger.info(f"Starting to fetch from Offshore Energy RSS: {url}")
        
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link
            
            if title and link:
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Offshore Energy'
                })
                logger.info(f"Found article: {title}")
        
        logger.info(f"Total articles found from Offshore Energy: {len(articles)}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching Offshore Energy: {str(e)}")
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
    
    # List of sources to try
    sources = [
        get_articles_oilprice,
        get_articles_reuters,
        get_articles_bloomberg,
        get_articles_offshore_energy
    ]
    
    # Test each source first
    logger.info("Starting to test all sources...")
    for source_func in sources:
        success, count = test_source(source_func)
        if success:
            try:
                articles = source_func()
                if articles:
                    all_articles.extend(articles)
                    logger.info(f"Successfully fetched {len(articles)} articles from {source_func.__name__}")
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"Error in source {source_func.__name__}: {str(e)}")
                continue
    
    logger.info(f"Total articles fetched across all sources: {len(all_articles)}")
    return sorted(all_articles, key=lambda x: x['source'])[:30]

