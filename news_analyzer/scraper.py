from datetime import datetime
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright
from .article_processor import create_stock_news
from .utils import clean_text
from asgiref.sync import sync_to_async

# LSE news URL
LSE_NEWS_URL = "https://www.londonstockexchange.com/news?tab=today-s-news"

def scrape_article_content(url, browser_context):
    """Scrape individual article content using Playwright."""
    try:
        page = browser_context.new_page()
        try:
            print(f"Scraping article content from {url}")
            # Load the page and wait for network to be idle
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for the content to be loaded
            page.wait_for_load_state('domcontentloaded', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Wait for the news-body-content to be present
            page.wait_for_selector('div.news-body-content', timeout=10000)
            
            # Get the content
            article_content = page.query_selector('div.news-body-content')
            
            if not article_content:
                print(f"Could not find news-body-content div for {url}")
                return None
            
            # Get all paragraphs
            paragraphs = article_content.query_selector_all('p')
            
            if paragraphs:
                # If paragraphs found, join them with newlines
                texts = [p.inner_text() for p in paragraphs]
                text = '\n\n'.join([clean_text(t) for t in texts])
            else:
                # If no paragraphs, get all text
                text = clean_text(article_content.inner_text())
            
            print(f"Found article content: {text[:200]}...")  # Print first 200 chars for debugging
            
            return {
                'text': text,
                'html': article_content.inner_html()
            }
            
        finally:
            page.close()
            
    except Exception as e:
        print(f"Error scraping article content from {url}: {str(e)}")
        return None

# Wrapper function to call create_stock_news in a synchronous context
async def create_stock_news_async(article_text, article_url, title, date_posted):
    return await sync_to_async(create_stock_news)(article_text, article_url, title, date_posted)

# Synchronous function to run Playwright
def run_playwright_sync():
    """Synchronous function to run Playwright and scrape news."""
    print("Scraping LSE news")
    articles = []
    
    with sync_playwright() as p:
        # Launch browser with slower default timeout
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}          
        )
        
        try:
            page = context.new_page()
            # Load the page with longer timeout
            print("Loading LSE news page...")
            page.goto(LSE_NEWS_URL, wait_until='networkidle', timeout=30000)
            
            # Wait for the page to be fully loaded
            print("Waiting for page to load...")
            page.wait_for_load_state('domcontentloaded', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Wait for any of these selectors that might indicate news content
            print("Waiting for news content...")
            selectors = [
                "a[href*='news-article/']",
            ]
            
            for selector in selectors:
                print(f"Waiting for selector: {selector}")
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    print(f"Found content with selector: {selector}")
                    break
                except Exception:
                    continue
            
            # Get all news links
            news_elements = page.query_selector_all("a[href*='news-article/']")
            print(f"Found {len(news_elements)} news elements")
            
            # If no news elements found, try getting page content for debugging
            if not news_elements:
                print("No news elements found. Page content:")
                content = page.content()
                print(content[:1000])  # Log first 1000 chars
                # save page content to file for debugging
                with open("lse_news_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
            
            # Process each news element
            for element in news_elements:
                title = clean_text(element.inner_text())
                article_url = element.get_attribute('href')
                
                if not article_url or not title:
                    continue
                
                print(f"Processing article: {title} ({article_url})")
                
                # Get full article content
                # add domain prefix to the URL
                if not article_url.startswith('http'):
                    article_url = f"https://www.londonstockexchange.com/{article_url}"
                    
                # Get article content
                article_content = scrape_article_content(article_url, context)
                if not article_content:
                    print(f"Could not fetch content for article: {title}")
                    continue
                print(f"Successfully scraped LSE article: {title}")
                
                # Store the article data for later processing
                articles.append({
                    'title': title,
                    'url': article_url,
                    'content': article_content['text'],
                    'html': article_content['html'],
                    'date': datetime.now().strftime("%Y/%m/%d")
                })
            
            print(f"Scraped {len(articles)} articles from LSE")
            
        finally:
            page.close()
            context.close()
            browser.close()
            print("Closed browser")
    
    return articles

async def scrape_lse_news():
    """Scrape news articles from the London Stock Exchange website."""
    # Run the synchronous Playwright code in a synchronous context
    articles = await sync_to_async(run_playwright_sync)()
    
    # Process the articles asynchronously
    processed_articles = []
    for article in articles:
        result = await create_stock_news_async(
            article['content'], 
            article['url'], 
            article['title'], 
            article['date']
        )
        if result:
            processed_articles.append(article)
    
    return processed_articles