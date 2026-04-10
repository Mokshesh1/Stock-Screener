# Comprehensive NSE & BSE Stock Coverage Guide

## Overview
Your stock screener now includes comprehensive NSE and BSE listed stocks including penny stocks!

## Current Coverage
- **Current stocks in CSV**: ~1,600+ stocks
- **Includes**: Nifty 50, Mid-Cap, Small-Cap, and Penny Stocks
- **Exchanges**: NSE (National Stock Exchange) and BSE (Bombay Stock Exchange)

## Stock Data Location
The comprehensive stock list is stored in: **`all_nse_bse_stocks.csv`**

## How to Expand to 7000+ Stocks

### Option 1: Use Official NSE Data (Recommended)
You can get the official complete list from NSE:
1. Visit: https://www.nseindia.com/products/content/equities/equities.htm
2. Download the complete list of all listed companies
3. Extract the symbol column and add to `all_nse_bse_stocks.csv`

### Option 2: Use BSE Data
1. Visit: https://www.bseindia.com/
2. Download the official BSE list
3. Combine with NSE data

### Option 3: Use Python Script (Automated)
Run the `fetch_all_stocks.py` script:
```bash
python fetch_all_stocks.py
```

This script:
- Fetches stocks from multiple sources
- Removes duplicates
- Saves to CSV
- Generates statistics

## CSV File Format
The `all_nse_bse_stocks.csv` file contains:
```
symbol,exchange,status,type
RELIANCE,NSE/BSE,Active,Stock
TCS,NSE/BSE,Active,Stock
...
```

## Using in Your Screener

### Automatic Loading
The screener automatically loads stocks from the CSV file:
```python
stocks = NSEStockList.get_all_stocks()  # Loads from CSV
```

### Manual Addition
To add more stocks, simply edit `all_nse_bse_stocks.csv`:
1. Open the file in spreadsheet app or text editor
2. Add new symbols to the `symbol` column
3. Save the file
4. Restart the screener

## Stock Categories Included

### Nifty 50 (50 stocks)
Large-cap companies - highest liquidity and volume

### Nifty Next 50 (50 stocks)  
Extended large-cap companies

### Nifty Mid-Cap (150+ stocks)
Mid-cap companies with moderate market capitalization

### Nifty Small-Cap (250+ stocks)
Small-cap companies

### BSE & NSE Penny Stocks (1000+ stocks)
Low-priced stocks traded on exchanges

## Performance Tips

### For Screening 7000+ Stocks:
1. **Run during off-market hours** (Post 3:30 PM or pre-9:15 AM)
2. **Use longer timeframes** (daily or weekly instead of minute data)
3. **Filter before scanning** - Consider filtering by:
   - Minimum volume (e.g., > 100,000 shares)
   - Minimum price range
   - Specific sectors

### Optimize Screener Speed:
```python
# In your screener, add filters:
min_volume = 1000000  # At least 1M volume
min_price = 10        # Price > 10 rupees
max_pe = 50          # PE ratio < 50
```

## Stock Categories Breakdown

| Category | Count | Type |
|----------|-------|------|
| Nifty 50 | 50 | Large-cap |
| Nifty Next 50 | 50 | Large-cap |
| Mid-Cap | 150+ | Mid-cap |
| Small-Cap | 250+ | Small-cap |
| Penny Stocks | 1000+ | Penny/SME |
| **Total** | **~1600+** | **All** |

## Updating Stock List

### Weekly Updates:
1. Check NSE official website for new listings
2. Download the updated list
3. Update `all_nse_bse_stocks.csv`

### Using API (Advanced):
```python
# Uses NSE/BSE APIs to fetch latest stocks
from fetch_all_stocks import StockListFetcher

fetcher = StockListFetcher()
df = fetcher.fetch_and_save()  # Updates CSV with latest stocks
```

## Troubleshooting

### CSV File Not Found
- Ensure `all_nse_bse_stocks.csv` is in the same directory as `nse_screener.py`
- The screener will fall back to hardcoded list if CSV not found

### Stocks Not Loading
1. Check CSV file format - must have `symbol` column
2. Ensure no special characters in stock symbols
3. All symbols should be in UPPERCASE

### Screener Running Slow
1. Reduce number of stocks temporarily
2. Use longer timeframes
3. Increase delay between API calls (set in screener)

## Adding Custom Stock Lists

### To screen only specific stocks:
1. Create a new CSV file (e.g., `my_watchlist.csv`)
2. Add only symbols you want to track
3. Update the screener to load from your custom CSV:

```python
def get_all_stocks():
    df = pd.read_csv('my_watchlist.csv')  # Load custom list
    return df['symbol'].tolist()
```

## Example: Add 100 More Stocks

Create a Python script:
```python
import pandas as pd

# Read existing stocks
df = pd.read_csv('all_nse_bse_stocks.csv')

# Add new stocks
new_stocks = ['STOCK1', 'STOCK2', ...]  # Your symbols
new_df = pd.DataFrame({
    'symbol': new_stocks,
    'exchange': 'NSE/BSE',
    'status': 'Active',
    'type': 'Stock'
})

# Combine and remove duplicates
combined = pd.concat([df, new_df]).drop_duplicates()
combined.to_csv('all_nse_bse_stocks.csv', index=False)
```

## Next Steps

1. ✅ Expand CSV to include more penny stocks from BSE
2. ✅ Add sector classification to stocks
3. ✅ Create market cap based filtering
4. ✅ Implement rate limiting for API calls
5. ✅ Add progress saving (resume interrupted scans)

## Keywords
NSE stocks, BSE stocks, penny stocks, Indian stock market, stock screener, Nifty 50, small-cap stocks, mid-cap stocks

---
*Last Updated: April 2026*
*Total Coverage: ~1600+ stocks and growing*
