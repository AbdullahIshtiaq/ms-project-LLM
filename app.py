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
    # Get parameters from the request - now we only need news_count
    news_count = int(request.form.get('news_count', 5))
    
    try:
        # Step 1: Scrape general financial news
        scraper = NewsScraper()
        news_articles = scraper.get_financial_news(limit=news_count)
        
        if not news_articles:
            return jsonify({
                'error': 'Could not retrieve any financial news articles'
            }), 500
        
        # Step 2: Extract stock symbols from the news articles using LLM
        articles_with_symbols = scraper.extract_symbols(news_articles)
        
        if not articles_with_symbols:
            # No symbols found - return mock data instead of error
            stock_client = StockData()
            mock_symbols = ['AAPL', 'MSFT', 'GOOGL']
            all_results = []
            
            for symbol in mock_symbols:
                stock_info = stock_client.get_stock_info(symbol)
                stock_history = stock_client.get_historical_data(symbol)
                
                # Use the mock news articles
                mock_articles = [a for a in news_articles if a['title'].startswith(symbol[:1])][:2]
                for article in mock_articles:
                    article['related_symbol'] = symbol
                
                # Create mock sentiment results
                analyzer = SentimentAnalyzer()
                sentiment_results = analyzer.analyze_news(mock_articles, stock_info, stock_history)
                
                all_results.append({
                    'stock_info': stock_info,
                    'sentiment_results': sentiment_results,
                    'news_count': len(mock_articles)
                })
            
            return jsonify({
                'results': all_results,
                'total_articles': len(news_articles),
                'articles_with_symbols': len(mock_articles),
                'unique_symbols': len(mock_symbols),
                'note': 'No stock symbols could be identified in the scraped news articles. Using mock data.'
            })
        
        # Initialize containers for results
        all_results = []
        processed_symbols = set()
        
        # Step 3: For each article with a symbol, fetch stock data and analyze sentiment
        stock_client = StockData()
        analyzer = SentimentAnalyzer()
        
        for article in articles_with_symbols:
            symbol = article['related_symbol']
            
            # Validate symbol
            if not stock_client.is_valid_symbol(symbol):
                print(f"Skipping invalid symbol: {symbol}")
                continue
                
            # Skip if we've already processed this symbol
            if symbol in processed_symbols:
                continue
                
            processed_symbols.add(symbol)
            
            try:
                # Fetch stock data for the identified symbol
                stock_info = stock_client.get_stock_info(symbol)
                
                # Skip if we couldn't get valid stock info
                if not stock_info or 'error' in stock_info:
                    print(f"Skipping {symbol} due to invalid stock info")
                    continue
                    
                stock_history = stock_client.get_historical_data(symbol)
                
                # Find all articles related to this symbol
                related_articles = [a for a in articles_with_symbols if a['related_symbol'] == symbol]
                
                # Analyze sentiment using DeepSeek R1 with RAG
                sentiment_results = analyzer.analyze_news(related_articles, stock_info, stock_history)
                
                # Add to results
                all_results.append({
                    'stock_info': stock_info,
                    'sentiment_results': sentiment_results,
                    'news_count': len(related_articles)
                })
            except Exception as e:
                print(f"Error processing symbol {symbol}: {e}")
                continue
        
        # If no valid results, return error
        if not all_results:
            return jsonify({
                'error': 'Could not get valid stock data for any of the identified symbols'
            }), 500
            
        # Return the combined results
        return jsonify({
            'results': all_results,
            'total_articles': len(news_articles),
            'articles_with_symbols': len(articles_with_symbols),
            'unique_symbols': len(processed_symbols)
        })
    
    except Exception as e:
        import traceback
        print(f"Error during analysis: {e}")
        print(traceback.format_exc())
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