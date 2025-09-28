# 🚀 Pump.fun API Client & SDK

A comprehensive, production-ready toolkit for interacting with the Pump.fun API. This repository provides official client libraries, detailed documentation, and practical examples in both Python and JavaScript/TypeScript.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node Version](https://img.shields.io/badge/node-14+-brightgreen.svg)](https://nodejs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/pump.fun-v3?style=social)](https://github.com/yourusername/pump.fun-v3)

## ✨ Features

- **Multi-language Support**
  - 🐍 Python 3.8+ client with async/await support
  - 🌐 JavaScript/TypeScript client for Node.js and browsers
  - 📦 Pre-built TypeScript type definitions
  
- **Production-Ready**
  - ⚡ Automatic rate limiting and retry logic
  - 🛡️ Comprehensive error handling
  - 📊 Request/response logging
  - 🔄 Connection pooling and keep-alive
  - 🕒 Timeout and circuit breaker patterns

- **Developer Experience**
  - 📚 Extensive documentation and examples
  - 🔍 Debug mode for development
  - 🧪 Test suite with mocks
  - 🔄 WebSocket support (coming soon)
  - 🔄 Webhook utilities (coming soon)

- **Advanced Capabilities**
  - 🏗️ Modular architecture for easy extension
  - 🔄 Automatic pagination handling
  - 📡 Proxying and middleware support
  - 🔐 API key rotation (when available)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ or Node.js 14+
- pip (Python) or npm (Node.js)
- Pump.fun API key (if required)

### Installation

#### Python Package
```bash
# Install from PyPI (recommended)
pip install pumpfun-api

# Or install from source
git clone https://github.com/yourusername/pump.fun-v3.git
cd pump.fun-v3
pip install -e .
```

#### JavaScript/Node.js
```bash
# Using npm
npm install pumpfun-api

# Or using Yarn
yarn add pumpfun-api

# Or install from source
git clone https://github.com/yourusername/pump.fun-v3.git
cd pump.fun-v3/examples/javascript
npm install
```

## 💻 Usage Examples

### Python

#### Basic Usage
```python
from pumpfun import PumpFunAPI

# Initialize client with default settings
client = PumpFunAPI()

# Enable debug logging
client.debug = True

# Get latest coins
async def get_latest_coins():
    coins = await client.get_latest_coins(limit=3)
    for coin in coins:
        print(f"{coin['symbol']}: {coin.get('market_cap', 'N/A')} USD")

# Get latest trades
async def get_latest_trades():
    trades = await client.get_latest_trades(limit=3)
    for trade in trades:
        print(f"{trade['symbol']}: {trade['sol_amount']} SOL")

# Run async functions
import asyncio
asyncio.run(get_latest_coins())
```

#### Advanced Usage with Custom Settings
```python
from pumpfun import PumpFunAPI
import asyncio

async def main():
    # Initialize with custom settings
    client = PumpFunAPI(
        base_url="https://api.pump.fun/v1",
        api_key="your-api-key",  # If required
        timeout=30,
        max_retries=3,
        retry_delay=1,
    )
    
    # Get coin by mint address
    coin = await client.get_coin_by_mint("mint-address-here")
    print(f"Coin details: {coin}")
    
    # Get trades for a specific token
    trades = await client.get_trades_by_token("token-address-here", limit=10)
    for trade in trades:
        print(f"Trade: {trade}")

asyncio.run(main())
```

### JavaScript/Node.js

#### Basic Usage
```javascript
const { PumpFunAPI } = require('pumpfun-api');
// or using ES modules:
// import { PumpFunAPI } from 'pumpfun-api';

// Initialize client
const client = new PumpFunAPI({
  debug: true,  // Enable debug logging
  timeout: 10000,  // 10 second timeout
});

// Get latest coins
async function getLatestCoins() {
  try {
    const coins = await client.getLatestCoins({ limit: 3 });
    console.log('Latest coins:', coins);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

getLatestCoins();
```

#### Advanced Usage with Error Handling
```javascript
const { PumpFunAPI } = require('pumpfun-api');

const client = new PumpFunAPI({
  baseUrl: 'https://api.pump.fun/v1',
  apiKey: 'your-api-key',  // If required
  maxRetries: 3,
  retryDelay: 1000,  // 1 second
});

// Get token details with error handling
async function getTokenDetails(mintAddress) {
  try {
    const token = await client.getTokenByMint(mintAddress);
    console.log('Token details:', token);
    
    // Get trades for this token
    const trades = await client.getTradesByToken(mintAddress, { limit: 5 });
    console.log('Recent trades:', trades);
    
    return { token, trades };
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      console.error('API Error:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
      });
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Error:', error.message);
    }
    throw error;
  }
}

// Example usage
getTokenDetails('mint-address-here')
  .catch(console.error);

## ⚡ Rate Limiting & Best Practices

### Current Rate Limits

| Endpoint | Method | Rate Limit | Notes |
|----------|--------|------------|-------|
| `/coins/latest` | GET | ~20 RPM | Returns latest coins |
| `/trades/latest` | GET | ~20 RPM | Returns latest trades |
| `/coins/{mint}` | GET | ~20 RPM | Get coin by mint address |
| `/trades/token/{mint}` | GET | ~20 RPM | Get trades by token |

### Handling Rate Limits

The client automatically handles rate limiting with exponential backoff. When a 429 status code is received, the client will:

1. Wait for the duration specified in the `Retry-After` header (if present)
2. If no header, use exponential backoff starting at 1 second
3. Retry the request up to the configured `maxRetries` (default: 3)

### Best Practices

1. **Caching**: Cache responses when possible to reduce API calls
   ```python
   # Python example with caching
   from cachetools import TTLCache, cached
   
   cache = TTLCache(maxsize=100, ttl=300)  # 5 minute cache
   
   @cached(cache)
   async def get_cached_coin(mint):
       return await client.get_coin_by_mint(mint)
   ```

2. **Batching**: Combine multiple requests when possible
   ```javascript
   // JavaScript example with batching
   async function getMultipleCoins(mintAddresses) {
     return Promise.all(
       mintAddresses.map(mint => client.getCoinByMint(mint))
     );
   }
   ```

3. **Error Handling**: Always implement proper error handling
   ```python
   try:
       result = await client.some_endpoint()
   except RateLimitError as e:
       print(f"Rate limited. Retry after: {e.retry_after} seconds")
   except APIError as e:
       print(f"API Error: {e}")
   ```

4. **Monitoring**: Monitor your API usage
   ```javascript
   client.on('request', (request) => {
     console.log(`Request: ${request.method} ${request.url}`);
   });
   
   client.on('response', (response) => {
     console.log(`Response: ${response.status} ${response.statusText}`);
     console.log('Rate limit:', response.headers['x-ratelimit-remaining']);
   });
   ```

5. **Performance Optimization**:
   - Use `limit` and `offset` parameters for pagination
   - Only request the fields you need
   - Use WebSockets for real-time data when available
   - Implement local caching to reduce API calls

## 📚 Documentation

### Core Concepts

#### Authentication
```python
# API Key Authentication (if required)
client = PumpFunAPI(api_key="your-api-key")
```

#### Making Requests
```javascript
// All API methods return Promises
client.getLatestCoins({ limit: 5 })
  .then(coins => console.log(coins))
  .catch(console.error);

// Or using async/await
async function fetchData() {
  const coins = await client.getLatestCoins({ limit: 5 });
  console.log(coins);
}
```

#### Error Handling
```python
try:
    result = await client.some_endpoint()
except pumpfun.APIError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
```

### Available Methods

#### Coins
- `get_latest_coins(limit=10, offset=0)` - Get latest coins
- `get_coin_by_mint(mint_address)` - Get coin by mint address
- `search_coins(query, limit=10)` - Search for coins

#### Trades
- `get_latest_trades(limit=10, offset=0)` - Get latest trades
- `get_trades_by_token(mint_address, limit=10, offset=0)` - Get trades by token
- `get_trade_by_signature(signature)` - Get trade by signature

#### Advanced
- `set_base_url(url)` - Change the base URL
- `set_api_key(api_key)` - Update the API key
- `set_timeout(timeout)` - Set request timeout in seconds

### WebSocket Support (Coming Soon)
```javascript
const ws = new PumpFunWebSocket();
ws.on('trade', (trade) => {
  console.log('New trade:', trade);
});
ws.connect();
```

### Detailed Documentation

Explore our detailed documentation in the `docs/` directory:

- [📘 API Reference](docs/endpoints.md) - Complete endpoint documentation
- [🔐 Authentication](docs/authentication.md) - API keys and authentication
- [💡 Usage Examples](docs/usage-guides.md) - Practical code examples
- [❓ FAQ](docs/faq.md) - Common questions and solutions
- [📊 Webhook Guide](docs/webhooks.md) - Setting up webhooks (coming soon)
- [🔌 WebSocket Guide](docs/websockets.md) - Real-time data (coming soon)

## 🛠 Development

### Project Structure
```
pump.fun-v3/
├── examples/               # Example code
│   ├── javascript/         # JavaScript/Node.js examples
│   └── python/             # Python examples
├── src/                    # Source code
│   ├── pumpfun/            # Python package
│   │   ├── __init__.py     # Package initialization
│   │   ├── client.py       # Main client implementation
│   │   ├── models.py       # Data models
│   │   └── exceptions.py   # Custom exceptions
│   └── js/                 # JavaScript/TypeScript source
│       ├── src/
│       │   ├── client.ts   # TypeScript client
│       │   └── types.ts    # TypeScript types
│       └── dist/           # Compiled JavaScript
├── tests/                  # Test files
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
└── docs/                   # Documentation
```

### Setting Up for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pump.fun-v3.git
   cd pump.fun-v3
   ```

2. Set up Python environment:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. Set up Node.js environment:
   ```bash
   cd examples/javascript
   npm install
   ```

### Running Tests

#### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pumpfun --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

#### JavaScript Tests
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

### Code Style & Linting

#### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [mypy](http://mypy-lang.org/) for static type checking

```bash
# Format code
black .

# Sort imports
isort .

# Check types
mypy pumpfun/
```

#### JavaScript/TypeScript
- Follow [StandardJS](https://standardjs.com/)
- Use [Prettier](https://prettier.io/) for code formatting
- Use [ESLint](https://eslint.org/) for linting

```bash
# Format code
npm run format

# Lint code
npm run lint

# Check types
tsc --noEmit
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Changes that don't affect the meaning of the code
- `refactor:` A code change that neither fixes a bug nor adds a feature
- `perf:` A code change that improves performance
- `test:` Adding missing tests or correcting existing tests
- `chore:` Changes to the build process or auxiliary tools

Example:
```
feat: add support for new API endpoint

- Add get_coin_by_mint method
- Add tests for new endpoint
- Update documentation

Resolves: #123
```

### Release Process

1. Update version in `pumpfun/__init__.py` and `package.json`
2. Update `CHANGELOG.md`
3. Create a release tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
4. Publish to PyPI:
   ```bash
   rm -rf dist/*
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```
5. Publish to npm:
   ```bash
   cd examples/javascript
   npm publish
   ```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### How to Contribute

1. **Report Bugs**
   - Check if the bug has already been reported in [GitHub Issues](https://github.com/yourusername/pump.fun-v3/issues)
   - If not, create a new issue with a clear title and description
   - Include code to reproduce the issue if possible

2. **Suggest Enhancements**
   - Open an issue to discuss your idea
   - Follow the issue template and provide as much detail as possible
   - We'll review and provide feedback

3. **Submit Code Changes**
   - Fork the repository
   - Create a feature branch: `git checkout -b feature/amazing-feature`
   - Make your changes
   - Add tests for your changes
   - Ensure all tests pass
   - Update documentation if needed
   - Commit your changes: `git commit -m 'feat: add amazing feature'`
   - Push to the branch: `git push origin feature/amazing-feature`
   - Open a Pull Request

### Development Workflow

1. **Setup**
   ```bash
   # Install pre-commit hooks
   pre-commit install
   ```

2. **Coding Standards**
   - Write clear, concise code with comments
   - Follow existing code style
   - Add type hints (Python) or TypeScript types
   - Write tests for new features

3. **Testing**
   - Run tests before pushing changes
   - Add tests for new features
   - Update tests if fixing a bug

4. **Documentation**
   - Update relevant documentation
   - Add docstrings to new functions/classes
   - Update examples if needed

### Code Review Process

1. Pull requests require at least one approval
2. All tests must pass
3. Code must be properly documented
4. Follows project coding standards
5. No decrease in test coverage

### Community

- Join our [Discord](https://discord.gg/your-discord) for discussions
- Follow us on [Twitter](https://twitter.com/pumpfun) for updates
- Read our [Blog](https://blog.pump.fun) for announcements

### Good First Issues

Looking for a place to start? Check out our [Good First Issues](https://github.com/yourusername/pump.fun-v3/labels/good%20first%20issue) for beginner-friendly tasks.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support & Contact

- **GitHub Issues**: [Open an issue](https://github.com/yourusername/pump.fun-v3/issues)
- **Email**: support@pump.fun
- **Twitter**: [@pumpfun](https://twitter.com/pumpfun)
- **Discord**: [Join our community](https://discord.gg/your-discord)

## 🙏 Acknowledgments

- Thanks to all [contributors](https://github.com/yourusername/pump.fun-v3/graphs/contributors) who have helped improve this project
- Built with ❤️ by the Pump.fun team
- Special thanks to our early adopters and beta testers

## 📈 Project Status

[![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/pump.fun-v3)](https://github.com/yourusername/pump.fun-v3/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/pump.fun-v3)](https://github.com/yourusername/pump.fun-v3/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/pump.fun-v3)](https://github.com/yourusername/pump.fun-v3/pulls)
[![GitHub stars](https://img.shields.io/github/stars/yourusername/pump.fun-v3?style=social)](https://github.com/yourusername/pump.fun-v3/stargazers)

## 🌟 Stargazers

[![Stargazers repo roster for @yourusername/pump.fun-v3](https://reporoster.com/stars/yourusername/pump.fun-v3)](https://github.com/yourusername/pump.fun-v3/stargazers)

## 🤝 Contributors

[![Contributors](https://contrib.rocks/image?repo=yourusername/pump.fun-v3)](https://github.com/yourusername/pump.fun-v3/graphs/contributors)

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes in each version.

## 📚 Additional Resources

- [API Documentation](https://docs.pump.fun)
- [Developer Blog](https://blog.pump.fun/developers)
- [Community Forum](https://forum.pump.fun)
- [Status Page](https://status.pump.fun)
