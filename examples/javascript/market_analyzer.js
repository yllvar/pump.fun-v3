/**
 * Example: Market Analyzer
 * 
 * This example demonstrates analyzing market data from Pump.fun
 */

const PumpFunAPI = require('../../utils/js_client');

class MarketAnalyzer {
  constructor() {
    this.client = new PumpFunAPI();
  }

  /**
   * Get top tokens by market cap
   * @param {number} limit - Number of tokens to fetch
   * @returns {Promise<Array>} - Array of top tokens
   */
  async getTopTokens(limit = 10) {
    try {
      console.log(`Fetching top ${limit} tokens...`);
      const tokens = await this.client.getLatestCoins({ limit });
      return tokens || [];
    } catch (error) {
      console.error('Error fetching top tokens:', error.message);
      return [];
    }
  }

  /**
   * Analyze token metrics
   * @param {string} tokenAddress - Token address to analyze
   * @returns {Promise<Object>} - Token metrics
   */
  async analyzeToken(tokenAddress) {
    try {
      console.log(`Analyzing token: ${tokenAddress}`);
      // Note: The actual endpoint might be different based on API availability
      const tokenData = await this.client.getTokenInfo(tokenAddress);
      return tokenData || {};
    } catch (error) {
      console.error(`Error analyzing token ${tokenAddress}:`, error.message);
      return null;
    }
  }

  /**
   * Display token information in a formatted way
   * @param {Object} token - Token data
   */
  displayTokenInfo(token) {
    if (!token) return;
    
    console.log('\n=== Token Analysis ===');
    console.log(`Name: ${token.name || 'N/A'}`);
    console.log(`Symbol: ${token.symbol || 'N/A'}`);
    console.log(`Price: $${token.price || 'N/A'}`);
    console.log(`Market Cap: $${token.market_cap || 'N/A'}`);
    console.log(`24h Volume: $${token.volume_24h || 'N/A'}`);
    console.log(`Total Supply: ${token.total_supply || 'N/A'}`);
    console.log(`Holders: ${token.holders_count || 'N/A'}`);
    console.log('====================\n');
  }
}

// Example usage
async function runMarketAnalysis() {
  const analyzer = new MarketAnalyzer();
  
  // Get top 5 tokens
  const topTokens = await analyzer.getTopTokens(5);
  
  if (topTokens.length > 0) {
    console.log(`\nFound ${topTokens.length} tokens. Analyzing...`);
    
    // Analyze each token
    for (const token of topTokens) {
      if (token.address) {
        const analysis = await analyzer.analyzeToken(token.address);
        analyzer.displayTokenInfo(analysis);
        
        // Add a small delay between requests to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  } else {
    console.log('No tokens found to analyze.');
  }
}

// Run the example
runMarketAnalysis().catch(console.error);
