import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

class ReportGenerator:
    def __init__(self):
        self.output_dir = 'reports'
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Set up Jinja2 environment
        self.template_env = Environment(loader=FileSystemLoader('templates'))
        self.template = self.template_env.get_template('report_template.html')
    
    def generate_pdf(self, data):
        """Generate a PDF report from the analyzed data using HTML template and Playwright"""
        stock_info = data.get('stock_info', {})
        sentiment_results = data.get('sentiment_results', [])
        
        # Count sentiments
        sentiments = [r['sentiment_analysis'].get('sentiment', 'unknown') for r in sentiment_results]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        
        # Generate overall sentiment
        if positive_count > negative_count:
            overall_sentiment = "Overall Positive"
        elif negative_count > positive_count:
            overall_sentiment = "Overall Negative"
        else:
            overall_sentiment = "Overall Neutral"
        
        # Prepare template data
        template_data = {
            'stock_info': stock_info,
            'sentiment_results': sentiment_results,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'overall_sentiment': overall_sentiment
        }
        
        # Render HTML
        html_content = self.template.render(**template_data)
        
        # Define file paths
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join(self.output_dir, f"report_{stock_info.get('symbol', 'stock')}_{timestamp}.html")
        pdf_path = os.path.join(self.output_dir, f"financial_report_{stock_info.get('symbol', 'stock')}_{timestamp}.pdf")
        
        # Save HTML file (useful for debugging)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML to PDF using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{os.path.abspath(html_path)}")
            page.pdf(path=pdf_path, format="A4")
            browser.close()
        
        return pdf_path 