import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin
import json

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
            
            # Try direct request first
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                logger.info(f"Successfully fetched {url} directly")
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Direct request failed: {str(e)}")
                
                # If direct request fails, try with a proxy
                try:
                    proxies = {
                        'http': 'http://proxy.example.com:8080',  # Replace with actual proxy
                        'https': 'http://proxy.example.com:8080'
                    }
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                    response.raise_for_status()
                    logger.info(f"Successfully fetched {url} via proxy")
                    return response
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Proxy request failed: {str(e)}")
                    raise
                
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
            
        # Save the HTML for debugging
        with open('oilprice_debug.html', 'w', encoding='utf-8') as f:
            f.write(res.text)
        logger.info("Saved OilPrice HTML for debugging")
            
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

def get_articles_rigzone():
    """Fetch articles from Rigzone.com"""
    try:
        url = "https://www.rigzone.com/news/"
        logger.info(f"Starting to fetch from Rigzone: {url}")
        
        res = safe_request(url)
        if not res:
            logger.error("Failed to get response from Rigzone")
            return []
            
        # Save the HTML for debugging
        with open('rigzone_debug.html', 'w', encoding='utf-8') as f:
            f.write(res.text)
        logger.info("Saved Rigzone HTML for debugging")
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'div.article-list-item',
            'article.article-list-item',
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
                title_selectors = ['h3 a', 'h2 a', 'a.title', 'a.headline', 'h2', 'h3', 'a']
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
                            link = urljoin('https://www.rigzone.com', link)
                            
                        articles.append({
                            'title': title_text,
                            'url': link,
                            'source': 'Rigzone'
                        })
                        logger.info(f"Found article: {title_text}")
                        break
        
        logger.info(f"Total articles found from Rigzone: {len(articles)}")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Rigzone: {str(e)}")
        return []

def get_articles_energy_voice():
    """Fetch articles from EnergyVoice.com"""
    try:
        url = "https://www.energyvoice.com/oilandgas/"
        logger.info(f"Starting to fetch from Energy Voice: {url}")
        
        res = safe_request(url)
        if not res:
            logger.error("Failed to get response from Energy Voice")
            return []
            
        # Save the HTML for debugging
        with open('energyvoice_debug.html', 'w', encoding='utf-8') as f:
            f.write(res.text)
        logger.info("Saved Energy Voice HTML for debugging")
            
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        
        # Try multiple selectors
        selectors = [
            'article.post',
            'div.article-item',
            'div.post-item',
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
                            link = urljoin('https://www.energyvoice.com', link)
                            
                        articles.append({
                            'title': title_text,
                            'url': link,
                            'source': 'Energy Voice'
                        })
                        logger.info(f"Found article: {title_text}")
                        break
        
        logger.info(f"Total articles found from Energy Voice: {len(articles)}")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Energy Voice: {str(e)}")
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
        get_articles_rigzone,
        get_articles_energy_voice
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

