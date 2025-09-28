"""
Example: Fetch Wallet Information and Token Details

This script demonstrates how to use the PumpFunAPI client to:
1. Fetch wallet holdings
2. Get token details
3. Get token trades
4. Get token comments

Usage:
    python wallet_info.py <wallet_address> [--limit N] [--debug]

Examples:
    python wallet_info.py 2AQdpHJ2JpcEgPiATUXjnmAWSYnzsFfUeH3L6r3jTmcX
    python wallet_info.py 2AQdpHJ2JpcEgPiATUXjnmAWSYnzsFfUeH3L6r3jTmcX --limit 5 --debug
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wallet_info.log')
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

def format_timestamp(timestamp):
    """Convert Unix timestamp to human-readable format."""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return str(timestamp)

def format_number(value, decimal_places=2):
    """Format large numbers with K, M, B suffixes."""
    if value is None:
        return 'N/A'
    try:
        value = float(value)
        if value >= 1_000_000_000:
            return f"{value/1_000_000_000:.{decimal_places}f}B"
        elif value >= 1_000_000:
            return f"{value/1_000_000:.{decimal_places}f}M"
        elif value >= 1_000:
            return f"{value/1_000:.{decimal_places}f}K"
        return f"{value:.{decimal_places}f}"
    except (TypeError, ValueError):
        return str(value)

def get_wallet_holdings(client, wallet_address, limit=10):
    """Fetch and display wallet holdings."""
    logger.info(f"Fetching holdings for wallet: {wallet_address}")
    try:
        # First try to get wallet holdings
        holdings = client.get_wallet_holdings(
            wallet_address=wallet_address,
            limit=limit,
            min_balance=0
        )
        
        # Handle different response formats
        if isinstance(holdings, dict):
            if 'data' in holdings:
                return holdings['data']
            elif 'tokens' in holdings:
                return holdings['tokens']
            elif 'items' in holdings:
                return holdings['items']
        
        # If we get a list directly, return it
        if isinstance(holdings, list):
            return holdings
            
        logger.warning(f"Unexpected response format: {holdings}")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching wallet holdings: {e}", exc_info=True)
        return []

def get_token_details(client, token_address):
    """Fetch token details."""
    logger.debug(f"Fetching details for token: {token_address}")
    try:
        # In the Pump.fun API, we can search for the token by address
        result = client.search_coins(
            search_term=token_address,
            limit=1,
            search_type='exact'
        )
        
        if isinstance(result, dict) and 'data' in result and result['data']:
            return result['data'][0]
        return None
        
    except Exception as e:
        logger.error(f"Error fetching token details: {e}", exc_info=True)
        return None

def get_token_trades(client, token_address, limit=5):
    """Fetch recent trades for a token."""
    logger.debug(f"Fetching trades for token: {token_address}")
    try:
        trades = client.get_token_trades(
            token_address=token_address,
            limit=limit
        )
        
        if isinstance(trades, dict) and 'trades' in trades:
            return trades['trades']
        return []
        
    except Exception as e:
        logger.error(f"Error fetching token trades: {e}", exc_info=True)
        return []

def display_wallet_info(holdings, client):
    """Display formatted wallet information."""
    if not holdings:
        print("\n" + colorize("No token holdings found.", 'yellow', bold=True))
        print("This could be because:")
        print("1. The wallet has no token holdings")
        print("2. The wallet doesn't exist")
        print("3. The API doesn't support this wallet type")
        return
        
    print("\n" + colorize(f"Found {len(holdings)} token holdings:", 'green', bold=True))
    
    print("\n" + "="*120)
    print(f"{'TOKEN':<10} {'BALANCE':<20} {'VALUE (SOL)':<15} {'PRICE (SOL)':<15} {'24H CHANGE':<15} {'HOLDINGS %'}")
    print("-"*120)
    
    total_value = 0
    token_details = []
    
    # First pass: collect all token details
    for item in holdings:
        token_address = item.get('mint')
        balance = float(item.get('balance', 0)) / 1e9  # Assuming 9 decimals
        
        if token_address:
            details = get_token_details(client, token_address)
            if details:
                price = float(details.get('price', 0)) if details.get('price') else 0
                value = balance * price
                total_value += value
                
                token_details.append({
                    'symbol': details.get('symbol', 'N/A'),
                    'balance': balance,
                    'price': price,
                    'value': value,
                    'change_24h': details.get('price_change_24h', 0),
                    'address': token_address
                })
    
    # Sort by value (highest first)
    token_details.sort(key=lambda x: x['value'], reverse=True)
    
    # Second pass: display the sorted list
    for token in token_details:
        value_pct = (token['value'] / total_value * 100) if total_value > 0 else 0
        
        # Color coding for price changes
        change = token['change_24h']
        change_str = f"{change:+.2f}%"
        if change > 0:
            change_str = f"\033[92m{change_str}↑\033[0m"
        elif change < 0:
            change_str = f"\033[91m{change_str}↓\033[0m"
        
        print(
            f"{token['symbol'][:10]:<10} "
            f"{format_number(token['balance'], 4):<20} "
            f"{token['value']:.4f} SOL{'':<11} "
            f"{token['price']:.8f} SOL{'':<7} "
            f"{change_str:<15} "
            f"{value_pct:.1f}%"
        )
    
    print("-"*120)
    print(f"{'TOTAL VALUE:':<20} {total_value:.4f} SOL")
    print("="*120 + "\n")
    
    # Show recent trades for the top token
    if token_details:
        top_token = token_details[0]
        print(f"\nRecent Trades for {top_token['symbol']}:")
        print("-"*120)
        trades = get_token_trades(client, top_token['address'], limit=5)
        
        if trades:
            print(f"{'TIME':<20} {'TYPE':<8} {'PRICE (SOL)':<15} {'AMOUNT':<20} {'VALUE (SOL)':<15} "
                  f"{'BUYER/SELLER':<30} TX")
            print("-"*120)
            
            for trade in trades:
                timestamp = format_timestamp(trade.get('timestamp'))
                trade_type = "BUY" if trade.get('is_buy') else "SELL"
                price = float(trade.get('price', 0)) if trade.get('price') else 0
                amount = float(trade.get('token_amount', 0)) / 1e9  # Assuming 9 decimals
                value = price * amount
                user = trade.get('user', '')[:28] + ('...' if len(trade.get('user', '')) > 28 else '')
                tx = trade.get('signature', '')[:8] + '...'
                
                print(
                    f"{timestamp:<20} "
                    f"{'\033[92m' if trade_type == 'BUY' else '\033[91m'}{trade_type}\033[0m{'':<5} "
                    f"{price:.8f} SOL{'':<7} "
                    f"{format_number(amount, 4):<20} "
                    f"{value:.4f} SOL{'':<7} "
                    f"{user:<30} "
                    f"{tx}"
                )
        else:
            print("No recent trades found.")
        
        print("\n" + "="*120 + "\n")

def is_valid_solana_address(address):
    """Check if the provided string is a valid Solana address."""
    import re
    # Basic Solana address validation (32-44 base58 chars)
    return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))

def get_wallet_created_coins(client, wallet_address, limit=10):
    """Fetch coins created by a wallet."""
    logger.info(f"Fetching created coins for wallet: {wallet_address}")
    try:
        # Get coins created by this wallet
        result = client.get_wallet_created_coins(
            wallet_address=wallet_address,
            limit=limit
        )
        
        # Handle different response formats
        if isinstance(result, dict):
            if 'data' in result and result['data']:
                return result['data']
            elif 'items' in result and result['items']:
                return result['items']
        
        # If we get a list directly, return it
        if isinstance(result, list):
            return result
            
        return []
        
    except Exception as e:
        logger.error(f"Error fetching created coins: {e}", exc_info=True)
        return []

def display_wallet_created_coins(coins, client):
    """Display coins created by the wallet."""
    if not coins:
        print("\n" + colorize("No created coins found for this wallet.", 'yellow'))
        return
    
    print("\n" + colorize(f"Found {len(coins)} coins created by this wallet:", 'green', bold=True))
    print("-" * 120)
    print(f"{'TOKEN':<10} {'SYMBOL':<10} {'NAME':<30} {'CREATED':<20} {'MARKET CAP'}")
    print("-" * 120)
    
    for coin in coins[:10]:  # Limit to first 10 for brevity
        symbol = coin.get('symbol', 'N/A')
        name = coin.get('name', 'N/A')[:28] + '...' if coin.get('name') and len(coin['name']) > 30 else coin.get('name', 'N/A')
        created = datetime.fromtimestamp(coin.get('created_timestamp', 0)/1000).strftime('%Y-%m-%d') if coin.get('created_timestamp') else 'N/A'
        market_cap = format_number(coin.get('market_cap', 0), 2, '$')
        
        print(f"{coin.get('mint', 'N/A')[:10]:<10} {symbol:<10} {name:<30} {created:<20} {market_cap}")
    
    if len(coins) > 10:
        print(f"\n... and {len(coins) - 10} more coins (use --limit to show more)")

def main():
    """Main function to run the wallet info example."""
    parser = argparse.ArgumentParser(
        description='Fetch wallet information from Pump.fun',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python wallet_info.py 2AQdpHJ2JpcEgPiATUXjnmAWSYnzsFfUeH3L6r3jTmcX
  python wallet_info.py 2AQdpHJ2JpcEgPiATUXjnmAWSYnzsFfUeH3L6r3jTmcX --limit 5 --debug
''')
    
    parser.add_argument('wallet_address', 
                      help='The Solana wallet address to query (32-44 base58 characters)')
    parser.add_argument('--limit', type=int, default=10, 
                      help='Maximum number of tokens to show (default: 10)')
    parser.add_argument('--debug', action='store_true', 
                      help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('PumpFunAPI').setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate wallet address format
    if not is_valid_solana_address(args.wallet_address):
        print(f"\n{colorize('Error:', 'red', bold=True)} Invalid Solana address format.")
        print("A valid Solana address should be 32-44 characters long and use base58 encoding.")
        print("Example: 2AQdpHJ2JpcEgPiATUXjnmAWSYnzsFfUeH3L6r3jTmcX\n")
        sys.exit(1)
    
    logger.info(f"Starting wallet info for address: {args.wallet_address}")
    print(f"\n{colorize('Fetching wallet information...', 'cyan')}")
    
    try:
        # Initialize the API client
        client = PumpFunAPI()
        
        # Get wallet holdings
        print("\n" + colorize("1. Fetching token holdings...", 'yellow'))
        holdings = get_wallet_holdings(client, args.wallet_address, args.limit)
        
        if holdings:
            display_wallet_info(holdings, client)
        else:
            print("\n" + colorize("No token holdings found.", 'yellow'))
        
        # Get created coins
        print("\n" + colorize("2. Checking for created coins...", 'yellow'))
        created_coins = get_wallet_created_coins(client, args.wallet_address, args.limit)
        display_wallet_created_coins(created_coins, client)
        
        if not holdings and not created_coins:
            print("\n" + colorize("No wallet information found. This could be because:", 'yellow'))
            print("1. The wallet has no token holdings")
            print("2. The wallet hasn't created any tokens")
            print("3. The wallet doesn't exist")
            print("4. The API doesn't support this wallet type\n")
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print(f"\n{colorize('Operation cancelled.', 'yellow')}")
        sys.exit(130)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"\n{colorize('Error:', 'red', bold=True)} {str(e)}")
        print(f"Check {colorize('wallet_info.log', 'cyan')} for more details.\n")
        sys.exit(1)
    
    print("\n" + colorize("Wallet info completed successfully!", 'green', bold=True))
    logger.info("Wallet info completed successfully")

if __name__ == "__main__":
    main()
