from datetime import datetime
from playwright.sync_api import sync_playwright
from .article_processor import create_stock_news
from .utils import clean_text
from asgiref.sync import sync_to_async
from .models import NewsArticle

# News URLs
LSE_NEWS_URL = "https://www.londonstockexchange.com/news?tab=today-s-news"
YAHOO_FINANCE_NEWS_URL = "https://uk.finance.yahoo.com/topic/stocks/"

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

def scrape_yahoo_article_content(url, browser_context):
    """Scrape individual article content from Yahoo Finance using Playwright."""
    try:
        page = browser_context.new_page()
        try:
            print(f"Scraping Yahoo Finance article content from {url}")
            # Load the page and wait for network to be idle
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for the content to be loaded
            page.wait_for_load_state('domcontentloaded', timeout=30000)
            
            # Remove ads from the page
            try:
                page.evaluate("""
                    const adElements = document.querySelectorAll('[data-testid="inarticle-ad"]');
                    adElements.forEach(el => el.remove());
                """)
                print("Removed ad elements from the page")
            except Exception as e:
                print(f"Error removing ads: {str(e)}")
            
            # Wait for the article content to be present - try multiple selectors
            selectors = [
                'div.article-wrap',
                'div[class*="article-wrap"]',
                'div.caas-body',
                'div.article-body',
                'div[data-test-locator="articleBody"]',
                'div[class*="article-body"]',
                'div[class*="caas-body"]'
            ]
            
            title_element = page.query_selector('div[class^="cover-title"]')
            if title_element:
                title = clean_text(title_element.inner_text())
            else:
                title = f"Yahoo Finance Article {url}"
            article_content = None
            for selector in selectors:
                try:
                    print(f"Trying to find content with selector: {selector}")
                    page.wait_for_selector(selector, timeout=5000)
                    article_content = page.query_selector(selector)
                    if article_content:
                        print(f"Found content with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Selector {selector} not found: {str(e)}")
                    continue
            
            if not article_content:
                print(f"Could not find article content for {url}")
                # Try to get any text content as fallback
                article_content = page.query_selector('body')
                if not article_content:
                    return None, None
            
            # Get all paragraphs
            paragraphs = article_content.query_selector_all('p')
            
            if paragraphs:
                # If paragraphs found, join them with newlines
                texts = [p.inner_text() for p in paragraphs]
                text = '\n\n'.join([clean_text(t) for t in texts])
            else:
                # If no paragraphs, get all text
                text = clean_text(article_content.inner_text())
            
            print(f"Found Yahoo Finance article content: {text[:200]}...")  # Print first 200 chars for debugging
            
            return {
                'text': text,
                'html': article_content.inner_html()
            }, title
            
        finally:
            page.close()
            
    except Exception as e:
        print(f"Error scraping Yahoo Finance article content from {url}: {str(e)}")
        return None, None

# Wrapper function to call create_stock_news in a synchronous context
async def create_stock_news_async(article_text, article_url, title, date_posted):
    return await sync_to_async(create_stock_news)(article_text, article_url, title, date_posted)

# Synchronous function to run Playwright for LSE
def run_playwright_sync():
    """Synchronous function to run Playwright and scrape LSE news."""
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

                # # skip if the URL is in Database
                # if NewsArticle.objects.filter(url=article_url).exists():
                #     print(f"Article already exists in database: {article_url}")
                #     continue
                    
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

# Synchronous function to run Playwright for Yahoo Finance
def run_yahoo_playwright_sync():
    """Synchronous function to run Playwright and scrape Yahoo Finance news."""
    print("Scraping Yahoo Finance news")
    articles = []
    
    with sync_playwright() as p:
        # Launch browser with slower default timeout and stealth mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        
        try:
            page = context.new_page()
            # Load the page with longer timeout but don't wait for networkidle
            print("Loading Yahoo Finance news page...")
            page.goto(YAHOO_FINANCE_NEWS_URL, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for the page to be fully loaded
            print("Waiting for page to load...")
            page.wait_for_load_state('domcontentloaded', timeout=30000)
            
            # Check if we're on a "Just a moment" page
            if "Just a moment" in page.content() or "Yahoo is part of the Yahoo family of brands" in page.content():
                print("Detected anti-bot page. Trying to bypass...")
                # Try to bypass the anti-bot page
                page.wait_for_timeout(5000)  # Wait 5 seconds
                
                # Try to click any buttons that might be present
                try:
                    page.click('button:has-text("Accept")', timeout=5000)
                    print("Clicked Accept button")
                except Exception:
                    print("No Accept button found")
                
                # Wait a bit more
                page.wait_for_timeout(5000)
                
                # Reload the page
                page.reload(wait_until='domcontentloaded', timeout=30000)
                page.wait_for_load_state('domcontentloaded', timeout=30000)
                
                # Check if we're still on the anti-bot page
                if "Just a moment" in page.content() or "Yahoo is part of the Yahoo family of brands" in page.content():
                    print("Still on anti-bot page. Cannot proceed.")
                    return articles
            
            # Try to find the specific div elements mentioned
            print("Looking for topic-stream, topic-stories, and topic-hero-block elements...")
            
            # First try to find the topic-stream container
            try:
                page.wait_for_selector('div.topic-stream', timeout=5000)
                print("Found topic-stream container")
                
                # Now look for article links within this container
                news_elements = page.query_selector_all('div.topic-stream a[href*="/news/"]')
                print(f"Found {len(news_elements)} news elements in topic-stream")
            except Exception as e:
                print(f"Could not find topic-stream: {str(e)}")
                news_elements = []
            
            # If no elements found in topic-stream, try topic-stories
            if not news_elements:
                try:
                    # Try to find any div with class starting with "topic-stories"
                    page.wait_for_selector('div[class^="topic-stories"]', timeout=5000)
                    print("Found topic-stories container")
                    
                    # Now look for article links within this container
                    news_elements = page.query_selector_all('div[class^="topic-stories"] a[href*="/news/"]')
                    print(f"Found {len(news_elements)} news elements in topic-stories")
                except Exception as e:
                    print(f"Could not find topic-stories: {str(e)}")
            
            # If still no elements found, try topic-hero-block
            if not news_elements:
                try:
                    # Try to find any div with class starting with "topic-hero-block"
                    page.wait_for_selector('div[class^="topic-hero-block"]', timeout=5000)
                    print("Found topic-hero-block container")
                    
                    # Now look for article links within this container
                    news_elements = page.query_selector_all('div[class^="topic-hero-block"] a[href*="/news/"]')
                    print(f"Found {len(news_elements)} news elements in topic-hero-block")
                except Exception as e:
                    print(f"Could not find topic-hero-block: {str(e)}")
            
            # If still no elements found, try the original selectors as fallback
            if not news_elements:
                print("No elements found in specific containers. Trying fallback selectors...")
                selectors = [
                    "a[href*='/news/']",
                    "a[href*='finance.yahoo.com/news']",
                    "a[data-test-locator='article']",
                    "a[class*='article']",
                    "a[class*='news']"
                ]
                
                for selector in selectors:
                    print(f"Trying to find news elements with selector: {selector}")
                    try:
                        # Wait a bit for the selector to appear
                        page.wait_for_selector(selector, timeout=5000)
                        elements = page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            print(f"Found {len(elements)} news elements with selector: {selector}")
                            news_elements = elements
                            break
                    except Exception as e:
                        print(f"Selector {selector} not found: {str(e)}")
                        continue
            
            # If no news elements found, try getting page content for debugging
            if not news_elements:
                print("No news elements found. Page content:")
                content = page.content()
                print(content[:1000])  # Log first 1000 chars
                # save page content to file for debugging
                with open("yahoo_news_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Try to find any links that might be news
                all_links = page.query_selector_all("a")
                print(f"Found {len(all_links)} total links on the page")
                
                # Filter links that might be news
                for link in all_links:
                    href = link.get_attribute('href')
                    text = clean_text(link.inner_text())
                    if href and '/news/' in href and text:
                        print(f"Potential news link: {text} ({href})")
                        news_elements.append(link)
            
            # Process each news element
            for element in news_elements:
                # Try to find the title using the cover-title class


                article_url = element.get_attribute('href')
                
                if not article_url:
                    continue
                
                print(f"Processing Yahoo Finance article: ({article_url})")
                
                # Get full article content
                # add domain prefix to the URL if needed
                if not article_url.startswith('http'):
                    article_url = f"https://uk.finance.yahoo.com{article_url}"

                
                # # skip if the URL is in Database
                # if NewsArticle.objects.filter(url=article_url).exists():
                #     print(f"Article already exists in database: {article_url}")
                #     continue
                    
                # Get article content
                article_content, title = scrape_yahoo_article_content(article_url, context)
                if not article_content:
                    print(f"Could not fetch content for article: {article_url}")
                    continue
                print(f"Successfully scraped Yahoo Finance article: {article_url}")
                
                # Store the article data for later processing
                articles.append({
                    'title': title,
                    'url': article_url,
                    'content': article_content['text'],
                    'html': article_content['html'],
                    'date': datetime.now().strftime("%Y/%m/%d")
                })
            
            print(f"Scraped {len(articles)} articles from Yahoo Finance")
            
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

async def scrape_yahoo_finance_news():
    """Scrape news articles from Yahoo Finance website."""
    # Run the synchronous Playwright code in a synchronous context
    articles = await sync_to_async(run_yahoo_playwright_sync)()
    
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