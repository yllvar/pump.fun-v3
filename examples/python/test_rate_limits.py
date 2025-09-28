"""
Pump.fun API Rate Limit Tester

This script tests all available endpoints to document their rate limiting behavior.
It makes requests to each endpoint and records the rate limit headers.
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rate_limit_test.log')
    ]
)
logger = logging.getLogger('RateLimitTester')

# Add the project root to the path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.python_client import PumpFunAPI

class RateLimitTester:
    """Test rate limits for all Pump.fun API endpoints."""
    
    def __init__(self, api_key: str = None):
        """Initialize the rate limit tester."""
        self.client = PumpFunAPI(api_key=api_key)
        self.results = {}
        self.test_wallet = "33UdRJm2p7FGYivdXEzMSM2qjpP3VcPGNTiDBhtCQybJ"  # Example wallet
        self.test_token = "5HvmxE9M24Z1EPxgyd6vCWeYnDF9bMnQYnfLvE2USMHF"  # Example token
    
    def test_endpoint(self, name: str, method: str, endpoint: str, **kwargs) -> Dict:
        """Test a single endpoint and record rate limit information."""
        logger.info(f"Testing endpoint: {name} ({method} {endpoint})")
        
        result = {
            'name': name,
            'endpoint': endpoint,
            'method': method,
            'tested_at': datetime.utcnow().isoformat(),
            'rate_limit_headers': {},
            'success': False,
            'error': None,
            'response_time_ms': None,
            'response_status': None
        }
        
        try:
            start_time = time.time()
            
            # Make the request
            response = self.client._request(method, endpoint, **kwargs)
            
            # Record response time
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            result['response_status'] = 200
            result['success'] = True
            
            # Record rate limit headers
            result['rate_limit_headers'] = {
                'X-RateLimit-Limit': getattr(response, 'headers', {}).get('X-RateLimit-Limit'),
                'X-RateLimit-Remaining': getattr(response, 'headers', {}).get('X-RateLimit-Remaining'),
                'X-RateLimit-Reset': getattr(response, 'headers', {}).get('X-RateLimit-Reset'),
                'Retry-After': getattr(response, 'headers', {}).get('Retry-After')
            }
            
            logger.info(f"✓ Success - Rate limit: {result['rate_limit_headers'].get('X-RateLimit-Remaining')}/{result['rate_limit_headers'].get('X-RateLimit-Limit')}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            
            # Try to get response status if available
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                result['response_status'] = e.response.status_code
                
                # If we hit a rate limit, record the Retry-After header
                if e.response.status_code == 429:
                    result['rate_limit_headers']['Retry-After'] = e.response.headers.get('Retry-After')
                    logger.warning(f"⚠️  Rate limited - Retry after: {result['rate_limit_headers'].get('Retry-After')}s")
                else:
                    logger.error(f"✗ Failed: {e}")
            else:
                logger.error(f"✗ Failed: {e}")
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all available endpoints."""
        logger.info("Starting rate limit tests...")
        
        # Define all endpoints to test
        tests = [
            # Search and discovery endpoints
            {"name": "Search Coins", "method": "GET", "endpoint": "search/coins", "params": {"query": "bitcoin"}},
            {"name": "Get Latest Coins", "method": "GET", "endpoint": "coins/latest"},
            
            # Token endpoints
            {"name": "Get Token Info", "method": "GET", "endpoint": f"tokens/{self.test_token}"},
            {"name": "Get Token Trades", "method": "GET", "endpoint": f"trades/token/{self.test_token}"},
            
            # Wallet endpoints
            {"name": "Get Wallet Holdings", "method": "GET", "endpoint": f"wallets/{self.test_wallet}/tokens"},
            {"name": "Get Wallet Created Coins", "method": "GET", "endpoint": f"wallets/{self.test_wallet}/created"},
            
            # Market data endpoints
            {"name": "Get Latest Trades", "method": "GET", "endpoint": "trades/latest"},
            {"name": "Get Trending Tokens", "method": "GET", "endpoint": "tokens/trending"},
            
            # Add more endpoints as needed
        ]
        
        # Run all tests
        for test in tests:
            # Add a small delay between tests to avoid hitting rate limits during testing
            time.sleep(1)
            
            # Run the test
            result = self.test_endpoint(
                name=test['name'],
                method=test['method'],
                endpoint=test['endpoint'],
                **test.get('params', {})
            )
            
            # Store the result
            self.results[test['name']] = result
        
        # Save results to a file
        self.save_results()
        
        logger.info("All tests completed!")
        return self.results
    
    def save_results(self, filename: str = 'rate_limit_results.json') -> None:
        """Save test results to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")
    
    def print_summary(self) -> None:
        """Print a summary of the test results."""
        print("\n" + "="*80)
        print("RATE LIMIT TEST SUMMARY")
        print("="*80)
        
        for name, result in self.results.items():
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            rate_limit = f"{result['rate_limit_headers'].get('X-RateLimit-Remaining', '?')}/{result['rate_limit_headers'].get('X-RateLimit-Limit', '?')}"
            print(f"{status} - {name}")
            print(f"  Endpoint: {result['method']} {result['endpoint']}")
            print(f"  Status: {result.get('response_status', 'N/A')}")
            print(f"  Rate Limit: {rate_limit}")
            if result.get('error'):
                print(f"  Error: {result['error']}")
            if 'Retry-After' in result['rate_limit_headers']:
                print(f"  Retry After: {result['rate_limit_headers']['Retry-After']}s")
            print()


def main():
    """Run the rate limit tests."""
    # Initialize the tester
    tester = RateLimitTester()
    
    # Run all tests
    tester.run_all_tests()
    
    # Print a summary
    tester.print_summary()
    
    logger.info("Rate limit testing complete!")


if __name__ == "__main__":
    main()
