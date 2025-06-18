import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from news_scraper import get_all_articles
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
    elif sentiment == "Mixed":
        return "orange"
    else:  # Neutral
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
    """Generate a narrative summary of the articles' impact on the market"""
    if not articles:
        return "No articles available for analysis."

    # Count impacts by category
    impact_counts = {
        'Bullish': 0,
        'Bearish': 0,
        'Mixed': 0,
        'Neutral': 0
    }
    
    # Track key themes
    themes = {
        'supply': [],
        'demand': [],
        'geopolitical': [],
        'economic': []
    }

    for article in articles:
        mechanism, impact, intensity = analyze_economic_impact(article['title'])
        impact_counts[impact] += 1
        
        # Categorize by theme
        if 'supply' in mechanism.lower():
            themes['supply'].append(article['title'])
        elif 'demand' in mechanism.lower():
            themes['demand'].append(article['title'])
        elif 'geopolitical' in mechanism.lower() or 'risk' in mechanism.lower():
            themes['geopolitical'].append(article['title'])
        else:
            themes['economic'].append(article['title'])

    # Determine overall market sentiment
    total_articles = len(articles)
    if total_articles == 0:
        return "No articles available for analysis."

    bullish_ratio = impact_counts['Bullish'] / total_articles
    bearish_ratio = impact_counts['Bearish'] / total_articles
    mixed_ratio = impact_counts['Mixed'] / total_articles

    # Generate narrative summary
    summary = "### Market Sentiment Analysis\n\n"
    
    if mixed_ratio > 0.4:
        summary += "🔄 **Mixed Market Sentiment**: The market shows conflicting signals with "
    elif bullish_ratio > 0.6:
        summary += "📈 **Strong Bullish Sentiment**: The market is showing strong upward pressure with "
    elif bullish_ratio > 0.4:
        summary += "📈 **Moderately Bullish Sentiment**: The market is showing moderate upward pressure with "
    elif bearish_ratio > 0.6:
        summary += "📉 **Strong Bearish Sentiment**: The market is showing strong downward pressure with "
    elif bearish_ratio > 0.4:
        summary += "📉 **Moderately Bearish Sentiment**: The market is showing moderate downward pressure with "
    else:
        summary += "↔️ **Neutral Market Sentiment**: The market is showing mixed signals with "

    summary += f"{impact_counts['Bullish']} bullish, {impact_counts['Bearish']} bearish, {impact_counts['Mixed']} mixed, and {impact_counts['Neutral']} neutral articles.\n\n"

    # Add key themes
    summary += "### Key Market Themes\n\n"
    
    if themes['geopolitical']:
        summary += "🌍 **Geopolitical Factors**: " + " ".join(themes['geopolitical'][:2]) + "\n\n"
    if themes['supply']:
        summary += "🛢️ **Supply Factors**: " + " ".join(themes['supply'][:2]) + "\n\n"
    if themes['demand']:
        summary += "📊 **Demand Factors**: " + " ".join(themes['demand'][:2]) + "\n\n"
    if themes['economic']:
        summary += "💰 **Economic Factors**: " + " ".join(themes['economic'][:2]) + "\n\n"

    return summary

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

        # For Mixed impact, always set intensity to Moderate
        if impact == "Mixed":
            intensity = "Moderate"

        return mechanism, impact, intensity

    except Exception as e:
        logger.error(f"Error in economic impact analysis: {str(e)}")
        return "Error in analysis", "Neutral", "Neutral"

def format_date(date):
    """Format date for display"""
    if date is None:
        return "Date not available"
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return date
    return date.strftime("%B %d, %Y %H:%M")

def main():
    st.title("Oil Market News Monitor")
    
    # Sidebar
    st.sidebar.header("Settings")
    
    # Date range selector
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(start_date, end_date),
        max_value=end_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        if start_date > end_date:
            st.sidebar.error("Start date must be before end date")
            return
    else:
        st.sidebar.error("Please select both start and end dates")
        return
    
    # Debug section
    with st.sidebar.expander("Debug Information"):
        if st.button("Test News Fetch", key="test_news_fetch"):
            try:
                articles = get_all_articles()
                st.write(f"Total articles fetched: {len(articles)}")
                if articles:
                    st.write("Sample article:")
                    st.write(articles[0])
            except Exception as e:
                st.error(f"Error fetching articles: {str(e)}")
    
    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader("Market Overview")
        st.write("""
        This section provides a comprehensive view of the oil market, including:
        - Latest price trends
        - Market sentiment
        - Key developments
        """)
    
    with col2:
        st.subheader("Latest News")
        try:
            articles = get_all_articles()
            if not articles:
                st.warning("No articles found. Please check the debug section for more information.")
            else:
                # Filter articles by date
                filtered_articles = []
                for article in articles:
                    try:
                        article_date = article.get('date')
                        if article_date is None:
                            filtered_articles.append(article)
                            continue
                            
                        if isinstance(article_date, str):
                            try:
                                article_date = datetime.strptime(article_date, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                filtered_articles.append(article)
                                continue
                                
                        if start_date <= article_date.date() <= end_date:
                            filtered_articles.append(article)
                    except Exception as e:
                        logger.error(f"Error processing article date: {str(e)}")
                        filtered_articles.append(article)
                
                # --- SUMMARY SECTION ---
                st.markdown("### 📝 Market Analysis Summary")
                summary = summarize_articles(filtered_articles)
                st.info(summary)
                # --- END SUMMARY SECTION ---
                
                # Display articles with source and date
                for article in filtered_articles:
                    with st.container():
                        st.markdown(f"### [{article['title']}]({article['url']})")
                        
                        # Source and date
                        source = article.get('source', 'Unknown Source')
                        date = format_date(article.get('date'))
                        st.markdown(f"**Source:** {source} | **Date:** {date}")
                        
                        # Economic Impact Analysis
                        mechanism, impact, intensity = analyze_economic_impact(article['title'])
                        sentiment_color = get_sentiment_color(impact, intensity)
                        
                        st.markdown("#### Economic Analysis")
                        st.markdown(f"**Transmission Mechanism:** {mechanism}")
                        st.markdown(f"**Market Impact:** :{sentiment_color}[{impact} - {intensity}]")
                        
                        st.markdown("---")
                
                # Debug information
                with st.expander("Debug Information"):
                    st.write(f"Total articles fetched: {len(articles)}")
                    st.write(f"Articles within date range: {len(filtered_articles)}")
                    st.write("Sample article data:")
                    if articles:
                        st.write(articles[0])
        
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
