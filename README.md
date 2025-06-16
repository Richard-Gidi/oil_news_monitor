# Oil News Monitor

A Streamlit-based application that monitors oil-related news from multiple sources, clusters similar articles, summarizes them, and gauges their potential impact on oil prices.

## Features

- Fetches news from oilprice.com (expandable to other sources like Bloomberg, investment.com, etc.)
- Clusters similar news articles using sentence embeddings
- Summarizes clustered news using a transformer-based summarization model
- Gauges the potential impact of news on oil prices using a simple rule-based approach
- Displays results in a user-friendly Streamlit dashboard

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd oil-news-monitor
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Usage

- Open your browser and navigate to the URL provided by Streamlit (usually http://localhost:8501)
- The app will fetch news, cluster similar articles, summarize them, and display the impact gauge

## Customization

- Modify `fetch_news()` in `app.py` to add more news sources
- Adjust clustering parameters in `cluster_news()` for better results
- Enhance the impact gauge logic in `gauge_impact()` for more accurate predictions

## Dependencies

- streamlit
- requests
- beautifulsoup4
- pandas
- sentence-transformers
- scikit-learn
- numpy
- transformers
- torch 