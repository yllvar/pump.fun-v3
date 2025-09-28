"""
Example: Fetch the latest trades from Pump.fun

This script demonstrates how to use the PumpFunAPI client to fetch the latest trades
across all tokens on Pump.fun.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pumpfun_api.log')
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

def main():
    logger.info("Starting Pump.fun API example: Get Latest Trades")
    
    try:
        # Initialize the API client with debug logging
        logger.debug("Initializing PumpFunAPI client")
        client = PumpFunAPI()
        
        # Fetch the latest trades
        logger.info("Fetching the latest trades...")
        result = client.get_latest_trades(limit=5)
        
        # Debug: Log the raw API response
        logger.debug(f"Raw API response: {json.dumps(result, indent=2)}")
        
        # Handle different response formats
        if isinstance(result, dict):
            if 'trades' in result and result['trades']:
                print("\nLatest Trades:")
                print("-" * 100)
                print(f"{'Token':<15} {'Amount In':<15} {'Amount Out':<15} {'Type':<8} {'Timestamp':<20} {'Tx Hash'}")
                print("-" * 100)
                
                for trade in result['trades']:
                    print(
                        f"{trade.get('symbol', 'N/A'):<15} "
                        f"{trade.get('sol_amount', 'N/A'):<15} "
                        f"{trade.get('token_amount', 'N/A'):<15} "
                        f"{'BUY' if trade.get('is_buy') else 'SELL':<8} "
                        f"{format_timestamp(trade.get('timestamp')):<20} "
                        f"{trade.get('signature', 'N/A')}"
                    )
            else:
                # Handle direct trade object (non-array response)
                print("\nLatest Trade:")
                print("-" * 100)
                print(json.dumps(result, indent=2, default=str))
                
                # Log the trade details
                logger.info(f"Trade: {result.get('symbol')} - "
                           f"SOL: {result.get('sol_amount')}, "
                           f"Tokens: {result.get('token_amount')}, "
                           f"Type: {'BUY' if result.get('is_buy') else 'SELL'}")
        else:
            logger.warning(f"Unexpected response format: {type(result)}")
            print("\nUnexpected response format. Raw response:")
            print(json.dumps(result, indent=2, default=str))
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        print("Check pumpfun_api.log for more details.")
        sys.exit(1)
    
    logger.info("Script completed successfully")
    print("\nDone! Check pumpfun_api.log for detailed logs.")

if __name__ == "__main__":
    main()
