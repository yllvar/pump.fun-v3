/**
 * Example: Search Coins
 * 
 * This example demonstrates how to search for coins on Pump.fun
 */

const PumpFunAPI = require('../../utils/js_client');

async function searchCoins() {
  try {
    // Initialize the client
    const client = new PumpFunAPI();

    const searchTerm = 'ethereum'; // Example search term
    console.log(`Searching for coins with term: ${searchTerm}`);
    
    // Search for coins
    const results = await client.searchCoins({
      search_term: searchTerm,
      limit: 5, // Limit to 5 results
      sort: 'market_cap',
      order: 'DESC'
    });
    
    if (results && results.length > 0) {
      console.log(`\nFound ${results.length} coins:`);
      results.forEach((coin, index) => {
        console.log(`\n${index + 1}. ${coin.name} (${coin.symbol})`);
        console.log(`   Address: ${coin.address}`);
        console.log(`   Price: $${coin.price || 'N/A'}`);
        console.log(`   Market Cap: $${coin.market_cap || 'N/A'}`);
        console.log(`   24h Volume: $${coin.volume_24h || 'N/A'}`);
      });
    } else {
      console.log('No coins found matching your search.');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    }
  }
}

// Run the example
searchCoins();
