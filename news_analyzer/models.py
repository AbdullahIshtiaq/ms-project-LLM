from django.db import models

class StockCompany(models.Model):
    symbol = models.CharField(max_length=20, unique=True, primary_key=True)  # Increased from 10 to 20
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.symbol
    


    def get_short_name(self):
        # First, try to retrieve the short stock name related to this company
        stock_name = self.stockname_set.filter(name_type="short").first()
        # If no short name exists, get any name available
        if not stock_name:
            stock_name = self.stockname_set.first()
        # Return the name if it exists, or the symbol if no names are available
        return stock_name.name if stock_name else self.symbol

class StockName(models.Model):
    stock_symbol = models.ForeignKey(StockCompany, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    name_type = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name
    
class NewsArticle(models.Model):
    url = models.URLField(unique=True, null=True)
    title = models.CharField(max_length=255, null=True)
    full_text = models.TextField()
    news_hash = models.CharField(max_length=64)
    publication_date = models.DateTimeField(null=True)
    stock_mentions = models.JSONField(default=list)  # Store mentions as a list of dicts
    created_at = models.DateTimeField(auto_now_add=True)  


class StockEvent(models.Model):
    EVENT_TYPES = [
        ('FINANCIAL_REPORT', 'Financial Report'),
        ('DIVIDEND_ANNOUNCEMENT', 'Dividend Announcement'),
        ('STOCK_SPLIT', 'Stock Split'),
        ('MERGER_ACQUISITION', 'Merger or Acquisition'),
        ('MANAGEMENT_CHANGE', 'Management Change'),
        ('NEW_LISTING', 'New Listing'),
        ('DELISTING', 'Delisting'),
        ('REGULATORY_ACTION', 'Regulatory Action'),
        ('PRODUCT_LAUNCH', 'Major Product Launch'),
        ('PARTNERSHIP', 'Strategic Partnership'),
        ('LEGAL_ISSUE', 'Legal Issue or Lawsuit'),
        ('MARKET_EXPANSION', 'Market Expansion'),
        ('RESTRUCTURING', 'Company Restructuring'),
        ('EARNINGS_SURPRISE', 'Significant Earnings Surprise'),
        ('INSIDER_TRADING', 'Significant Insider Trading'),
        ('ANALYST_RATING_CHANGE', 'Major Analyst Rating Change'),
        ('OTHER', 'Other Important Event'),
    ]

    SENTIMENT_CHOICES = [
        ('VP', 'Very Positive'),
        ('P', 'Positive'),
        ('SP', 'Slightly Positive'),
        ('N', 'Neutral'),
        ('SN', 'Slightly Negative'),
        ('NG', 'Negative'),
        ('VN', 'Very Negative'),
    ]

    IMPORTANCE_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('IMPORTANT', 'Important'),
        ('REGULAR', 'Regular'),
    ]

    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='events_old')
    stock_symbol = models.ForeignKey(StockCompany, on_delete=models.CASCADE, null=True, blank=True, related_name='events')
    stock_name = models.CharField(max_length=255, null=True, blank=True)
    mentioned_stock_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=25, choices=EVENT_TYPES)
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='REGULAR')
    description = models.TextField()
    sentiment = models.CharField(max_length=2, choices=SENTIMENT_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_event_type_display()} for {self.mentioned_stock_name}"