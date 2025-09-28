# Usage Guides

## Getting Started with the API

### Prerequisites
- Python 3.6+ or Node.js 14+
- `requests` library for Python (`pip install requests`)
- `node-fetch` for Node.js (`npm install node-fetch`)

### Making Your First API Call

#### Python Example
```python
import requests

# Get latest trades
response = requests.get('https://frontend-api-v3.pump.fun/trades/latest')
data = response.json()
print(data)
```

#### JavaScript Example
```javascript
import fetch from 'node-fetch';

async function getLatestTrades() {
  const response = await fetch('https://frontend-api-v3.pump.fun/trades/latest');
  const data = await response.json();
  console.log(data);
}

getLatestTrades();
```

## Common Use Cases

### 1. Fetching the Latest Trades

Get the most recent trades across all tokens on Pump.fun.

#### Python
```python
import requests

def get_latest_trades(limit=10):
    url = 'https://frontend-api-v3.pump.fun/trades/latest'
    response = requests.get(url, params={'limit': limit})
    return response.json()

# Example usage
trades = get_latest_trades(5)
for trade in trades['trades']:
    print(f"{trade['token_symbol']}: {trade['amount_in']} -> {trade['amount_out']}")
```

### 2. Searching for Tokens

Search for tokens by name or symbol.

#### JavaScript
```javascript
import fetch from 'node-fetch';

async function searchTokens(query, limit = 10) {
  const url = new URL('https://frontend-api-v3.pump.fun/coins/search');
  url.searchParams.append('searchTerm', query);
  url.searchParams.append('limit', limit);
  
  const response = await fetch(url);
  return await response.json();
}

// Example usage
searchTokens('ethereum').then(console.log);
```

### 3. Getting Wallet Holdings

Get all tokens held by a specific wallet address.

#### Python
```python
import requests

def get_wallet_holdings(wallet_address, limit=50):
    url = f'https://frontend-api-v3.pump.fun/balances/{wallet_address}'
    response = requests.get(url, params={'limit': limit})
    return response.json()

# Example usage
holdings = get_wallet_holdings('0x123...')
for token in holdings['data']:
    print(f"{token['symbol']}: {token['balance']}")
```

### 4. Tracking Token Trades

Monitor trades for a specific token.

#### JavaScript
```javascript
import fetch from 'node-fetch';

async function getTokenTrades(tokenAddress, limit = 50) {
  const url = `https://frontend-api-v3.pump.fun/trades/all/${tokenAddress}`;
  const response = await fetch(`${url}?limit=${limit}`);
  return await response.json();
}

// Example usage
const tokenAddress = '0x123...';
getTokenTrades(tokenAddress).then(trades => {
  console.log(`Found ${trades.length} trades for token ${tokenAddress}`);
});
```

## Advanced Usage

### Using Pagination

Many endpoints support pagination using `offset` and `limit` parameters.

```python
import requests

def get_all_trades(token_address, batch_size=100):
    all_trades = []
    offset = 0
    
    while True:
        url = f'https://frontend-api-v3.pump.fun/trades/all/{token_address}'
        params = {
            'offset': offset,
            'limit': batch_size,
            'minimumSize': 50000000  # Only include significant trades
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data.get('trades'):
            break
            
        all_trades.extend(data['trades'])
        offset += batch_size
        
        # Optional: Add delay to avoid rate limiting
        time.sleep(0.5)
    
    return all_trades
```

### Error Handling

Always implement proper error handling in your API clients.

```python
import requests
import time

def safe_api_call(url, max_retries=3, **params):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                retry_after = int(e.response.headers.get('Retry-After', 5))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            raise
        except Exception as e:
            print(f"Error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Wait before retrying
    
    raise Exception("Max retries exceeded")
```

## Best Practices

1. **Rate Limiting**: Always respect rate limits and implement backoff strategies.
2. **Caching**: Cache responses when possible to reduce API calls.
3. **Error Handling**: Implement robust error handling and retries.
4. **Pagination**: Use pagination to handle large datasets efficiently.
5. **Logging**: Log API requests and responses for debugging.

## Next Steps

Explore the example scripts in the `examples/` directory for more complete implementations.
