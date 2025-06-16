import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0'}

def get_articles_oilprice():
    try:
        url = "https://oilprice.com/"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = [a.text.strip() for a in soup.select('a.category-article__title')]
        return articles[:10] if articles else ["No articles found"]
    except Exception as e:
        return [f"Error fetching OilPrice: {e}"]

def get_articles_bloomberg():
    try:
        url = "https://www.bloomberg.com/energy"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = [a.text.strip() for a in soup.select('a[data-testid="StoryPackageHeadline"]')]
        return articles[:10] if articles else ["No articles found"]
    except Exception as e:
        return [f"Error fetching Bloomberg: {e}"]

def get_articles_investing():
    try:
        url = "https://www.investing.com/news/commodities-news"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = [a.text.strip() for a in soup.select('a.title')]
        return articles[:10] if articles else ["No articles found"]
    except Exception as e:
        return [f"Error fetching Investing: {e}"]

def fetch_all_articles():
    return {
        "OilPrice": get_articles_oilprice(),
        "Bloomberg": get_articles_bloomberg(),
        "Investing": get_articles_investing()
    }

