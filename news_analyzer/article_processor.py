import json
import hashlib
from datetime import datetime
from .utils import get_final_stock, clean_text
from .stock_data import StockData
from .llm_client import OpenRouterClient

# # Initialize OpenRouterClient
client = OpenRouterClient(api_key="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")


from .models import NewsArticle, StockCompany, NewsSentiment

# Initialize StockData
stock_data = StockData()

def analyze_sentiment(article, mentioned_stocks, stock_companies):
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
Today is {datetime.now().strftime("%B %d, %Y")}.  
Analyze the following financial news article carefully. Based on Loughran-McDonald financial sentiment categories, determine the **overall sentiment** of the article as it relates to the companies mentioned: {mentioned_stocks_str}. Choose one of:
- very positive  
- positive  
- slightly positive  
- neutral  
- slightly negative  
- negative  
- very negative  

Also assign an **importance** level—CRITICAL, IMPORTANT, or REGULAR—based on how material the news is to the company's prospects.  

Then, provide:
1. **company_name**: which company this analysis refers to (one of {mentioned_stocks_str})  
2. **summary**: a brief, standalone summary in fluent English (like a headline or very short news snippet), naming the company and key facts  
3. **reasons**: a list of concise lines explaining why you chose that sentiment (can be multiple)

Respond **only** in this JSON format (valid and properly escaped):
{{
  "sentiment": "…",
  "importance": "…",
  "company_name": "…",
  "summary": "…",
  "reasons": [
    "Reason 1: very concise explanation",
    "Reason 2: another short explanation",
    "Reason 3: etc."
  ]
}}

Article Title:
{title}

Article:
{article_text}
        """
        try:
            # Use LangChain for local inference
            try:
                # result = ollama_llm.invoke(prompt)
                result = client.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        model_name="deepseek",
                        # temperature=0.7
                    )
                print("analyze_sentiment Result: ", result)
                
                # Extract the content from the OpenRouter API response
                if isinstance(result, dict) and 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Clean up the response by removing any non-JSON content
                    if isinstance(content, str):
                        # Find the first occurrence of a JSON-like structure
                        json_start = content.find('{')
                        if json_start != -1:
                            content = content[json_start:]
                        # Find the last occurrence of a closing brace
                        json_end = content.rfind('}')
                        if json_end != -1:
                            content = content[:json_end + 1]
                    
                    parsed_result = json.loads(content)
                else:
                    print("Invalid response format from OpenRouter API")
                    return []
            except Exception as e:
                print(f"Error calling OpenRouter API: {str(e)}")
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
            

            # save result to NewsSentiment 

            news_sentiment = NewsSentiment.objects.create(
                article=article,
                mentioned_stock_name=mentioned_stocks_str,
                importance=parsed_result.get('importance', 'REGULAR'),
                summary=parsed_result.get('summary', ''),
                sentiment=sentiment_map.get(parsed_result.get('sentiment'), None),
                reason='; '.join(parsed_result.get('reasons', []))
            )

            news_article = NewsArticle.objects.get(id=article.id)
            news_article.analyzed = True
            news_article.analyzed_at = datetime.now()
            news_article.save()
            # Add many-to-many relationships for stock symbols
            for stock in stock_companies:
                try:
                    stock_company = StockCompany.objects.get(symbol=stock)
                    news_sentiment.stock_symbol.add(stock_company)
                except StockCompany.DoesNotExist:
                    print(f"Stock company not found: {stock}")
            print(f"Created news sentiment: {news_sentiment.id} for article: {article.id}")

            # Save the sentiment object
            news_sentiment.save()
            # Return the created sentiment object
            return news_sentiment
        except Exception as e:  
            print(f"Error processing sentiment: {str(e)}")
            return {}
    except Exception as e:
        print(f"Error in analyze_sentiment: {str(e)}")
        return {}


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
    
    IMPORTANT: The key in your response MUST be "mentions" (plural), not "mention" (singular).
    """

    # Use LangChain for local inference
    try:
        # result = ollama_llm.invoke(prompt)
        result = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model_name="deepseek",
            # temperature=0.7
        )
        print("CREATE STOCK NEWS Result: ", result)
        
        # Extract the content from the OpenRouter API response
        if isinstance(result, dict) and 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            
            # Clean up the response by removing any non-JSON content
            if isinstance(content, str):
                # Find the first occurrence of a JSON-like structure
                json_start = content.find('{')
                if json_start != -1:
                    content = content[json_start:]
                # Find the last occurrence of a closing brace
                json_end = content.rfind('}')
                if json_end != -1:
                    content = content[:json_end + 1]
            
            parsed_result = json.loads(content)
            print(f"Parsed result: {parsed_result}")
        else:
            print("Invalid response format from OpenRouter API")
            parsed_result = {"mentions": []}
    except Exception as e:
        print(f"Error calling OpenRouter API: {str(e)}")
        parsed_result = {"mentions": []}

    stock_mentions = []

    # Handle both "mention" and "mentions" keys
    mentions_list = []
    if 'mentions' in parsed_result:
        mentions_list = parsed_result['mentions']
    elif 'mention' in parsed_result:
        mentions_list = parsed_result['mention']
    
    for mention in mentions_list:
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

    result = analyze_sentiment(news_article, [m['mentioned_name'] for m in stock_mentions], [m['stock_company'] for m in stock_mentions])
    if result:
        print(f"Created {result} stock events for article: {news_article.id}")
    else:
        print("No stock events created")
    return news_article, result