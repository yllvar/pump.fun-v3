# API Endpoints Reference

## General Endpoints

### Search for Tokens
- **URL**: `https://frontend-api-v3.pump.fun/coins/search`
- **Method**: `GET`
- **Query Parameters**:
  - `searchTerm`: The search query string
  - `offset`: Pagination offset (default: 0)
  - `limit`: Number of results to return (default: 50, max: 100)
  - `sort`: Field to sort by (e.g., 'market_cap')
  - `order`: Sort order ('ASC' or 'DESC')
  - `includeNsfw`: Include NSFW content (true/false)
  - `type`: Search type ('exact' or 'fuzzy')

### Get Latest Trade
- **URL**: `https://frontend-api-v3.pump.fun/trades/latest`
- **Method**: `GET`
- **Description**: Returns the most recent trades across all tokens
- **Response**: Array of trade objects

### Get Latest Coin
- **URL**: `https://frontend-api-v3.pump.fun/coins/latest`
- **Method**: `GET`
- **Description**: Returns the most recently created tokens
- **Query Parameters**:
  - `offset`: Pagination offset
  - `limit`: Number of results to return
  - `includeNsfw`: Include NSFW content (true/false)

## Wallet Endpoints

### Get Wallet Holdings
- **URL**: `https://frontend-api-v3.pump.fun/balances/{wallet_address}`
- **Method**: `GET`
- **URL Parameters**:
  - `wallet_address`: The Ethereum wallet address
- **Query Parameters**:
  - `limit`: Number of holdings to return (default: 50)
  - `offset`: Pagination offset (default: 0)
  - `minBalance`: Minimum balance to include (default: -1)

### Get Coins Created by Wallet
- **URL**: `https://frontend-api-v3.pump.fun/coins/user-created-coins/{wallet_address}`
- **Method**: `GET`
- **URL Parameters**:
  - `wallet_address`: The Ethereum wallet address
- **Query Parameters**:
  - `offset`: Pagination offset (default: 0)
  - `limit`: Number of results to return (default: 10)
  - `includeNsfw`: Include NSFW content (true/false)

## Token-Specific Endpoints

### Get Token Trades
- **URL**: `https://frontend-api-v3.pump.fun/trades/all/{token_address}`
- **Method**: `GET`
- **URL Parameters**:
  - `token_address`: The token contract address
- **Query Parameters**:
  - `limit`: Number of trades to return (default: 200)
  - `offset`: Pagination offset (default: 0)
  - `minimumSize`: Minimum trade size to include

### Get Token Comments
- **URL**: `https://frontend-api-v3.pump.fun/replies/{token_address}`
- **Method**: `GET`
- **URL Parameters**:
  - `token_address`: The token contract address
- **Query Parameters**:
  - `limit`: Number of comments to return (default: 1000)
  - `offset`: Pagination offset (default: 0)

## Response Format

Most endpoints return JSON responses with the following structure:

```json
{
  "data": [
    // Array of items
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "pages": 10,
    "limit": 10
  }
}
```

## Error Responses

Common error responses include:

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Example error response:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests, please try again later.",
    "retry_after": 60
  }
}
```
