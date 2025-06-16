import streamlit as st
import requests
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from transformers import pipeline
import numpy as np
from dotenv import load_dotenv
import os

# --- Setup ---
st.set_page_config(page_title="📰 Oil Market News Tracker", layout="wide")
st.title("🛢️ Oil Market News Tracker")


# --- Load Environment Variables ---
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")
SEARCH_QUERY = "oil OR crude oil OR OPEC OR war OR tariff"
URL = f"https://newsapi.org/v2/everything?q={SEARCH_QUERY}&language=en&sortBy=publishedAt&apiKey={API_KEY}"

# --- Hugging Face Pipelines ---
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
sentiment_analyzer = pipeline("sentiment-analysis")

# --- Fetch News ---
def fetch_news():
    response = requests.get(URL)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get("articles", [])

# --- Intelligent Filtering Based on Market Impact ---
def is_relevant(article):
    title = (article.get('title') or '').lower()
    description = (article.get('description') or '').lower()
    content = title + " " + description

    triggers = [
        "opec", "opec+", "production cut", "supply cut", "output cut",
        "sanction", "houthi", "middle east", "iran", "russia", "saudi arabia",
        "geopolitical", "conflict", "strike", "pipeline", "suez canal", 
        "refinery", "demand", "inflation", "recession", "forecast", 
        "inventory", "stockpile", "tariff", "war", "attack", "crude draw",
        "api report", "eia report", "bls data", "interest rate"
    ]

    return any(trigger in content for trigger in triggers)


# --- Cluster News Titles ---
def cluster_titles(titles):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(titles)
    clustering = DBSCAN(eps=0.4, min_samples=2).fit(embeddings)
    clusters = {}
    for i, label in enumerate(clustering.labels_):
        if label == -1:
            continue  # Noise
        clusters.setdefault(label, []).append(i)
    return clusters

# --- Summarize Clusters ---
def summarize_clusters(clusters, articles):
    summaries = {}
    for label, indices in clusters.items():
        text = " ".join([articles[i]['title'] for i in indices])
        summary = summarizer(text, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
        summaries[label] = summary
    return summaries

# --- Assess Sentiment & Impact ---
def assess_impact(summaries):
    impact_scores = {}
    for label, summary in summaries.items():
        sentiment = sentiment_analyzer(summary)[0]
        label_text = sentiment['label']
        score = sentiment['score']
        if label_text == "POSITIVE":
            impact = f"Low (confidence {score:.2f})"
        elif label_text == "NEGATIVE":
            impact = f"High (confidence {score:.2f})"
        else:
            impact = f"Medium (confidence {score:.2f})"
        impact_scores[label] = (label_text, impact)
    return impact_scores

# --- Most Pressing Development ---
def get_most_pressing(impacts, summaries):
    worst_label = None
    max_score = -1
    for label, (sentiment, impact_text) in impacts.items():
        score = float(impact_text.split("confidence")[1].replace(")", "").strip())
        if sentiment == "NEGATIVE" and score > max_score:
            max_score = score
            worst_label = label
    return worst_label, summaries.get(worst_label, ""), max_score

# --- Market Sentiment Score ---
def compute_market_sentiment(impacts):
    score_map = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}
    scores = [score_map.get(sentiment, 0) for sentiment, _ in impacts.values()]
    avg_score = np.mean(scores)
    if avg_score > 0.3:
        return "🟢 Overall Positive Market Sentiment"
    elif avg_score < -0.3:
        return "🔴 Overall Negative Market Sentiment"
    else:
        return "🟡 Mixed or Neutral Market Sentiment"

# --- Run Pipeline ---
with st.spinner("Fetching and analyzing news..."):
    articles = fetch_news()

    # Apply relevance filter
    relevant_articles = [article for article in articles if is_relevant(article)]
    titles = [article['title'] for article in relevant_articles if article['title']]

    if titles:
        clusters = cluster_titles(titles)
        summaries = summarize_clusters(clusters, relevant_articles)
        impacts = assess_impact(summaries)
        pressing_label, pressing_summary, pressing_confidence = get_most_pressing(impacts, summaries)
        sentiment_summary = compute_market_sentiment(impacts)
    else:
        clusters, summaries, impacts = {}, {}, {}
        pressing_label, pressing_summary, pressing_confidence = None, "", 0
        sentiment_summary = ""

# --- Display Results ---
if not titles:
    st.error("No impactful articles found. Try again later or check your API key.")
else:
    # Most Pressing Development
    if pressing_label is not None:
        st.header("🚨 Most Pressing Oil Market Development")
        st.markdown(f"**Summary:** {pressing_summary}")
        st.markdown(f"**Confidence of Impact:** `{pressing_confidence:.2f}`")
        st.markdown("---")

    # Overall Market Sentiment
    st.header("📊 Oil Market Sentiment")
    st.markdown(f"### {sentiment_summary}")
    st.markdown("---")

    # Clustered Summaries
    st.subheader("🗂️ Clustered News Summaries & Impact")
    for label, indices in clusters.items():
        st.markdown(f"### 🧠 Cluster {label}")
        for i in indices:
            st.markdown(f"- [{relevant_articles[i]['title']}]({relevant_articles[i]['url']})")
        st.markdown(f"**📝 Summary:** {summaries[label]}")
        sentiment, impact = impacts[label]
        st.markdown(f"**📈 Sentiment:** `{sentiment}`")
        st.markdown(f"**📊 Estimated Impact on Oil Price:** `{impact}`")
        st.markdown("---")
