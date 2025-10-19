import os
import re
import math
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter

# Optional heavy deps guarded behind try/except
_HAS_ST = True
_HAS_TX = True
try:
    from sentence_transformers import SentenceTransformer, util
except Exception:
    _HAS_ST = False
try:
    from transformers import pipeline
except Exception:
    _HAS_TX = False

# -----------------------------
# Tiny utils
# -----------------------------
def model_ok():
    return {"sentence_transformers": _HAS_ST, "transformers": _HAS_TX}

def _fallback_embeddings(texts):
    # Very small deterministic hash embedding (fallback)
    embs = []
    for t in texts:
        h = abs(hash(t)) % (10**6)
        vec = np.array([ (h % 97)/97.0, (h % 193)/193.0, (h % 389)/389.0, (h % 997)/997.0 ], dtype=float)
        embs.append(vec / (np.linalg.norm(vec) + 1e-9))
    return np.vstack(embs)

def get_embeddings(texts, enable_models=True):
    if enable_models and _HAS_ST:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(texts, convert_to_tensor=False, normalize_embeddings=True)
    return _fallback_embeddings(texts)

def cluster_headlines(titles, embeddings, threshold=0.75, min_community_size=2):
    if _HAS_ST:
        em = np.array(embeddings)
        # use community detection from sentence-transformers util
        from sentence_transformers import util as st_util
        clusters = st_util.community_detection(em, threshold=threshold, min_community_size=min_community_size)
        # clusters come as lists of indices
        return clusters if clusters else [[i] for i in range(len(titles))]
    # naive fallback: group by top-2 words
    groups = {}
    for i, t in enumerate(titles):
        toks = re.findall(r"[a-zA-Z]{4,}", t.lower())
        key = " ".join(sorted(toks[:2])) if toks else f"solo-{i}"
        groups.setdefault(key, []).append(i)
    return [v for v in groups.values() if len(v) >= min_community_size] or [[i] for i in range(len(titles))]

def summarize_cluster(titles, enable_models=True):
    text = " ".join(titles)[:1500]
    if enable_models and _HAS_TX:
        try:
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn", truncation=True)
            out = summarizer(text, max_length=110, min_length=35, do_sample=False)[0]["summary_text"]
            return out
        except Exception:
            pass
    # fallback
    return f"{titles[0]}" if titles else "No content"

# -----------------------------
# Economic impact (hybrid)
# -----------------------------
BULLISH_WORDS = set("surge rally jump soar spike upward tighten deficit outage strike sanction".split())
BEARISH_WORDS = set("plunge drop decline fall bearish glut oversupply slowdown recession ceasefire".split())

def _keyword_impact_score(texts):
    bull = bear = 0
    mech = Counter()
    for t in texts:
        T = t.lower()
        bull += sum(w in T for w in BULLISH_WORDS)
        bear += sum(w in T for w in BEARISH_WORDS)
        if any(k in T for k in ["war","attack","missile","tension","sanction","ceasefire","strike"]):
            mech["Geopolitical risk / premium"] += 1
        if any(k in T for k in ["inventory","stock","build","draw","spr","storage"]):
            mech["Inventory signal (build/draw)"] += 1
        if any(k in T for k in ["output","production","supply","pipeline","refinery"]):
            mech["Physical supply change"] += 1
        if any(k in T for k in ["demand","recession","slowdown","pmi","china","interest rate","fed"]):
            mech["Macro-demand channel"] += 1
    if bull>bear:
        impact, intensity = "Bullish", "Strong" if bull-bear>3 else "Moderate"
    elif bear>bull:
        impact, intensity = "Bearish", "Strong" if bear-bull>3 else "Moderate"
    else:
        impact, intensity = "Mixed", "Moderate"
    mechanism = (mech.most_common(1)[0][0] if mech else "No clear mechanism")
    return mechanism, impact, intensity

def analyze_sentiment_llm(texts, enable_models=True):
    if enable_models and _HAS_TX:
        try:
            clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
            joined = [t[:256] for t in texts]
            outs = clf(joined)
            # average score: map labels to +/-
            score = 0.0
            for o in outs:
                lbl = o["label"].lower()
                val = o.get("score", 0)
                if "positive" in lbl:
                    score += val
                elif "negative" in lbl:
                    score -= val
            avg = score / max(1, len(outs))
            if avg > 0.15: return "Positive"
            if avg < -0.15: return "Negative"
            return "Neutral"
        except Exception:
            pass
    # fallback: neutral
    return "Neutral"

def hybrid_economic_impact(titles, enable_models=True):
    mech, impact, intensity = _keyword_impact_score(titles)
    sent = analyze_sentiment_llm(titles, enable_models=enable_models)
    return mech, impact, intensity, sent

# -----------------------------
# Themes
# -----------------------------
def theme_tally(titles):
    counts = {"geopolitical":0,"supply":0,"demand":0,"monetary":0}
    for t in titles:
        T = t.lower()
        if any(k in T for k in ["war","tension","attack","ceasefire","sanction","geopolit"]):
            counts["geopolitical"] += 1
        if any(k in T for k in ["output","production","supply","pipeline","refinery","outage","capacity"]):
            counts["supply"] += 1
        if any(k in T for k in ["demand","slowdown","recession","china","pmi","consumption"]):
            counts["demand"] += 1
        if any(k in T for k in ["fed","rate","central bank","inflation","monetary"]):
            counts["monetary"] += 1
    return counts

# -----------------------------
# Export
# -----------------------------
def export_markdown_report(df_articles, df_clusters, theme_counts, fname="market_digest.md"):
    lines = []
    lines.append(f"# Oil Market Intelligence — Pro\n")
    lines.append(f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")
    bull = (df_clusters['Impact']=="Bullish").sum()
    bear = (df_clusters['Impact']=="Bearish").sum()
    mix = (df_clusters['Impact']=="Mixed").sum()
    neu = (df_clusters['Impact']=="Neutral").sum()
    total = max(1,(bull+bear+mix+neu))
    bull_pct = round(100*bull/total,2)
    bear_pct = round(100*bear/total,2)
    lines.append(f"**Headline Mood:** Bullish {bull_pct}% · Bearish {bear_pct}% · Mixed {mix} · Neutral {neu}\n")
    lines.append("## Theme Snapshot")
    for k,v in theme_counts.items():
        lines.append(f"- **{k.title()}**: {v}")
    lines.append("\n---\n## Thematic Clusters")
    for _, r in df_clusters.iterrows():
        lines.append(f"### Cluster {r['Cluster #']} · {r['Articles']} article(s)")
        lines.append(f"- **Summary:** {r['Summary']}")
        lines.append(f"- **Mechanism:** {r['Mechanism']}")
        lines.append(f"- **Impact:** {r['Impact']} — {r['Intensity']}")
        lines.append(f"- **Sentiment (LLM):** {r['Sentiment']}")
        lines.append(f"- **Articles:**")
        for t,u in zip(r['Titles'], r['URLs']):
            lines.append(f"  - [{t}]({u})")
        lines.append("")
    path = f"/mnt/data/{fname}"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

def safe_cache_df(df, path):
    try:
        df.to_csv(path, index=False)
    except Exception:
        pass