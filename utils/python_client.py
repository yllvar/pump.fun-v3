"""
Pump.fun API Client

A simple Python client for interacting with the Pump.fun API.
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class PumpFunAPI:
    """A client for interacting with the Pump.fun API."""
    
    BASE_URL = 'https://frontend-api-v3.pump.fun'
    
    def __init__(self, api_key: str = None, max_retries: int = 3, backoff_factor: float = 1.0):
        """Initialize the API client.
        
        Args:
            api_key: Optional API key for authenticated requests
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor for retries (exponential backoff)
        """
        self.api_key = api_key or os.getenv('PUMPFUN_API_KEY')
        self.logger = logging.getLogger('PumpFunAPI')
        self.session = self._create_session(max_retries, backoff_factor)
        
        # Rate limiting attributes
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.rate_limit_limit = None
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum time between requests in seconds
    
    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Mount the retry strategy to all HTTPS requests
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        
        # Set default headers
        session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'PumpFunAPI/1.0.0',
        })
        
        if self.api_key:
            session.headers.update({'Authorization': f'Bearer {self.api_key}'})
            
        return session
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request with rate limit handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., 'tokens/search')
            **kwargs: Additional arguments to pass to requests.request()
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            Exception: If the request fails after all retries
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Respect rate limits
        self._handle_rate_limiting()
        
        try:
            # Make the request
            response = self.session.request(method, url, **kwargs)
            
            # Update rate limit information from headers
            self._update_rate_limits(response.headers)
            
            # Log rate limit information
            self._log_rate_limit_info(endpoint)
            
            # Check for rate limit exceeded (429 status code)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                self.logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying...")
                time.sleep(retry_after)
                return self._request(method, endpoint, **kwargs)
                
            # Raise an exception for other error status codes
            response.raise_for_status()
            
            # Update last request time
            self.last_request_time = time.time()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', error_msg)
                    
                    # Check for rate limit in error response
                    if e.response.status_code == 429:
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        return self._request(method, endpoint, **kwargs)
                        
                except ValueError:
                    error_msg = e.response.text or error_msg
                    
            self.logger.error(f"API request failed: {error_msg}")
            raise Exception(f"API request failed: {error_msg}") from e
    
    def _update_rate_limits(self, headers: Dict[str, str]) -> None:
        """Update rate limit information from response headers."""
        # These header names might vary by API, adjust as needed
        self.rate_limit_remaining = headers.get('X-RateLimit-Remaining')
        self.rate_limit_limit = headers.get('X-RateLimit-Limit')
        
        # Parse rate limit reset time if available
        reset_time = headers.get('X-RateLimit-Reset')
        if reset_time:
            try:
                self.rate_limit_reset = int(reset_time)
            except (ValueError, TypeError):
                self.rate_limit_reset = None
    
    def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by waiting if necessary."""
        current_time = time.time()
        
        # Enforce minimum time between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        # Check if we're close to hitting rate limits
        if self.rate_limit_remaining is not None and self.rate_limit_remaining.isdigit():
            remaining = int(self.rate_limit_remaining)
            if remaining <= 1:  # If we have 1 or 0 requests left
                if self.rate_limit_reset:
                    reset_time = self.rate_limit_reset
                    wait_time = max(0, reset_time - time.time() + 1)  # Add 1 second buffer
                    if wait_time > 0:
                        self.logger.warning(f"Approaching rate limit. Waiting {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
    
    def _log_rate_limit_info(self, endpoint: str) -> None:
        """Log rate limit information for debugging."""
        if self.rate_limit_remaining is not None and self.rate_limit_limit is not None:
            self.logger.debug(
                f"Rate limits - Endpoint: {endpoint}, "
                f"Remaining: {self.rate_limit_remaining}/{self.rate_limit_limit}, "
                f"Reset: {self.rate_limit_reset}"
            )
    
    # General Endpoints
    
    def search_coins(
        self,
        search_term: str,
        limit: int = 50,
        offset: int = 0,
        sort: str = 'market_cap',
        order: str = 'DESC',
        include_nsfw: bool = False,
        search_type: str = 'exact'
    ) -> Dict:
        """Search for tokens.
        
        Args:
            search_term: The search query string
            limit: Number of results to return (default: 50, max: 100)
            offset: Pagination offset (default: 0)
            sort: Field to sort by (default: 'market_cap')
            order: Sort order ('ASC' or 'DESC')
            include_nsfw: Include NSFW content (default: False)
            search_type: Search type ('exact' or 'fuzzy')
            
        Returns:
            Dictionary containing search results
        """
        params = {
            'searchTerm': search_term,
            'limit': limit,
            'offset': offset,
            'sort': sort,
            'order': order,
            'includeNsfw': str(include_nsfw).lower(),
            'type': search_type
        }
        return self._request('GET', '/coins/search', params=params)
    
    def get_latest_trades(self, limit: int = 10) -> Dict:
        """Get the latest trades across all tokens.
        
        Args:
            limit: Number of trades to return (default: 10)
            
        Returns:
            Dictionary containing latest trades
        """
        return self._request('GET', f'/trades/latest?limit={limit}')
    
    def get_latest_coins(self, limit: int = 10, offset: int = 0, include_nsfw: bool = False) -> Dict:
        """Get the most recently created tokens with pagination support.
        
        Args:
            limit: Number of coins to return (default: 10)
            offset: Pagination offset (default: 0)
            include_nsfw: Include NSFW content (default: False)
            
        Returns:
            Dictionary containing latest coins with basic information
        """
        params = {
            'limit': limit,
            'offset': offset,
            'includeNsfw': str(include_nsfw).lower(),
            'sort': 'created_timestamp',
            'order': 'desc'
        }
        
        try:
            # Get the list of latest coins
            response = self._request('GET', '/coins/latest', params=params)
            
            # Process the response to ensure consistent format
            if isinstance(response, dict) and 'data' in response:
                tokens = response['data']
            elif isinstance(response, list):
                tokens = response
            else:
                tokens = [response] if response else []
            
            # Add additional calculated fields
            for token in tokens:
                # Calculate market cap if we have price and supply
                if 'price' in token and 'total_supply' in token:
                    try:
                        price = float(token['price'])
                        supply = float(token['total_supply'])
                        token['market_cap'] = price * supply
                    except (ValueError, TypeError):
                        pass
                
                # Add a link to the token on Pump.fun
                if 'mint' in token:
                    token['explorer_url'] = f"https://pump.fun/token/{token['mint']}"
            
            return {'data': tokens}
                
        except Exception as e:
            self.logger.error(f"Error in get_latest_coins: {str(e)}", exc_info=True)
            return {'data': []}
    
    # Wallet Endpoints
    
    def get_wallet_holdings(
        self,
        wallet_address: str,
        limit: int = 50,
        offset: int = 0,
        min_balance: int = -1
    ) -> Dict:
        """Get token holdings for a wallet.
        
        Args:
            wallet_address: The wallet address to query
            limit: Number of holdings to return (default: 50)
            offset: Pagination offset (default: 0)
            min_balance: Minimum balance to include (default: -1)
            
        Returns:
            Dictionary containing wallet holdings with 'data' key
            
        Note:
            Returns empty list in 'data' key if no holdings found or on error
        """
        try:
            self.logger.debug(f"Fetching token balances for wallet: {wallet_address}")
            
            # Try to get token balances using the /balances endpoint
            params = {
                'limit': limit,
                'offset': offset,
                'minBalance': min_balance
            }
            
            try:
                response = self._request('GET', f'/balances/{wallet_address}', params=params)
                if response and ('data' in response or 'tokens' in response):
                    # Normalize the response format
                    data = response.get('data', response.get('tokens', []))
                    self.logger.info(f"Found {len(data)} token holdings for wallet")
                    return {'data': data}
            except Exception as e:
                self.logger.warning(f"Error fetching token balances: {str(e)}")
                
            # If we get here, no tokens found
            self.logger.info("No token balances found for wallet")
            return {'data': []}
            
        except Exception as e:
            self.logger.error(f"Error in get_wallet_holdings: {str(e)}", exc_info=True)
            return {'data': []}
    
    def get_wallet_created_coins(
        self,
        wallet_address: str,
        limit: int = 10,
        offset: int = 0,
        include_nsfw: bool = False
    ) -> Dict:
        """Get coins created by a wallet.
        
        Args:
            wallet_address: The wallet address that created the coins
            limit: Number of coins to return (default: 10)
            offset: Pagination offset (default: 0)
            include_nsfw: Include NSFW content (default: False)
            
        Returns:
            Dictionary containing created coins with 'data' key
        """
        try:
            self.logger.debug(f"Fetching created coins for wallet: {wallet_address}")
            
            # First try the user-created-coins endpoint
            params = {
                'offset': offset,
                'limit': limit,
                'includeNsfw': str(include_nsfw).lower(),
                'sort': 'created_timestamp',
                'order': 'desc'
            }
            
            try:
                response = self._request('GET', f'/coins/user-created-coins/{wallet_address}', params=params)
                if response and ('data' in response or 'items' in response):
                    # Normalize the response format
                    data = response.get('data', response.get('items', []))
                    self.logger.info(f"Found {len(data)} created coins for wallet")
                    return {'data': data}
            except Exception as e:
                self.logger.warning(f"Error using user-created-coins endpoint: {str(e)}")
            
            # Fallback to search with creator filter
            try:
                search_params = {
                    'creator': wallet_address,
                    'limit': limit,
                    'offset': offset,
                    'includeNsfw': str(include_nsfw).lower(),
                    'sort': 'created_timestamp',
                    'order': 'desc'
                }
                response = self._request('GET', '/coins/search', params=search_params)
                if response and ('data' in response or 'items' in response):
                    # Normalize the response format
                    data = response.get('data', response.get('items', []))
                    self.logger.info(f"Found {len(data)} created coins using search endpoint")
                    return {'data': data}
            except Exception as e:
                self.logger.warning(f"Error searching for created coins: {str(e)}")
            
            # If we get here, no coins found
            self.logger.info("No created coins found for wallet")
            return {'data': []}
            
        except Exception as e:
            self.logger.error(f"Error in get_wallet_created_coins: {str(e)}", exc_info=True)
            return {'data': []}
    
    # Token-Specific Endpoints
    
    def get_token_trades(
        self,
        token_address: str,
        limit: int = 200,
        offset: int = 0,
        minimum_size: int = 50000000
    ) -> Dict:
        """Get trades for a specific token.
        
        Args:
            token_address: The token contract address
            limit: Number of trades to return (default: 200)
            offset: Pagination offset (default: 0)
            minimum_size: Minimum trade size to include (default: 50000000)
            
        Returns:
            Dictionary containing token trades
        """
        params = {
            'limit': limit,
            'offset': offset,
            'minimumSize': minimum_size
        }
        return self._request('GET', f'/trades/all/{token_address}', params=params)
    
    def get_token_comments(
        self,
        token_address: str,
        limit: int = 1000,
        offset: int = 0
    ) -> Dict:
        """Get comments for a specific token.
        
        Args:
            token_address: The token contract address
            limit: Number of comments to return (default: 1000)
            offset: Pagination offset (default: 0)
            
        Returns:
            Dictionary containing token comments
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._request('GET', f'/replies/{token_address}', params=params)
    
    # Helper Methods
    
    def get_all_trades(
        self,
        token_address: str,
        batch_size: int = 200,
        max_trades: int = None,
        minimum_size: int = 50000000
    ) -> List[Dict]:
        """Get all trades for a token, handling pagination automatically.
        
        Args:
            token_address: The token contract address
            batch_size: Number of trades to fetch per request (default: 200)
            max_trades: Maximum number of trades to return (default: None, return all)
            minimum_size: Minimum trade size to include (default: 50000000)
            
        Returns:
            List of trade dictionaries
        """
        all_trades = []
        offset = 0
        
        while True:
            if max_trades and len(all_trades) >= max_trades:
                break
                
            batch = self.get_token_trades(
                token_address=token_address,
                limit=min(batch_size, max_trades - len(all_trades)) if max_trades else batch_size,
                offset=offset,
                minimum_size=minimum_size
            )
            
            if not batch.get('trades'):
                break
                
            all_trades.extend(batch['trades'])
            offset += len(batch['trades'])
            
            # Be nice to the API
            time.sleep(0.5)
        
        return all_trades

# Example usage
if __name__ == "__main__":
    # Initialize the client
    client = PumpFunAPI()
    
    # Example: Get latest trades
    print("Latest Trades:")
    latest_trades = client.get_latest_trades(limit=5)
    for trade in latest_trades.get('trades', [])[:5]:
        print(f"{trade.get('token_symbol')}: {trade.get('amount_in')} -> {trade.get('amount_out')}")
    
    # Example: Search for tokens
    print("\nSearch Results for 'ethereum':")
    search_results = client.search_coins('ethereum', limit=3)
    for coin in search_results.get('data', [])[:3]:
        print(f"{coin.get('symbol')}: {coin.get('name')}")
    
    # Example: Get all trades for a token (first 10)
    # token_address = '0x123...'  # Replace with actual token address
    # all_trades = client.get_all_trades(token_address, max_trades=10)
    # print(f"\nFound {len(all_trades)} trades for token {token_address}")
