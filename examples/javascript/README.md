# JavaScript Examples for Pump.fun API

This directory contains JavaScript examples demonstrating how to use the Pump.fun API client.

## Prerequisites

- Node.js 14.x or higher
- npm or yarn package manager

## Installation

1. Install dependencies:
   ```bash
   npm install node-fetch
   ```

2. Set up your API key (optional):
   ```bash
   export PUMPFUN_API_KEY='your-api-key-here'
   ```
   Or create a `.env` file in the project root:
   ```
   PUMPFUN_API_KEY=your-api-key-here
   ```

## Available Examples

### 1. Get Latest Trade
Fetch the most recent trade from the Pump.fun platform.

```bash
node get_latest_trade.js
```

### 2. Search Coins
Search for tokens by name or symbol.

```bash
node search_coins.js
```

### 3. Market Analyzer
Analyze market data and token metrics.

```bash
node market_analyzer.js
```

## Error Handling

All examples include basic error handling. If an API request fails, the error will be logged to the console with details about what went wrong.

## Rate Limiting

The examples include basic rate limiting handling. If you encounter rate limits, the client will automatically retry the request after the specified delay.

## Contributing

Feel free to contribute more examples or improve the existing ones. Please follow the existing code style and include appropriate error handling and documentation.
