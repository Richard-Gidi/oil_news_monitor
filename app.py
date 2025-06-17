import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from transformers import pipeline
import numpy as np
from datetime import datetime, timedelta
from news_scraper import fetch_all_articles
from textblob import TextBlob
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from io import StringIO
import yfinance as yf
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a string buffer to capture logs
log_buffer = StringIO()
handler = logging.StreamHandler(log_buffer)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Set page config - must be the first Streamlit command
st.set_page_config(page_title="Oil News Monitor", layout="wide")

# --- Setup ---
st.title("🛢️ Oil Market News Tracker")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

# Debug section at the top
st.sidebar.header("🔧 Debug Information")
if st.sidebar.button("Test News Fetch"):
    with st.spinner("Testing news fetch..."):
        articles = fetch_all_articles()
        st.sidebar.write(f"Total articles fetched: {len(articles)}")
        if articles:
            st.sidebar.write("Sample articles:")
            for article in articles[:3]:
                st.sidebar.write(f"- {article['title']} ({article['source']})")
        else:
            st.sidebar.error("No articles were fetched")

# --- Hugging Face Pipelines ---
@st.cache_resource
def load_models():
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        logger.info("Successfully loaded BART summarizer")
    except Exception as e:
        logger.warning(f"Could not load BART summarizer: {str(e)}")
        st.warning("Could not load BART summarizer, falling back to TextBlob")
        summarizer = None
    
    try:
        sentiment_analyzer = pipeline(
            "sentiment-analysis", 
            model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
        )
        logger.info("Successfully loaded DistilBERT sentiment analyzer")
    except Exception as e:
        logger.warning(f"Could not load DistilBERT sentiment analyzer: {str(e)}")
        st.warning("Could not load DistilBERT sentiment analyzer, falling back to TextBlob")
        sentiment_analyzer = None
    
    return summarizer, sentiment_analyzer

summarizer, sentiment_analyzer = load_models()

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
@st.cache_resource
def load_sentence_transformer():
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Successfully loaded SentenceTransformer model")
        return model
    except Exception as e:
        logger.error(f"Error loading SentenceTransformer: {str(e)}")
        raise e

def cluster_titles(titles):
    model = load_sentence_transformer()
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
            try:
                if summarizer is not None:
                    summary = summarizer(text, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
                else:
                    # Fallback to TextBlob for basic summarization
                    blob = TextBlob(text)
                    sentences = blob.sentences
                    summary = " ".join([str(s) for s in sentences[:2]])  # Take first two sentences
                summaries[label] = summary
            except Exception as e:
                logger.error(f"Error summarizing cluster {label}: {str(e)}")
                summaries[label] = f"Error summarizing cluster: {str(e)}"
    return summaries

# --- Sentiment & Impact ---
def assess_impact(summaries):
    impact_scores = {}
    for label, summary in summaries.items():
        try:
            if sentiment_analyzer is not None:
                sentiment = sentiment_analyzer(summary)[0]
                label_text = sentiment['label']
                score = sentiment['score']
            else:
                # Fallback to TextBlob for sentiment analysis
                blob = TextBlob(summary)
                polarity = blob.sentiment.polarity
                if polarity > 0.1:
                    label_text = "POSITIVE"
                    score = polarity
                elif polarity < -0.1:
                    label_text = "NEGATIVE"
                    score = abs(polarity)
                else:
                    label_text = "NEUTRAL"
                    score = 0.5

            if label_text == "POSITIVE":
                impact = f"Low (confidence {score:.2f})"
            elif label_text == "NEGATIVE":
                impact = f"High (confidence {score:.2f})"
            else:
                impact = f"Medium (confidence {score:.2f})"
            impact_scores[label] = (label_text, impact)
        except Exception as e:
            logger.error(f"Error assessing impact for cluster {label}: {str(e)}")
            impact_scores[label] = ("NEUTRAL", f"Error assessing impact: {str(e)}")
    return impact_scores

# --- Most Pressing ---
def get_most_pressing(impacts, summaries):
    worst_label = None
    max_score = -1
    for label, (sentiment, impact_text) in impacts.items():
        try:
            score = float(impact_text.split("confidence")[1].replace(")", "").strip())
            if sentiment == "NEGATIVE" and score > max_score:
                max_score = score
                worst_label = label
        except Exception as e:
            logger.error(f"Error processing impact for cluster {label}: {str(e)}")
            continue
    return worst_label, summaries.get(worst_label, ""), max_score

# --- Market Sentiment ---
def compute_market_sentiment(impacts):
    score_map = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}
    scores = [score_map.get(sentiment, 0) for sentiment, _ in impacts.values()]
    if not scores:
        return "🟡 No sentiment data available"
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
    try:
        logger.info("Starting news fetch")
        articles = fetch_all_articles()
        logger.info(f"Fetched {len(articles)} total articles")
        
        # Show raw articles in debug section
        with st.expander("🔍 Debug: Raw Articles"):
            if articles:
                st.write(f"Total articles fetched: {len(articles)}")
                for article in articles:
                    st.write(f"- [{article['title']}]({article['url']}) ({article['source']})")
            else:
                st.error("No articles were fetched")
        
        if not articles:
            st.error("No articles were fetched from any source. Please check your internet connection and try again.")
            st.stop()
            
        relevant_articles = [a for a in articles if is_relevant(a, custom_triggers)]
        logger.info(f"Found {len(relevant_articles)} relevant articles")
        
        if not relevant_articles:
            st.error("No articles matched the relevance criteria. Try adding more keywords in the sidebar.")
            st.stop()
            
        titles = [a['title'] for a in relevant_articles if a.get('title')]
        logger.info(f"Processing {len(titles)} titles")

        if titles:
            clusters = cluster_titles(titles)
            logger.info(f"Created {len(clusters)} clusters")
            
            summaries = summarize_clusters(clusters, relevant_articles)
            logger.info("Generated summaries")
            
            impacts = assess_impact(summaries)
            logger.info("Assessed impacts")
            
            pressing_label, pressing_summary, pressing_confidence = get_most_pressing(impacts, summaries)
            sentiment_summary = compute_market_sentiment(impacts)
        else:
            clusters, summaries, impacts = {}, {}, {}
            pressing_label, pressing_summary, pressing_confidence = None, "", 0
            sentiment_summary = ""
    except Exception as e:
        logger.error(f"An error occurred during analysis: {str(e)}")
        st.error(f"An error occurred during analysis: {str(e)}")
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

# Cache the model loading
@st.cache_resource
def load_sentiment_model():
    """Load sentiment analysis model"""
    try:
        logger.info("Loading sentiment analysis model...")
        # No need to load anything for TextBlob
        return True
    except Exception as e:
        logger.error(f"Error loading sentiment model: {str(e)}")
        return False

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    try:
        if not text or not isinstance(text, str):
            return 0.0
            
        # Clean the text
        text = text.strip()
        if not text:
            return 0.0
            
        # Get sentiment
        analysis = TextBlob(text)
        # Convert from -1 to 1 scale to 0 to 1 scale
        sentiment = (analysis.sentiment.polarity + 1) / 2
        return sentiment
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return 0.0

def get_oil_price_data():
    """Get oil price data from Yahoo Finance"""
    try:
        # Get data for both WTI and Brent
        wti = yf.download("CL=F", start=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                         end=datetime.now().strftime('%Y-%m-%d'), progress=False)
        brent = yf.download("BZ=F", start=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                          end=datetime.now().strftime('%Y-%m-%d'), progress=False)
        
        # Create a DataFrame with both prices
        df = pd.DataFrame({
            'WTI': wti['Close'],
            'Brent': brent['Close']
        })
        
        return df
    except Exception as e:
        logger.error(f"Error fetching oil price data: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("Oil News Monitor")
    
    # Sidebar
    st.sidebar.title("Settings")
    
    # Debug section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Debug")
    if st.sidebar.button("Test News Fetch"):
        try:
            articles = fetch_all_articles()
            st.sidebar.write(f"Total articles fetched: {len(articles)}")
            if articles:
                st.sidebar.write("Sample articles:")
                for article in articles[:3]:
                    st.sidebar.write(f"- {article['title']} ({article['source']})")
        except Exception as e:
            st.sidebar.error(f"Error testing news fetch: {str(e)}")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Oil Price Trends")
        df = get_oil_price_data()
        
        if not df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['WTI'], name='WTI', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df.index, y=df['Brent'], name='Brent', line=dict(color='red')))
            fig.update_layout(
                title='WTI vs Brent Crude Oil Prices',
                xaxis_title='Date',
                yaxis_title='Price (USD)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to fetch oil price data")
    
    with col2:
        st.subheader("Latest News")
        try:
            articles = fetch_all_articles()
            
            if not articles:
                st.warning("No articles found. Please check the debug section for more information.")
            else:
                # Debug expander
                with st.expander("Debug: Raw Articles"):
                    st.write(f"Total articles fetched: {len(articles)}")
                    for article in articles:
                        st.write(f"- {article['title']} ({article['source']})")
                
                # Process articles
                for article in articles:
                    with st.container():
                        st.markdown(f"### {article['title']}")
                        st.markdown(f"Source: {article['source']}")
                        st.markdown(f"[Read more]({article['url']})")
                        
                        # Analyze sentiment
                        sentiment = analyze_sentiment(article['title'])
                        sentiment_color = 'green' if sentiment > 0.6 else 'red' if sentiment < 0.4 else 'gray'
                        st.markdown(f"Sentiment: :{sentiment_color}[{sentiment:.2f}]")
                        
                        st.markdown("---")
        except Exception as e:
            st.error(f"Error processing news: {str(e)}")
            logger.error(f"Error in main news processing: {str(e)}")

if __name__ == "__main__":
    main()
