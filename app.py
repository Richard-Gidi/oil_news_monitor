import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from news_scraper import fetch_all_articles
import logging
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config - must be the first Streamlit command
st.set_page_config(page_title="Oil News Monitor", layout="wide")

def analyze_sentiment(text):
    """Simple sentiment analysis based on keyword matching"""
    try:
        if not text or not isinstance(text, str):
            return 0.5
            
        text = text.lower().strip()
        if not text:
            return 0.5
            
        # Define positive and negative keywords
        positive_keywords = [
            'rise', 'up', 'gain', 'increase', 'surge', 'rally', 'growth',
            'positive', 'bullish', 'recovery', 'higher', 'strong', 'boost'
        ]
        negative_keywords = [
            'fall', 'down', 'drop', 'decrease', 'plunge', 'decline', 'loss',
            'negative', 'bearish', 'weaker', 'lower', 'weak', 'crash'
        ]
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in positive_keywords if word in text)
        negative_count = sum(1 for word in negative_keywords if word in text)
        
        # Calculate sentiment score
        total = positive_count + negative_count
        if total == 0:
            return 0.5
        return positive_count / total
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return 0.5

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

def filter_articles_by_keywords(articles, keywords):
    """Filter articles based on keywords"""
    if not keywords:
        return articles
        
    filtered_articles = []
    for article in articles:
        title = article['title'].lower()
        if any(keyword.lower() in title for keyword in keywords):
            filtered_articles.append(article)
    return filtered_articles

def summarize_articles(articles):
    """Summarize articles focusing on USD and oil market impact"""
    if not articles:
        return "No articles to summarize."
    
    # Group articles by source
    articles_by_source = {}
    for article in articles:
        source = article['source']
        if source not in articles_by_source:
            articles_by_source[source] = []
        articles_by_source[source].append(article)
    
    # Create summary for each source
    summaries = []
    for source, source_articles in articles_by_source.items():
        titles = [a['title'] for a in source_articles]
        summary = f"{source}: {'; '.join(titles)}"
        summaries.append(summary)
    
    # Combine all summaries
    full_summary = "\n\n".join(summaries)
    
    # Add market impact analysis
    impact_keywords = {
        'price': ['price', 'cost', 'value', 'dollar', 'usd'],
        'supply': ['supply', 'production', 'output', 'inventory'],
        'demand': ['demand', 'consumption', 'usage'],
        'geopolitical': ['opec', 'russia', 'saudi', 'iran', 'conflict', 'sanction']
    }
    
    impact_analysis = []
    for category, keywords in impact_keywords.items():
        relevant_articles = [
            article for article in articles
            if any(kw in article['title'].lower() for kw in keywords)
        ]
        if relevant_articles:
            impact_analysis.append(f"{category.title()}: {len(relevant_articles)} articles")
    
    if impact_analysis:
        full_summary += "\n\nMarket Impact Analysis:\n" + "\n".join(impact_analysis)
    
    return full_summary

def main():
    st.title("Oil News Monitor")
    
    # Sidebar
    st.sidebar.title("Settings")
    
    # Keyword filter in sidebar
    st.sidebar.subheader("Keyword Filter")
    keywords_input = st.sidebar.text_input(
        "Enter keywords (comma-separated):",
        "oil, OPEC, crude, price"
    )
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    # Debug section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Debug")
    if st.sidebar.button("Test News Fetch", key="test_news_fetch"):
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
                # Filter articles by keywords
                filtered_articles = filter_articles_by_keywords(articles, keywords)
                
                # Debug expander
                with st.expander("Debug: Raw Articles", expanded=False):
                    st.write(f"Total articles fetched: {len(articles)}")
                    st.write(f"Articles matching keywords: {len(filtered_articles)}")
                    for article in articles:
                        st.write(f"- {article['title']} ({article['source']})")
                
                # Process filtered articles
                if not filtered_articles:
                    st.info(f"No articles found matching the keywords: {', '.join(keywords)}")
                else:
                    for i, article in enumerate(filtered_articles):
                        with st.container():
                            st.markdown(f"### {article['title']}")
                            st.markdown(f"Source: {article['source']}")
                            st.markdown(f"[Read more]({article['url']})")
                            
                            # Analyze sentiment
                            sentiment = analyze_sentiment(article['title'])
                            sentiment_color = 'green' if sentiment > 0.6 else 'red' if sentiment < 0.4 else 'gray'
                            st.markdown(f"Sentiment: :{sentiment_color}[{sentiment:.2f}]")
                            
                            st.markdown("---")

                    # --- SUMMARY SECTION ---
                    st.markdown("### 📝 Summary: Impact on USD and Oil Market")
                    summary = summarize_articles(filtered_articles)
                    st.info(summary)
                    # --- END SUMMARY SECTION ---
        except Exception as e:
            st.error(f"Error processing news: {str(e)}")
            logger.error(f"Error in main news processing: {str(e)}")

if __name__ == "__main__":
    main()
