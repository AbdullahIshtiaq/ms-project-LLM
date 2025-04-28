import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
import json
from datetime import datetime
from news_analyzer.stock_data import StockData
from news_analyzer.llm_client import OpenRouterClient



# # Initialize OpenRouterClient
client = OpenRouterClient(api_key="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")
# Initialize StockData
stock_data = StockData()

def analyze_sentiment(article, stock_companies, model_name="deepseek"):
    """Process a news article to extract stock mentions and events.
    
    Args:
        article_id: Article ID
        article_data: Article data
    """
    try:
        mentioned_stocks_str = ', '.join(stock_companies)
        title = article['title']
        article_text = article['content']  # Changed from article.content to article.content

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
            print("model_name: ", model_name)
            result = client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model_name=model_name,
                    # temperature=0.7
                )
            print("Analyze Result: ", result)

            # Extract the content from the result
            if isinstance(result, dict) and 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                # Extract JSON from the content (it might be wrapped in ```json ... ```)
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content.strip()
                
                # Parse the JSON string
                parsed_result = json.loads(json_str)
                
                # Check if the result is valid
                if not isinstance(parsed_result, dict) or 'sentiment' not in parsed_result:
                    print("Invalid response format. Expected a dictionary with 'sentiment' key.")
                    return []
                # Check if the sentiment is valid
                if parsed_result['sentiment'] not in ['very positive', 'positive', 'slightly positive', 'neutral', 'slightly negative', 'negative', 'very negative']:
                    print("Invalid sentiment value.")
                    return []
                # Check if the importance is valid
                if parsed_result['importance'].upper() not in ['CRITICAL', 'IMPORTANT', 'REGULAR']:
                    print("Invalid importance value.")
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
        
                return [
                    {
                        'importance': parsed_result['importance'],
                        'company_name': parsed_result['company_name'],
                        'description': parsed_result['summary'],
                        'sentiment': sentiment_map.get(parsed_result['sentiment'].lower(), 'N'),
                        'reasons': parsed_result['reasons'],
                    }
                ]
            else:
                print("Invalid response format from LLM.")
                return []
        except Exception as e:
            print(f"Error processing article: {e}")
            return []
        
    except Exception as e:
        print(f"Error in analyze_sentiment: {e}")
        return []
                

def fetch_eodhd_news(api_token, limit=1000, offset=0):
    """
    Fetch news from EODHD API
    """
    url = f"https://eodhd.com/api/news?offset={offset}&limit={limit}&api_token={api_token}&fmt=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching news: {response.status_code}")
        return None

def save_news_to_json(news_data, filename="eodhd_news.json"):
    """
    Save news data to JSON file
    """
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(news_data, file, indent=4, ensure_ascii=False)
    print(f"News data saved to {filename}")
    return filename

def get_overall_sentiment(sentiment_data):
    """
    Extract a simpler overall sentiment from the EODHD sentiment data
    """
    if sentiment_data['polarity'] >= 0.7:
        return 'VP'  # Very Positive
    elif sentiment_data['polarity'] >= 0.3:
        return 'P'   # Positive
    elif sentiment_data['polarity'] >= 0.1:
        return 'SP'  # Slightly Positive
    elif sentiment_data['polarity'] > -0.1:
        return 'N'   # Neutral
    elif sentiment_data['polarity'] > -0.3:
        return 'SN'  # Slightly Negative
    elif sentiment_data['polarity'] > -0.7:
        return 'NG'  # Negative
    else:
        return 'VN'  # Very Negative


def compare_sentiments(eodhd_news):
    """
    Compare EODHD sentiments with our sentiment analyzer results
    """
    results = []
    
    for article in eodhd_news:
        print(f"Processing article: {article['title'][:50]}...")
        
        # Get EODHD sentiment
        eodhd_sentiment = get_overall_sentiment(article['sentiment'])

        model_list = [
            "deepseek",
            "gemini",
            "llama4",
            "gpt4_mini",
        ]
        
        deepseek_result = None
        gemini_result = None
        llama4_result = None
        gpt4_mini_result = None


        # Process with our sentiment analyzer
        for model_name in model_list:
            processor_sentiments_list = analyze_sentiment(article, article['symbols'], model_name)

            # If no sentiments were returned, skip this article
            if not processor_sentiments_list:
                print("No processor sentiments returned for this article.")
                continue

            processor_sentiments_list = processor_sentiments_list[0]  # Assuming we only need the first result

            if model_name == "deepseek":
                deepseek_result = processor_sentiments_list
            elif model_name == "gemini":
                gemini_result = processor_sentiments_list
            elif model_name == "llama4":
                llama4_result = processor_sentiments_list
            elif model_name == "gpt4_mini":
                gpt4_mini_result = processor_sentiments_list
            else:
                print(f"Unknown model name: {model_name}")
                continue
        
        # Compare results
        result = {
            'title': article['title'],
            'symbols': article['symbols'],
            'eodhd_sentiment': eodhd_sentiment,
            'eodhd_sentiment_data': article['sentiment'],
            'deepseek_sentiment': {
                'sentiment': deepseek_result['sentiment'] if deepseek_result else None,
                'importance': deepseek_result['importance'] if deepseek_result else None,  
                'company_name': deepseek_result['company_name'] if deepseek_result else None,
                'description': deepseek_result['description'] if deepseek_result else None,
                'reasons': deepseek_result['reasons'] if deepseek_result else None,
                'match': deepseek_result['sentiment'] == eodhd_sentiment if deepseek_result else None,
            },
            'gemini_sentiment': {
                'sentiment': gemini_result['sentiment'] if gemini_result else None,
                'importance': gemini_result['importance'] if gemini_result else None,  
                'company_name': gemini_result['company_name'] if gemini_result else None,
                'description': gemini_result['description'] if gemini_result else None,
                'reasons': gemini_result['reasons'] if gemini_result else None,
                'match': gemini_result['sentiment'] == eodhd_sentiment if gemini_result else None,
            },
            'llama4_sentiment': {
                'sentiment': llama4_result['sentiment'] if llama4_result else None,
                'importance': llama4_result['importance'] if llama4_result else None,  
                'company_name': llama4_result['company_name'] if llama4_result else None,
                'description': llama4_result['description'] if llama4_result else None,
                'reasons': llama4_result['reasons'] if llama4_result else None, 
                'match': llama4_result['sentiment'] == eodhd_sentiment if llama4_result else None,
            },
            'gpt4_mini_sentiment': {
                'sentiment': gpt4_mini_result['sentiment'] if gpt4_mini_result else None,
                'importance': gpt4_mini_result['importance'] if gpt4_mini_result else None,  
                'company_name': gpt4_mini_result['company_name'] if gpt4_mini_result else None,
                'description': gpt4_mini_result['description'] if gpt4_mini_result else None,
                'reasons': gpt4_mini_result['reasons'] if gpt4_mini_result else None,
                'match': gpt4_mini_result['sentiment'] == eodhd_sentiment if gpt4_mini_result else None,
            },

        }
        
        results.append(result)
    
    return results

def validate_sentiments(chached=False):
    """
    Main function to run the validation
    """
    # Replace with your actual API token
    api_token = "6808079edd73e5.58079457"
    
    # Fetch news
    print("Fetching news from EODHD API...")
    if chached:
        # Load from cached file
        print("Loading cached news data...")
        with open('eodhd_news.json', 'r', encoding='utf-8') as file:
            news_data = json.load(file)
    else:
        news_data = fetch_eodhd_news(api_token)
            # Save to JSON
        news_file = save_news_to_json(news_data)
    
    if not news_data:
        print("Failed to fetch news data.")
        return
    
    print(f"Successfully fetched {len(news_data)} news articles")
    
    # for now first 10 articles  
    # Compare sentiments
    print("Comparing sentiments...")
    comparison_results = compare_sentiments(news_data[:10])

    results_file = f"sentiment_comparison.json"
    
    with open(results_file, 'w', encoding='utf-8') as file:
        json.dump(comparison_results, file, indent=4, ensure_ascii=False)
    
    print(f"Comparison results saved to {results_file}")
    
    # Calculate statistics
    total = len(comparison_results)
    # matches = sum(1 for r in comparison_results if r['match'])
    deepseek_matches = sum(1 for r in comparison_results if r['deepseek_sentiment']['match'])
    gemini_matches = sum(1 for r in comparison_results if r['gemini_sentiment']['match'])
    llama4_matches = sum(1 for r in comparison_results if r['llama4_sentiment']['match'])
    gpt4_mini_matches = sum(1 for r in comparison_results if r['gpt4_mini_sentiment']['match'])
    matches = deepseek_matches + gemini_matches + llama4_matches # + gpt4_mini_matches
    print(f"Total articles processed: {total}")
    print(f"DeepSeek sentiment match rate: {deepseek_matches}/{total} ({deepseek_matches/total*100:.2f}%)")
    print(f"Gemini sentiment match rate: {gemini_matches}/{total} ({gemini_matches/total*100:.2f}%)")
    print(f"Llama4 sentiment match rate: {llama4_matches}/{total} ({llama4_matches/total*100:.2f}%)")
    print(f"GPT4 Mini sentiment match rate: {gpt4_mini_matches}/{total} ({gpt4_mini_matches/total*100:.2f}%)")
    # Overall sentiment match rate  
    matches = sum(1 for r in comparison_results if r['deepseek_sentiment']['match'] or r['gemini_sentiment']['match'] or r['llama4_sentiment']['match'] or r['gpt4_mini_sentiment']['match'])
    # matches = sum(1 for r in comparison_results if r['deepseek_sentiment']['match'] or r['gemini_sentiment']['match'] or r['llama4_sentiment']['match'])
    
    print(f"Sentiment match rate: {matches}/{total} ({matches/total*100:.2f}%)")
    
    # Get overall sentiment distribution
    eodhd_sentiments = {}
    deepseek_sentiments = {}
    gemini_sentiments = {}
    llama4_sentiments = {}
    gpt4_mini_sentiments = {}
    
    for result in comparison_results:
        eodhd_sent = result['eodhd_sentiment']
        deepseek_sent = result['deepseek_sentiment']['sentiment'] if result['deepseek_sentiment']['sentiment'] else 'N/A'
        gemini_sent = result['gemini_sentiment']['sentiment'] if result['gemini_sentiment']['sentiment'] else 'N/A'
        llama4_sent = result['llama4_sentiment']['sentiment'] if result['llama4_sentiment']['sentiment'] else 'N/A'
        gpt4_mini_sent = result['gpt4_mini_sentiment']['sentiment'] if result['gpt4_mini_sentiment']['sentiment'] else 'N/A'
        
        eodhd_sentiments[eodhd_sent] = eodhd_sentiments.get(eodhd_sent, 0) + 1
        deepseek_sentiments[deepseek_sent] = deepseek_sentiments.get(deepseek_sent, 0) + 1
        gemini_sentiments[gemini_sent] = gemini_sentiments.get(gemini_sent, 0) + 1
        llama4_sentiments[llama4_sent] = llama4_sentiments.get(llama4_sent, 0) + 1
        gpt4_mini_sentiments[gpt4_mini_sent] = gpt4_mini_sentiments.get(gpt4_mini_sent, 0) + 1
    
    print("\nEODHD Sentiment Distribution:")
    for sent, count in eodhd_sentiments.items():
        print(f"{sent}: {count} ({count/total*100:.2f}%)")
    
    print("\nDeepSeek Sentiment Distribution:")
    for sent, count in deepseek_sentiments.items():
        print(f"{sent}: {count} ({count/total*100:.2f}%)")
        
    print("\nGemini Sentiment Distribution:")
    for sent, count in gemini_sentiments.items():
        print(f"{sent}: {count} ({count/total*100:.2f}%)")
        
    print("\nLlama4 Sentiment Distribution:")
    for sent, count in llama4_sentiments.items():
        print(f"{sent}: {count} ({count/total*100:.2f}%)")

    print("\nGPT4 Mini Sentiment Distribution:")
    for sent, count in gpt4_mini_sentiments.items():
        print(f"{sent}: {count} ({count/total*100:.2f}%)")

if __name__ == "__main__":
    validate_sentiments(chached=True)





