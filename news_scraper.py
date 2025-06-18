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
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('div', class_='categoryArticle'):
            try:
                title_elem = article.find('h2', class_='categoryArticleTitle')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = title_elem.find('a')['href']
                
                # Get the date
                date_elem = article.find('span', class_='articleByline')
                date = None
                if date_elem:
                    date_text = date_elem.text.strip()
                    try:
                        date = datetime.strptime(date_text, "%b %d, %Y")
                    except ValueError:
                        logger.error(f"Error parsing date '{date_text}'")
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'OilPrice',  # Explicitly set source
                    'date': date
                })
                logger.info(f"Found OilPrice article: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing OilPrice article: {str(e)}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching from OilPrice: {str(e)}")
        return []

def get_articles_reuters():
    """Get articles from Reuters"""
    try:
        url = "https://www.reuters.com/markets/commodities/"
        logger.info(f"Starting to fetch from Reuters: {url}")
        
        response = safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('div', class_='media-story-card'):
            try:
                title_elem = article.find('h3', class_='media-story-card__heading__eqhp9')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = title_elem.find('a')['href']
                if not link.startswith('http'):
                    link = 'https://www.reuters.com' + link
                
                # Get the date
                date_elem = article.find('time')
                date = None
                if date_elem:
                    date_text = date_elem.get('datetime', '')
                    try:
                        date = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        logger.error(f"Error parsing date '{date_text}'")
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Reuters',  # Explicitly set source
                    'date': date
                })
                logger.info(f"Found Reuters article: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing Reuters article: {str(e)}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching from Reuters: {str(e)}")
        return []

def get_articles_bloomberg():
    """Get articles from Bloomberg"""
    try:
        url = "https://www.bloomberg.com/markets/commodities"
        logger.info(f"Starting to fetch from Bloomberg: {url}")
        
        response = safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('div', class_='story-list-story'):
            try:
                title_elem = article.find('h3', class_='headline__text')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = title_elem.find('a')['href']
                if not link.startswith('http'):
                    link = 'https://www.bloomberg.com' + link
                
                # Get the date
                date_elem = article.find('time')
                date = None
                if date_elem:
                    date_text = date_elem.get('datetime', '')
                    try:
                        date = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        logger.error(f"Error parsing date '{date_text}'")
                
                articles.append({
                    'title': title,
                    'url': link,
                    'source': 'Bloomberg',  # Explicitly set source
                    'date': date
                })
                logger.info(f"Found Bloomberg article: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing Bloomberg article: {str(e)}")
                continue
        
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
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = safe_request(url, headers=headers)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for article in soup.find_all('article'):
            try:
                title_elem = article.find('h3') or article.find('h4')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = title_elem.find('a')['href']
                if link.startswith('./'):
                    link = 'https://news.google.com' + link[1:]
                
                # Get the source and time
                source_elem = article.find('div', {'class': ['article-meta', 'time']})
                source_text = source_elem.text.strip() if source_elem else ''
                
                source_parts = source_text.split('·')
                source_name = source_parts[0].strip() if source_parts else 'Unknown Source'
                time_text = source_parts[1].strip() if len(source_parts) > 1 else ''
                
                # Parse the date
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
                    'title': title,
                    'url': link,
                    'source': source_name,  # Use the source name from Google News
                    'date': date
                })
                logger.info(f"Found Google News article: {title} from {source_name}")
                
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

