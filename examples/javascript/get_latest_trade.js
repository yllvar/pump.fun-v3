/**
 * Pump.fun API Example: Get Latest Market Data
 * 
 * This example demonstrates how to fetch and display the latest market data
 * from the Pump.fun API with enhanced formatting and error handling.
 */

const { PumpFunAPI } = require('../../utils/js_client');

/**
 * Format a trade object for display
 * @param {Object} trade - Trade data
 * @param {PumpFunAPI} client - API client instance for formatting
 * @returns {string} Formatted trade string
 */
function formatTrade(trade, client) {
  if (!trade) return 'No trade data available';
  
  const timestamp = trade.timestamp ? new Date(trade.timestamp * 1000).toLocaleString() : 'N/A';
  const solAmount = client._formatSol(trade.sol_amount || 0);
  const tokenAmount = client._formatNumber(trade.token_amount || 0);
  const price = trade.price ? client._formatNumber(trade.price) : 'N/A';
  
  return [
    `🔄 ${trade.is_buy ? 'BUY' : 'SELL'}`,
    `Token: ${trade.symbol || 'N/A'} (${trade.mint || 'N/A'})`,
    `Amount: ${tokenAmount} ${trade.symbol || 'tokens'}`,
    `Value: ${solAmount}`,
    `Price: ${price} SOL`,
    `User: ${trade.user ? trade.user.substring(0, 6) + '...' + trade.user.slice(-4) : 'N/A'}`,
    `Time: ${timestamp}`,
    `Tx: ${trade.signature ? trade.signature.substring(0, 10) + '...' + trade.signature.slice(-8) : 'N/A'}`,
    trade.image_uri ? `Image: ${trade.image_uri}` : ''
  ].filter(Boolean).join('\n  ');
}

/**
 * Format a coin object for display
 * @param {Object} coin - Coin data
 * @param {PumpFunAPI} client - API client instance for formatting
 * @returns {string} Formatted coin string
 */
function formatCoin(coin, client) {
  if (!coin) return 'No coin data available';
  
  const marketCap = coin.market_cap ? `$${client._formatNumber(coin.market_cap, 2)}` : 'N/A';
  const price = coin.price ? `$${client._formatNumber(coin.price, 6)}` : 'N/A';
  const created = coin.created_at ? new Date(coin.created_at * 1000).toLocaleString() : 'N/A';
  
  return [
    `💰 ${coin.name || 'Unnamed Token'} (${coin.symbol || 'N/A'})`,
    `Price: ${price}`,
    `Market Cap: ${marketCap}`,
    `Mint: ${coin.mint || 'N/A'}`,
    `Created: ${created}`,
    coin.description ? `Description: ${coin.description.substring(0, 100)}${coin.description.length > 100 ? '...' : ''}` : '',
    coin.image_uri ? `Image: ${coin.image_uri}` : ''
  ].filter(Boolean).join('\n  ');
}

/**
 * Main function to fetch and display market data
 */
async function getMarketData() {
  // Initialize the client with debug mode enabled
  const client = new PumpFunAPI({
    // apiKey: 'your-api-key', // Optional: Add your API key for authenticated requests
  });
  client.debug = true; // Enable debug logging

  console.log('📊 Pump.fun Market Data');
  console.log('='.repeat(40));
  
  try {
    // 1. Get latest trades
    console.log('\n🔍 Fetching latest trades...');
    try {
      const response = await client._request('GET', '/trades/latest', { limit: 3 });
      
      if (response) {
        // Handle single trade object
        if (response.mint) {
          console.log('\n🔄 Latest Trade:');
          console.log('='.repeat(40));
          console.log(formatTrade(response, client));
        } 
        // Handle array of trades (if the API changes in the future)
        else if (Array.isArray(response) && response.length > 0) {
          console.log(`\n🔄 Latest ${response.length} Trades:`);
          console.log('='.repeat(40));
          response.forEach((trade, index) => {
            console.log(`\nTrade #${index + 1}:`);
            console.log(formatTrade(trade, client));
          });
        } else {
          console.log('ℹ️  No recent trades found');
          console.log('Response structure:', JSON.stringify(response, null, 2));
        }
      } else {
        console.log('❌ No response received for trades');
      }
    } catch (error) {
      console.error('\n❌ Error fetching trades:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Details:', error.response.data?.error || 'No additional details');
      }
    }

    // 2. Get latest coins
    console.log('\n🔍 Fetching latest coins...');
    try {
      const response = await client._request('GET', '/coins/latest', { limit: 3, includeNsfw: false });
      
      if (response) {
        // Handle single coin object
        if (response.mint) {
          console.log('\n🆕 Latest Coin:');
          console.log('='.repeat(40));
          console.log(formatCoin(response, client));
        } 
        // Handle array of coins (if the API changes in the future)
        else if (Array.isArray(response) && response.length > 0) {
          console.log(`\n🆕 Latest ${response.length} Coins:`);
          console.log('='.repeat(40));
          response.forEach((coin, index) => {
            console.log(`\nCoin #${index + 1}:`);
            console.log(formatCoin(coin, client));
          });
        } else {
          console.log('ℹ️  No coins found');
          console.log('Response structure:', JSON.stringify(response, null, 2));
        }
      } else {
        console.log('❌ No response received for coins');
      }
    } catch (error) {
      console.error('\n❌ Error fetching coins:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Details:', error.response.data?.error || 'No additional details');
      }
    }

  } catch (error) {
    console.error('\n❌ Unhandled error:', error.message);
    if (error.stack) {
      console.error('Stack trace:', error.stack.split('\n').slice(0, 3).join('\n') + '...');
    }
  }
  
  console.log('\n' + '='.repeat(40));
  console.log('✅ Data fetch complete');
}

// Run the example
console.log('Starting Pump.fun API example...\n');
getMarketData().catch(console.error);
