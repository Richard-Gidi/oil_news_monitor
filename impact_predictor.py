from textblob import TextBlob

def estimate_impact(text):
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.2:
        return f"📈 Possible increase in oil price (Sentiment: {sentiment:.2f})"
    elif sentiment < -0.2:
        return f"📉 Possible drop in oil price (Sentiment: {sentiment:.2f})"
    else:
        return f"⚖️ Minimal impact expected (Sentiment: {sentiment:.2f})"
