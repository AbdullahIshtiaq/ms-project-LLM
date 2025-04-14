import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
import random
import re
from config import STOCK_HISTORY_PERIOD
from modules.mock_data import get_mock_stock_info

class StockData:
    def __init__(self):
        # Regular expression to validate stock symbols
        self.symbol_pattern = re.compile(r'^[A-Z]{1,5}$')

    def is_valid_symbol(self, symbol):
        """Check if a symbol appears to be a valid stock symbol"""
        if not symbol or not isinstance(symbol, str):
            return False
        return bool(self.symbol_pattern.match(symbol))

    def get_stock_info(self, symbol):
        """Get current stock information for the given symbol with caching"""
        # Validate symbol first
        if not self.is_valid_symbol(symbol):
            print(f"Invalid symbol format: {symbol}")
            return get_mock_stock_info("INVALID")

        # If no valid cache, fetch from API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                stock = yf.Ticker(symbol)
                print(f"Fetching stock info for {symbol}")
                info = stock.info
                
                # Check if we got valid info
                # if not info or not isinstance(info, dict) or len(info) < 5:
                #     print(f"Incomplete data received for {symbol}")
                #     raise ValueError(f"Incomplete data for {symbol}")
                
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
                
                # Validate that we have essential data
                if relevant_info['current_price'] == 0 or relevant_info['company_name'] == 'Unknown':
                    print(f"Missing critical data for {symbol}")
                    raise ValueError(f"Missing critical data for {symbol}")
                
                return relevant_info
                
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries}: Error fetching stock info for {symbol}: {e}")
                # Wait longer before retry
                # if attempt < max_retries - 1:
                #     time.sleep(random.uniform(3, 5))
        
        # If all retries fail, use mock data
        print(f"All attempts failed - using mock data for {symbol}")
        return get_mock_stock_info(symbol)
    
    def get_historical_data(self, symbol):
        """Get historical stock data for the given symbol with caching"""
        # Validate symbol first
        if not self.is_valid_symbol(symbol):
            print(f"Invalid symbol format for historical data: {symbol}")
            return []

        # If no valid cache, fetch from API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                stock = yf.Ticker(symbol)
                print(f"Fetching historical data for {symbol}")
                
                # Check if the ticker exists by trying to get info
                info = stock.info
                # if not info or len(info) < 5:
                #     raise ValueError(f"Invalid ticker symbol: {symbol}")
                
                history = stock.history(period=STOCK_HISTORY_PERIOD)
                print(f"History data fetched - {len(history)} records")
                
                if history.empty:
                    print(f"No historical data available for {symbol}")
                    return []
                
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
                
                return history_records
                
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries}: Error fetching historical data for {symbol}: {e}")
                # Wait longer before retry
                # if attempt < max_retries - 1:
                #     time.sleep(random.uniform(3, 5))
        
        # If all retries fail, return empty list
        print(f"All attempts failed to get historical data for {symbol}")
        return []

    def _generate_mock_history(self, symbol, period):
        """Generate mock historical data when Yahoo Finance is unavailable"""
        today = datetime.now()
        days = 180  # Approximately 6 months
        
        # Get the mock stock info to use the current price as a starting point
        mock_info = get_mock_stock_info(symbol)
        current_price = mock_info['current_price']
        
        # Generate mock data with some randomness
        history = []
        for i in range(days):
            date = today - timedelta(days=days-i)
            # Create some price movement with random walks
            price_multiplier = 1 + (random.random() - 0.5) * 0.02  # ±1% daily change
            price = current_price * (1 - (days-i)/days*0.2)  # Trend upward over time
            price = price * price_multiplier
            
            # Daily high/low variation
            daily_range = price * 0.015  # 1.5% daily range
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(price * (1 + (random.random() - 0.5) * 0.005), 2),
                'high': round(price + random.random() * daily_range, 2),
                'low': round(price - random.random() * daily_range, 2),
                'close': round(price, 2),
                'volume': int(random.uniform(0.8, 1.2) * mock_info['volume'])
            })
        
        return history 