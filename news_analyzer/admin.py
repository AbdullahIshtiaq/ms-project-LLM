from django.contrib import admin
from .models import StockCompany, StockName, NewsArticle, NewsSentiment

@admin.register(StockCompany)
class StockCompanyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'created_at', 'updated_at')
    search_fields = ('symbol',)
    ordering = ('symbol',)

@admin.register(StockName)
class StockNameAdmin(admin.ModelAdmin):
    list_display = ('stock_symbol', 'name', 'name_type')
    search_fields = ('name', 'stock_symbol__symbol')
    list_filter = ('name_type',)
    ordering = ('stock_symbol', 'name')

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'created_at')
    search_fields = ('title', 'full_text')
    list_filter = ('publication_date',)
    ordering = ('-publication_date',)

@admin.register(NewsSentiment)
class NewsSentimentAdmin(admin.ModelAdmin):
    list_display = ('mentioned_stock_name', 'importance', 'sentiment', 'created_at')
    search_fields = ('mentioned_stock_name', 'description')
    list_filter = ('importance', 'sentiment')
    ordering = ('-created_at',)


    
