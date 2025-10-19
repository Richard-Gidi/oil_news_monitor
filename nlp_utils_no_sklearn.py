import os, math, re
from typing import List
import numpy as np
from datetime import datetime

_HAS_TX = True
try:
    from transformers import AutoTokenizer, AutoModel, pipeline
except Exception:
    _HAS_TX = False
    AutoTokenizer = AutoModel = pipeline = None

_tok = None
_mod = None

def _load_embedder():
    global _tok, _mod
    if _tok is None or _mod is None:
        model_name = "intfloat/e5-small-v2"
        _tok = AutoTokenizer.from_pretrained(model_name)
        _mod = AutoModel.from_pretrained(model_name)
    return _tok, _mod

def _mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    return (last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)

def embed_titles(titles: List[str], enable_models=True):
    if not enable_models or not _HAS_TX:
        embs = []
        for t in titles:
            h = abs(hash(t)) % (10**6)
            vec = np.array([ (h % 97)/97.0, (h % 193)/193.0, (h % 389)/389.0, (h % 997)/997.0 ], dtype=float)
            embs.append(vec / (np.linalg.norm(vec) + 1e-9))
        return np.vstack(embs)
    tok, mod = _load_embedder()
    import torch
    mod.eval()
    with torch.no_grad():
        toks = tok([f"passage: {t}" for t in titles], padding=True, truncation=True, return_tensors="pt")
        out = mod(**toks)
        pooled = _mean_pool(out.last_hidden_state, toks["attention_mask"])
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled.cpu().numpy()

def cluster_by_cosine_threshold(embeddings: np.ndarray, threshold: float=0.78, min_size: int=2):
    n = embeddings.shape[0]
    sims = embeddings @ embeddings.T
    visited = set()
    clusters = []
    for i in range(n):
        if i in visited: continue
        group = [i]; visited.add(i)
        added = True
        while added:
            added = False
            for j in range(n):
                if j in visited: continue
                if any(sims[j,k] >= threshold for k in group):
                    group.append(j); visited.add(j); added=True
        if len(group) >= min_size:
            clusters.append(sorted(group))
    if not clusters:
        clusters = [[i] for i in range(n)]
    return clusters

def summarize_text(text: str, enable_models=True) -> str:
    if enable_models and _HAS_TX:
        try:
            summ = pipeline("summarization", model="facebook/bart-large-cnn", truncation=True)
            out = summ(text, max_length=110, min_length=35, do_sample=False)[0]["summary_text"]
            return out
        except Exception:
            pass
    return (text[:220] + "…") if len(text) > 220 else text

BULL = set("surge rally jump soar spike upward tighten deficit outage sanction strike".split())
BEAR = set("plunge drop decline fall bearish glut oversupply slowdown recession ceasefire".split())

def _keyword_mechanism_and_score(titles: List[str]):
    bull = bear = 0
    mech_counts = {"Geopolitical risk / premium":0, "Physical supply change":0,
                   "Macro-demand channel":0, "Inventory signal (build/draw)":0}
    for t in titles:
        T = t.lower()
        bull += sum(w in T for w in BULL)
        bear += sum(w in T for w in BEAR)
        if any(k in T for k in ["war","tension","attack","ceasefire","sanction","missile","strike"]):
            mech_counts["Geopolitical risk / premium"] += 1
        if any(k in T for k in ["output","production","supply","pipeline","refinery","outage"]):
            mech_counts["Physical supply change"] += 1
        if any(k in T for k in ["demand","slowdown","recession","pmi","china","consumption"]):
            mech_counts["Macro-demand channel"] += 1
        if any(k in T for k in ["inventory","stock","build","draw","spr","storage"]):
            mech_counts["Inventory signal (build/draw)"] += 1
    if bull>bear:
        impact = "Bullish"; intensity = "Strong" if bull-bear>3 else "Moderate"
    elif bear>bull:
        impact = "Bearish"; intensity = "Strong" if bear-bull>3 else "Moderate"
    else:
        impact = "Mixed"; intensity = "Moderate"
    mechanism = max(mech_counts, key=mech_counts.get) if any(mech_counts.values()) else "No clear mechanism"
    return mechanism, impact, intensity

def _llm_sentiment(titles: List[str], enable_models=True):
    if enable_models and _HAS_TX:
        try:
            clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
            outs = clf([t[:256] for t in titles])
            score = 0.0
            for o in outs:
                lbl = o["label"].lower(); val = o.get("score",0)
                if "positive" in lbl: score += val
                elif "negative" in lbl: score -= val
            avg = score / max(1,len(outs))
            if avg > 0.15: return "Positive"
            if avg < -0.15: return "Negative"
            return "Neutral"
        except Exception:
            pass
    return "Neutral"

def hybrid_impact_from_keywords_and_llm(titles: List[str], enable_models=True):
    mech, impact, intensity = _keyword_mechanism_and_score(titles)
    sent = _llm_sentiment(titles, enable_models=enable_models)
    return mech, impact, intensity, sent

def theme_tally(titles: List[str]):
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

def export_markdown_report(df_articles, df_clusters, theme_counts, fname="market_digest.md"):
    lines = []
    lines.append("# Oil Market Intelligence — Pro (Lean)\n")
    lines.append(f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")
    bull = (df_clusters['Impact']=="Bullish").sum()
    bear = (df_clusters['Impact']=="Bearish").sum()
    mix  = (df_clusters['Impact']=="Mixed").sum()
    neu  = (df_clusters['Impact']=="Neutral").sum()
    total = max(1,(bull+bear+mix+neu))
    bull_pct = round(100*bull/total,2)
    lines.append(f"**Headline Mood:** Bullish {bull_pct}% · Bearish {round(100*bear/total,2)}% · Mixed {mix} · Neutral {neu}\n")
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