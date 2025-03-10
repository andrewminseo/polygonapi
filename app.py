import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    interval = request.args.get('interval', '1mo')
    
    # Convert interval from frontend format to yfinance format
    interval_map = {
        '1D': '1d',
        '1W': '1wk',
        '1M': '1mo',
        '3M': '3mo',
        '1Y': '1y',
        'YTD': 'ytd'
    }
    
    yf_interval = interval_map.get(interval, '1mo')
    period_map = {
        '1D': '1d',
        '1W': '5d',
        '1M': '1mo',
        '3M': '3mo',
        '1Y': '1y',
        'YTD': 'ytd'
    }
    
    period = period_map.get(interval, '1mo')
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get historical data
        hist = ticker.history(period=period, interval=yf_interval)
        
        # Format data for the frontend chart
        data = []
        for index, row in hist.iterrows():
            data.append({
                'date': index.strftime('%Y-%m-%d %H:%M:%S'),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/details/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get additional data
        try:
            hist = ticker.history(period="1d")
            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else info.get('previousClose', 0)
        except:
            latest = None
            prev_close = info.get('previousClose', 0)
        
        market_cap = info.get('marketCap', 0)
        formatted_market_cap = f"${market_cap/1000000000:.2f}B" if market_cap >= 1000000000 else f"${market_cap/1000000:.2f}M"
        
        pe_ratio = info.get('trailingPE', 0)
        
        response = {
            'status': 'success',
            'data': {
                'symbol': symbol,
                'name': info.get('shortName', ''),
                'price': info.get('currentPrice', 0),
                'change': info.get('currentPrice', 0) - prev_close,
                'changePercent': ((info.get('currentPrice', 0) - prev_close) / prev_close * 100) if prev_close else 0,
                'open': info.get('open', 0),
                'high': info.get('dayHigh', 0),
                'low': info.get('dayLow', 0),
                'prevClose': prev_close,
                'volume': info.get('volume', 0),
                'avgVolume': info.get('averageVolume', 0),
                'marketCap': formatted_market_cap,
                'peRatio': pe_ratio
            }
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/technical/<symbol>', methods=['GET'])
def get_technical_analysis(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="60d")
        
        # Calculate RSI (14)
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Calculate SMAs
        sma20 = hist['Close'].rolling(window=20).mean()
        sma50 = hist['Close'].rolling(window=50).mean()
        
        # Determine the technical signal
        current_price = hist['Close'].iloc[-1]
        rsi_value = rsi.iloc[-1]
        macd_value = macd.iloc[-1]
        macd_signal = signal.iloc[-1]
        sma20_value = sma20.iloc[-1]
        sma50_value = sma50.iloc[-1]
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI signals
        if rsi_value < 30:
            buy_signals += 1
        elif rsi_value > 70:
            sell_signals += 1
        
        # MACD signals
        if macd_value > macd_signal:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # SMA signals
        if current_price > sma20_value and current_price > sma50_value:
            buy_signals += 1
        elif current_price < sma20_value and current_price < sma50_value:
            sell_signals += 1
        
        if buy_signals > sell_signals:
            signal_value = "BUY"
        elif sell_signals > buy_signals:
            signal_value = "SELL"
        else:
            signal_value = "HOLD"
        
        return jsonify({
            'status': 'success',
            'data': {
                'rsi': round(rsi_value, 2),
                'macd': round(macd_value, 2),
                'sma20': round(sma20_value, 2),
                'sma50': round(sma50_value, 2),
                'signal': signal_value
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/news/<symbol>', methods=['GET'])
def get_stock_news(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # Yahoo Finance doesn't provide news through yfinance directly
        # So we'll create some placeholder news
        # In a real app, you might want to use a news API
        
        # Mock news data
        news_topics = [
            "Quarterly Earnings", "Analyst Ratings", "Product Launch", 
            "Market Outlook", "Industry Trends", "Dividend Announcement",
            "Executive Changes", "Regulatory Updates", "Strategic Partnership"
        ]
        
        # Get company name for more realistic news
        company_name = ticker.info.get('shortName', symbol)
        
        news = []
        for _ in range(5):
            days_ago = random.randint(0, 6)
            news_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
            topic = random.choice(news_topics)
            
            news.append({
                'title': f"{company_name} {topic}: What Investors Need to Know",
                'published_utc': news_date,
                'article_url': "#",
                'description': f"Latest updates on {company_name}'s {topic.lower()} and how it might affect investors in the coming quarters.",
                'source': "Yahoo Finance"
            })
        
        # Sort by date
        news.sort(key=lambda x: x['published_utc'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': news
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/search/<query>', methods=['GET'])
def search_stocks(query):
    try:
        # Use yfinance's search functionality
        tickers = yf.Tickers(query)
        results = []
        
        # This is a simple workaround as yfinance doesn't have a direct search API
        # In a real app, you might want to use a more comprehensive solution
        for ticker_symbol in query.split():
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                if 'shortName' in info:
                    results.append({
                        'symbol': ticker_symbol,
                        'name': info['shortName'],
                        'type': 'Common Stock'
                    })
            except:
                pass
        
        # Add some common stocks if the search is empty
        if not results and len(query) >= 2:
            common_stocks = {
                'AAPL': 'Apple Inc.',
                'MSFT': 'Microsoft Corporation',
                'AMZN': 'Amazon.com, Inc.',
                'GOOGL': 'Alphabet Inc.',
                'META': 'Meta Platforms, Inc.',
                'TSLA': 'Tesla, Inc.',
                'NVDA': 'NVIDIA Corporation',
                'JPM': 'JPMorgan Chase & Co.',
                'V': 'Visa Inc.',
                'JNJ': 'Johnson & Johnson'
            }
            
            for symbol, name in common_stocks.items():
                if query.upper() in symbol or query.lower() in name.lower():
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'Common Stock'
                    })
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/sentiment/<symbol>', methods=['GET'])
def get_sentiment_data(symbol):
    try:
        # Generate mock sentiment data
        # In a real app, you might want to use a sentiment analysis API
        sentiment_data = []
        
        # Generate data for the last 7 days
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            # Generate a random sentiment between 0 and 1
            sentiment = random.uniform(0.2, 0.8)
            sentiment_data.append({
                'date': date,
                'sentiment': sentiment
            })
        
        # Sort by date
        sentiment_data.sort(key=lambda x: x['date'])
        
        # Calculate overall sentiment
        avg_sentiment = sum(item['sentiment'] for item in sentiment_data) / len(sentiment_data)
        
        if avg_sentiment > 0.6:
            overall = "BUY"
        elif avg_sentiment < 0.4:
            overall = "SELL"
        else:
            overall = "HOLD"
        
        # Generate insights
        insights = []
        ticker = yf.Ticker(symbol)
        company_name = ticker.info.get('shortName', symbol)
        
        insight_templates = [
            f"{company_name} has shown strong momentum in recent trading sessions.",
            f"Trading volume for {symbol} has been {random.choice(['above', 'below'])} average.",
            f"Recent analyst ratings have leaned {random.choice(['bullish', 'bearish', 'neutral'])} on {company_name}.",
            f"Technical indicators suggest potential {random.choice(['support', 'resistance'])} at current price levels.",
            f"Market sentiment around {company_name} remains {random.choice(['positive', 'mixed', 'cautious'])}."
        ]
        
        for template in random.sample(insight_templates, 3):
            sentiment_type = random.choice(['positive', 'negative', 'neutral'])
            insights.append({
                'text': template,
                'type': sentiment_type
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'sentimentData': sentiment_data,
                'overall': overall,
                'insights': insights,
                'priceTarget': round(ticker.info.get('currentPrice', 0) * random.uniform(0.9, 1.2), 2),
                'priceUpside': round(random.uniform(-10, 20), 2)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
