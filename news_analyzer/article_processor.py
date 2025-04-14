import json
import hashlib
from datetime import datetime
import requests
from .utils import get_final_stock, clean_text
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM
from .stock_data import StockData

# Initialize Ollama LLM
ollama_llm = OllamaLLM(
    model="deepseek-r1:1.5b",
    # If you need to connect to a remote Ollama instance, uncomment:
    # base_url="http://localhost:11434"
)

from .models import NewsArticle, StockCompany, StockEvent

# Initialize StockData
stock_data = StockData()

def detect_and_create_events(article, mentioned_stocks, stock_companies):
    """Process a news article to extract stock mentions and events.
    
    Args:
        article_id: Article ID
        article_data: Article data
    """
    try:
        mentioned_stocks_str = ', '.join(mentioned_stocks)
        title = article.title
        article_text = article.full_text  # Changed from article.content to article.full_text

        # Fetch stock history data for valid stocks
        stock_history_data = {}
        for stock in stock_companies:
            if stock_data.is_valid_symbol(stock):
                history = stock_data.get_historical_data(stock)
                if history:
                    # Get the last 5 days of history for context
                    recent_history = history[-5:] if len(history) > 5 else history
                    stock_history_data[stock] = recent_history

        # Create stock history context for the prompt
        stock_history_context = ""
        if stock_history_data:
            stock_history_context = "\nRecent Stock Price History:\n"
            for stock, history in stock_history_data.items():
                stock_history_context += f"\n{stock} recent price movement:\n"
                for day in history:
                    stock_history_context += f"- {day['date']}: Open: {day['open']}, Close: {day['close']}, Volume: {day['volume']}\n"

        prompt = f"""
Today is {datetime.now().strftime("%B %d, %Y")}. Analyze the following financial news article carefully. Detect any **recent** or **upcoming** important events related to the stocks or companies mentioned: {mentioned_stocks_str}.
Focus on current, or anticipated significant events that could have a material impact on the company's operations, financials, or stock price.

{stock_history_context}

**Only consider the most recent events or those anticipated in the immediate future. Disregard any events that are not current or upcoming.**

Consider these event types:
- FINANCIAL_REPORT: Quarterly or annual financial results
- DIVIDEND_ANNOUNCEMENT: Declaration of dividends
- STOCK_SPLIT: Announcement of a stock split
- MERGER_ACQUISITION: Mergers, acquisitions, or major investments
- MANAGEMENT_CHANGE: Changes in key leadership positions (CEO, CFO, etc.)
- NEW_LISTING: Initial public offerings or new stock listings
- DELISTING: Company being delisted from a stock exchange
- REGULATORY_ACTION: Major regulatory decisions affecting the company
- PRODUCT_LAUNCH: Launch of significant new products or services
- PARTNERSHIP: Formation of major strategic partnerships
- LEGAL_ISSUE: Significant legal challenges or resolutions
- MARKET_EXPANSION: Entry into new markets or significant expansion
- RESTRUCTURING: Major company reorganizations
- EARNINGS_SURPRISE: Earnings significantly above or below expectations
- INSIDER_TRADING: Substantial insider buying or selling
- ANALYST_RATING_CHANGE: Significant changes in analyst recommendations
- OTHER: Any other event that could materially impact the company

Note: Daily stock price movements or minor fluctuations in market cap are not considered significant events unless they are exceptionally large or unusual.

Title:
{title}
Article:
{article_text}

Categorize each event's importance as follows:
- CRITICAL: Events with immediate and significant impact (e.g., major mergers, unexpected CEO departures, extreme earnings surprises)
- IMPORTANT: Events with notable impact but not requiring immediate attention (e.g., new partnerships, market expansions)
- REGULAR: Events worth noting but with less immediate impact (e.g., minor management changes, small product updates)

Respond in the following JSON format. Ensure that the JSON is valid and all strings are properly escaped:
{{
    "events": [
        {{
            "event_type": "One of the event types listed above",
            "importance": "CRITICAL, IMPORTANT, or REGULAR",
            "company_name": "The name of the company this event relates to. one of {mentioned_stocks_str}",
            "English_description": "Provide a brief, concise description of the event in fluent English, suitable for a LSE audience. Consider it a standalone description so include the name of the company and key facts, but keep it short and to the point. The description should read like a headline or a very short news snippet.",
            "sentiment": "The sentiment towards the company related to this specific. Choose from: very positive, positive, slightly positive, neutral, slightly negative, negative, very negative. Base this on the potential impact of the event on the company's prospects."
        }}
    ]
}}
If no significant events are detected, return an empty list for "events".
        """
        try:
            # Use LangChain for local inference
            try:
                result = ollama_llm.invoke(prompt)
                print("DETECT_AND_CREATE_EVENTS Result: ", result)
                parsed_result = json.loads(result)
            except requests.exceptions.ConnectionError:
                print(f"Connection error to Ollama. Is Ollama running?")
                return []
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error in detect_and_create_events: {str(json_error)}")
                return []
            except Exception as api_error:
                print(f"Error calling Ollama in detect_and_create_events: {str(api_error)}")
                return []
            
            sentiment_map = {
                'very positive': 'VP',
                'positive': 'P',
                'slightly positive': 'SP',
                'neutral': 'N',
                'slightly negative': 'SN',
                'negative': 'NG',
                'very negative': 'VN',
            }
            
            created_events = []
            for i, event in enumerate(parsed_result.get('events', [])):
                try:
                    company_name = event['company_name']
                    sentiment = sentiment_map.get(event['sentiment'].lower(), 'N')
                    stock_name = None
                    if event['event_type'] not in ['NEW_LISTING']:
                        try:
                            index_of_stock = mentioned_stocks.index(company_name)
                            # Determine stock symbol based on verification
                            stock_symbol = stock_companies[index_of_stock]
                        except ValueError:
                            print(f"ValueError: company_name '{company_name}' not found in mentioned_stocks: {mentioned_stocks}")
                            stock_info = get_final_stock(company_name)
                            if stock_info:
                                print("Found stock info:", stock_info)
                                stock_symbol, name = stock_info
                                # stock_name = stock_name.replace(".SR", "")
                                stock_name = name
                            else:
                                print("No stock info found. Setting stock_symbol to None")
                                stock_symbol = None
                                stock_name = None
                    else:
                        stock_symbol = None
                        stock_name = None
                    
                    if stock_symbol:
                        print(f"SEARCHING FOR STOCK SYMBOL: {stock_symbol}")
                        try:
                            stock_company = StockCompany.objects.get(symbol=stock_symbol)
                        except StockCompany.DoesNotExist:
                            print(f"StockCompany with symbol {stock_symbol} not found")
                            stock_company = None
                        except Exception as stock_error:
                            print(f"Error getting StockCompany: {str(stock_error)}")
                            stock_company = None
                    else:
                        stock_company = None
                    
                    try:
                        stock_event = StockEvent.objects.create(
                            article=article,
                            stock_symbol=stock_company,
                            stock_name=stock_name,
                            mentioned_stock_name=company_name,
                            event_type=event['event_type'],
                            importance=event['importance'],
                            description=event['English_description'],
                            sentiment=sentiment
                        )
                        created_events.append(stock_event)
                        print(f"Created event: {stock_event.id} - {company_name} - {event['event_type']}")
                    except Exception as create_error:
                        print(f"Error creating StockEvent: {str(create_error)}")
                        
                    if event['event_type'] == 'NEW_LISTING':
                        print("NEW LISTING EVENT")
                except Exception as event_error:
                    print(f"Error processing event: {str(event_error)}")
                    continue
                    
            return created_events
        except Exception as e:
            print(f"Error in processing article: {str(e)}")
            return []
    except Exception as e:
        print(f"Error in detect_and_create_events: {str(e)}")
        return []


def create_news_article(article_url, title, article_text, news_hash, published_date):
    """Create a news article in the database."""
    news_article, created = NewsArticle.objects.get_or_create(
        url=article_url,
        defaults={
            'title': title,
            'full_text': article_text,
            'news_hash': news_hash,
            'publication_date': published_date
        }
    )
    return news_article, created

def create_stock_news(article_text, article_url, title, date_posted):
    # Clean the article text
    article_text = clean_text(article_text)

    if not article_text:
        print("Empty article text provided")
        return None

    news_hash = hashlib.sha256(article_text.encode()).hexdigest()

    # Step 1: Parse the date_posted string into a date object
    date_posted_object = datetime.strptime(date_posted, "%Y/%m/%d").date()

    # Step 2: Get the current time
    current_time_object = datetime.now().time()

    # Step 3: Combine the date and time into a datetime object
    published_date = datetime.combine(date_posted_object, current_time_object)

    # Check if article already exists
    existing_article = NewsArticle.objects.filter(url=article_url).first()
    if existing_article:
        print(f"Article already exists in database: {article_url}")
        # return existing_article, []
        news_article = existing_article
    else:
        # Create the news article
        try:
            news_article = NewsArticle.objects.create(
                url=article_url,
                title=title,
                full_text=article_text,
                news_hash=news_hash,
                publication_date=published_date
            )
            print(f"Successfully created news article: {news_article.id} - {title}")
        except Exception as db_error:
            print(f"Database error creating news article: {str(db_error)}")
            return None, None

    prompt = f"""
    Analyze the following financial news article carefully. Extract all LSE stock or index names mentioned (in English).

    Title:
    {title}
    Article:
    {article_text}

    Be sure to capture only the important LSE stock or index entities mentioned in the article. Ignore any non-LSE or global stock/index mentions.

    Respond in the following JSON format. Ensure that the JSON is valid and all strings are properly escaped:
    {{
        "mentions": ["LSE stock or index name 1", "LSE stock or index name 2", ...]
    }}
    If no LSE stock or index mentions are detected, return an empty list for "mentions".

    IMPORTANT: Return an empty list for "mentions" if the article is not latest news, such as:
    - Monthly/yearly summaries (e.g., "أهم الأحداث", "أبرز الأخبار")
    - Historical reviews (e.g., "خلال عام", "خلال الشهر", "منذ بداية العام")
    - Look-back articles (e.g., "في الفترة الماضية", "خلال الفترة")
    """

    # Use LangChain for local inference
    try:
        result = ollama_llm.invoke(prompt)
        print("CREATE STOCK NEWS Result: ", result)
        parsed_result = json.loads(result)
        print(f"Parsed result: {parsed_result}")
    except requests.exceptions.ConnectionError:
        print(f"Connection error to Ollama. Is Ollama running?")
        # Continue with empty mentions
        parsed_result = {"mentions": []}
    except json.JSONDecodeError as json_error:
        print(f"JSON parsing error: {str(json_error)}")
        # Continue with empty mentions
        parsed_result = {"mentions": []}
    except Exception as api_error:
        print(f"Error calling Ollama: {str(api_error)}")
        # Continue with empty mentions
        parsed_result = {"mentions": []}

    stock_mentions = []

    for mention in parsed_result['mentions']:
        name = mention
        stock_info = get_final_stock(mention, exact_only=True)
        if stock_info:
            symbol, stock_name = stock_info
            symbol = symbol.split('.')[0]
            try:
                stock_company, _ = StockCompany.objects.get_or_create(symbol=symbol)
                is_verified = True
            except Exception as stock_error:
                print(f"Error creating/getting stock company: {str(stock_error)}")
                stock_company = None
                is_verified = False
        else:
            stock_name = None
            stock_company = None
            symbol = None
            is_verified = False
            print(f"Unverified stock mentioned: {name}")

        stock_mentions.append({
            'mentioned_name': name,
            'stock_name': stock_name,
            'stock_company': stock_company.symbol if stock_company else None,
            'is_verified': is_verified,
        })

    # Update the NewsArticle with stock mentions
    try:
        news_article.stock_mentions = stock_mentions
        news_article.is_verified_stock = any(m['is_verified'] for m in stock_mentions)
        news_article.save()
        print(f"Updated news article with {len(stock_mentions)} stock mentions")
    except Exception as update_error:
        print(f"Error updating news article with stock mentions: {str(update_error)}")

    # Process events if needed
    created_events = []
    if stock_mentions:
        all_mentioned_names = [m['mentioned_name'] for m in stock_mentions]
        all_stock_companies = [m['stock_company'] for m in stock_mentions]
        batch_size = 7
        for i in range(0, len(all_mentioned_names), batch_size):
            batch_mentioned_stocks = all_mentioned_names[i:i+batch_size]
            batch_is_verified_stocks = all_stock_companies[i:i+batch_size]
            try:
                batch_events = detect_and_create_events(news_article, batch_mentioned_stocks, batch_is_verified_stocks)
                created_events.extend(batch_events)
            except Exception as event_error:
                print(f"Error creating events for batch: {str(event_error)}")
            
        print(f"Processed {len(all_mentioned_names)} mentions in batches of {batch_size}")
    else:
        print(f"No stock mentions detected for article: {article_url}. Skipping event detection.")

    print(f"Successfully processed article: {article_url}. Updated with {len(stock_mentions)} mentions and created {len(created_events)} events.")
    return news_article, created_events