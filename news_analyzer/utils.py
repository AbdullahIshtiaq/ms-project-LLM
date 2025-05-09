import logging
from fuzzywuzzy import fuzz, process
import re

from .models import StockCompany, StockName, StockDetail
from django.db.models import Prefetch, Q
from django.core.cache import cache

# UK stock exchange suffixes
UK_SUFFIXES = ['.XLON']

# UK market indices
UK_INDICES = {
    'FTSE 100': '^FTSE',
    'FTSE 250': '^FTMC',
    'FTSE 350': '^FTLC',
    'FTSE All-Share': '^FTAS',
    'FTSE Small Cap': '^FTSC',
    'FTSE AIM 100': '^FTAM',
    'FTSE AIM All-Share': '^FTAI'
}

# UK market sectors
UK_SECTORS = [
    'Financial Services',
    'Consumer Goods',
    'Healthcare',
    'Industrials',
    'Technology',
    'Energy',
    'Materials',
    'Real Estate',
    'Utilities',
    'Telecommunications',
    'Consumer Services'
]

def clean_stock_name(stock_name_input):
    """Clean and normalize a stock name.
    
    Args:
        stock_name_input: Stock name to clean
        
    Returns:
        str: Cleaned stock name
    """
    if not stock_name_input:
        return ""
        
    # Convert to lowercase for case-insensitive comparison
    stock_name = stock_name_input.lower()
    
    # Remove common prefixes
    prefixes = ['the ', 'ltd.', 'limited', 'plc', 'plc.', 'group', 'holdings', 'holdings plc']
    for prefix in prefixes:
        if stock_name.startswith(prefix):
            stock_name = stock_name[len(prefix):]
    
    # Remove common suffixes
    suffixes = [' ltd', ' limited', ' plc', ' plc.', ' group', ' holdings', ' holdings plc']
    for suffix in suffixes:
        if stock_name.endswith(suffix):
            stock_name = stock_name[:-len(suffix)]
    
    # Remove parenthetical information
    if '(' in stock_name and ')' in stock_name:
        start = stock_name.find('(')
        end = stock_name.find(')') + 1
        stock_name = stock_name[:start].strip() + ' ' + stock_name[end:].strip()
    
    # Remove share type information
    share_types = [' ord', ' ordinary', ' ord 28 4/7p', ' ord 28 4/7p']
    for share_type in share_types:
        if stock_name.endswith(share_type):
            stock_name = stock_name[:-len(share_type)]
    
    # Remove extra whitespace
    stock_name = ' '.join(stock_name.split())
    
    return stock_name.strip()
    
def generate_json():
    # Pre-fetch related StockNames for each StockCompany
    stock_companies = StockCompany.objects.prefetch_related(
        Prefetch(
            "stockname_set",
            queryset=StockName.objects.all(),
            to_attr="related_names",
        )
    ).all()

    # Construct the result
    results = []
    for company in stock_companies:
        # Fetch the alternative names for the stock company
        alternative_names = [related.name for related in company.related_names]

        # Construct the JSON object for each stock company
        stock_company_info = {
            "symbol": company.symbol,
            "name": str(company),
            "alternativeName": alternative_names,
        }
        results.append(stock_company_info)
    
    print("Generated JSON data")
    # Return the JSON data
    # Note: In a real application, you would probably want to return a JSON response
    print("JSON data:", results)

    return {"results": results}

def get_code_new(name_input, index=False, exact_only=False):
    list_by_exchange_data = cached_generate_json()

    # Create a dictionary to map normalized names to original names
    name_map = {clean_stock_name(alt_name): alt_name 
                for result in list_by_exchange_data["results"]
                for alt_name in result["alternativeName"]}

    # Create a dictionary to map symbols to their details
    symbol_map = {result["symbol"]: result for result in list_by_exchange_data["results"]}

    alternative_stock_names = list(name_map.keys())


    # Check if input is a symbol
    if name_input in symbol_map:
        matching_item = symbol_map[name_input]
        return (
            matching_item["symbol"] + ".XLON",
            matching_item["alternativeName"][-1]  # Returning the last alternative name
        )

    # Clean input
    cleaned_name_input = clean_stock_name(name_input)
    if cleaned_name_input == "":
        return None

    if index:
        alternative_names = alternative_index_names
        list_data = index_list
    else:
        alternative_names = alternative_stock_names
        list_data = list_by_exchange_data

    print(f"Searching for: {cleaned_name_input}")

    # Check for exact match first
    exact_matches = [item for item in alternative_names if cleaned_name_input == item]
    if exact_matches:
        final_match = exact_matches[0]
        print(f"Exact match found: {final_match}")
        try:
            matching_item = next(
                item
                for item in list_data["results"]
                if any(clean_stock_name(alt) == final_match for alt in item["alternativeName"])
            )
            return (
                matching_item["symbol"] + ".XLON",
                name_map[final_match],
            )
        except StopIteration:
            print(f"Exact match found but no corresponding item in results: {final_match}")

    if exact_only:
        # If exact_only is True and no exact match was found, return None
        print(f"No exact match found for {cleaned_name_input} with exact_only=True")
        return None

    # If no exact match or no corresponding item, proceed with partial matching
    matches = [item for item in alternative_names if cleaned_name_input in item or item in cleaned_name_input]

    print(f"Partial matches: {matches}")

    if matches:
        count = float('inf')
        final_match = None
        for match in matches:
            length_diff = abs(len(match) - len(cleaned_name_input))
            if length_diff < count:
                count = length_diff
                final_match = match

        print(f"Best partial match: {final_match}")
        try:
            matching_item = next(
                item
                for item in list_data["results"]
                if any(clean_stock_name(alt) == final_match for alt in item["alternativeName"])
            )
            return (
                matching_item["symbol"] + ".XLON",
                name_map[final_match],
            )
        except StopIteration:
            print(f"Partial match found but no corresponding item in results: {final_match}")

    # If no partial matches or no corresponding item, use fuzzy matching as a last resort
    best_match = process.extractOne(
        cleaned_name_input, alternative_names, scorer=fuzz.ratio
    )
    if best_match:
        best_match_value, score = best_match
        print(f"Fuzzy match: {best_match_value}, Score: {score}")

        if score >= 75:
            try:
                matching_item = next(
                    item
                    for item in list_data["results"]
                    if any(clean_stock_name(alt) == best_match_value for alt in item["alternativeName"])
                )
                print(f"Fuzzy match symbol: {matching_item['symbol']}")
                return (
                    matching_item["symbol"] + ".XLON",
                    name_map[best_match_value],
                )
            except StopIteration:
                print(f"Fuzzy match found but no corresponding item in results: {best_match_value}")

    print(f"No match found for {cleaned_name_input}")
    return None

def cached_generate_json():
    cache_key = 'stock_info_json'
    cached_data = cache.get(cache_key)
    if cached_data is None:
        cached_data = generate_json()
        cache.set(cache_key, cached_data, timeout=86400)  # Cache for 24 hours
    return cached_data

def get_final_stock(stock_name, exact_only=False):
    """Get the final stock symbol and name from a given stock name.
    
    Args:
        stock_name (str): The stock name to look up
        exact_only (bool): Whether to only return exact matches
        
    Returns:
        tuple: (stock_symbol, stock_name) or None if no match found
    """
    print(f"Looking up stock: {stock_name}")
    
    # Handle special cases
    if stock_name == "TASI" or stock_name == "تاسي":
        return "TASI", "تاسي"
    elif stock_name == "NOMU" or stock_name == "نمو":
        return "NOMUC", "نمو"
        
    # Split by hyphen and try each part
    stock_name_splits = stock_name.split("-")
    print(f"Split stock name parts: {stock_name_splits}")
    
    if len(stock_name_splits) > 1:
        for split in stock_name_splits:
            result = get_code_new(split.strip(), exact_only=exact_only)
            if result:
                stock_symbol, stock_name = result
                print(f"Found match for split part '{split}': {stock_symbol}")
                return stock_symbol, stock_name
    else:
        # Try direct lookup first
        result = get_code_new(stock_name, exact_only=exact_only)
        if result:
            stock_symbol, stock_name = result
            print(f"Found direct match: {stock_symbol}")
            return stock_symbol, stock_name
            
        # If no direct match and not exact_only, try fuzzy matching
        if not exact_only:
            # Get all stock names from database
            from .models import StockName
            all_stock_names = StockName.objects.all()
            
            # Create a list of (name, symbol) tuples
            stock_options = [(name.name, name.stock_symbol.symbol) for name in all_stock_names]
            
            # Use fuzzy matching to find the best match
            from fuzzywuzzy import process
            matches = process.extract(stock_name, stock_options, limit=3)
            
            print(f"Fuzzy matches found: {matches}")
            
            # If we have a good match (score > 80)
            if matches and matches[0][1] > 80:
                best_match = matches[0][0]
                print(f"Best fuzzy match: {best_match}")
                return best_match[1], best_match[0]
    
    print(f"No match found for: {stock_name}")
    return None



"""
Text utility functions for the UK Market Reference System.
"""

def clean_text(text):
    """Clean text by removing extra whitespace, emails, and phone numbers."""
    if not text:
        return ""
    # Remove emails
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", text)
    # Remove phone numbers (various formats)
    text = re.sub(r"\b\+?\d{1,3}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b", "", text)
    # Remove extra whitespace
    return ' '.join(text.split()).strip() 