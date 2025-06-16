import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

def get_articles_oilprice():
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        logger.info(f"Fetching from OilPrice: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"OilPrice response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.categoryArticle, article.categoryArticle'):
            title = article.select_one('h2 a, h3 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                if not link.startswith('http'):
                    link = 'https://oilprice.com' + link
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
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Reuters response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div[data-testid="MediaStoryCard"], div[data-testid="StoryCard"]'):
            title = article.select_one('h3, h2')
            link = article.select_one('a')
            if title and link:
                title_text = title.text.strip()
                article_url = link.get('href', '')
                if not article_url.startswith('http'):
                    article_url = 'https://www.reuters.com' + article_url
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
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Rigzone response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.article-list-item, article.article-list-item'):
            title = article.select_one('h3 a, h2 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.rigzone.com' + link
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

def get_articles_platts():
    try:
        url = "https://www.spglobal.com/platts/en/market-insights/latest-news/oil"
        logger.info(f"Fetching from Platts: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Platts response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.article-card, article.article-card'):
            title = article.select_one('h3 a, h2 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.spglobal.com' + link
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': 'S&P Global Platts'
                })
        logger.info(f"Found {len(articles)} articles from Platts")
        return articles[:10] if articles else []
    except Exception as e:
        logger.error(f"Error fetching Platts: {str(e)}")
        return []

def get_articles_energy_voice():
    try:
        url = "https://www.energyvoice.com/oilandgas/"
        logger.info(f"Fetching from Energy Voice: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Energy Voice response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('article.post'):
            title = article.select_one('h2 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.energyvoice.com' + link
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
        res = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Upstream response status: {res.status_code}")
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.article-item'):
            title = article.select_one('h3 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.upstreamonline.com' + link
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

def fetch_all_articles():
    all_articles = []
    
    # Fetch from all sources
    sources = [
        get_articles_oilprice,
        get_articles_reuters,
        get_articles_rigzone,
        get_articles_platts,
        get_articles_energy_voice,
        get_articles_upstream
    ]
    
    for source_func in sources:
        try:
            articles = source_func()
            if articles:  # Only add if we got articles
                all_articles.extend(articles)
                logger.info(f"Successfully fetched {len(articles)} articles from {source_func.__name__}")
            # Add a small delay between requests to be respectful
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.error(f"Error in source {source_func.__name__}: {str(e)}")
            continue
    
    logger.info(f"Total articles fetched: {len(all_articles)}")
    # Sort by source and limit to most recent
    return sorted(all_articles, key=lambda x: x['source'])[:30]

