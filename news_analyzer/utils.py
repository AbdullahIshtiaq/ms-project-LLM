import logging
from fuzzywuzzy import fuzz, process

# UK stock exchange suffixes
UK_SUFFIXES = ['.L', '.LSE']

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
    # Remove common prefixes
    prefixes = ['The ', 'Ltd.', 'Limited', 'PLC', 'plc', 'Group', 'Holdings', 'Holdings plc']
    stock_name = stock_name_input
    for prefix in prefixes:
        if stock_name.startswith(prefix):
            stock_name = stock_name[len(prefix):]
    
    # Remove common suffixes
    suffixes = [' Ltd', ' Limited', ' PLC', ' plc', ' Group', ' Holdings', ' Holdings plc']
    for suffix in suffixes:
        if stock_name.endswith(suffix):
            stock_name = stock_name[:-len(suffix)]
    
    return stock_name.strip()
    


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
            matching_item["symbol"] + ".SR",
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
                matching_item["symbol"] + ".SR",
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
                matching_item["symbol"] + ".SR",
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
                    matching_item["symbol"] + ".SR",
                    name_map[best_match_value],
                )
            except StopIteration:
                print(f"Fuzzy match found but no corresponding item in results: {best_match_value}")

    print(f"No match found for {cleaned_name_input}")
    return None



def get_final_stock(stock_name, exact_only=False):
    if stock_name == "TASI" or stock_name == "تاسي":
        return "TASI", "تاسي"
    elif stock_name == "NOMU" or stock_name == "نمو":
        return "NOMUC", "نمو"
    stock_name_splits = stock_name.split("-")
    print("stock_name_splits", stock_name_splits)
    if len(stock_name_splits) > 1:
        print("LENGTH", len(stock_name_splits))
        for split in stock_name_splits:
            result = get_code_new(split.strip(), exact_only=exact_only)
            if result:
                stock_name = result[0]
                stock_name_yf = result[1]
                return stock_name, stock_name_yf
    else:
        result = get_code_new(stock_name, exact_only=exact_only)
        if result:
            stock_name = result[0]
            stock_name_yf = result[1]
            return stock_name, stock_name_yf
        else:
            pass
    return None



"""
Text utility functions for the UK Market Reference System.
"""

def clean_text(text):
    """Clean text by removing extra whitespace."""
    if not text:
        return ""
    return ' '.join(text.split()).strip() 