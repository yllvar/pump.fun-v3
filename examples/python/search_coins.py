"""
Example: Search for tokens on Pump.fun

This script demonstrates how to use the PumpFunAPI client to search for tokens
on Pump.fun by name or symbol.
"""

import json
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pumpfun_search.log')
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

def print_usage():
    """Print usage instructions."""
    print("\nUsage: python search_coins.py <search_term> [options]")
    print("\nOptions:")
    print("  <search_term>    The token name or symbol to search for (required)")
    print("  --limit N       Number of results to return (default: 5)")
    print("  --exact         Use exact match instead of fuzzy search")
    print("  --debug         Enable debug logging")
    print("\nExamples:")
    print("  python search_coins.py ethereum")
    print("  python search_coins.py btc --limit 10")
    print("  python search_coins.py ""solana"" --exact")

def parse_arguments(args):
    """Parse command line arguments."""
    if not args or args[0] in ('-h', '--help'):
        print_usage()
        sys.exit(0)
    
    search_term = args[0]
    limit = 5
    search_type = 'fuzzy'
    
    i = 1
    while i < len(args):
        if args[i] == '--limit' and i + 1 < len(args):
            try:
                limit = max(1, min(100, int(args[i + 1])))  # Clamp between 1 and 100
                i += 2
            except ValueError:
                logger.error(f"Invalid limit value: {args[i+1]}. Using default limit of 5.")
                i += 2
        elif args[i] == '--exact':
            search_type = 'exact'
            i += 1
        elif args[i] == '--debug':
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
            i += 1
        else:
            logger.warning(f"Unknown argument: {args[i]}")
            i += 1
    
    return {
        'search_term': search_term,
        'limit': limit,
        'search_type': search_type
    }

def format_market_cap(market_cap):
    """Format market cap value for display."""
    if market_cap is None:
        return 'N/A'
    
    try:
        market_cap = float(market_cap)
        if market_cap >= 1_000_000_000:
            return f"${market_cap/1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:
            return f"${market_cap/1_000_000:.2f}M"
        elif market_cap >= 1_000:
            return f"${market_cap/1_000:.2f}K"
        return f"${market_cap:.2f}"
    except (TypeError, ValueError):
        return str(market_cap)

def main():
    logger.info("Starting Pump.fun API example: Search Coins")
    
    try:
        # Parse command line arguments
        if len(sys.argv) < 2:
            print_usage()
            sys.exit(1)
            
        args = parse_arguments(sys.argv[1:])
        search_term = args['search_term']
        limit = args['limit']
        search_type = args['search_type']
        
        logger.info(f"Searching for '{search_term}' (limit: {limit}, type: {search_type})")
        
        # Initialize the API client
        client = PumpFunAPI()
        
        # Search for coins
        result = client.search_coins(
            search_term=search_term,
            limit=limit,
            sort='market_cap',
            order='DESC',
            include_nsfw=False,
            search_type=search_type
        )
        
        # Debug: Log the raw API response
        logger.debug(f"Raw API response: {json.dumps(result, indent=2)}")
        
        # Print the results
        if isinstance(result, dict) and 'data' in result:
            data = result['data']
            if data:
                print(f"\nFound {len(data)} results for '{search_term}':")
                print("-" * 140)
                print(f"{'Symbol':<10} {'Name':<25} {'Address':<44} {'Market Cap':<15} {'Price (USD)':<12} {'24h Change':<12} {'7d Change'}")
                print("-" * 140)
                
                for coin in data:
                    symbol = coin.get('symbol', 'N/A') or 'N/A'
                    name = (coin.get('name') or 'N/A')[:23] + '...' if coin.get('name', '') else 'N/A'
                    address = coin.get('address', 'N/A') or 'N/A'
                    market_cap = format_market_cap(coin.get('market_cap'))
                    
                    price = coin.get('price')
                    if price is not None:
                        price = f"${float(price):.6f}".rstrip('0').rstrip('.')
                        if price == '0': price = 'N/A'
                    else:
                        price = 'N/A'
                    
                    change_24h = coin.get('price_change_24h')
                    change_24h_str = f"{change_24h:+.2f}%" if change_24h is not None else 'N/A'
                    
                    change_7d = coin.get('price_change_7d')
                    change_7d_str = f"{change_7d:+.2f}%" if change_7d is not None else 'N/A'
                    
                    # Color code price changes
                    def colorize(value, is_percent=True):
                        if value == 'N/A' or not is_percent:
                            return value
                        try:
                            num = float(value.rstrip('%'))
                            if num > 0:
                                return f"\033[92m{value}↑\033[0m"  # Green for positive
                            elif num < 0:
                                return f"\033[91m{value}↓\033[0m"  # Red for negative
                            return f"{value}→"  # Neutral for zero
                        except (ValueError, AttributeError):
                            return value
                    
                    print(
                        f"{symbol:<10} {name:<25} {address[:10]}...{address[-6:] if len(address) > 16 else '':<6}  "
                        f"{market_cap:<15} {price:<12} "
                        f"{colorize(change_24h_str):<12} {colorize(change_7d_str)}"
                    )
                
                print("-" * 140)
                
                # Show pagination info if available
                if 'pagination' in result:
                    pagination = result['pagination']
                    total = int(pagination.get('total', 0))
                    if total > 0:
                        print(f"\nShowing {len(data)} of {total} results. "
                              f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)}")
                        if total > limit:
                            print("Tip: Use --limit N to show more results (max 100 per page)")
            else:
                logger.warning(f"No results found for '{search_term}'")
                print(f"\nNo results found for '{search_term}'.")
                print("Try a different search term or check the spelling.")
        else:
            logger.error(f"Unexpected API response format: {type(result)}")
            print("\nError: Unexpected response format from the API.")
            print("Raw response:")
            print(json.dumps(result, indent=2, default=str))
            
    except KeyboardInterrupt:
        logger.info("Search cancelled by user")
        print("\nSearch cancelled.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        print("Check pumpfun_search.log for more details.")
        sys.exit(1)
    
    logger.info("Search completed successfully")
    print("\nDone! Check pumpfun_search.log for detailed logs.")

if __name__ == "__main__":
    main()
