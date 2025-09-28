"""
Pump.fun API Rate Limit Tester

This script tests the rate limiting behavior of the Pump.fun API endpoints.
It makes requests to each endpoint and records the rate limit headers.
"""

import os
import sys
import time
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add the parent directory to the path so we can import the client
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.python_client import PumpFunAPI

# Ensure log directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'log')
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOG_DIR, 'rate_limit_test.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

class RateLimitTester:
    """Class to test rate limits of Pump.fun API endpoints."""
    
    def __init__(self, api_key: str = None):
        """Initialize the rate limit tester.
        
        Args:
            api_key: Optional API key for authenticated requests
        """
        self.client = PumpFunAPI(api_key=api_key)
        self.results = []
        
        # Known endpoints to test with their required parameters
        self.endpoints = [
            {
                'name': 'search_coins',
                'method': 'GET',
                'params': {'search_term': 'ethereum', 'limit': 1}
            },
            {
                'name': 'get_latest_trades',
                'method': 'GET',
                'params': {'limit': 1}
            },
            {
                'name': 'get_latest_coins',
                'method': 'GET',
                'params': {'limit': 1}
            },
            {
                'name': 'get_wallet_holdings',
                'method': 'GET',
                'params': {'wallet_address': '0x0000000000000000000000000000000000000000', 'limit': 1}
            },
            {
                'name': 'get_wallet_created_coins',
                'method': 'GET',
                'params': {'wallet_address': '0x0000000000000000000000000000000000000000', 'limit': 1}
            },
            {
                'name': 'get_token_trades',
                'method': 'GET',
                'params': {'token_address': '0x0000000000000000000000000000000000000000', 'limit': 1}
            },
            {
                'name': 'get_token_comments',
                'method': 'GET',
                'params': {'token_address': '0x0000000000000000000000000000000000000000', 'limit': 1}
            }
        ]
    
    def test_endpoint(self, endpoint: Dict) -> Dict:
        """Test a single API endpoint and record rate limit information.
        
        Args:
            endpoint: Dictionary containing endpoint configuration
            
        Returns:
            Dictionary containing test results
        """
        endpoint_name = endpoint['name']
        method = endpoint['method']
        params = endpoint.get('params', {})
        
        logger.info(f"Testing endpoint: {endpoint_name}")
        
        result = {
            'endpoint': endpoint_name,
            'method': method,
            'params': params,
            'status': 'pending',
            'timestamp': int(time.time()),
            'requests': []
        }
        
        try:
            # Make the API call
            start_time = time.time()
            
            # Call the appropriate method on the client
            method_to_call = getattr(self.client, endpoint_name)
            response = method_to_call(**params)
            
            end_time = time.time()
            
            # Get rate limit info from the client
            rate_info = {
                'status_code': 200,
                'response_time_sec': end_time - start_time,
                'rate_limit_remaining': self.client.rate_limit_remaining,
                'rate_limit_limit': self.client.rate_limit_limit,
                'rate_limit_reset': self.client.rate_limit_reset,
                'response_sample': self._sample_response(response) if response else None
            }
            
            result['status'] = 'success'
            result['requests'].append(rate_info)
            
            # If we have rate limit info, try to hit the limit
            if self.client.rate_limit_remaining and int(self.client.rate_limit_remaining) > 0:
                self._test_rate_limit(endpoint, result)
            
        except Exception as e:
            logger.error(f"Error testing {endpoint_name}: {str(e)}")
            result['status'] = 'error'
            result['error'] = str(e)
            
            # Check if this was a rate limit error
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                result['rate_limited'] = True
                result['retry_after'] = e.response.headers.get('Retry-After')
        
        return result
    
    def _test_rate_limit(self, endpoint: Dict, result: Dict) -> None:
        """Test the rate limit by making requests until rate limited.
        
        Args:
            endpoint: Endpoint configuration
            result: Result dictionary to update with test data
        """
        endpoint_name = endpoint['name']
        method = endpoint['method']
        params = endpoint.get('params', {})
        
        # Get the method to call
        method_to_call = getattr(self.client, endpoint_name)
        
        # Make requests until we hit the rate limit or reach max_attempts
        max_attempts = 100  # Safety limit
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            try:
                start_time = time.time()
                response = method_to_call(**params)
                end_time = time.time()
                
                rate_info = {
                    'status_code': 200,
                    'request_number': attempts + 1,  # +1 because we already made one request
                    'response_time_sec': end_time - start_time,
                    'rate_limit_remaining': self.client.rate_limit_remaining,
                    'rate_limit_limit': self.client.rate_limit_limit,
                    'rate_limit_reset': self.client.rate_limit_reset
                }
                
                result['requests'].append(rate_info)
                
                # If we've hit the rate limit, stop
                if self.client.rate_limit_remaining == '0':
                    logger.info(f"Hit rate limit after {attempts + 1} requests to {endpoint_name}")
                    result['rate_limit_hit'] = True
                    result['requests_to_limit'] = attempts + 1
                    break
                
                # Small delay between requests to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error during rate limit test for {endpoint_name}: {str(e)}")
                result['error_during_test'] = str(e)
                
                # Check if this was a rate limit error
                if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                    result['rate_limited'] = True
                    result['retry_after'] = e.response.headers.get('Retry-After')
                    result['requests_to_limit'] = attempts + 1
                
                break
    
    def _sample_response(self, response: Any, max_length: int = 200) -> Any:
        """Create a sample of the response for logging purposes.
        
        Args:
            response: The API response to sample
            max_length: Maximum length of the sample
            
        Returns:
            A sampled version of the response
        """
        if response is None:
            return None
            
        try:
            # Convert to string and truncate if necessary
            response_str = str(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + '...'
            return response_str
        except Exception:
            return "[Unable to serialize response]"
    
    def run_all_tests(self) -> List[Dict]:
        """Run tests on all endpoints.
        
        Returns:
            List of test results for each endpoint
        """
        logger.info("Starting rate limit tests...")
        
        for endpoint in self.endpoints:
            try:
                result = self.test_endpoint(endpoint)
                self.results.append(result)
                
                # Add a small delay between testing different endpoints
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error testing {endpoint.get('name', 'unknown')}: {str(e)}")
                self.results.append({
                    'endpoint': endpoint.get('name', 'unknown'),
                    'status': 'error',
                    'error': f"Unexpected error: {str(e)}"
                })
        
        return self.results
    
    def save_results(self, filename: str = 'rate_limit_results.json') -> str:
        """Save test results to a JSON file in the log directory.
        
        Args:
            filename: Name of the file to save results to (will be saved in log directory)
            
        Returns:
            str: Full path to the saved file
        """
        try:
            # Ensure the filename has a .json extension
            if not filename.endswith('.json'):
                filename += '.json'
                
            # Save to log directory
            filepath = os.path.join(LOG_DIR, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2)
                
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise
    
    def print_summary(self) -> None:
        """Print a summary of the test results."""
        print("\n=== Rate Limit Test Summary ===")
        print(f"Tested {len(self.results)} endpoints\n")
        
        for result in self.results:
            status = result.get('status', 'unknown').upper()
            status_color = '\033[92m' if status == 'SUCCESS' else '\033[91m' if status == 'ERROR' else '\033[93m'
            
            print(f"{status_color}{status}\033[0m - {result['endpoint']}")
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
            
            if 'requests' in result and result['requests']:
                first_req = result['requests'][0]
                print(f"  Rate Limit: {first_req.get('rate_limit_remaining', '?')}/{first_req.get('rate_limit_limit', '?')} remaining")
                
                if 'requests_to_limit' in result:
                    print(f"  Requests to hit limit: {result['requests_to_limit']}")
            
            print()


def main():
    """Main function to run the rate limit tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test rate limits of Pump.fun API endpoints')
    parser.add_argument('--api-key', type=str, help='Pump.fun API key (optional)')
    parser.add_argument('--output', type=str, default='rate_limit_results', 
                       help='Output filename (without extension) for test results (default: rate_limit_results)')
    
    args = parser.parse_args()
    
    # Initialize the tester
    tester = RateLimitTester(api_key=args.api_key)
    
    # Run the tests
    results = tester.run_all_tests()
    
    # Save and display results
    tester.save_results(args.output)
    tester.print_summary()


if __name__ == "__main__":
    main()
