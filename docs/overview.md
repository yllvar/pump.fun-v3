# Pump.fun API Overview

## What is Pump.fun API?

Pump.fun provides a set of public API endpoints that allow developers to access various data points from the Pump.fun platform. This includes information about tokens, trades, wallet holdings, and more.

## Available Endpoints

The API is organized into several categories:

1. **General Endpoints**
   - Search for tokens
   - Get latest trades
   - Get latest coins
   - Get current market metadata

2. **Wallet Endpoints**
   - Get coins created by a wallet
   - Get wallet holdings and balances

3. **Token-Specific Endpoints**
   - Get trade history for a specific token
   - Get comments for a specific token

## Example Response Format

Most endpoints return JSON responses. For example, the latest trades endpoint returns data in this format:

```json
{
  "trades": [
    {
      "token_address": "0x...",
      "amount_in": "1000000",
      "amount_out": "950000",
      "price_impact": "0.05",
      "timestamp": 1641234567,
      "tx_hash": "0x..."
    }
  ]
}
```

## Rate Limiting

Please be mindful of rate limits when making requests to the API. The current rate limits are:
- 60 requests per minute per IP address
- Additional rate limiting may apply for specific endpoints

## Authentication

Most endpoints are publicly accessible and do not require authentication. However, some endpoints might require API keys in the future. See the [authentication guide](authentication.md) for more details.
