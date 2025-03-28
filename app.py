from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import our custom modules
from modules.news_scraper import NewsScraper
from modules.stock_data import StockData
from modules.sentiment import SentimentAnalyzer
from modules.report_generator import ReportGenerator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get parameters from the request
    stock_symbol = request.form.get('stock_symbol', 'AAPL')  # Default to Apple if not provided
    news_count = int(request.form.get('news_count', 5))
    
    try:
        # Fetch stock data
        stock_client = StockData()
        stock_info = stock_client.get_stock_info(stock_symbol)
        stock_history = stock_client.get_historical_data(stock_symbol)
        
        # Check if we got an error from yahoo finance
        if 'error' in stock_info:
            print(f"Warning: Using potentially limited stock data for {stock_symbol}")
        
        # Scrape news related to the stock
        scraper = NewsScraper()
        # If we had an error with stock data, use mock data to avoid further rate limiting
        use_mock = 'error' in stock_info
        news_articles = scraper.get_financial_news(stock_symbol, limit=news_count, use_mock=use_mock)
        
        # Analyze sentiment using Gemini with RAG
        analyzer = SentimentAnalyzer()
        results = analyzer.analyze_news(news_articles, stock_info, stock_history)
        
        # Return the analyzed results
        return jsonify({
            'stock_info': stock_info,
            'sentiment_results': results,
            'news_count': len(news_articles)
        })
    
    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    data = request.json
    
    # Generate PDF report
    report_gen = ReportGenerator()
    report_path = report_gen.generate_pdf(data)
    
    # Return the PDF file
    return send_file(report_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 