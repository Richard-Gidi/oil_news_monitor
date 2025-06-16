from collections import Counter
import re

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def find_common_topics(all_articles):
    flattened = [clean_text(item) for source in all_articles.values() for item in source]
    counts = Counter(flattened)
    duplicates = [item for item, count in counts.items() if count > 1]
    return duplicates[:1]  # Most pressing

def generate_summary(news_items):
    from transformers import pipeline
    summarizer = pipeline("summarization")
    combined = " ".join(news_items)
    return summarizer(combined[:1000])[0]['summary_text']
