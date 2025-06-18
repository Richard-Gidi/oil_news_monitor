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

def safe_request(url, max_retries=3, headers=None):
    """Make a request with retries and proper headers"""
    if headers is None:
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
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d %b %Y'
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
                            
                            # Get date - try multiple selectors
                            date_selectors = [
                                'span.article_byline',
                                'span.date',
                                'time',
                                'span.timestamp',
                                'div.date',
                                'div.timestamp'
                            ]
                            
                            date_str = None
                            for date_selector in date_selectors:
                                date_elem = article.select_one(date_selector)
                                if date_elem:
                                    date_str = date_elem.get_text(strip=True)
                                    if date_str:
                                        break
                            
                            date = parse_date(date_str, 'OilPrice')
                            
                            articles.append({
                                'title': title_text,
                                'url': link,
                                'source': 'OilPrice',
                                'date': date
                            })
                            logger.info(f"Found article: {title_text} with date: {date}")
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
        
        # Bloomberg-specific headers
        bloomberg_headers = {
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
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.bloomberg.com/',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        response = safe_request(url, headers=bloomberg_headers)
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
            'div.headline-list__item',
            'div.story-package-module__story',
            'div.story-list-story__info'
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
                        'div.headline__text',
                        'a.story-list-story__headline'
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
                                'div.timestamp',
                                'div.story-list-story__timestamp',
                                'div.story-package-module__timestamp'
                            ]
                            
                            date_str = None
                            for date_selector in date_selectors:
                                date_elem = article.select_one(date_selector)
                                if date_elem:
                                    date_str = date_elem.get_text(strip=True)
                                    if date_str:
                                        break
                            
                            # If no date found in the listing, try to get it from the article page
                            if not date_str:
                                article_response = safe_request(link, headers=bloomberg_headers)
                                if article_response:
                                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                                    date_elem = article_soup.select_one('time.timestamp, span.timestamp, time, span.date')
                                    if date_elem:
                                        date_str = date_elem.get_text(strip=True)
                            
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

def get_articles_google_news():
    """Get articles from Google News search for oil and energy"""
    try:
        url = "https://news.google.com/search?q=oil+energy+market+crude+price&hl=en&gl=US&ceid=US:en"
        logger.info(f"Starting to fetch from Google News: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = safe_request(url, headers=headers)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('article'):
            try:
                link_elem = article.find('a', href=True)
                if not link_elem:
                    continue
                    
                link = link_elem['href']
                if link.startswith('./'):
                    link = 'https://news.google.com' + link[1:]
                
                title_elem = article.find('h3') or article.find('h4')
                if not title_elem:
                    continue
                    
                title_text = title_elem.text.strip()
                if not title_text:
                    continue
                
                source_elem = article.find('div', {'class': ['article-meta', 'time']})
                source_text = source_elem.text.strip() if source_elem else ''
                
                source_parts = source_text.split('·')
                source_name = source_parts[0].strip() if source_parts else 'Unknown Source'
                time_text = source_parts[1].strip() if len(source_parts) > 1 else ''
                
                date = None
                if time_text:
                    try:
                        if 'hour' in time_text.lower():
                            hours = int(''.join(filter(str.isdigit, time_text)))
                            date = datetime.now() - timedelta(hours=hours)
                        elif 'day' in time_text.lower():
                            days = int(''.join(filter(str.isdigit, time_text)))
                            date = datetime.now() - timedelta(days=days)
                        elif 'week' in time_text.lower():
                            weeks = int(''.join(filter(str.isdigit, time_text)))
                            date = datetime.now() - timedelta(weeks=weeks)
                        elif 'month' in time_text.lower():
                            months = int(''.join(filter(str.isdigit, time_text)))
                            date = datetime.now() - timedelta(days=months*30)
                    except Exception as e:
                        logger.error(f"Error parsing date '{time_text}': {str(e)}")
                
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': source_name,
                    'date': date
                })
                
            except Exception as e:
                logger.error(f"Error parsing Google News article: {str(e)}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching from Google News: {str(e)}")
        return []

def get_all_articles():
    """Get articles from all sources"""
    all_articles = []
    
    # Get articles from Google News
    google_articles = get_articles_google_news()
    all_articles.extend(google_articles)
    
    # Get articles from OilPrice
    oilprice_articles = get_articles_oilprice()
    all_articles.extend(oilprice_articles)
    
    # Get articles from Reuters
    reuters_articles = get_articles_reuters()
    all_articles.extend(reuters_articles)
    
    # Get articles from Bloomberg
    bloomberg_articles = get_articles_bloomberg()
    all_articles.extend(bloomberg_articles)
    
    # Sort articles by date (most recent first)
    all_articles.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    
    return all_articles

