import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'DNT': '1'
}

def safe_request(url, timeout=15, max_retries=3):
    """Make a request with retries and error handling"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(random.uniform(2, 4))
    return None

def get_articles_oilprice():
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        logger.info(f"Fetching from OilPrice: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'div.categoryArticle',
            'article.categoryArticle',
            'div.article-list-item',
            'div.article-item',
            'div.article'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h2 a, h3 a, a.title, a.headline')
                if title:
                    title_text = title.text.strip()
                    link = title.get('href', '')
                    if not link.startswith('http'):
                        link = urljoin('https://oilprice.com', link)
                    articles.append({
                        'title': title_text,
                        'url': link,
                        'source': 'OilPrice'
                    })
        
        logger.info(f"Found {len(articles)} articles from OilPrice")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching OilPrice: {str(e)}")
        return []

def get_articles_reuters():
    try:
        url = "https://www.reuters.com/business/energy/"
        logger.info(f"Fetching from Reuters: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'div[data-testid="MediaStoryCard"]',
            'div[data-testid="StoryCard"]',
            'article.story-card',
            'div.story-card'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h3, h2, a[data-testid="Headline"]')
                link = article.select_one('a')
                if title and link:
                    title_text = title.text.strip()
                    article_url = link.get('href', '')
                    if not article_url.startswith('http'):
                        article_url = urljoin('https://www.reuters.com', article_url)
                    articles.append({
                        'title': title_text,
                        'url': article_url,
                        'source': 'Reuters'
                    })
        
        logger.info(f"Found {len(articles)} articles from Reuters")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Reuters: {str(e)}")
        return []

def get_articles_rigzone():
    try:
        url = "https://www.rigzone.com/news/"
        logger.info(f"Fetching from Rigzone: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'div.article-list-item',
            'article.article-list-item',
            'div.article-item',
            'div.article'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h3 a, h2 a, a.title, a.headline')
                if title:
                    title_text = title.text.strip()
                    link = title.get('href', '')
                    if not link.startswith('http'):
                        link = urljoin('https://www.rigzone.com', link)
                    articles.append({
                        'title': title_text,
                        'url': link,
                        'source': 'Rigzone'
                    })
        
        logger.info(f"Found {len(articles)} articles from Rigzone")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Rigzone: {str(e)}")
        return []

def get_articles_energy_voice():
    try:
        url = "https://www.energyvoice.com/oilandgas/"
        logger.info(f"Fetching from Energy Voice: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'article.post',
            'div.article-item',
            'div.post-item',
            'div.article'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h2 a, h3 a, a.title, a.headline')
                if title:
                    title_text = title.text.strip()
                    link = title.get('href', '')
                    if not link.startswith('http'):
                        link = urljoin('https://www.energyvoice.com', link)
                    articles.append({
                        'title': title_text,
                        'url': link,
                        'source': 'Energy Voice'
                    })
        
        logger.info(f"Found {len(articles)} articles from Energy Voice")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Energy Voice: {str(e)}")
        return []

def get_articles_upstream():
    try:
        url = "https://www.upstreamonline.com/latest-news"
        logger.info(f"Fetching from Upstream: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'div.article-item',
            'article.article-item',
            'div.news-item',
            'div.article'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h3 a, h2 a, a.title, a.headline')
                if title:
                    title_text = title.text.strip()
                    link = title.get('href', '')
                    if not link.startswith('http'):
                        link = urljoin('https://www.upstreamonline.com', link)
                    articles.append({
                        'title': title_text,
                        'url': link,
                        'source': 'Upstream'
                    })
        
        logger.info(f"Found {len(articles)} articles from Upstream")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Upstream: {str(e)}")
        return []

def get_articles_offshore_energy():
    try:
        url = "https://www.offshore-energy.biz/news/"
        logger.info(f"Fetching from Offshore Energy: {url}")
        res = safe_request(url)
        if not res:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'article.post',
            'div.post-item',
            'div.article-item',
            'div.article'
        ]
        
        for selector in selectors:
            for article in soup.select(selector):
                title = article.select_one('h2 a, h3 a, a.title, a.headline')
                if title:
                    title_text = title.text.strip()
                    link = title.get('href', '')
                    if not link.startswith('http'):
                        link = urljoin('https://www.offshore-energy.biz', link)
                    articles.append({
                        'title': title_text,
                        'url': link,
                        'source': 'Offshore Energy'
                    })
        
        logger.info(f"Found {len(articles)} articles from Offshore Energy")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Offshore Energy: {str(e)}")
        return []

def test_source(source_func):
    """Test a single source and return the results"""
    try:
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
    all_articles = []
    
    # Fetch from all sources
    sources = [
        get_articles_oilprice,
        get_articles_reuters,
        get_articles_rigzone,
        get_articles_energy_voice,
        get_articles_upstream,
        get_articles_offshore_energy
    ]
    
    # Test each source first
    logger.info("Testing all sources...")
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
    
    logger.info(f"Total articles fetched: {len(all_articles)}")
    # Sort by source and limit to most recent
    return sorted(all_articles, key=lambda x: x['source'])[:30]

