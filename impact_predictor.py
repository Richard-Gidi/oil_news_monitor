from textblob import TextBlob

def estimate_impact(text):
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.2:
        return "Possible increase in oil price 📈"
    elif sentiment < -0.2:
        return "Possible drop in oil price 📉"
    else:
        return "Minimal impact expected ⚖️"
