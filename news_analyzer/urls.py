from django.urls import path
from . import views

app_name = 'news_analyzer'

urlpatterns = [
    path('scrape_and_analyze/', views.scrape_and_analyze, name='scrape_news'),
    path('', views.home, name='home'),
    path('articles/', views.articles, name='articles'),
    path('get_articles/', views.get_articles, name='get_articles'),
    path('validation/', views.validation_results, name='validation_results'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
] 