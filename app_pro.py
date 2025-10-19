import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf

# Local utils
from nlp_utils import (
    get_embeddings,
    cluster_headlines,
    summarize_cluster,
    hybrid_economic_impact,
    model_ok,
    analyze_sentiment_llm,
    safe_cache_df,
    theme_tally,
    export_markdown_report,
)
try:
    from news_scraper import get_all_articles  # reuse your existing scraper
except Exception:
    # very defensive: if import fails, create a stub
    def get_all_articles():
        return []

st.set_page_config(page_title="Oil Market Intel — Pro", layout="wide")
st.title("🛢️ Oil Market Intelligence — Pro Edition")

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Controls")
days_back = st.sidebar.slider("Lookback window (days)", 1, 30, 7)
threshold = st.sidebar.slider("Clustering similarity threshold", 50, 95, 75,
                              help="Higher means stricter clustering. Uses cosine similarity in %.")
min_cluster = st.sidebar.slider("Minimum articles per cluster", 2, 6, 2)
use_llm = st.sidebar.toggle("Use transformer models (if available)", value=True)
show_debug = st.sidebar.checkbox("Show debug info", value=False)

# -----------------------------
# Fetch articles
# -----------------------------
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days_back)
articles = get_all_articles() or []

# Normalize schema
def _norm(a):
    return {
        "title": a.get("title", "").strip(),
        "url": a.get("url", ""),
        "source": a.get("source", "Unknown"),
        "date": a.get("date") if isinstance(a.get("date"), datetime) else None,
    }

articles = list(map(_norm, articles))

# Filter by date (keep items without date too)
flt = []
for a in articles:
    if a["date"] is None or (start_date.date() <= a["date"].date() <= end_date.date()):
        flt.append(a)
articles = flt

st.caption(f"Fetched {len(articles)} articles in the last {days_back} day(s).")

if not articles:
    st.warning("No articles found. Try increasing the lookback window.")
    st.stop()

df = pd.DataFrame(articles)
df = df.drop_duplicates(subset=["title"]).reset_index(drop=True)

# -----------------------------
# Embeddings & Clustering
# -----------------------------
with st.spinner("Encoding headlines and discovering themes…"):
    emb = get_embeddings(df["title"].tolist(), enable_models=use_llm)
    clusters = cluster_headlines(
        titles=df["title"].tolist(),
        embeddings=emb,
        threshold=threshold/100.0,
        min_community_size=min_cluster
    )

# Map cluster -> rows
cluster_rows = []
for i, cluster in enumerate(clusters):
    titles = [df.loc[idx, "title"] for idx in cluster]
    urls = [df.loc[idx, "url"] for idx in cluster]
    sources = [df.loc[idx, "source"] for idx in cluster]
    dates = [df.loc[idx, "date"] for idx in cluster]
    summary = summarize_cluster(titles, enable_models=use_llm)
    # economic & sentiment hybrid
    mech, impact, intensity, sentiment = hybrid_economic_impact(titles, enable_models=use_llm)
    cluster_rows.append({
        "Cluster #": i+1,
        "Articles": len(cluster),
        "Summary": summary,
        "Mechanism": mech,
        "Impact": impact,
        "Intensity": intensity,
        "Sentiment": sentiment,
        "Titles": titles,
        "URLs": urls,
        "Sources": sources,
        "Dates": dates
    })

cluster_df = pd.DataFrame(cluster_rows)

# -----------------------------
# Theming / KPI Cards
# -----------------------------
theme_counts = theme_tally(df["title"].tolist())
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Articles", f"{len(df)}")
kpi2.metric("Themes • Geopolitical", f"{theme_counts.get('geopolitical',0)}")
kpi3.metric("Themes • Supply", f"{theme_counts.get('supply',0)}")
kpi4.metric("Themes • Demand", f"{theme_counts.get('demand',0)}")

# -----------------------------
# Sentiment Gauge (from cluster sentiments)
# -----------------------------
bull = (cluster_df["Impact"] == "Bullish").sum()
bear = (cluster_df["Impact"] == "Bearish").sum()
mix = (cluster_df["Impact"] == "Mixed").sum()
neu = (cluster_df["Impact"] == "Neutral").sum()
total = max(1, (bull + bear + mix + neu))
bull_pct = round(100 * bull / total, 2)
bear_pct = round(100 * bear / total, 2)

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=bull_pct,
        title={"text": "Bullish Share (%)"},
        gauge={"axis": {"range":[0,100]},
               "bar":{"thickness":0.25},
               "steps":[
                   {"range":[0,25],"color":"#ffcccc"},
                   {"range":[25,50],"color":"#ffe0cc"},
                   {"range":[50,75],"color":"#d9f2d9"},
                   {"range":[75,100],"color":"#c2f0c2"},
               ]}
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    theme_bar = px.bar(
        x=list(theme_counts.keys()), y=list(theme_counts.values()),
        labels={"x":"Theme","y":"Count"},
        title="Theme Frequency"
    )
    st.plotly_chart(theme_bar, use_container_width=True)

# -----------------------------
# Oil Prices (WTI/Brent)
# -----------------------------
with st.expander("Oil Prices • WTI vs Brent (last 30 days)"):
    try:
        wti = yf.download("CL=F", period="1mo", interval="1d", progress=False)["Close"]
        brent = yf.download("BZ=F", period="1mo", interval="1d", progress=False)["Close"]
        price_df = pd.DataFrame({"WTI": wti, "Brent": brent})
        line = go.Figure()
        line.add_trace(go.Scatter(x=price_df.index, y=price_df["WTI"], name="WTI"))
        line.add_trace(go.Scatter(x=price_df.index, y=price_df["Brent"], name="Brent"))
        line.update_layout(hovermode="x unified", yaxis_title="USD")
        st.plotly_chart(line, use_container_width=True)
    except Exception as e:
        st.error(f"Price fetch failed: {e}")

# -----------------------------
# Clustered Intelligence Feed
# -----------------------------
st.subheader("🧭 Thematic Intelligence Feed")
for _, row in cluster_df.iterrows():
    with st.container(border=True):
        st.markdown(f"### Cluster {row['Cluster #']} • {row['Articles']} article(s)")
        st.markdown(f"**Summary**: {row['Summary']}")
        st.markdown(f"**Mechanism**: {row['Mechanism']}")
        st.markdown(f"**Market Impact**: {row['Impact']} — {row['Intensity']}")
        st.markdown(f"**Sentiment (LLM)**: {row['Sentiment']}")
        with st.expander("View articles"):
            for t,u,s,d in zip(row["Titles"], row["URLs"], row["Sources"], row["Dates"]):
                date_txt = d.strftime("%Y-%m-%d %H:%M") if d else "n/a"
                st.markdown(f"- [{t}]({u}) · _{s}_ · {date_txt}")

# -----------------------------
# Export / Download
# -----------------------------
st.subheader("⬇️ Export")
default_name = f"market_digest_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.md"
fname = st.text_input("Report filename", value=default_name)
if st.button("Generate Markdown Report"):
    path = export_markdown_report(df, cluster_df, theme_counts, fname=fname)
    st.success(f"Report saved: {path}")
    st.download_button("Download report", data=open(path, "rb").read(),
                       file_name=fname, mime="text/markdown")

# -----------------------------
# Debug
# -----------------------------
if show_debug:
    st.write("Model available:", model_ok())
    st.write(df.head(10))
    st.write(cluster_df.head(10))