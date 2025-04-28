import requests
import os
from django.conf import settings
from news_analyzer.models import StockCompany, StockName
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def get_api_key():
    """Get the Marketstack API key from environment or settings"""
    api_key = os.environ.get('MARKETSTACK_API_KEY')
    if not api_key:
        try:
            api_key = getattr(settings, 'MARKETSTACK_API_KEY', '3bf4300a992feb65986ce192e7038d8a')
        except AttributeError:
            api_key = '3bf4300a992feb65986ce192e7038d8a'
    return api_key

def fetch_stocks_page(api_key, base_url, offset=0, limit=1000):
    """Fetch a page of stocks from the Marketstack API"""
    params = {
        'access_key': api_key,
        'exchange': 'XLON',
        'limit': limit,
        'offset': offset
    }
    
    response = requests.get(f'{base_url}/tickers', params=params)
    response.raise_for_status()
    return response.json()

def update_lse_stocks():
    """Fetch and update LSE stocks from Marketstack API"""
    api_key = get_api_key()
    base_url = 'http://api.marketstack.com/v1'
    
    # Initialize results
    results = {
        "total_processed": 0,
        "successful_updates": 0,
        "failed_updates": 0,
        "skipped_symbols": 0,
        "failed_symbols": []
    }
    
    try:
        # Fetch first page to get total count
        logger.info("Fetching first page of stocks...")
        data = fetch_stocks_page(api_key, base_url)
        
        if 'data' not in data or 'pagination' not in data:
            logger.error(f"Unexpected API response format: {data}")
            return results
            
        total_stocks = data['pagination']['total']
        limit = data['pagination']['limit']
        logger.info(f"Found {total_stocks} total stocks")
        
        # Process all pages
        offset = 0
        while offset < total_stocks:
            if offset > 0:
                logger.info(f"Fetching stocks {offset+1}-{min(offset+limit, total_stocks)}...")
                data = fetch_stocks_page(api_key, base_url, offset)
                if 'data' not in data:
                    logger.error(f"Unexpected API response format in page {offset//limit + 1}")
                    break
            
            stocks_data = data['data']
            results["total_processed"] += len(stocks_data)
            
            for stock_data in stocks_data:
                symbol = stock_data.get('symbol')
                if not symbol:
                    results["skipped_symbols"] += 1
                    continue
                    
                try:
                    # Extract stock name
                    stock_name = stock_data.get('name', '')
                    
                    # Use transaction to ensure data consistency
                    with transaction.atomic():
                        # Create or update the StockCompany (only using symbol)
                        stock, created = StockCompany.objects.get_or_create(
                            symbol=symbol
                        )
                        
                        # Create or update the StockName entries
                        # First, delete any existing names for this stock
                        StockName.objects.filter(stock_symbol=stock).delete()
                        
                        # Add the name
                        if stock_name:
                            StockName.objects.create(
                                stock_symbol=stock,
                                name=stock_name,
                                name_type='long'
                            )
                            
                            # Also add a short name if it's different
                            short_name = stock_name.split()[0] if len(stock_name.split()) > 1 else stock_name
                            if short_name != stock_name:
                                StockName.objects.create(
                                    stock_symbol=stock,
                                    name=short_name,
                                    name_type='short'
                                )
                    
                    results["successful_updates"] += 1
                    logger.info(f"{'Created' if created else 'Updated'} stock: {symbol} - {stock_name}")
                    
                except Exception as e:
                    results["failed_updates"] += 1
                    results["failed_symbols"].append(symbol)
                    logger.error(f"Error processing stock {symbol}: {str(e)}")
            
            offset += limit
                
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        
    logger.info(f"LSE stock update completed:")
    logger.info(f"Total stocks processed: {results['total_processed']}")
    logger.info(f"Successfully updated: {results['successful_updates']}")
    logger.info(f"Failed updates: {results['failed_updates']}")
    logger.info(f"Skipped symbols: {results['skipped_symbols']}")
    if results['failed_symbols']:
        logger.info(f"Failed symbols: {', '.join(results['failed_symbols'])}")
        
    return results 