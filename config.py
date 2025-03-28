import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# News sources
NEWS_SOURCES = {
    'bbc': 'https://www.bbc.co.uk/news/business',
    'ft': 'https://www.ft.com',
    'reuters': 'https://www.reuters.com/business',
    'yahoo_finance': 'https://finance.yahoo.com/news'
}

# Stock data configuration
STOCK_HISTORY_PERIOD = '6mo'  # 6 months of historical data

# Sentiment analysis
SENTIMENT_PROMPT_TEMPLATE = """
Analyze the sentiment of the following financial news article about {stock_symbol} ({company_name}):

Article Title: {title}
Article Content: {content}
Publication Date: {date}

Current stock price: {current_price}
52-week high: {year_high}
52-week low: {year_low}

Based on this information:
1. Determine if the sentiment is positive, negative, or neutral for the stock
2. Rate the importance of this news (scale 1-10)
3. Provide a brief explanation of your analysis
4. Estimate potential impact on stock price

Output in JSON format with fields: sentiment, importance, explanation, potential_impact
""" 