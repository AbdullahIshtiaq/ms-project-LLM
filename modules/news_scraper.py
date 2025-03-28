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
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re

class NewsScraper:
    def __init__(self):
        self.sources = NEWS_SOURCES
        # Set a user agent to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        }
        
        # Initialize LLM for symbol extraction
        self.llm = OllamaLLM(
            model="deepseek-r1:1.5b",
        )
        
        # Create a template for stock symbol extraction
        self.symbol_extraction_template = PromptTemplate(
            input_variables=["title", "content"],
            template="""
            Extract the stock symbols mentioned in this financial news article. 
            Look for:
            1. Explicit ticker symbols in parentheses like (AAPL), (TSLA), (MSFT)
            2. Companies with known stock tickers (Apple/AAPL, Microsoft/MSFT, etc.)
            
            Article Title: {title}
            Article Content: {content}
            
            Return ONLY valid stock ticker symbols separated by commas (e.g., "AAPL, MSFT, TSLA").
            If no valid symbols are found, return "NONE".
            
            Important:
            - Respond ONLY with the ticker symbols or "NONE"
            - No other text, explanation or preamble allowed
            - Tickers must be 1-5 letters (standard stock symbols)
            """
        )
        
        # Create the LLM chain for symbol extraction
        self.symbol_chain = LLMChain(llm=self.llm, prompt=self.symbol_extraction_template)
    
    def get_financial_news(self, limit=5, use_mock=False):
        """Scrape general financial news without requiring a specific stock symbol"""
        # Check if mock data is requested
        if use_mock:
            print("Using mock news data")
            return get_mock_news_articles("GENERAL", limit)
        
        all_articles = []
        
        # Try multiple potential sources with more specific paths to financial news
        sources = [
            # Yahoo Finance Top Stories
            {
                'url': 'https://finance.yahoo.com/',
                'article_selector': 'li.js-stream-content',
                'title_selector': 'h3',
                'link_selector': 'a',
                'date_selector': 'span'
            },
            # Yahoo Finance Market News
            {
                'url': 'https://finance.yahoo.com/topic/stock-market-news/',
                'article_selector': 'li.js-stream-content',
                'title_selector': 'h3',
                'link_selector': 'a',
                'date_selector': 'span'
            },
            # MarketWatch Headlines
            {
                'url': 'https://www.marketwatch.com/',
                'article_selector': 'div.article__content',
                'title_selector': 'h3.article__headline',
                'link_selector': 'a',
                'date_selector': 'span.article__timestamp'
            },
            # CNBC Market News
            {
                'url': 'https://www.cnbc.com/markets/',
                'article_selector': 'div.Card-standardBreakerCard',
                'title_selector': 'a.Card-title',
                'link_selector': 'a.Card-title',
                'date_selector': 'span.Card-time'
            },
        ]
        
        for source in sources:
            try:
                source_name = source['url'].split('/')[2]  # Extract domain name
                print(f"\nAttempting to scrape from {source_name}")
                
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(2, 4))
                
                response = requests.get(source['url'], headers=self.headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Error scraping {source_name}: Status code {response.status_code}")
                    continue
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news articles 
                selector = source['article_selector']
                news_items = soup.select(selector)
                print(f"Found {len(news_items)} potential news items with selector: {selector}")
                
                # Keep track of articles found from this source
                source_articles = []
                
                # Process the found items if any
                for item in news_items[:limit*2]:  # Get more than needed in case some fail
                    try:
                        # Get the title
                        title_element = item.select_one(source['title_selector'])
                        if not title_element:
                            continue
                        
                        title = title_element.text.strip()
                        if not title:
                            continue
                        
                        # Skip non-financial news (sports, etc.)
                        if any(kw in title.lower() for kw in ['sport', 'game', 'movie', 'film', 'celebrity']):
                            continue
                            
                        print(f"Found title: {title}")
                        
                        # Get the link
                        link_element = item.select_one(source['link_selector']) if source['link_selector'] else title_element
                        if not link_element:
                            continue
                            
                        link = link_element.get('href')
                        if not link:
                            continue
                            
                        # Fix relative URLs
                        if link.startswith('/'):
                            base_url = '/'.join(source['url'].split('/')[:3])  # https://domain.com
                            link = base_url + link
                        
                        print(f"Found link: {link}")
                        
                        # Get publication date if available
                        date_element = item.select_one(source['date_selector'])
                        pub_date = date_element.text.strip() if date_element else "Unknown"
                        
                        # Get article content by visiting the link
                        print(f"Fetching content for: {title}")
                        article_content = self._get_article_content(link)
                        
                        # Skip articles with insufficient content
                        if len(article_content) < 150:
                            print(f"Skipping article with too little content ({len(article_content)} chars)")
                            continue
                        
                        article = {
                            'title': title,
                            'url': link,
                            'date': pub_date,
                            'source': source_name,
                            'content': article_content,
                            'related_symbol': None
                        }
                        
                        source_articles.append(article)
                        
                        # Random delay to avoid overwhelming the server
                        time.sleep(random.uniform(1.5, 3))
                        
                        # If we have enough articles from this source, stop
                        if len(source_articles) >= limit:
                            break
                            
                    except Exception as e:
                        print(f"Error parsing news item: {e}")
                        continue
                
                # Add articles from this source to our collection
                all_articles.extend(source_articles)
                
                # If we have enough total articles, stop scraping other sources
                if len(all_articles) >= limit:
                    all_articles = all_articles[:limit]  # Trim to requested limit
                    break
                    
            except Exception as e:
                print(f"Error scraping {source['url']}: {e}")
                continue
        
        if all_articles:
            print(f"\nSuccessfully scraped {len(all_articles)} articles from {len(set([a['source'] for a in all_articles]))} sources")
            return all_articles
        
        # If we didn't get any articles, use mock data
        print("No articles found from any source, using mock data")
        return get_mock_news_articles("GENERAL", limit)
    
    def extract_symbols(self, articles):
        """Extract stock symbols from news articles using LLM"""
        # Common US stock tickers for validation
        common_tickers = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 
            'V', 'WMT', 'BAC', 'PG', 'DIS', 'NFLX', 'ADBE', 'CRM', 'CSCO', 'INTC', 
            'VZ', 'KO', 'PEP', 'CMCSA', 'T', 'HD', 'MRK', 'PFE', 'ABT', 'CVX', 'XOM'
        }
        
        # Pattern for validating stock symbols (1-5 uppercase letters)
        ticker_pattern = re.compile(r'^[A-Z]{1,5}$')
        
        for article in articles:
            try:
                # Prepare the input for the LLM
                chain_input = {
                    "title": article['title'],
                    "content": article['content']
                }
                
                # Get the response from the LLM
                print(f"\nExtracting symbols from: {article['title']}")
                response = self.symbol_chain.invoke(chain_input)
                
                # Handle different response formats
                if isinstance(response, dict):
                    print(f"Response is a dictionary: {response}")
                    # Try to extract text from various potential fields
                    if 'text' in response:
                        response_text = response['text']
                    elif 'response' in response:
                        response_text = response['response']
                    elif 'result' in response:
                        response_text = response['result']
                    elif 'content' in response:
                        response_text = response['content']
                    else:
                        # If we can't find a suitable field, convert the entire dict to string
                        print("Could not find text field in response")
                        response_text = str(response)
                elif hasattr(response, 'text'):  # Handle new LangChain version
                    response_text = response.text
                elif hasattr(response, 'content'):
                    response_text = response.content
                elif isinstance(response, str):
                    response_text = response
                else:
                    print(f"Unexpected response type: {type(response)}")
                    response_text = str(response)
                
                print(f"Raw LLM response text: {response_text}")
                
                # Extract ticker symbols using regex - look for 1-5 capital letters that could be stock symbols
                # This is a fallback if the LLM response is not in the expected format
                potential_symbols = re.findall(r'\b[A-Z]{1,5}\b', response_text)
                
                # Parse the response - it might contain the symbols we're looking for
                response_text = response_text.strip()
                
                # Try to extract symbols from response, checking for "NONE" or actual symbols
                if response_text and not response_text.upper().endswith("NONE"):
                    # First try to find comma-separated symbols at the end of the string
                    # This pattern looks for a list of ticker symbols at the end of the text
                    symbol_list_match = re.search(r'(?::|symbols are|symbols:|tickers:|symbols mentioned are|are)\s*(.+?)$', response_text)
                    if symbol_list_match:
                        symbol_list = symbol_list_match.group(1).strip()
                        # Split by comma and clean up
                        symbols = [symbol.strip() for symbol in symbol_list.split(',')]
                    else:
                        # If no comma-separated list is found, use the extracted potential symbols
                        symbols = potential_symbols
                    
                    # Validate symbols against pattern and common tickers
                    valid_symbols = []
                    for symbol in symbols:
                        # Additional cleanup - remove any non-alphanumeric characters
                        symbol = re.sub(r'[^A-Z]', '', symbol)
                        
                        if ticker_pattern.match(symbol) and (len(symbol) <= 5):
                            # Prioritize common tickers or longer symbols (more likely to be real)
                            if symbol in common_tickers or len(symbol) >= 2:
                                valid_symbols.append(symbol)
                                print(f"Found valid symbol: {symbol}")
                    
                    # Take the first valid symbol for simplicity
                    article['related_symbol'] = valid_symbols[0] if valid_symbols else None
                    if not valid_symbols and symbols:
                        print(f"Warning: Found symbols {symbols} but none passed validation")
                else:
                    article['related_symbol'] = None
                    print("No symbols found")
                    
            except Exception as e:
                print(f"Error extracting symbols from article {article['title']}: {e}")
                article['related_symbol'] = None
                
        # Filter articles with identified symbols
        articles_with_symbols = [article for article in articles if article['related_symbol']]
        
        return articles_with_symbols
    
    def _get_article_content(self, url):
        """Extract the content of a news article from its URL"""
        try:
            # Add random delay before fetching content
            time.sleep(random.uniform(1, 2))
            
            print(f"Fetching content from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Error fetching article: Status code {response.status_code}")
                return "Could not retrieve article content due to server response."
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple approaches to get content
            content = ""
            
            # Approach 1: Look for article element
            article_element = soup.find('article')
            if article_element:
                paragraphs = article_element.find_all('p')
                if paragraphs:
                    content = ' '.join([p.text.strip() for p in paragraphs])
                    print(f"Found content using article element: {len(content)} characters")
            
            # Approach 2: Look for common content div classes
            if not content:
                for content_class in ['caas-body', 'article-body', 'content', 'story-body']:
                    content_div = soup.find('div', {'class': content_class})
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        if paragraphs:
                            content = ' '.join([p.text.strip() for p in paragraphs])
                            print(f"Found content using div.{content_class}: {len(content)} characters")
                            break
            
            # Approach 3: Default to all p tags if other approaches failed
            if not content:
                # Article content is usually in p tags
                paragraphs = soup.find_all('p')
                content = ' '.join([p.text.strip() for p in paragraphs])
                print(f"Found content using all p tags: {len(content)} characters")
            
            # If still no content, try to extract anything meaningful
            if not content:
                # Just get all text from the body
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
                    print(f"Extracted entire body text: {len(content)} characters")
            
            # Limit content length - DeepSeek R1 may have token limits
            if len(content) > 4000:
                content = content[:4000] + "..."
                
            # If content is too short, it's probably not useful
            if len(content) < 100:
                print(f"Warning: Content is suspiciously short ({len(content)} chars)")
                
            return content
            
        except Exception as e:
            print(f"Error fetching article content: {str(e)}")
            return "Could not retrieve article content." 