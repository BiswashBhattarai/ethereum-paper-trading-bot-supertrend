import ccxt

# Use Kraken instead of Binance
exchange = ccxt.kraken()

# Fetch current Bitcoin price
ticker = exchange.fetch_ticker('BTC/USDT')

# Display results
print("=" * 50)
print("BITCOIN PRICE (BTC/USDT)")
print("=" * 50)
print(f"Exchange:      Kraken")
print(f"Current Price: ${ticker['last']:,.2f}")
print(f"24h High:      ${ticker['high']:,.2f}")
print(f"24h Low:       ${ticker['low']:,.2f}")
print(f"24h Volume:    {ticker['baseVolume']:,.2f} BTC")
print(f"24h Change:    {ticker['percentage']:.2f}%")
print("=" * 50)