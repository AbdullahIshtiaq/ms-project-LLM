"""Mock data for testing when Yahoo Finance API is unavailable"""

def get_mock_stock_info(symbol):
    """Get mock stock info for testing"""
    mock_data = {
        'INVALID': {
            'symbol': 'UNKNOWN',
            'company_name': 'Unknown Company',
            'sector': 'Unknown',
            'industry': 'Unknown',
            'current_price': 100.00,
            'previous_close': 100.00,
            'open': 100.00,
            'day_high': 100.00,
            'day_low': 100.00,
            'year_high': 120.00,
            'year_low': 80.00,
            'market_cap': 1000000000,
            'volume': 1000000,
            'pe_ratio': 20.00,
            'dividend_yield': 1.0,
            'description': 'This is mock data for an invalid symbol.'
        },
        'AAPL': {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'current_price': 175.34,
            'previous_close': 174.23,
            'open': 174.56,
            'day_high': 176.82,
            'day_low': 173.95,
            'year_high': 198.23,
            'year_low': 142.18,
            'market_cap': 2750000000000,
            'volume': 65432100,
            'pe_ratio': 28.76,
            'dividend_yield': 0.54,
            'description': 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.'
        },
        'MSFT': {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'industry': 'Software—Infrastructure',
            'current_price': 378.92,
            'previous_close': 377.85,
            'open': 378.10,
            'day_high': 380.25,
            'day_low': 376.98,
            'year_high': 390.68,
            'year_low': 272.05,
            'market_cap': 2820000000000,
            'volume': 23456700,
            'pe_ratio': 36.89,
            'dividend_yield': 0.72,
            'description': 'Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.'
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'sector': 'Technology',
            'industry': 'Internet Content & Information',
            'current_price': 139.87,
            'previous_close': 138.56,
            'open': 138.90,
            'day_high': 140.34,
            'day_low': 138.45,
            'year_high': 142.68,
            'year_low': 89.42,
            'market_cap': 1780000000000,
            'volume': 25678900,
            'pe_ratio': 26.45,
            'dividend_yield': 0,
            'description': 'Alphabet Inc. offers various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.'
        }
    }
    
    # Return data for the requested symbol, or a default if not found
    return mock_data.get(symbol, {
        'symbol': symbol,
        'company_name': f'{symbol} Inc.',
        'sector': 'Unknown',
        'industry': 'Unknown',
        'current_price': 100.00,
        'previous_close': 99.50,
        'open': 99.75,
        'day_high': 101.25,
        'day_low': 99.25,
        'year_high': 120.00,
        'year_low': 80.00,
        'market_cap': 10000000000,
        'volume': 1000000,
        'pe_ratio': 20.00,
        'dividend_yield': 1.5,
        'description': f'Mock data for {symbol}.'
    })

def get_mock_news_articles(symbol, count=5):
    """Get mock news articles for testing"""
    # General financial news articles (not tied to specific stocks)
    general_financial_news = [
        {
            'title': 'Market Rebounds After Recent Selloff',
            'url': 'https://example.com/market-rebound',
            'date': '2023-03-12',
            'source': 'Financial News Today',
            'content': 'Markets showed signs of recovery today after last week\'s selloff, with technology stocks leading the charge. Analysts point to strong economic data and renewed optimism about inflation control as key factors driving the rebound. Apple (AAPL) and Microsoft (MSFT) were among the top performers.',
            'related_symbol': None
        },
        {
            'title': 'Fed Signals Potential Rate Cut Later This Year',
            'url': 'https://example.com/fed-signals',
            'date': '2023-03-10',
            'source': 'Economic Times',
            'content': 'The Federal Reserve has indicated it may consider rate cuts later this year if inflation continues to trend downward. This news sent stocks higher as investors anticipated improved conditions for growth-oriented companies like Amazon (AMZN) and Tesla (TSLA).',
            'related_symbol': None
        },
        {
            'title': 'Tech Sector Leads Market Rally Amid AI Optimism',
            'url': 'https://example.com/tech-sector-rally',
            'date': '2023-03-14',
            'source': 'Tech Investor Daily',
            'content': 'The technology sector led a broad market rally today as investors remain optimistic about AI development prospects. Nvidia (NVDA) shares jumped 4% after announcing new AI chip advancements, while Google parent Alphabet (GOOGL) gained 2.5% on news of AI integration across its services.',
            'related_symbol': None
        },
        {
            'title': 'Oil Prices Stabilize Following Supply Concerns',
            'url': 'https://example.com/oil-stabilizes',
            'date': '2023-03-13',
            'source': 'Energy Market Watch',
            'content': 'Oil prices stabilized today after volatile trading last week caused by concerns over global supply. Energy stocks like Exxon Mobil (XOM) and Chevron (CVX) saw modest gains as analysts predicted more balanced markets in the coming months.',
            'related_symbol': None
        },
        {
            'title': 'Retail Sales Data Exceeds Expectations, Boosting Consumer Stocks',
            'url': 'https://example.com/retail-sales-data',
            'date': '2023-03-11',
            'source': 'Market Insights',
            'content': 'The latest retail sales data showed stronger-than-expected consumer spending, pushing consumer discretionary stocks higher. Amazon (AMZN) and Walmart (WMT) were standout performers as analysts upgraded their revenue forecasts for the quarter.',
            'related_symbol': None
        },
        {
            'title': 'Banking Sector Stabilizes After Recent Volatility',
            'url': 'https://example.com/banking-stabilizes',
            'date': '2023-03-09',
            'source': 'Financial Sector News',
            'content': 'The banking sector showed signs of stabilization today following recent volatility. JPMorgan Chase (JPM) and Bank of America (BAC) led the gains after positive comments from regulatory officials regarding the sector\'s overall health.',
            'related_symbol': None
        },
        {
            'title': 'Semiconductor Shortage Easing, Industry Reports',
            'url': 'https://example.com/semiconductor-shortage',
            'date': '2023-03-08',
            'source': 'Tech Supply Chain News',
            'content': 'Industry reports suggest the global semiconductor shortage is gradually easing, which could benefit technology and automotive manufacturers. Intel (INTC) and AMD (AMD) shares rose on expectations of improved production capacity.',
            'related_symbol': None
        }
    ]
    
    common_articles = [
        {
            'title': 'Market Rebounds After Recent Selloff',
            'url': 'https://example.com/market-rebound',
            'date': '2023-03-12',
            'source': 'Financial News Today',
            'content': 'Markets showed signs of recovery today after last week\'s selloff, with technology stocks leading the charge. Analysts point to strong economic data and renewed optimism about inflation control as key factors driving the rebound.',
            'related_symbol': 'MARKET'
        },
        {
            'title': 'Fed Signals Potential Rate Cut Later This Year',
            'url': 'https://example.com/fed-signals',
            'date': '2023-03-10',
            'source': 'Economic Times',
            'content': 'The Federal Reserve has indicated it may consider rate cuts later this year if inflation continues to trend downward. This news sent stocks higher as investors anticipated improved conditions for growth-oriented companies.',
            'related_symbol': 'FED'
        }
    ]
    
    # If the symbol is "GENERAL", return general financial news
    if symbol == "GENERAL":
        return general_financial_news[:count]
        
    # Rest of the function remains the same for specific stock symbols
    symbol_specific_articles = {
        'AAPL': [
            {
                'title': 'Apple Unveils New iPhone with Revolutionary AI Features',
                'url': 'https://example.com/apple-new-iphone',
                'date': '2023-03-15',
                'source': 'Tech Insider',
                'content': 'Apple Inc. announced its newest iPhone model featuring advanced AI capabilities that transform how users interact with their devices. The new model is expected to drive significant upgrade demand among existing iPhone users.',
                'related_symbol': 'AAPL'
            },
            {
                'title': 'Apple\'s Services Revenue Hits All-Time High',
                'url': 'https://example.com/apple-services',
                'date': '2023-03-11',
                'source': 'Market Watch',
                'content': 'Apple reported that its services division, which includes Apple Music, iCloud, and the App Store, has reached record revenue levels. This diversification beyond hardware sales has been viewed positively by investors looking for recurring revenue streams.',
                'related_symbol': 'AAPL'
            },
            {
                'title': 'Supply Chain Issues Continue to Impact Apple Production',
                'url': 'https://example.com/apple-supply-chain',
                'date': '2023-03-08',
                'source': 'Bloomberg',
                'content': 'Ongoing global supply chain constraints are affecting Apple\'s production capacity for several key products. The company is working to diversify its manufacturing base but expects some impact on availability for the upcoming quarter.',
                'related_symbol': 'AAPL'
            }
        ],
        'MSFT': [
            {
                'title': 'Microsoft Cloud Revenue Surpasses Expectations',
                'url': 'https://example.com/microsoft-cloud',
                'date': '2023-03-14',
                'source': 'Tech Report',
                'content': 'Microsoft\'s cloud services division, Azure, reported growth exceeding analyst expectations. The strong performance highlights the company\'s successful transition to cloud-based revenue streams.',
                'related_symbol': 'MSFT'
            },
            {
                'title': 'Microsoft Expands AI Integration Across Product Suite',
                'url': 'https://example.com/microsoft-ai',
                'date': '2023-03-09',
                'source': 'AI Today',
                'content': 'Microsoft announced expanded AI features across its Office 365 and Windows platforms. These enhancements are expected to improve productivity and maintain Microsoft\'s competitive edge in the enterprise software market.',
                'related_symbol': 'MSFT'
            },
            {
                'title': 'Microsoft Gaming Division Shows Strong Growth Post-Acquisition',
                'url': 'https://example.com/microsoft-gaming',
                'date': '2023-03-07',
                'source': 'Gaming Industry News',
                'content': 'Following strategic acquisitions in the gaming sector, Microsoft\'s gaming division is showing robust growth. The expansion of Game Pass subscriptions has created a stable recurring revenue stream for the company.',
                'related_symbol': 'MSFT'
            }
        ],
        'GOOGL': [
            {
                'title': 'Google\'s Ad Revenue Bounces Back After Industry-Wide Slowdown',
                'url': 'https://example.com/google-ad-revenue',
                'date': '2023-03-13',
                'source': 'Digital Marketing Today',
                'content': 'Alphabet reported that Google\'s advertising revenue has recovered faster than expected following the recent industry slowdown. The company attributes this to improved targeting algorithms and new ad formats.',
                'related_symbol': 'GOOGL'
            },
            {
                'title': 'Google Cloud Gains Market Share in Enterprise Segment',
                'url': 'https://example.com/google-cloud',
                'date': '2023-03-10',
                'source': 'Cloud Computing News',
                'content': 'Google Cloud Platform has reported significant gains in the enterprise segment, challenging the dominance of AWS and Azure. Analysts note that Google\'s AI capabilities are proving to be a key differentiator in attracting corporate clients.',
                'related_symbol': 'GOOGL'
            },
            {
                'title': 'Regulatory Concerns Persist for Google\'s Ad Business',
                'url': 'https://example.com/google-regulatory',
                'date': '2023-03-06',
                'source': 'Regulation Watch',
                'content': 'Google continues to face regulatory scrutiny regarding its dominant position in online advertising. While no immediate action is expected, investors remain concerned about potential future restrictions on the company\'s core business model.',
                'related_symbol': 'GOOGL'
            }
        ]
    }
    
    # Get symbol-specific articles or generic ones for unknown symbols
    specific_articles = symbol_specific_articles.get(symbol, [
        {
            'title': f'{symbol} Reports Better Than Expected Earnings',
            'url': f'https://example.com/{symbol.lower()}-earnings',
            'date': '2023-03-14',
            'source': 'Financial Review',
            'content': f'{symbol} announced quarterly results that exceeded analyst expectations, with revenue growing by 15% year-over-year. The company also raised its guidance for the upcoming fiscal year.',
            'related_symbol': symbol
        },
        {
            'title': f'{symbol} Expands Into New Markets',
            'url': f'https://example.com/{symbol.lower()}-expansion',
            'date': '2023-03-11',
            'source': 'Business Insider',
            'content': f'{symbol} is expanding its operations into emerging markets, with a particular focus on Southeast Asia and Latin America. Analysts view this move as potentially opening significant new revenue streams.',
            'related_symbol': symbol
        },
        {
            'title': f'Analyst Upgrades {symbol} to "Buy" Rating',
            'url': f'https://example.com/{symbol.lower()}-upgrade',
            'date': '2023-03-09',
            'source': 'Market Analysis',
            'content': f'Several major investment firms have upgraded {symbol} to a "Buy" rating, citing improved growth prospects and attractive valuation. The stock saw increased trading volume following these recommendations.',
            'related_symbol': symbol
        }
    ])
    
    # Combine and limit to requested count
    all_articles = specific_articles + common_articles
    return all_articles[:count] 