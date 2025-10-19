# Oil Market Intelligence — Pro Edition

A production-grade Streamlit dashboard that scrapes multi-source oil market news, clusters headlines by theme using sentence embeddings, summarizes each cluster with a transformer model, and infers likely price impact and mechanisms (geopolitical risk, supply, demand, monetary).

## Highlights
- **Multi-source ingestion** (reuses your `news_scraper.get_all_articles()`)
- **Embeddings + community detection** (theme clustering)
- **LLM-powered summaries** with fallback to heuristics
- **Hybrid impact engine** (keyword economics + transformer sentiment)
- **KPI cards, sentiment gauge, theme bar** and **exportable Markdown report**

## Run
```bash
pip install -r requirements_pro.txt
streamlit run app_pro.py
```

> If transformer downloads are blocked or you lack a GPU, the app will automatically fall back to lightweight heuristics.


## Files
- `app_pro.py` – Streamlit UI
- `nlp_utils.py` – embeddings, clustering, summaries, impact analysis, export
- `requirements_pro.txt` – pinned deps for Pro features

## Notes
- Optional: set `HF_TOKEN` in your environment for faster/authorized model pulls.
- This app reuses your existing `news_scraper.py` for consistency with your current sources.