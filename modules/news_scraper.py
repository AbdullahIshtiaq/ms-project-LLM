import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import os
import json
from config import NEWS_SOURCES
from modules.mock_data import get_mock_news_articles

class NewsScraper:
    def __init__(self):
        self.sources = NEWS_SOURCES
        # Set a user agent to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Create a cache directory if it doesn't exist
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_financial_news(self, stock_symbol, limit=5, use_cache=True, use_mock=False):
        """Scrape financial news related to the given stock symbol"""
        # Check if mock data is requested
        if use_mock:
            print(f"Using mock news data for {stock_symbol}")
            return get_mock_news_articles(stock_symbol, limit)
        
        # Check for cached data
        cache_file = os.path.join(self.cache_dir, f"{stock_symbol}_news.json")
        if use_cache and os.path.exists(cache_file):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time < timedelta(hours=4):  # News cache valid for 4 hours
                try:
                    with open(cache_file, 'r') as f:
                        cached_articles = json.load(f)
                        print(f"Using cached news for {stock_symbol}")
                        return cached_articles[:limit]
                except Exception as e:
                    print(f"Error reading news cache: {e}")
        
        all_articles = []
        
        # Scrape Yahoo Finance as it allows searching by stock symbol
        url = f'https://finance.yahoo.com/quote/{stock_symbol}/news'
        
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error scraping Yahoo Finance: Status code {response.status_code}")
                # If API fails, use mock data
                return get_mock_news_articles(stock_symbol, limit)
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles on Yahoo Finance
            news_items = soup.find_all('div', {'class': 'Ov(h)'})
            
            for item in news_items[:limit]:
                try:
                    # Get the title
                    title_element = item.find('h3')
                    if not title_element:
                        continue
                    title = title_element.text.strip()
                    
                    # Get the link
                    link_element = item.find('a')
                    if not link_element:
                        continue
                    link = link_element.get('href')
                    if link and not link.startswith('http'):
                        link = 'https://finance.yahoo.com' + link
                    
                    # Get publication date if available
                    date_element = item.find('span', {'class': 'C($tertiaryColor)'})
                    pub_date = date_element.text.strip() if date_element else "Unknown"
                    
                    # Get article content by visiting the link
                    article_content = self._get_article_content(link)
                    
                    article = {
                        'title': title,
                        'url': link,
                        'date': pub_date,
                        'source': 'Yahoo Finance',
                        'content': article_content,
                        'related_symbol': stock_symbol
                    }
                    
                    all_articles.append(article)
                    
                    # Random delay to avoid overwhelming the server
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"Error parsing news item: {e}")
                    continue
                    
            # Cache the results
            if all_articles:
                with open(cache_file, 'w') as f:
                    json.dump(all_articles, f)
            
        except Exception as e:
            print(f"Error scraping Yahoo Finance: {e}")
            # If scraping fails, use mock data
            return get_mock_news_articles(stock_symbol, limit)
        
        # If we didn't get any articles, use mock data
        if not all_articles:
            print(f"No articles found for {stock_symbol}, using mock data")
            return get_mock_news_articles(stock_symbol, limit)
            
        return all_articles
    
    def _get_article_content(self, url):
        """Extract the content of a news article from its URL"""
        try:
            # Add random delay before fetching content
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return "Could not retrieve article content due to server response."
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Article content is usually in p tags
            paragraphs = soup.find_all('p')
            content = ' '.join([p.text.strip() for p in paragraphs])
            
            # Limit content length - Gemini may have token limits
            if len(content) > 4000:
                content = content[:4000] + "..."
                
            return content
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return "Could not retrieve article content." 