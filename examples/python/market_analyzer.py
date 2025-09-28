"""
Pump.fun Market Analyzer

A practical example for crypto developers showing how to use various Pump.fun API endpoints
to analyze market data, token performance, and trading activity.

Usage:
    python market_analyzer.py [--top N] [--search TERM] [--token TOKEN_ADDRESS] [--wallet WALLET_ADDRESS]

Examples:
    # Show top 10 trending tokens
    python market_analyzer.py --top 10

    # Search for a specific token
    python market_analyzer.py --search "ethereum"

    # Analyze a specific token
    python market_analyzer.py --token TOKEN_ADDRESS

    # Check wallet's created tokens
    python market_analyzer.py --wallet WALLET_ADDRESS
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the parent directory to the path so we can import the client
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.python_client import PumpFunAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('market_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

# Terminal colors for better output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text: str, color: str, bold: bool = False) -> str:
    """Apply color and formatting to text for terminal output."""
    color_code = getattr(Colors, color.upper(), '')
    bold_code = Colors.BOLD if bold else ''
    return f"{bold_code}{color_code}{text}{Colors.ENDC}"

def format_number(value: float, decimal_places: int = 2) -> str:
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

def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to human-readable format."""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return str(timestamp)

class MarketAnalyzer:
    def __init__(self):
        self.client = PumpFunAPI()

    def get_top_tokens(self, limit: int = 10) -> List[Dict]:
        """Get top tokens by market cap.
        
        Uses the latest coins endpoint which returns tokens sorted by creation time (newest first).
        This is the closest approximation to 'top tokens' available in the API.
        """
        logger.info(f"Fetching top {limit} latest tokens...")
        try:
            # Get multiple tokens in a single request if possible
            response = self.client.get_latest_coins(limit=limit)
            
            # Handle different response formats
            if isinstance(response, dict) and 'data' in response:
                tokens = response['data']
            elif isinstance(response, list):
                tokens = response
            else:
                tokens = []
                
            logger.info(f"Found {len(tokens)} tokens")
            return tokens if isinstance(tokens, list) else []
        except Exception as e:
            logger.error(f"Error fetching top tokens: {e}", exc_info=True)
            return []

    def search_tokens(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tokens by name, symbol, or address with enhanced results.
        
        Args:
            query: The search term (can be token name, symbol, or address)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            List of token dictionaries matching the search query
        """
        logger.info(f"Searching for tokens matching: {query}")
        results = []
        
        try:
            # First try an exact match search
            logger.debug(f"Trying exact match search for: {query}")
            exact_results = self.client.search_coins(
                search_term=query,
                limit=limit,
                search_type='exact'
            )
            
            # Process exact match results
            if isinstance(exact_results, dict) and 'data' in exact_results:
                results.extend(exact_results['data'])
            elif isinstance(exact_results, list):
                results.extend(exact_results)
            
            # If we don't have enough results, try a fuzzy search
            if len(results) < limit:
                logger.debug(f"Trying fuzzy search for: {query}")
                fuzzy_results = self.client.search_coins(
                    search_term=query,
                    limit=limit - len(results),
                    search_type='fuzzy'
                )
                
                # Process fuzzy match results, avoiding duplicates
                if isinstance(fuzzy_results, dict) and 'data' in fuzzy_results:
                    # Filter out duplicates by mint address
                    existing_mints = {t.get('mint') for t in results if t.get('mint')}
                    new_results = [t for t in fuzzy_results['data'] 
                                 if t.get('mint') and t['mint'] not in existing_mints]
                    results.extend(new_results)
                elif isinstance(fuzzy_results, list):
                    existing_mints = {t.get('mint') for t in results if t.get('mint')}
                    new_results = [t for t in fuzzy_results 
                                 if isinstance(t, dict) and t.get('mint') and t['mint'] not in existing_mints]
                    results.extend(new_results)
            
            # If we still don't have results and it looks like an address, try direct fetch
            if not results and len(query) > 20:  # Likely a token address
                logger.debug(f"Trying direct token fetch for address: {query}")
                try:
                    # Try to get token details directly
                    token_details = self.client._request('GET', f'/tokens/{query}')
                    if token_details:
                        results.append(token_details)
                except Exception as e:
                    logger.debug(f"Direct token fetch failed: {e}")
            
            # Ensure we don't exceed the limit
            results = results[:limit]
            
            # Log the number of results found
            logger.info(f"Found {len(results)} matching tokens")
            
            # Enhance results with additional data if needed
            for token in results:
                # Add explorer URLs
                if 'mint' in token:
                    token['explorer_url'] = f"https://pump.fun/token/{token['mint']}"
                
                # Calculate market cap if we have price and supply
                if 'price' in token and 'total_supply' in token:
                    try:
                        price = float(token['price'])
                        supply = float(token['total_supply'])
                        token['market_cap'] = price * supply
                    except (ValueError, TypeError):
                        pass
            
            return results
                
        except Exception as e:
            logger.error(f"Error searching tokens: {e}", exc_info=True)
            return []
    
    def get_token_analysis(self, token_address: str) -> Dict:
        """Get detailed analysis for a specific token."""
        logger.info(f"Analyzing token: {token_address}")
        result = {
            'token_info': None,
            'trades': [],
            'comments': []
        }
        
        try:
            # Get token details
            logger.debug(f"Searching for token: {token_address}")
            search_results = self.client.search_coins(
                search_term=token_address,
                limit=1,
                search_type='exact'
            )
            logger.debug(f"Token search results: {json.dumps(search_results, indent=2)}")
            
            # Handle different response formats
            token_data = []
            if isinstance(search_results, dict):
                token_data = search_results.get('data', [])
            elif isinstance(search_results, list):
                token_data = search_results
            
            if token_data and len(token_data) > 0:
                result['token_info'] = token_data[0] if isinstance(token_data[0], dict) else {}
                
                # Get recent trades
                logger.debug(f"Fetching trades for token: {token_address}")
                try:
                    trades = self.client.get_token_trades(
                        token_address=token_address,
                        limit=10
                    )
                    logger.debug(f"Trades response: {json.dumps(trades, indent=2)}")
                    if isinstance(trades, dict):
                        result['trades'] = trades.get('trades', [])[:5]
                    elif isinstance(trades, list):
                        result['trades'] = trades[:5]
                except Exception as trade_error:
                    logger.error(f"Error fetching trades: {trade_error}", exc_info=True)
                
                # Get token comments
                logger.debug(f"Fetching comments for token: {token_address}")
                try:
                    comments = self.client.get_token_comments(token_address, limit=5)
                    logger.debug(f"Comments response: {json.dumps(comments, indent=2)}")
                    if isinstance(comments, dict):
                        result['comments'] = comments.get('replies', [])[:3]
                    elif isinstance(comments, list):
                        result['comments'] = comments[:3]
                except Exception as comment_error:
                    logger.error(f"Error fetching comments: {comment_error}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Error analyzing token: {e}", exc_info=True)
            
        return result

    def get_wallet_analysis(self, wallet_address: str) -> Dict[str, Any]:
        """Get analysis for a wallet address."""
        logger.info(f"Analyzing wallet: {wallet_address}")
        result = {
            'holdings': [],
            'created_tokens': []
        }
        
        try:
            # Get wallet holdings
            logger.debug(f"Fetching holdings for wallet: {wallet_address}")
            holdings = self.client.get_wallet_holdings(
                wallet_address=wallet_address,
                limit=10
            )
            logger.debug(f"Holdings response: {json.dumps(holdings, indent=2)}")
            
            # Handle different response formats for holdings
            if isinstance(holdings, dict):
                result['holdings'] = holdings.get('data', [])
            elif isinstance(holdings, list):
                result['holdings'] = holdings
            
            # Get created tokens
            logger.debug(f"Fetching created tokens for wallet: {wallet_address}")
            created = self.client.get_wallet_created_coins(
                wallet_address=wallet_address,
                limit=10
            )
            logger.debug(f"Created tokens response: {json.dumps(created, indent=2)}")
            
            # Handle different response formats for created tokens
            if isinstance(created, dict):
                result['created_tokens'] = created.get('data', [])
            elif isinstance(created, list):
                result['created_tokens'] = created
            
        except Exception as e:
            logger.error(f"Error analyzing wallet: {e}", exc_info=True)
            
        return result

def display_top_tokens(tokens: List[Dict]):
    """Display top tokens in a detailed format with key metrics."""
    if not tokens:
        print("No tokens found.")
        return
    
    # Calculate some statistics
    total_market_cap = sum(float(token.get('market_cap', 0)) for token in tokens)
    avg_market_cap = total_market_cap / len(tokens) if tokens else 0
    
    print("\n" + "=" * 90)
    print(f"{colorize('TOP TOKENS', 'yellow', bold=True)} (Showing {len(tokens)} latest tokens)")
    print(f"Total Market Cap: {colorize(f'${total_market_cap:,.2f}', 'green' if total_market_cap > 0 else 'red')}")
    print(f"Average Market Cap: {colorize(f'${avg_market_cap:,.2f}', 'cyan')}")
    print("=" * 90)
    
    for i, token in enumerate(tokens, 1):
        print("\n" + "-" * 90)
        print(f"{colorize(f'TOKEN #{i}:', 'yellow', bold=True)} {colorize(token.get('name', 'N/A'), 'cyan', bold=True)} "
              f"({colorize(token.get('symbol', 'N/A'), 'green')})")
        print("-" * 90)
        
        # Basic Info
        print(f"\n{colorize('📝 BASIC INFORMATION', 'blue', bold=True)}")
        print(f"  {colorize('• Symbol:', 'cyan')} {token.get('symbol', 'N/A')}")
        print(f"  {colorize('• Name:', 'cyan')} {token.get('name', 'N/A')}")
        print(f"  {colorize('• Mint Address:', 'cyan')} {token.get('mint', 'N/A')}")
        print(f"  {colorize('• Creator:', 'cyan')} {token.get('creator', 'N/A')}")
        
        # Format creation time
        created_at = token.get('created_at', token.get('created_timestamp', 0))
        if created_at:
            try:
                # Handle both Unix timestamp (in seconds or milliseconds) and string timestamps
                if isinstance(created_at, (int, float)):
                    # If it's a very large number, it's likely in milliseconds
                    if created_at > 1e12:
                        created_at = created_at / 1000
                    created_str = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    created_str = str(created_at)
                print(f"  {colorize('• Created:', 'cyan')} {created_str}")
            except (ValueError, TypeError, OverflowError) as e:
                print(f"  {colorize('• Created:', 'cyan')} {created_at}")
        
        # Market Data
        print(f"\n{colorize('📊 MARKET DATA', 'blue', bold=True)}")
        
        # Price information
        price = token.get('price_usd') or token.get('price')
        if price is not None:
            try:
                price_float = float(price)
                print(f"  {colorize('• Price:', 'cyan')} ${price_float:,.8f}")
            except (ValueError, TypeError):
                print(f"  {colorize('• Price:', 'cyan')} {price}")
        
        # Market cap
        market_cap = token.get('market_cap')
        if market_cap is not None:
            try:
                market_cap_float = float(market_cap)
                print(f"  {colorize('• Market Cap:', 'cyan')} ${market_cap_float:,.2f}")
            except (ValueError, TypeError):
                print(f"  {colorize('• Market Cap:', 'cyan')} {market_cap}")
        
        # 24h change
        price_change = token.get('price_change_24h')
        if price_change is not None:
            try:
                change = float(price_change)
                change_str = f"{abs(change):.2f}%"
                change_color = "green" if change >= 0 else "red"
                change_arrow = "↑" if change >= 0 else "↓"
                print(f"  {colorize('• 24h Change:', 'cyan')} {colorize(f'{change_arrow} {change_str}', change_color)}")
            except (ValueError, TypeError):
                pass
        
        # Supply Info
        print(f"\n{colorize('📦 SUPPLY', 'blue', bold=True)}")
        
        # Total supply
        total_supply = token.get('total_supply')
        if total_supply is not None:
            try:
                supply = float(total_supply)
                print(f"  {colorize('• Total Supply:', 'cyan')} {format_number(supply, 0)}")
            except (ValueError, TypeError):
                print(f"  {colorize('• Total Supply:', 'cyan')} {total_supply}")
        
        # Circulating supply if available
        circ_supply = token.get('circulating_supply')
        if circ_supply is not None:
            try:
                circ = float(circ_supply)
                print(f"  {colorize('• Circulating Supply:', 'cyan')} {format_number(circ, 0)}")
                
                # Calculate and show percentage of total supply in circulation
                if total_supply and float(total_supply) > 0:
                    circ_pct = (circ / float(total_supply)) * 100
                    print(f"  {colorize('• % in Circulation:', 'cyan')} {circ_pct:.2f}%")
            except (ValueError, TypeError):
                print(f"  {colorize('• Circulating Supply:', 'cyan')} {circ_supply}")
        
        # Explorer link
        if 'mint' in token:
            print(f"\n{colorize('🔗 EXPLORER', 'blue', bold=True)}")
            print(f"  {colorize('• Pump.fun:', 'cyan')} https://pump.fun/token/{token['mint']}")
            print(f"  {colorize('• Solscan:', 'cyan')} https://solscan.io/token/{token['mint']}")
        
        print("-" * 90)
        
        # Add a separator between tokens if not the last one
        if i < len(tokens):
            print("\n" + "=" * 90 + "\n")

def display_token_analysis(analysis: Dict):
    """Display detailed token analysis."""
    if not analysis.get('token_info'):
        print(colorize("Token not found or no data available.", "red", bold=True))
        return
        
    token = analysis['token_info']
    
    print(f"\n{colorize('TOKEN ANALYSIS', 'blue', bold=True)}\n")
    print(f"{colorize('Name:', 'yellow')} {token.get('name', 'N/A')} ({token.get('symbol', 'N/A')})")
    print(f"{colorize('Address:', 'yellow')} {token.get('mint', 'N/A')}")
    print(f"{colorize('Price:', 'yellow')} {format_number(token.get('price'), 6)} SOL")
    print(f"{colorize('Market Cap:', 'yellow')} ${format_number(token.get('market_cap'))}")
    print(f"{colorize('24h Change:', 'yellow')} {token.get('price_change_24h', 0):.2f}%")
    print(f"{colorize('24h Volume:', 'yellow')} ${format_number(token.get('volume_24h'))}")
    
    # Recent trades
    if analysis['trades']:
        print(f"\n{colorize('Recent Trades:', 'blue', bold=True)}")
        for trade in analysis['trades'][:3]:  # Show only 3 most recent trades
            side = "BUY" if trade.get('is_buy') else "SELL"
            side_color = "green" if side == "BUY" else "red"
            print(f"- {format_timestamp(trade.get('timestamp'))}: {colorize(side, side_color)} "
                  f"{format_number(trade.get('amount_in'), 4)} SOL for {format_number(trade.get('amount_out'), 2)} tokens")
    
    # Recent comments
    if analysis['comments']:
        print(f"\n{colorize('Recent Comments:', 'blue', bold=True)}")
        for comment in analysis['comments']:
            print(f"- {comment.get('author', 'Anonymous')}: {comment.get('content', '')}")

def main():
    parser = argparse.ArgumentParser(description='Pump.fun Market Analyzer')
    parser.add_argument('--top', type=int, help='Show top N tokens by market cap')
    parser.add_argument('--search', type=str, help='Search for tokens matching the query')
    parser.add_argument('--token', type=str, help='Analyze a specific token by address')
    parser.add_argument('--wallet', type=str, help='Analyze a wallet address')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    analyzer = MarketAnalyzer()
    
    if args.top:
        tokens = analyzer.get_top_tokens(limit=args.top)
        display_top_tokens(tokens)
    elif args.search:
        tokens = analyzer.search_tokens(args.search)
        display_top_tokens(tokens)
    elif args.token:
        analysis = analyzer.get_token_analysis(args.token)
        display_token_analysis(analysis)
    elif args.wallet:
        wallet_data = analyzer.get_wallet_analysis(args.wallet)
        
        if wallet_data['created_tokens']:
            print(f"\n{colorize('Created Tokens:', 'blue', bold=True)}")
            for token in wallet_data['created_tokens']:
                print(f"- {token.get('symbol', 'N/A')} ({token.get('name', 'N/A')}): {token.get('mint', 'N/A')}")
        else:
            print(colorize("No created tokens found for this wallet.", "yellow"))
            
        if wallet_data['holdings']:
            print(f"\n{colorize('Token Holdings:', 'blue', bold=True)}")
            for holding in wallet_data['holdings']:
                print(f"- {holding.get('symbol', 'N/A')}: {format_number(holding.get('balance', 0))} tokens")
        else:
            print(colorize("No token holdings found for this wallet.", "yellow"))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python market_analyzer.py --top 10")
        print("  python market_analyzer.py --search \"ethereum\"")
        print("  python market_analyzer.py --token TOKEN_ADDRESS")
        print("  python market_analyzer.py --wallet WALLET_ADDRESS")

if __name__ == "__main__":
    main()
