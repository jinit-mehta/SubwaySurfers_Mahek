import sqlite3
import pandas as pd
import numpy as np
import requests
import nltk
import socket
import json
import threading
from nltk.sentiment import SentimentIntensityAnalyzer
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import uvicorn

# Download necessary NLTK data
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

# Initialize FastAPI app
app = FastAPI()

# Configure Gemini AI Key
genai.configure(api_key="AIzaSyDMadTpG56ELKSBYirqU-8yE7nMySEfdIU")

# Agent Classes
class DataAgent:
    def __init__(self, alpha_vantage_key, news_api_key, fred_api_key):
        self.alpha_vantage_key = alpha_vantage_key
        self.news_api_key = news_api_key
        self.fred_api_key = fred_api_key

    def fetch_stock_data(self, symbol):
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.alpha_vantage_key}&outputsize=compact'
        response = requests.get(url).json()
        return response.get("Time Series (Daily)", {})

    def fetch_news_data(self, query):
        url = f'https://newsapi.org/v2/everything?q={query}&apiKey={self.news_api_key}'
        response = requests.get(url).json()
        return response.get("articles", [])

    def fetch_economic_data(self):
        url = f'https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={self.fred_api_key}&file_type=json'
        response = requests.get(url).json()
        return response.get("observations", [])

class AnalysisAgent:
    def __init__(self):
        pass

    def analyze_sentiment(self, news_data):
        return [{"title": news["title"], "sentiment": sia.polarity_scores(news["title"])["compound"]} for news in news_data]

    def detect_trends(self, stock_data):
        df = pd.DataFrame(stock_data).T.astype(float)
        df['SMA_10'] = df['4. close'].rolling(window=10).mean()
        df['SMA_50'] = df['4. close'].rolling(window=50).mean()
        df['trend'] = np.where(df['SMA_10'] > df['SMA_50'], 'Bullish', 'Bearish')
        return df[['4. close', 'SMA_10', 'SMA_50', 'trend']]

class DecisionAgent:
    def __init__(self):
        pass

    def generate_insight(self, stock_trends, sentiment_data, gdp_data):
        last_trend = stock_trends.iloc[-1]['trend']
        avg_sentiment = np.mean([s['sentiment'] for s in sentiment_data])
        latest_gdp = float(gdp_data[-1]['value']) if gdp_data else None
        decision = "Buy" if last_trend == "Bullish" and avg_sentiment > 0 and latest_gdp > 0 else "Sell"
        return {"market_trend": last_trend, "sentiment_score": avg_sentiment, "latest_gdp": latest_gdp, "recommendation": decision}

    def generate_gemini_insights(self, stock_trends, sentiment_data, gdp_data):
        prompt = f"""
        Based on the following market data:
        - Stock Market Trend: {stock_trends.iloc[-1]['trend']}
        - Sentiment Score: {np.mean([s['sentiment'] for s in sentiment_data])}
        - Latest GDP Data: {gdp_data[-1]['value'] if gdp_data else 'Unavailable'}
        Provide an in-depth financial insight and investment strategy.
        """
        response = genai.GenerativeModel("gemini-pro").generate_content(prompt)
        return response.text if response else "No insights available."

# API for Insights
class StockQuery(BaseModel):
    symbol: str
    news_query: str
    alpha_vantage_key: str
    news_api_key: str
    fred_api_key: str
    gemini_api_key: str

@app.post("/insights/")
def get_insights(query: StockQuery):
    data_agent = DataAgent(query.alpha_vantage_key, query.news_api_key, query.fred_api_key)
    analysis_agent = AnalysisAgent()
    decision_agent = DecisionAgent()

    stock_data = data_agent.fetch_stock_data(query.symbol)
    news_data = data_agent.fetch_news_data(query.news_query)
    economic_data = data_agent.fetch_economic_data()

    sentiment_data = analysis_agent.analyze_sentiment(news_data)
    stock_trends = analysis_agent.detect_trends(stock_data)
    insights = decision_agent.generate_insight(stock_trends, sentiment_data, economic_data)
    gemini_insights = decision_agent.generate_gemini_insights(stock_trends, sentiment_data, economic_data)

    return {"basic_insights": insights, "advanced_insights": gemini_insights}

# Socket Server Configuration
HOST = "127.0.0.1"
PORT = 8080

def handle_client(client_socket):
    try:
        data = client_socket.recv(4096).decode("utf-8")
        if not data:
            return
        
        print("[SERVER] Received request:", data)
        
        # Convert JSON string to dictionary
        request_data = json.loads(data)
        
        # Call FastAPI endpoint
        response = requests.post("http://127.0.0.1:8000/insights/", json=request_data)
        
        # Send response back to client
        client_socket.sendall(response.text.encode("utf-8"))
    
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client_socket.close()

def start_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[SOCKET SERVER] Listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[SOCKET SERVER] Connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Start FastAPI & Socket Server
if __name__ == "__main__":
    threading.Thread(target=start_socket_server, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)