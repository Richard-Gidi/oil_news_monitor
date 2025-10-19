# Oil Market Intelligence — Pro (Lean, Cloud-friendly)

This variant avoids `scikit-learn` and `sentence-transformers` to prevent build failures on Python 3.13 in Streamlit Cloud. It uses **`transformers` + `torch`** for embeddings and summaries and implements **custom cosine-threshold clustering** in NumPy.

## Run locally
```bash
pip install -r requirements_min.txt
streamlit run app_pro_lean.py
```

## Deploy to Streamlit Cloud
1. Ensure a `runtime.txt` at repo root with `3.10.13` (or simply `3.10`).
2. Replace the repo `requirements.txt` with `requirements_min.txt` (or copy contents).
3. Set **Main file path** to `app_pro_lean.py`.