from django.core.management.base import BaseCommand
from news_analyzer.fetch_lse_stocks import update_lse_stocks
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Fetches stock information from the Marketstack API for London Stock Exchange stocks'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, help='Marketstack API key (optional)')

    def handle(self, *args, **options):
        # Check if API key is provided via command line
        api_key = options.get('api_key')
        
        # If not provided via command line, check environment variable
        if not api_key:
            api_key = os.environ.get('MARKETSTACK_API_KEY')
            
        # If still not found, check Django settings
        if not api_key:
            try:
                api_key = getattr(settings, 'MARKETSTACK_API_KEY', '3bf4300a992feb65986ce192e7038d8a')
            except AttributeError:
                api_key = '3bf4300a992feb65986ce192e7038d8a'
                
        # If API key is found, set it as an environment variable
        if api_key:
            os.environ['MARKETSTACK_API_KEY'] = api_key
            self.stdout.write(self.style.SUCCESS(f'Using Marketstack API key: {api_key}'))
        else:
            self.stdout.write(self.style.WARNING('No Marketstack API key found. Using default key.'))
        
        self.stdout.write('Starting LSE stock update using Marketstack API...')
        results = update_lse_stocks()
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'LSE stock update completed:'))
        self.stdout.write(f'Total stocks processed: {results["total_processed"]}')
        self.stdout.write(f'Successfully updated: {results["successful_updates"]}')
        self.stdout.write(f'Failed updates: {results["failed_updates"]}')
        self.stdout.write(f'Skipped symbols: {results["skipped_symbols"]}')
        
        if results["failed_symbols"]:
            self.stdout.write(self.style.WARNING(f'Failed symbols: {", ".join(results["failed_symbols"])}')) 