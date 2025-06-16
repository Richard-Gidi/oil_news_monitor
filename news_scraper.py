import requests
from bs4 import BeautifulSoup

def get_articles_oilprice():
    url = "https://oilprice.com/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return [a.text.strip() for a in soup.select('a.category-article__title')][:10]

def get_articles_bloomberg():
    url = "https://www.bloomberg.com/energy"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return [a.text.strip() for a in soup.select('a[data-testid="StoryPackageHeadline"]')][:10]

def get_articles_investing():
    url = "https://www.investing.com/news/commodities-news"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    return [a.text.strip() for a in soup.select('a.title')][:10]

def fetch_all_articles():
    return {
        "OilPrice": get_articles_oilprice(),
        "Bloomberg": get_articles_bloomberg(),
        "Investing": get_articles_investing()
    }
