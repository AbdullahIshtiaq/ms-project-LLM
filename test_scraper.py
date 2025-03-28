from modules.news_scraper import NewsScraper

def main():
    print("Initializing scraper...")
    scraper = NewsScraper()
    
    print("Attempting to fetch news articles...")
    articles = scraper.get_financial_news(limit=3)
    
    print(f"Found {len(articles)} articles")
    
    if articles:
        print("\nArticle titles:")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            
        print("\nExtracting symbols...")
        articles_with_symbols = scraper.extract_symbols(articles)
        print(f"Found {len(articles_with_symbols)} articles with identifiable stock symbols")
        
        if articles_with_symbols:
            print("\nIdentified symbols:")
            for i, article in enumerate(articles_with_symbols, 1):
                print(f"{i}. {article['title']} -> {article['related_symbol']}")

if __name__ == "__main__":
    main() 