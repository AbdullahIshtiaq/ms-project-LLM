from django.shortcuts import render
from .scraper import scrape_lse_news

# Create your views here.

async def scrape_news_view(request):
    # try:
    # Run the scraping function
    news_items = await scrape_lse_news()
    return render(request, 'news_analyzer/news_list.html', {'news_items': news_items})
    # except Exception as e:
    #     print(f"Error in scrape_news_view: {str(e)}")
    #     return render(request, 'news_analyzer/news_list.html', {'error': str(e), 'news_items': []})
