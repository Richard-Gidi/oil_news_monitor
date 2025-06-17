import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin
import json
import feedparser
import re

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

def parse_date(date_str, source):
    """Parse date string based on source format"""
    if not date_str:
        return None
        
    date_str = date_str.strip()
    
    # Common date formats
    date_formats = [
        '%B %d, %Y',  # January 15, 2024
        '%b %d, %Y',  # Jan 15, 2024
        '%Y-%m-%d',   # 2024-01-15
        '%d %B %Y',   # 15 January 2024
        '%d %b %Y',   # 15 Jan 2024
        '%m/%d/%Y',   # 01/15/2024
        '%d/%m/%Y',   # 15/01/2024
    ]
    
    # Source-specific date formats
    source_formats = {
        'OilPrice': [
            '%b %d, %Y, %I:%M %p %Z',  # Jun 17, 2025, 1:54 AM CDT
            '%B %d, %Y, %I:%M %p %Z',  # June 17, 2025, 1:54 AM CDT
            '%b %d, %Y',  # Jun 17, 2025
            '%B %d, %Y',  # June 17, 2025
        ],
        'Reuters': [
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d %b %Y'
        ],
        'Bloomberg': [
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d %b %Y'
        ]
    }
    
    # Try source-specific formats first
    formats_to_try = source_formats.get(source, []) + date_formats
    
    for date_format in formats_to_try:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
            
    # If all parsing attempts fail, try to extract date using regex
    try:
        # Look for patterns like "2 hours ago", "5 days ago", etc.
        if 'ago' in date_str.lower():
            number = int(''.join(filter(str.isdigit, date_str)))
            if 'hour' in date_str.lower():
                return datetime.now() - timedelta(hours=number)
            elif 'day' in date_str.lower():
                return datetime.now() - timedelta(days=number)
            elif 'week' in date_str.lower():
                return datetime.now() - timedelta(weeks=number)
            elif 'month' in date_str.lower():
                return datetime.now() - timedelta(days=number*30)
    except:
        pass
        
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
        
        # Find all article containers
        article_containers = soup.find_all('div', class_='categoryArticle')
        logger.info(f"Found {len(article_containers)} article containers")
        
        for article in article_containers:
            try:
                # Get title and link
                title_elem = article.find('h2')
                if not title_elem:
                    continue
                    
                title_text = title_elem.text.strip()
                if not title_text:
                    continue
                
                # Get link
                link = title_elem.find('a')['href'] if title_elem.find('a') else None
                if not link:
                    continue
                    
                if not link.startswith('http'):
                    link = urljoin('https://oilprice.com', link)
                
                # Get date from the article page
                article_response = safe_request(link)
                if article_response:
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    # Try to find the date in the article page
                    date_elem = article_soup.find('div', class_='article_byline')
                    date_str = None
                    
                    if date_elem:
                        full_text = date_elem.text.strip()
                        logger.info(f"Found article byline: {full_text}")
                        
                        # Extract date using regex
                        date_match = re.search(r'By.*?-\s*(.*?)(?:\s*$|\s*\|)', full_text)
                        if date_match:
                            date_str = date_match.group(1).strip()
                            logger.info(f"Extracted date string: {date_str}")
                
                # Parse the date
                date = None
                if date_str:
                    try:
                        # Try to parse the date
                        date = datetime.strptime(date_str, '%b %d, %Y')
                        logger.info(f"Successfully parsed date: {date}")
                    except ValueError as e:
                        logger.error(f"Failed to parse date '{date_str}': {str(e)}")
                        date = None
                
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': 'OilPrice',
                    'date': date
                })
                logger.info(f"Added article: {title_text} with date: {date}")
                
            except Exception as e:
                logger.error(f"Error parsing article: {str(e)}")
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
                            
                            # Get date - try multiple selectors
                            date_selectors = [
                                'time[data-testid="PublishedDate"]',
                                'span[data-testid="PublishedDate"]',
                                'time',
                                'span.timestamp',
                                'div.timestamp'
                            ]
                            
                            date_str = None
                            for date_selector in date_selectors:
                                date_elem = article.select_one(date_selector)
                                if date_elem:
                                    date_str = date_elem.get_text(strip=True)
                                    if date_str:
                                        break
                            
                            date = parse_date(date_str, 'Reuters')
                            
                            articles.append({
                                'title': title_text,
                                'url': link,
                                'source': 'Reuters',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text} with date: {date}")
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
                            
                            # Get date - try multiple selectors
                            date_selectors = [
                                'time.timestamp',
                                'span.timestamp',
                                'time',
                                'span.date',
                                'div.timestamp'
                            ]
                            
                            date_str = None
                            for date_selector in date_selectors:
                                date_elem = article.select_one(date_selector)
                                if date_elem:
                                    date_str = date_elem.get_text(strip=True)
                                    if date_str:
                                        break
                            
                            date = parse_date(date_str, 'Bloomberg')
                            
                            articles.append({
                                'title': title_text,
                                'url': link,
                                'source': 'Bloomberg',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text} with date: {date}")
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

def test_oilprice_scraper():
    """Test function to debug OilPrice scraping"""
    articles = get_articles_oilprice()
    print("\n=== OilPrice Scraper Test Results ===")
    print(f"Total articles found: {len(articles)}")
    
    for i, article in enumerate(articles, 1):
        print(f"\nArticle {i}:")
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['date']}")
        print("-" * 50)

if __name__ == "__main__":
    # Run the test function
    test_oilprice_scraper()

