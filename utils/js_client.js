/**
 * Pump.fun API Client for JavaScript/Node.js
 * 
 * A simple client for interacting with the Pump.fun API.
 */

const https = require('node:https');

class PumpFunAPI {
  /**
   * Initialize the API client
   * @param {Object} options - Configuration options
   * @param {string} [options.apiKey] - Optional API key for authenticated requests
   * @param {number} [options.maxRetries=3] - Maximum number of retry attempts
   * @param {number} [options.retryDelay=1000] - Delay between retries in milliseconds
   */
  constructor({ apiKey = null, maxRetries = 3, retryDelay = 1000 } = {}) {
    this.baseUrl = 'https://frontend-api-v3.pump.fun';
    this.apiKey = apiKey || process.env.PUMPFUN_API_KEY;
    this.maxRetries = maxRetries;
    this.retryDelay = retryDelay;
    
    // Default headers
    this.headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'PumpFunAPI/1.0.0 (Node.js)'
    };
    
    if (this.apiKey) {
      this.headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
  }

  /**
   * Make an API request with retry logic
   * @private
   */
  /**
   * Format a timestamp to a readable date string
   * @private
   */
  _formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    // Check if timestamp is in seconds or milliseconds
    const date = new Date(timestamp * (timestamp < 1e12 ? 1000 : 1));
    return date.toISOString();
  }

  /**
   * Format a number to a human-readable string
   * @private
   */
  _formatNumber(num, decimals = 4) {
    if (num === undefined || num === null) return 'N/A';
    
    // Handle very large numbers
    if (num >= 1e9) return (num / 1e9).toFixed(decimals) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(decimals) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(decimals) + 'K';
    
    // Handle very small numbers
    if (num > 0 && num < 0.0001) return num.toExponential(4);
    
    return num.toString();
  }

  /**
   * Format SOL amount
   * @private
   */
  _formatSol(lamports) {
    if (lamports === undefined || lamports === null) return 'N/A';
    return `${(lamports / 1e9).toFixed(4)} SOL`;
  }

  /**
   * Make an API request with retry logic and improved response handling
   * @private
   */
  _request(method, endpoint, params = {}) {
    return new Promise((resolve, reject) => {
      const url = new URL(`${this.baseUrl}${endpoint}`);
      
      // Add query parameters for GET requests
      if (method === 'GET' && Object.keys(params).length > 0) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            url.searchParams.append(key, String(value));
          }
        });
      }
      
      const makeRequest = (attempt = 0) => {
        const options = {
          method,
          headers: this.headers,
          timeout: 10000 // 10 second timeout
        };
        
        if (this.debug) {
          console.log(`[${new Date().toISOString()}] ${method} ${url}`);
          if (method !== 'GET') {
            console.log('Request Body:', JSON.stringify(params, null, 2));
          }
        }
        
        const req = https.request(url, options, (res) => {
          let data = [];
          let dataLength = 0;
          
          res.on('data', (chunk) => {
            data.push(chunk);
            dataLength += chunk.length;
          });
          
          res.on('end', () => {
            try {
              const response = Buffer.concat(data, dataLength).toString();
              
              if (this.debug) {
                console.log(`[${new Date().toISOString()}] Status: ${res.statusCode}`);
                console.log('Response Headers:', JSON.stringify(res.headers, null, 2));
              }
              
              // Handle empty responses
              if (!response.trim()) {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                  return resolve({});
                } else {
                  return reject(new Error(`Empty response with status ${res.statusCode}`));
                }
              }
              
              // Parse JSON response
              let jsonResponse;
              try {
                jsonResponse = JSON.parse(response);
              } catch (e) {
                return reject(new Error(`Failed to parse JSON response: ${e.message}\nResponse: ${response.substring(0, 200)}...`));
              }
              
              // Handle error responses
              if (res.statusCode >= 400) {
                const errorMessage = jsonResponse.message || jsonResponse.error || 'Unknown error';
                const error = new Error(`API request failed with status ${res.statusCode}: ${errorMessage}`);
                error.response = {
                  status: res.statusCode,
                  data: jsonResponse,
                  headers: res.headers
                };
                return reject(error);
              }
              
              // Handle rate limiting
              if (res.statusCode === 429) {
                const retryAfter = res.headers['retry-after'] || this.retryDelay / 1000;
                if (attempt < this.maxRetries) {
                  if (this.debug) {
                    console.log(`Rate limited. Retrying after ${retryAfter} seconds... (Attempt ${attempt + 1}/${this.maxRetries})`);
                  }
                  return setTimeout(() => makeRequest(attempt + 1), retryAfter * 1000);
                } else {
                  return reject(new Error(`Rate limited after ${this.maxRetries} attempts`));
                }
              }
              
              // Successful response
              resolve(jsonResponse);
              
            } catch (error) {
              reject(new Error(`Failed to process response: ${error.message}`));
            }
          });
        });
        
        req.on('error', (error) => {
          if (attempt < this.maxRetries) {
            const delay = Math.min(this.retryDelay * Math.pow(2, attempt), 30000);
            if (this.debug) {
              console.error(`Request failed (${error.message}). Retrying in ${delay}ms... (Attempt ${attempt + 1}/${this.maxRetries})`);
            }
            setTimeout(() => makeRequest(attempt + 1), delay);
          } else {
            reject(error);
          }
        });
        
        // Set request timeout
        req.setTimeout(options.timeout, () => {
          req.destroy(new Error(`Request timed out after ${options.timeout}ms`));
        });
        
        // Add body for non-GET requests
        if (method !== 'GET' && Object.keys(params).length > 0) {
          const body = JSON.stringify(params);
          req.setHeader('Content-Length', Buffer.byteLength(body));
          req.write(body);
        }
        
        req.end();
      };
      
      makeRequest();
    });
  }
  
  /**
   * Sleep helper function
   * @private
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ===== General Endpoints =====
  
  /**
   * Search for tokens
   * @param {Object} options - Search options
   * @param {string} options.searchTerm - The search query string
   * @param {number} [options.limit=50] - Number of results to return (max: 100)
   * @param {number} [options.offset=0] - Pagination offset
   * @param {string} [options.sort='market_cap'] - Field to sort by
   * @param {'ASC'|'DESC'} [options.order='DESC'] - Sort order
   * @param {boolean} [options.includeNsfw=false] - Include NSFW content
   * @param {'exact'|'fuzzy'} [options.type='exact'] - Search type
   * @returns {Promise<Object>} Search results
   */
  async searchCoins({
    searchTerm,
    limit = 50,
    offset = 0,
    sort = 'market_cap',
    order = 'DESC',
    includeNsfw = false,
    type = 'exact'
  }) {
    return this._request('GET', '/coins/search', {
      searchTerm,
      limit,
      offset,
      sort,
      order,
      includeNsfw,
      type
    });
  }
  
  /**
   * Get the latest trades across all tokens
   * @param {number} [limit=10] - Number of trades to return
   * @returns {Promise<Object>} Latest trades
   */
  async getLatestTrades(limit = 10) {
    return this._request('GET', '/trades/latest', { limit });
  }
  
  /**
   * Get the most recently created tokens
   * @param {Object} options - Query options
   * @param {number} [options.limit=10] - Number of tokens to return
   * @param {boolean} [options.includeNsfw=false] - Include NSFW content
   * @returns {Promise<Object>} Latest tokens
   */
  async getLatestCoins({ limit = 10, includeNsfw = false } = {}) {
    return this._request('GET', '/coins/latest', { limit, includeNsfw });
  }
  
  // ===== Wallet Endpoints =====
  
  /**
   * Get token holdings for a wallet
   * @param {Object} options - Query options
   * @param {string} options.walletAddress - The wallet address to query
   * @param {number} [options.limit=50] - Number of holdings to return
   * @param {number} [options.offset=0] - Pagination offset
   * @param {number} [options.minBalance=-1] - Minimum balance to include
   * @returns {Promise<Object>} Wallet holdings
   */
  async getWalletHoldings({ walletAddress, limit = 50, offset = 0, minBalance = -1 }) {
    return this._request('GET', `/balances/${walletAddress}`, { limit, offset, minBalance });
  }
  
  /**
   * Get coins created by a wallet
   * @param {Object} options - Query options
   * @param {string} options.walletAddress - The wallet address that created the coins
   * @param {number} [options.limit=10] - Number of coins to return
   * @param {number} [options.offset=0] - Pagination offset
   * @param {boolean} [options.includeNsfw=false] - Include NSFW content
   * @returns {Promise<Object>} Created coins
   */
  async getWalletCreatedCoins({ walletAddress, limit = 10, offset = 0, includeNsfw = false }) {
    return this._request('GET', `/coins/user-created-coins/${walletAddress}`, {
      limit,
      offset,
      includeNsfw
    });
  }
  
  // ===== Token-Specific Endpoints =====
  
  /**
   * Get trades for a specific token
   * @param {Object} options - Query options
   * @param {string} options.tokenAddress - The token contract address
   * @param {number} [options.limit=200] - Number of trades to return
   * @param {number} [options.offset=0] - Pagination offset
   * @param {number} [options.minimumSize=50000000] - Minimum trade size to include
   * @returns {Promise<Object>} Token trades
   */
  async getTokenTrades({ tokenAddress, limit = 200, offset = 0, minimumSize = 50000000 }) {
    return this._request('GET', `/trades/all/${tokenAddress}`, {
      limit,
      offset,
      minimumSize
    });
  }
  
  /**
   * Get all trades for a token with pagination
   * @param {Object} options - Query options
   * @param {string} options.tokenAddress - The token contract address
   * @param {number} [options.batchSize=200] - Number of trades per request
   * @param {number} [options.maxTrades] - Maximum number of trades to return
   * @param {number} [options.minimumSize=50000000] - Minimum trade size to include
   * @returns {Promise<Array>} Array of trades
   */
  async getAllTokenTrades({
    tokenAddress,
    batchSize = 200,
    maxTrades,
    minimumSize = 50000000
  }) {
    let allTrades = [];
    let offset = 0;
    let hasMore = true;
    
    while (hasMore) {
      if (maxTrades && allTrades.length >= maxTrades) {
        break;
      }
      
      const limit = maxTrades 
        ? Math.min(batchSize, maxTrades - allTrades.length)
        : batchSize;
      
      const response = await this.getTokenTrades({
        tokenAddress,
        limit,
        offset,
        minimumSize
      });
      
      const trades = response.trades || [];
      if (trades.length === 0) {
        hasMore = false;
      } else {
        allTrades = allTrades.concat(trades);
        offset += trades.length;
        
        // Be nice to the API
        if (trades.length === batchSize) {
          await this._sleep(500);
        }
      }
    }
    
    return allTrades;
  }
  
  /**
   * Get comments for a specific token
   * @param {Object} options - Query options
   * @param {string} options.tokenAddress - The token contract address
   * @param {number} [options.limit=1000] - Number of comments to return
   * @param {number} [options.offset=0] - Pagination offset
   * @returns {Promise<Object>} Token comments
   */
  async getTokenComments({ tokenAddress, limit = 1000, offset = 0 }) {
    return this._request('GET', `/replies/${tokenAddress}`, { limit, offset });
  }
  
  // ===== Helper Methods =====
  
  /**
   * Get the current market metadata
   * @returns {Promise<Object>} Current market metadata
   */
  async getCurrentMetas() {
    return this._request('GET', '/metas/current');
  }
  
  /**
   * Get the current "King of the Hill" token
   * @returns {Promise<Object>} King of the Hill token data
   */
  async getKingOfTheHill() {
    return this._request('GET', '/coins/king-of-the-hill');
  }
}

// Example usage
async function example() {
  try {
    // Initialize the client
    const client = new PumpFunAPI({
      // apiKey: 'your-api-key-here', // Optional
      maxRetries: 3,
      retryDelay: 1000
    });
    
    // Example: Get latest trades
    console.log('Fetching latest trades...');
    const latestTrades = await client.getLatestTrades(5);
    console.log('Latest Trades:', JSON.stringify(latestTrades, null, 2));
    
    // Example: Search for tokens
    console.log('\nSearching for tokens...');
    const searchResults = await client.searchCoins({
      searchTerm: 'ethereum',
      limit: 3
    });
    console.log('Search Results:', JSON.stringify(searchResults, null, 2));
    
    // Example: Get all trades for a token (first 10)
    // const tokenAddress = '0x123...'; // Replace with actual token address
    // console.log(`\nFetching trades for token ${tokenAddress}...`);
    // const allTrades = await client.getAllTokenTrades({
    //   tokenAddress,
    //   maxTrades: 10
    // });
    // console.log(`Found ${allTrades.length} trades`);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Export the PumpFunAPI class
module.exports = { PumpFunAPI };

// Example usage (commented out by default)
// Uncomment to run the example
// example();
