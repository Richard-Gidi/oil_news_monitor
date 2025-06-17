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
    """Analyze sentiment and classify as Neutral, Bullish, or Bearish with intensity"""
    try:
        if not text or not isinstance(text, str):
            return "Neutral", 0
            
        text = text.lower().strip()
        if not text:
            return "Neutral", 0
            
        # Define keywords for each sentiment
        bullish_keywords = {
            'strong': ['surge', 'rally', 'jump', 'soar', 'spike', 'leap', 'rocket'],
            'moderate': ['rise', 'gain', 'increase', 'up', 'growth', 'recovery', 'higher'],
            'weak': ['slight', 'modest', 'gradual', 'steady', 'stable']
        }
        
        bearish_keywords = {
            'strong': ['plunge', 'crash', 'collapse', 'tumble', 'plummet', 'dive', 'freefall'],
            'moderate': ['fall', 'drop', 'decline', 'down', 'lower', 'weaker', 'decrease'],
            'weak': ['slight', 'modest', 'gradual', 'steady', 'stable']
        }
        
        # Count keyword matches for each intensity level
        bullish_counts = {level: sum(1 for word in words if word in text) 
                         for level, words in bullish_keywords.items()}
        bearish_counts = {level: sum(1 for word in words if word in text) 
                         for level, words in bearish_keywords.items()}
        
        # Calculate total scores
        bullish_score = (bullish_counts['strong'] * 3 + 
                        bullish_counts['moderate'] * 2 + 
                        bullish_counts['weak'])
        bearish_score = (bearish_counts['strong'] * 3 + 
                        bearish_counts['moderate'] * 2 + 
                        bearish_counts['weak'])
        
        # Determine sentiment and intensity
        if bullish_score > bearish_score:
            if bullish_score >= 3:
                return "Bullish", "Strong"
            elif bullish_score >= 2:
                return "Bullish", "Moderate"
            else:
                return "Bullish", "Weak"
        elif bearish_score > bullish_score:
            if bearish_score >= 3:
                return "Bearish", "Strong"
            elif bearish_score >= 2:
                return "Bearish", "Moderate"
            else:
                return "Bearish", "Weak"
        else:
            return "Neutral", "Neutral"

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return "Neutral", 0

def get_sentiment_color(sentiment, intensity):
    """Get color based on sentiment and intensity"""
    if sentiment == "Bullish":
        if intensity == "Strong":
            return "green"
        elif intensity == "Moderate":
            return "lightgreen"
        else:
            return "lime"
    elif sentiment == "Bearish":
        if intensity == "Strong":
            return "red"
        elif intensity == "Moderate":
            return "pink"
        else:
            return "lightcoral"
    else:
        return "gray"

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

def analyze_economic_impact(text):
    """Analyze the economic impact and transmission mechanism of news"""
    try:
        if not text or not isinstance(text, str):
            return "No clear economic impact", "Neutral", "Neutral"
            
        text = text.lower().strip()
        if not text:
            return "No clear economic impact", "Neutral", "Neutral"

        # Define economic impact categories and their keywords
        impact_categories = {
            'supply_shock': {
                'keywords': ['production cut', 'output reduction', 'supply disruption', 'pipeline attack', 
                           'refinery fire', 'facility damage', 'production halt', 'export ban', 'sanctions'],
                'impact': 'Bearish',
                'mechanism': 'Direct supply reduction leading to higher prices'
            },
            'demand_shock': {
                'keywords': ['economic slowdown', 'recession', 'demand drop', 'consumption fall', 
                           'industrial slowdown', 'manufacturing decline', 'economic crisis'],
                'impact': 'Bearish',
                'mechanism': 'Reduced demand leading to lower prices'
            },
            'geopolitical_risk': {
                'keywords': ['war', 'conflict', 'tension', 'attack', 'military', 'sanctions', 
                           'diplomatic', 'protest', 'unrest', 'strike'],
                'impact': 'Bullish',
                'mechanism': 'Supply disruption risk leading to price volatility'
            },
            'inventory_change': {
                'keywords': ['inventory', 'stockpile', 'storage', 'reserve', 'drawdown', 'build'],
                'impact': 'Mixed',
                'mechanism': 'Supply-demand balance indicator'
            },
            'monetary_policy': {
                'keywords': ['interest rate', 'fed', 'central bank', 'inflation', 'monetary policy', 
                           'quantitative easing', 'tapering'],
                'impact': 'Mixed',
                'mechanism': 'Currency and economic growth effects'
            },
            'infrastructure': {
                'keywords': ['pipeline', 'refinery', 'terminal', 'storage', 'capacity', 'expansion', 
                           'maintenance', 'upgrade'],
                'impact': 'Mixed',
                'mechanism': 'Supply chain and logistics impact'
            }
        }

        # Analyze text for each category
        category_matches = {}
        for category, data in impact_categories.items():
            matches = [keyword for keyword in data['keywords'] if keyword in text]
            if matches:
                category_matches[category] = {
                    'matches': matches,
                    'impact': data['impact'],
                    'mechanism': data['mechanism']
                }

        if not category_matches:
            return "No clear economic impact", "Neutral", "Neutral"

        # Determine primary impact
        primary_category = max(category_matches.items(), key=lambda x: len(x[1]['matches']))
        impact = primary_category[1]['impact']
        mechanism = primary_category[1]['mechanism']

        # Calculate intensity based on number of matching keywords
        intensity = "Strong" if len(primary_category[1]['matches']) > 2 else "Moderate" if len(primary_category[1]['matches']) > 1 else "Weak"

        return mechanism, impact, intensity

    except Exception as e:
        logger.error(f"Error in economic impact analysis: {str(e)}")
        return "Error in analysis", "Neutral", "Neutral"

def main():
    st.title("Oil News Monitor")
    st.sidebar.title("Settings")
    st.sidebar.subheader("Keyword Filter")
    keywords_input = st.sidebar.text_input(
        "Enter keywords (comma-separated):",
        "oil, OPEC, crude, price"
    )
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
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

    # Main content with three columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader("Market Overview")
        st.markdown("""
        This section provides a quick overview of the oil market:
        - Latest price trends
        - Market sentiment
        - Key developments
        """)
    
    with col2:
        st.subheader("Latest News")
        try:
            articles = fetch_all_articles()
            if not articles:
                st.warning("No articles found. Please check the debug section for more information.")
            else:
                filtered_articles = filter_articles_by_keywords(articles, keywords)
                with st.expander("Debug: Raw Articles", expanded=False):
                    st.write(f"Total articles fetched: {len(articles)}")
                    st.write(f"Articles matching keywords: {len(filtered_articles)}")
                    for article in articles:
                        st.write(f"- {article['title']} ({article['source']})")
                # --- SUMMARY SECTION ---
                st.markdown("### 📝 Summary: Impact on USD and Oil Market")
                summary = summarize_articles(filtered_articles)
                st.info(summary)
                # --- END SUMMARY SECTION ---
                if not filtered_articles:
                    st.info(f"No articles found matching the keywords: {', '.join(keywords)}")
                else:
                    for i, article in enumerate(filtered_articles):
                        with st.container():
                            st.markdown(f"### {article['title']}")
                            st.markdown(f"Source: {article['source']}")
                            st.markdown(f"[Read more]({article['url']})")
                            
                            # Economic Impact Analysis
                            mechanism, impact, intensity = analyze_economic_impact(article['title'])
                            sentiment_color = get_sentiment_color(impact, intensity)
                            
                            st.markdown("#### Economic Analysis")
                            st.markdown(f"**Transmission Mechanism:** {mechanism}")
                            st.markdown(f"**Market Impact:** :{sentiment_color}[{impact} - {intensity}]")
                            
                            st.markdown("---")
        except Exception as e:
            st.error(f"Error processing news: {str(e)}")
            logger.error(f"Error in main news processing: {str(e)}")
    
    with col3:
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

if __name__ == "__main__":
    main()
