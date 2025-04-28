from django.shortcuts import render
from .scraper import scrape_lse_news, scrape_yahoo_finance_news, create_stock_news_async
from django.http import JsonResponse
import traceback
from .article_processor import create_stock_news
from rest_framework.decorators import api_view
from .models import NewsSentiment
from django.core.paginator import Paginator
import json
import asyncio
import concurrent.futures
from asgiref.sync import sync_to_async, async_to_sync
import os

@api_view(['GET'])
def scrape_and_analyze(request):
    """
    Scrape news articles from LSE and Yahoo Finance, analyze them, and return the results.
    """
    try:
        # Create an event loop to run the async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async functions in the event loop
        lse_news = loop.run_until_complete(scrape_lse_news())
        yahoo_news = loop.run_until_complete(scrape_yahoo_finance_news())
        
        # Close the event loop
        loop.close()
        
        return JsonResponse({'status': 'success', 'message': 'News articles scraped and analyzed successfully.'}, status=200)
    except Exception as e:
        print("exception:", e)
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def home(request):
    """
    Render the home page with a professional and attractive design.
    """
    return render(request, 'news_analyzer/home.html')

def articles(request):
    """
    Render the articles page to display analyzed news articles.
    """
    return render(request, 'news_analyzer/articles.html')

@api_view(['GET'])
def get_articles(request):
    """
    Get analyzed news articles with sentiment analysis.
    """
    try:
        # Get query parameters for filtering
        sentiment = request.GET.get('sentiment', None)
        importance = request.GET.get('importance', None)
        symbol = request.GET.get('symbol', None)
        page = request.GET.get('page', 1)
        
        # Base query
        query = NewsSentiment.objects.all().order_by('-created_at')
        
        # Apply filters if provided
        if sentiment:
            query = query.filter(sentiment=sentiment)
        if importance:
            query = query.filter(importance=importance)
        if symbol:
            query = query.filter(stock_symbol__symbol=symbol)
        
        # Paginate results
        paginator = Paginator(query, 10)
        page_obj = paginator.get_page(page)
        
        # Format the results
        articles = []
        for item in page_obj:
            # Get the reasons as a list
            reasons = []
            if item.reason:
                try:
                    reasons = json.loads(item.reason)
                except:
                    reasons = [item.reason]
            
            # Get the stock symbols
            symbols = []
            for stock in item.stock_symbol.all():
                symbols.append(stock.symbol)
            
            article_data = {
                "title": item.article.title,
                "symbols": symbols,
                "sentiment": item.sentiment,
                "importance": item.importance.lower(),
                "company_name": item.stock_name,
                "description": item.summary,
                "reasons": reasons,
                "analyzer": "deepseek",
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            articles.append(article_data)
        
        return JsonResponse({
            'status': 'success',
            'articles': articles,
            'total_pages': paginator.num_pages,
            'current_page': page
        }, status=200)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def validation_results(request):
    """
    Display validation results from sentiment_comparison.json
    """
    try:
        # Get the path to the sentiment_comparison.json file
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                'news_analyzer', 'validation', 'sentiment_comparison.json')
        
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as file:
            validation_data = json.load(file)
        
        # Calculate statistics
        total_articles = len(validation_data)
        
        # DeepSeek matches
        deepseek_matches = sum(1 for item in validation_data if item.get('deepseek_sentiment', {}).get('match', False))
        deepseek_match_percentage = (deepseek_matches / total_articles * 100) if total_articles > 0 else 0
        
        # Gemini matches
        gemini_matches = sum(1 for item in validation_data if item.get('gemini_sentiment', {}).get('match', False))
        gemini_match_percentage = (gemini_matches / total_articles * 100) if total_articles > 0 else 0
        
        # Llama4 matches
        llama4_matches = sum(1 for item in validation_data if item.get('llama4_sentiment', {}).get('match', False))
        llama4_match_percentage = (llama4_matches / total_articles * 100) if total_articles > 0 else 0

        # gpt4 mini matches
        gpt4_mini_matches = sum(1 for item in validation_data if item.get('gpt4_mini_sentiment', {}).get('match', False))
        gpt4_mini_match_percentage = (gpt4_mini_matches / total_articles * 100) if total_articles > 0 else 0

        
        # Count sentiment distribution
        sentiment_counts = {
            'VP': 0, 'P': 0, 'SP': 0, 'N': 0, 'SN': 0, 'NG': 0, 'VN': 0
        }
        
        for item in validation_data:
            sentiment = item.get('deepseek_sentiment', {}).get('sentiment')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        # Prepare data for pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(validation_data, 10)  # 10 items per page
        page_obj = paginator.get_page(page)
        
        context = {
            'validation_data': page_obj,
            'total_articles': total_articles,
            'sentiment_matches': deepseek_matches,
            'gemini_matches': gemini_matches,
            'llama4_matches': llama4_matches,
            'deepseek_match_percentage': round(deepseek_match_percentage, 2),
            'gemini_match_percentage': round(gemini_match_percentage, 2),
            'llama4_match_percentage': round(llama4_match_percentage, 2),
            'gpt4_mini_match_percentage': round(gpt4_mini_match_percentage, 2),
            'gpt4_mini_matches': gpt4_mini_matches,
            'sentiment_counts': sentiment_counts,
        }
        
        return render(request, 'news_analyzer/validation_results.html', context)
    
    except Exception as e:
        print(f"Error loading validation results: {str(e)}")
        traceback.print_exc()
        return render(request, 'news_analyzer/validation_results.html', {'error': str(e)})


