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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session for persistent cookies and headers
session = requests.Session()

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

def safe_request(url, max_retries=3, delay=2):
    """Make a request with retries and proper headers"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Making request to {url} (attempt {attempt + 1}/{max_retries})")
            
            # Add a small random delay
            time.sleep(delay + random.random())
            
            # Make the request with our session and headers
            response = session.get(url, headers=headers, timeout=10)
            
            # Log response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                return response
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            
        if attempt < max_retries - 1:
            wait_time = delay * (attempt + 1)
            logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
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
            
        # Log the response status and content length
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content length: {len(response.text)}")
        
        # Save the HTML content for debugging
        with open('oilprice_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Saved HTML content to oilprice_debug.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Log the page title to verify we got the right page
        page_title = soup.find('title')
        logger.info(f"Page title: {page_title.text if page_title else 'No title found'}")
        
        # Try to find the main content area
        main_content = soup.find('div', class_='categoryArticleList')
        if main_content:
            logger.info("Found main content area")
            article_containers = main_content.find_all('div', class_='categoryArticle')
            logger.info(f"Found {len(article_containers)} article containers in main content")
        else:
            logger.info("Main content area not found, trying alternative selectors")
            article_containers = []
        
        # If no articles found in main content, try alternative selectors
        if not article_containers:
            selectors = [
                'div.categoryArticle',
                'article.categoryArticle',
                'div.article-list-item',
                'div.article-item',
                'div.article',
                'div.article-content',
                'div.article-wrapper',
                'div.article-list',
                'div.article-list-wrapper'
            ]
            
            for selector in selectors:
                logger.info(f"Trying selector: {selector}")
                elements = soup.select(selector)
                logger.info(f"Found {len(elements)} elements with selector {selector}")
                
                if elements:
                    article_containers.extend(elements)
                    # Log the first element's HTML for debugging
                    logger.info(f"First element HTML: {elements[0].prettify()}")
        
        # Remove duplicates while preserving order
        seen = set()
        article_containers = [x for x in article_containers if not (x in seen or seen.add(x))]
        logger.info(f"Total unique article containers found: {len(article_containers)}")
        
        for article in article_containers:
            try:
                # Log the article HTML for debugging
                logger.info(f"Processing article HTML: {article.prettify()}")
                
                # Try multiple title selectors
                title_selectors = ['h2', 'h3', 'a.title', 'a.headline', 'div.title']
                title_text = None
                link = None
                
                for selector in title_selectors:
                    title_elem = article.select_one(selector)
                    if title_elem:
                        title_text = title_elem.text.strip()
                        if title_text:
                            # Try to get link from title element or its parent
                            link_elem = title_elem.find('a') or title_elem.parent.find('a')
                            if link_elem and 'href' in link_elem.attrs:
                                link = link_elem['href']
                                break
                
                if not title_text or not link:
                    logger.info("Skipping article - no title or link found")
                    continue
                
                if not link.startswith('http'):
                    link = urljoin('https://oilprice.com', link)
                
                logger.info(f"Found article - Title: {title_text}, Link: {link}")
                
                # Get date from the article page
                article_response = safe_request(link)
                if article_response:
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    # Try multiple date selectors
                    date_selectors = [
                        'div.article_byline',
                        'div.article-meta',
                        'div.article-meta-info',
                        'span.date',
                        'time'
                    ]
                    
                    date_str = None
                    for selector in date_selectors:
                        date_elem = article_soup.select_one(selector)
                        if date_elem:
                            full_text = date_elem.text.strip()
                            logger.info(f"Found date element text: {full_text}")
                            
                            # Extract date using regex
                            date_match = re.search(r'By.*?-\s*(.*?)(?:\s*$|\s*\|)', full_text)
                            if date_match:
                                date_str = date_match.group(1).strip()
                                logger.info(f"Extracted date string: {date_str}")
                                break
                
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

