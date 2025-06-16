# ----- 2. Text Cleaning & Keyword Extraction -----
def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def find_common_keywords(all_articles):
    word_counts = Counter()
    for source in all_articles.values():
        for headline in source:
            words = clean_text(headline).split()
            word_counts.update(words)
    common = [word for word, count in word_counts.items() if count > 2 and len(word) > 3]
    return common[:5]

# ----- 3. Optional: Semantic Similarity -----
def find_similar_topics(all_articles):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    headlines = [item for source in all_articles.values() for item in source]
    embeddings = model.encode(headlines, convert_to_tensor=True)
    scores = util.pytorch_cos_sim(embeddings, embeddings)
    
    pairs = [(i, j, float(scores[i][j])) for i in range(len(headlines)) for j in range(i+1, len(headlines))]
    pairs = sorted(pairs, key=lambda x: x[2], reverse=True)
    
    top_pairs = [(headlines[i], headlines[j], score) for i, j, score in pairs[:3] if score > 0.75]
    return top_pairs

# ----- 4. Summarization -----
def generate_summary(news_items):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn",
                          use_auth_token=os.getenv("HF_TOKEN"))
    combined = " ".join(news_items)
    max_len = 1024
    summary_input = combined[:max_len]
    result = summarizer(summary_input)[0]
    return result['summary_text']
