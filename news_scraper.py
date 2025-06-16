import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

def get_articles_oilprice():
    try:
        url = "https://oilprice.com/Latest-Energy-News/World-News/"
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.categoryArticle'):
            title = article.select_one('h2 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': 'OilPrice'
                })
        return articles[:10] if articles else []
    except Exception as e:
        print(f"Error fetching OilPrice: {e}")
        return []

def get_articles_reuters():
    try:
        url = "https://www.reuters.com/business/energy/"
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div[data-testid="MediaStoryCard"]'):
            title = article.select_one('h3')
            link = article.select_one('a')
            if title and link:
                title_text = title.text.strip()
                article_url = 'https://www.reuters.com' + link.get('href', '')
                articles.append({
                    'title': title_text,
                    'url': article_url,
                    'source': 'Reuters'
                })
        return articles[:10] if articles else []
    except Exception as e:
        print(f"Error fetching Reuters: {e}")
        return []

def get_articles_rigzone():
    try:
        url = "https://www.rigzone.com/news/"
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.article-list-item'):
            title = article.select_one('h3 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': 'Rigzone'
                })
        return articles[:10] if articles else []
    except Exception as e:
        print(f"Error fetching Rigzone: {e}")
        return []

def get_articles_platts():
    try:
        url = "https://www.spglobal.com/platts/en/market-insights/latest-news/oil"
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = []
        for article in soup.select('div.article-card'):
            title = article.select_one('h3 a')
            if title:
                title_text = title.text.strip()
                link = title.get('href', '')
                articles.append({
                    'title': title_text,
                    'url': link,
                    'source': 'S&P Global Platts'
                })
        return articles[:10] if articles else []
    except Exception as e:
        print(f"Error fetching Platts: {e}")
        return []

def fetch_all_articles():
    all_articles = []
    
    # Fetch from all sources
    sources = [
        get_articles_oilprice,
        get_articles_reuters,
        get_articles_rigzone,
        get_articles_platts
    ]
    
    for source_func in sources:
        try:
            articles = source_func()
            all_articles.extend(articles)
            # Add a small delay between requests to be respectful
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error in source {source_func.__name__}: {e}")
            continue
    
    # Sort by source and limit to most recent
    return sorted(all_articles, key=lambda x: x['source'])[:30]

