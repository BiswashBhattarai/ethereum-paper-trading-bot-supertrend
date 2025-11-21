import ccxt

# Check version
print(f"CCXT version: {ccxt.__version__}")

# See all available exchanges
print(f"\nTotal exchanges: {len(ccxt.exchanges)}")
print(f"First 10 exchanges: {ccxt.exchanges[:10]}")