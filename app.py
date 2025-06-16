import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from transformers import pipeline
import numpy as np
from datetime import datetime
from news_scraper import fetch_all_articles

# --- Setup ---
st.set_page_config(page_title="📰 Oil Market News Tracker", layout="wide")
st.title("🛢️ Oil Market News Tracker")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

# --- Hugging Face Pipelines ---
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
sentiment_analyzer = pipeline(
    "sentiment-analysis", 
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
)

# --- Relevance Filter ---
def is_relevant(article, extra_triggers=[]):
    title = article.get('title', '').lower()
    content = title

    triggers = [
        "opec", "opec+", "production cut", "supply cut", "output cut",
        "sanction", "houthi", "middle east", "iran", "russia", "saudi arabia",
        "geopolitical", "conflict", "strike", "pipeline", "suez canal", 
        "refinery", "demand", "inflation", "recession", "forecast", 
        "inventory", "stockpile", "tariff", "war", "attack", "crude draw",
        "api report", "eia report", "bls data", "interest rate"
    ] + [term.strip() for term in extra_triggers if term.strip()]

    return any(trigger in content for trigger in triggers)

# --- Cluster Titles ---
def cluster_titles(titles):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(titles)
    clustering = DBSCAN(eps=0.4, min_samples=2).fit(embeddings)
    clusters = {}
    for i, label in enumerate(clustering.labels_):
        if label == -1:
            continue
        clusters.setdefault(label, []).append(i)
    return dict(sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True))

# --- Summarize ---
def summarize_clusters(clusters, articles):
    summaries = {}
    for label, indices in clusters.items():
        text = " ".join([articles[i]['title'] for i in indices])
        if not text.strip():
            summaries[label] = "No meaningful titles in this cluster."
        else:
            summaries[label] = summarizer(text, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
    return summaries

# --- Sentiment & Impact ---
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

# --- Most Pressing ---
def get_most_pressing(impacts, summaries):
    worst_label = None
    max_score = -1
    for label, (sentiment, impact_text) in impacts.items():
        score = float(impact_text.split("confidence")[1].replace(")", "").strip())
        if sentiment == "NEGATIVE" and score > max_score:
            max_score = score
            worst_label = label
    return worst_label, summaries.get(worst_label, ""), max_score

# --- Market Sentiment ---
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

# --- Sidebar ---
st.sidebar.header("🔍 Custom Trigger Terms")
custom_triggers = st.sidebar.text_area(
    "Enter additional keywords (comma-separated):",
    "oil, OPEC, conflict, recession"
).lower().split(",")

# --- Run Analysis ---
with st.spinner("Fetching and analyzing news..."):
    articles = fetch_all_articles()
    relevant_articles = [a for a in articles if is_relevant(a, custom_triggers)]
    titles = [a['title'] for a in relevant_articles if a.get('title')]

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
    st.error("No impactful articles found. Try again later or check your internet connection.")
else:
    st.success("✅ News analysis complete.")

    # 🚨 Most Pressing Development
    if pressing_label is not None:
        st.header("🚨 Most Pressing Oil Market Development")
        st.markdown(f"**Summary:** {pressing_summary}")
        st.markdown(f"**Confidence of Impact:** `{pressing_confidence:.2f}`")
        st.markdown("---")

    # 📊 Sentiment Summary
    st.header("📊 Oil Market Sentiment")
    st.markdown(f"### {sentiment_summary}")
    st.markdown("---")

    # 🧠 Clustered Summaries
    st.subheader("🗂️ Clustered News Summaries & Impact")
    for label, indices in clusters.items():
        st.markdown(f"### 🧠 Cluster {label}")
        for i in indices:
            article = relevant_articles[i]
            st.markdown(f"- [{article['title']}]({article['url']}) ({article['source']})")
        st.markdown(f"**📝 Summary:** {summaries[label]}")
        sentiment, impact = impacts[label]
        st.markdown(f"**📈 Sentiment:** `{sentiment}`")
        st.markdown(f"**📊 Estimated Impact on Oil Price:** `{impact}`")
        st.markdown("---")

    # 📄 Raw Article View
    with st.expander("📄 See All Fetched Articles (Raw Feed)"):
        for article in articles:
            st.markdown(f"- [{article['title']}]({article['url']}) ({article['source']})")

    # 📥 Download Button
    report = "\n\n".join([f"Cluster {label}:\nSummary: {summaries[label]}\nImpact: {impacts[label][1]}" for label in summaries])
    st.download_button("📥 Download Summary Report", report, file_name="oil_news_summary.txt")
