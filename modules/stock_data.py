import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
import random
from config import STOCK_HISTORY_PERIOD

class StockData:
    def __init__(self):
        # Create a cache directory if it doesn't exist
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_stock_info(self, symbol):
        """Get current stock information for the given symbol with caching"""
        # Check if we have a recent cache for this symbol
        cache_file = os.path.join(self.cache_dir, f"{symbol}_info.json")
        
        # Try to use cached data if it exists and is less than 1 hour old
        if os.path.exists(cache_file):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time < timedelta(hours=1):
                try:
                    with open(cache_file, 'r') as f:
                        print(f"Using cached data for {symbol}")
                        return json.load(f)
                except Exception as e:
                    print(f"Error reading cache: {e}")
        
        # If no valid cache, fetch from API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Extract relevant information
                relevant_info = {
                    'symbol': symbol,
                    'company_name': info.get('shortName', 'Unknown'),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'current_price': info.get('currentPrice', info.get('previousClose', 0)),
                    'previous_close': info.get('previousClose', 0),
                    'open': info.get('open', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                    'year_high': info.get('fiftyTwoWeekHigh', 0),
                    'year_low': info.get('fiftyTwoWeekLow', 0),
                    'market_cap': info.get('marketCap', 0),
                    'volume': info.get('volume', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'dividend_yield': info.get('dividendYield', 0) if info.get('dividendYield') else 0,
                    'description': info.get('longBusinessSummary', 'No description available')
                }
                
                # Cache the data
                with open(cache_file, 'w') as f:
                    json.dump(relevant_info, f)
                
                return relevant_info
                
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries}: Error fetching stock info for {symbol}: {e}")
                if attempt < max_retries - 1:
                    # Wait longer before retry
                    time.sleep(random.uniform(3, 5))
        
        # If all retries fail, return a default object
        return {
            'symbol': symbol,
            'company_name': symbol,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'current_price': 0,
            'previous_close': 0,
            'open': 0,
            'day_high': 0,
            'day_low': 0,
            'year_high': 0,
            'year_low': 0,
            'market_cap': 0,
            'volume': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'description': 'Data temporarily unavailable',
            'error': 'Failed to retrieve data after multiple attempts'
        }
    
    def get_historical_data(self, symbol, period=STOCK_HISTORY_PERIOD):
        """Get historical stock data for the given symbol with caching"""
        # Check if we have a recent cache for this symbol's history
        cache_file = os.path.join(self.cache_dir, f"{symbol}_history_{period}.json")
        
        # Try to use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time < timedelta(days=1):
                try:
                    with open(cache_file, 'r') as f:
                        print(f"Using cached history data for {symbol}")
                        return json.load(f)
                except Exception as e:
                    print(f"Error reading history cache: {e}")
        
        # If no valid cache, fetch from API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                stock = yf.Ticker(symbol)
                history = stock.history(period=period)
                
                # Convert to list of dictionaries for easier processing
                history_records = []
                for date, row in history.iterrows():
                    history_records.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row.get('Open', 0)),
                        'high': float(row.get('High', 0)),
                        'low': float(row.get('Low', 0)),
                        'close': float(row.get('Close', 0)),
                        'volume': int(row.get('Volume', 0))
                    })
                
                # Cache the data
                with open(cache_file, 'w') as f:
                    json.dump(history_records, f)
                
                return history_records
                
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries}: Error fetching historical data for {symbol}: {e}")
                if attempt < max_retries - 1:
                    # Wait longer before retry
                    time.sleep(random.uniform(3, 5))
        
        # If all retries fail, return an empty list with a simulated data point
        today = datetime.now().strftime('%Y-%m-%d')
        return [
            {
                'date': today,
                'open': 0,
                'high': 0,
                'low': 0,
                'close': 0,
                'volume': 0
            }
        ] 