"""
Example: Track Token Metrics and Price History

This script demonstrates how to use the PumpFunAPI to track token metrics,
including price history, market cap, and trading volume.

Features:
- Fetch token details by address or symbol
- Display price history with configurable timeframes
- Show key metrics (market cap, volume, liquidity)
- Generate simple price charts in the terminal

Usage:
    python token_metrics.py <token_identifier> [--days N] [--chart] [--debug]

Examples:
    python token_metrics.py SOL
    python token_metrics.py 0x123... --days 30 --chart
"""

import argparse
import json
import logging
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('token_metrics.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the client
sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from utils.python_client import PumpFunAPI
except ImportError as e:
    logger.error("Failed to import PumpFunAPI. Make sure you've installed the required dependencies.")
    logger.error(f"Error: {e}")
    sys.exit(1)

# Terminal color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'reset': '\033[0m',
    'bold': '\033[1m',
    'underline': '\033[4m'
}

def colorize(text, color=None, bold=False, underline=False):
    """Apply color and styling to text for terminal output."""
    if not color or color.lower() not in COLORS:
        color = ''
    else:
        color = COLORS[color.lower()]
    
    result = f"{color}{text}{COLORS['reset']}"
    if bold:
        result = f"{COLORS['bold']}{result}"
    if underline:
        result = f"{COLORS['underline']}{result}"
    
    return result

def format_number(value, decimal_places=2, prefix='', suffix=''):
    """Format large numbers with K, M, B suffixes."""
    if value is None:
        return 'N/A'
    
    try:
        value = float(value)
        abs_value = abs(value)
        
        if abs_value >= 1_000_000_000:
            return f"{prefix}{value/1_000_000_000:.{decimal_places}f}B{suffix}"
        elif abs_value >= 1_000_000:
            return f"{prefix}{value/1_000_000:.{decimal_places}f}M{suffix}"
        elif abs_value >= 1_000:
            return f"{prefix}{value/1_000:.{decimal_places}f}K{suffix}"
        return f"{prefix}{value:.{decimal_places}f}{suffix}"
    except (TypeError, ValueError):
        return 'N/A'

def format_price(price, currency='SOL'):
    """Format price with appropriate decimal places."""
    if price is None:
        return 'N/A'
    
    try:
        price = float(price)
        if price >= 1:
            return f"{price:,.4f} {currency}"
        elif price >= 0.0001:
            return f"{price:.8f} {currency}".rstrip('0').rstrip('.')
        else:
            return f"{price:.4e} {currency}"
    except (TypeError, ValueError):
        return 'N/A'

def format_change(change, is_percent=True):
    """Format price/percent change with color coding."""
    if change is None:
        return 'N/A'
    
    try:
        change = float(change)
        suffix = '%' if is_percent else ''
        
        if change > 0:
            return f"{colorize(f'+{change:.2f}{suffix}', 'green')} ↑"
        elif change < 0:
            return f"{colorize(f'{change:.2f}{suffix}', 'red')} ↓"
        else:
            return f"{change:.2f}{suffix} →"
    except (TypeError, ValueError):
        return 'N/A'

def get_token_by_identifier(client, identifier):
    """Find a token by its address or symbol."""
    logger.info(f"Looking up token: {identifier}")
    
    try:
        # First, try to get by exact symbol match
        result = client.search_coins(
            search_term=identifier,
            limit=10,  # Get more results to find better matches
            search_type='exact'
        )
        
        # Handle different response formats
        if isinstance(result, list) and len(result) > 0:
            # If the API returns a list directly, use the first item
            return result[0]
        elif isinstance(result, dict):
            if 'data' in result and result['data']:
                # If response has a 'data' field with results
                return result['data'][0]
            elif 'tokens' in result and result['tokens']:
                # Alternative response format with 'tokens' field
                return result['tokens'][0]
        
        # If no exact match, try fuzzy search
        result = client.search_coins(
            search_term=identifier,
            limit=10  # Get more results to find better matches
        )
        
        # Process fuzzy search results
        if isinstance(result, list) and len(result) > 0:
            # If the API returns a list directly, find the best match
            for token in result:
                if isinstance(token, dict):
                    # Check if the symbol or name matches (case-insensitive)
                    if (token.get('symbol', '').lower() == identifier.lower() or 
                        token.get('name', '').lower() == identifier.lower()):
                        return token
            # If no exact match, return the first result
            return result[0]
        elif isinstance(result, dict):
            if 'data' in result and result['data']:
                return result['data'][0]
            elif 'tokens' in result and result['tokens']:
                return result['tokens'][0]
        
        # If we get here, no token was found
        logger.warning(f"No token found matching: {identifier}")
        
    except Exception as e:
        logger.error(f"Error searching for token: {e}", exc_info=True)
    
    return None

def display_token_info(token):
    """Display detailed token information."""
    if not token:
        print("\nToken not found.")
        return
    
    # Basic info
    print("\n" + "="*100)
    print(f"{colorize(token.get('name', 'N/A'), 'cyan', bold=True)} ({colorize(token.get('symbol', 'N/A'), 'yellow', bold=True)})")
    print("-"*100)
    
    # Price and market data
    price = float(token.get('price', 0)) if token.get('price') else 0
    market_cap = float(token.get('market_cap', 0)) if token.get('market_cap') else 0
    volume_24h = float(token.get('volume_24h', 0)) if token.get('volume_24h') else 0
    change_24h = float(token.get('price_change_24h', 0)) if token.get('price_change_24h') is not None else None
    
    print(f"{'Price:':<15} {format_price(price)}  {format_change(change_24h) if change_24h is not None else ''}")
    print(f"{'Market Cap:':<15} {format_number(market_cap, 2, '$')}")
    print(f"{'24h Volume:':<15} {format_number(volume_24h, 2, '$')}")
    print(f"{'Supply:':<15} {format_number(token.get('total_supply', 0) / 1e9, 2)} {token.get('symbol', 'tokens')}")
    
    # Additional metadata
    print("\n" + colorize("Details:", 'white', bold=True, underline=True))
    print(f"{'Address:':<15} {token.get('mint', 'N/A')}")
    print(f"{'Created:':<15} {datetime.fromtimestamp(token.get('created_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S') if token.get('created_timestamp') else 'N/A'}")
    
    # Social links
    print("\n" + colorize("Links:", 'white', bold=True, underline=True))
    if token.get('website'):
        print(f"{'Website:':<15} {token.get('website')}")
    if token.get('twitter'):
        print(f"{'Twitter:':<15} {token.get('twitter')}")
    if token.get('telegram'):
        print(f"{'Telegram:':<15} {token.get('telegram')}")
    
    print("="*100 + "\n")

def generate_price_chart(prices, width=60, height=15):
    """Generate a simple price chart for terminal display."""
    if not prices or len(prices) < 2:
        return "Not enough data to generate chart"
    
    try:
        # Extract timestamps and prices
        timestamps = [p.get('timestamp', 0) for p in prices]
        values = [float(p.get('price', 0)) for p in prices]
        
        if not values:
            return "No price data available"
        
        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val if max_val > min_val else 1
        
        # Calculate chart dimensions
        chart_width = min(width, len(values))
        chart_height = height
        
        # Sample data points to fit chart width
        step = max(1, len(values) // chart_width)
        sampled_values = values[::step]
        sampled_timestamps = timestamps[::step]
        
        # Generate chart
        chart = []
        for y in range(chart_height, 0, -1):
            line = []
            threshold = min_val + (value_range * (y / chart_height))
            
            for i, val in enumerate(sampled_values):
                if i > 0 and i < len(sampled_values) - 1:
                    prev_val = sampled_values[i-1]
                    next_val = sampled_values[i+1]
                    
                    # Simple line drawing with unicode box characters
                    if val >= threshold and (prev_val >= threshold or next_val >= threshold):
                        line.append('▄')
                    else:
                        line.append(' ')
                else:
                    line.append(' ' if val < threshold else '▄')
            
            chart.append(''.join(line))
        
        # Add x-axis with timestamps
        if sampled_timestamps:
            start_time = datetime.fromtimestamp(sampled_timestamps[0])
            end_time = datetime.fromtimestamp(sampled_timestamps[-1])
            time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')}  →  {end_time.strftime('%Y-%m-%d %H:%M')}"
            chart.append('─' * chart_width)
            chart.append(time_range.center(chart_width))
        
        # Add price range
        price_range = f"{format_price(min_val)} - {format_price(max_val)}"
        chart.append(price_range.center(chart_width))
        
        return '\n'.join(chart)
    
    except Exception as e:
        logger.error(f"Error generating chart: {e}", exc_info=True)
        return "Error generating chart"

def main():
    """Main function to run the token metrics example."""
    parser = argparse.ArgumentParser(description='Track token metrics and price history')
    parser.add_argument('token_identifier', help='Token symbol or address')
    parser.add_argument('--days', type=int, default=7, help='Number of days of history to fetch')
    parser.add_argument('--chart', action='store_true', help='Display price chart')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    logger.info(f"Starting token metrics for: {args.token_identifier}")
    
    try:
        # Initialize the API client
        client = PumpFunAPI()
        
        # Get token information
        token = get_token_by_identifier(client, args.token_identifier)
        
        if not token:
            logger.error(f"Token not found: {args.token_identifier}")
            print(f"\n{colorize('Error:', 'red', bold=True)} Token '{args.token_identifier}' not found.")
            sys.exit(1)
        
        # Display token information
        display_token_info(token)
        
        # If chart is requested, fetch price history and display chart
        if args.chart and token.get('mint'):
            print(colorize("Loading price history...", 'yellow'))
            
            # Note: The current API client doesn't have direct price history endpoint
            # This is a placeholder for future implementation
            print("\n" + "="*60)
            print("Price history chart (placeholder - requires API update)")
            print("="*60)
            
            # Mock data for demonstration
            mock_prices = [
                {'timestamp': int((datetime.now() - timedelta(days=i)).timestamp()), 
                 'price': float(token.get('price', 0)) * (0.95 + 0.1 * (i % 5))}
                for i in range(args.days, -1, -1)
            ]
            
            chart = generate_price_chart(mock_prices)
            print(f"\n{chart}\n")
        
        print("\n" + colorize("Note:", 'yellow', bold=True) + " Some features may require additional API endpoints.")
        print("Check the documentation for the latest available features.\n")
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"\n{colorize('Error:', 'red', bold=True)} {str(e)}")
        print(f"Check token_metrics.log for more details.\n")
        sys.exit(1)
    
    logger.info("Token metrics completed successfully")

if __name__ == "__main__":
    main()
