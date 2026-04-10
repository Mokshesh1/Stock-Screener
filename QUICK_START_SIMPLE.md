# 🤖 Simplified Trading Bot - Quick Start Guide

## Overview

This is a **Moving Average Crossover** trading bot that:
- ✅ Scans 10 stocks in your watchlist
- ✅ Generates BUY/SELL signals using EMA 12/26 crossover
- ✅ Includes sentiment filter (VIX)
- ✅ Manages risk with 2% per trade rule
- ✅ Works on any stock/index options on Zerodha

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Download Files

Download these 2 files to your project folder:
- `bot_simple.py` - Main bot that scans all stocks
- `backtest_simple.py` - Backtest your strategy on historical data

### Step 2: Run Backtest First

```bash
python backtest_simple.py
```

**What it does:**
- Tests strategy on last 365 days of data
- Shows win rate % for each stock
- Shows total return %
- Saves results to `backtest_results_simple.csv`

**Example Output:**
```
RELIANCE: 8 trades, Win Rate: 62.5%, Return: 8.45%
INFY: 12 trades, Win Rate: 75.0%, Return: 15.30%
TCS: 6 trades, Win Rate: 66.7%, Return: 4.20%

SIMPLIFIED STRATEGY BACKTEST REPORT
====================================
Total Trades: 85
Win Rate: 68.2%
Total Return: 52.3%
```

**Interpretation:**
- If **Win Rate > 50%** → Strategy is profitable ✓
- If **Total Return > 0%** → Positive P&L ✓

### Step 3: Scan Live Stocks

Once backtest looks good, scan all your stocks:

```bash
python bot_simple.py
```

**What it does:**
- Analyzes all 10 stocks in your watchlist
- Shows BUY signals with entry price & stop loss
- Shows SELL signals
- Shows stocks with no signal

**Example Output:**
```
SCANNING WATCHLIST
==================

TRADING SIGNALS
===============

🟢 BUY SIGNALS (3):
  RELIANCE: Entry @ 2850.50, SL @ 2805.25
  INFY: Entry @ 1520.75, SL @ 1495.30
  WIPRO: Entry @ 425.90, SL @ 410.50

🔴 SELL SIGNALS (1):
  TCS

⚪ NO SIGNAL (6):
  ICICIBANK
  HDFC
  ...
```

### Step 4: Paper Trade (Optional)

Before real money, test with paper trading:
1. Create a "Paper Trading" account in Zerodha
2. Run the bot in paper mode for 2-4 weeks
3. Compare results with backtest

---

## 📊 Understanding the Strategy

### How It Works:

```
Price Action
    ↓
Calculate EMA 12 & EMA 26 (Moving Averages)
    ↓
Check if EMA12 crosses above EMA26
    ↓
Check if Volume confirms the move
    ↓
Check if Sentiment is Bullish/Neutral
    ↓
GENERATE BUY SIGNAL ✓
```

### Entry Signal:
```
IF (EMA12 > EMA26)  ← Moving average says uptrend
AND (Volume > Average)  ← Volume confirms
AND (Sentiment != Bearish)  ← Not scared market
THEN → BUY
```

### Exit Signals:
1. **Take Profit**: +5% gain (sell high)
2. **Stop Loss**: Below 20-bar support (protect downside)
3. **Bearish Signal**: EMA12 crosses below EMA26 (trend reversal)

---

## 🎯 Configuration

Your `config.json` has these important settings:

```json
{
  "trading_params": {
    "risk_per_trade": 0.02,  ← 2% risk per trade
    "initial_capital": 100000,  ← Your capital
    "position_size_percent": 5  ← Max 5% per position
  },
  "stock_screener": {
    "watchlist": [
      "RELIANCE",
      "INFY",
      "TCS",
      ...  ← Add/remove stocks here
    ]
  }
}
```

### To Change Watchlist:

Edit `config.json` and add your stocks:

```json
"watchlist": [
  "RELIANCE",
  "INFY",
  "HDFC",
  "ICICIBANK",
  "WIPRO",
  "BAJAJFINSV",
  "TCS",
  "ITC",
  "SUNPHARMA",
  "MARUTI"
]
```

---

## 📈 Backtest Results Interpretation

### Win Rate
- **> 50%** = More winners than losers ✓ GOOD
- **> 60%** = Strong strategy ✓✓ EXCELLENT
- **< 50%** = More losers than winners ✗ BAD

### Return %
- **Positive** = Overall profit ✓
- **Negative** = Overall loss ✗
- **> 50%** = Excellent historical performance ✓✓

### Example Analysis

```
Win Rate: 68.2%, Total Return: 52.3%
↓
This means:
- 68 out of 100 trades were winners
- Average profit was 52.3% over 365 days
- Trading this strategy would have been profitable
```

---

## 🚀 Running Continuously (24/7)

To run the bot automatically during market hours:

### Option 1: On Your Laptop

Edit `bot_simple.py` and uncomment the last line:

```python
# Uncomment to run continuously:
bot.run()  # ← Remove the #
```

Then run:
```bash
python bot_simple.py
```

Bot will scan every 15 minutes during 9:15 AM - 3:30 PM IST.

### Option 2: On VPS (24/7 Trading)

1. Rent a VPS (₹100-500/month)
2. Copy your bot files there
3. Use `tmux` or `screen` to run in background:

```bash
tmux new-session -d -s trading-bot
tmux send-keys -t trading-bot "python bot_simple.py" Enter
```

---

## ⚠️ Important Notes

### Before Going Live:
- ✅ Backtest first (shows historical performance)
- ✅ Paper trade for 2-4 weeks (verify with real signals)
- ✅ Start with small capital (₹10,000-50,000)
- ✅ Monitor daily (check logs and trades)

### Risk Management:
- 🔴 Never risk more than 2% per trade
- 🔴 Never leverage (use only available capital)
- 🔴 Have a stop loss on EVERY trade
- 🔴 Don't overtrade (max 5 trades/day)

### Common Mistakes:
- ❌ Going live without backtesting
- ❌ Changing strategy after 1-2 losses
- ❌ Trading without stop loss
- ❌ Doubling down on losing trades
- ❌ Ignoring bot logs and errors

---

## 📊 Files Overview

| File | Purpose | Command |
|------|---------|---------|
| `bot_simple.py` | Main bot, scans all stocks | `python bot_simple.py` |
| `backtest_simple.py` | Test strategy on past data | `python backtest_simple.py` |
| `config.json` | Your API keys & watchlist | Edit this for settings |
| `backtest_results_simple.csv` | Detailed backtest data | Open in Excel/CSV viewer |
| `trading_bot_simple.log` | Bot activity log | Check for errors |

---

## 🆘 Troubleshooting

### No Trades Generated (0 trades in backtest)
- **Cause:** Crossovers are rare, volume filter too strict
- **Fix:** Adjust EMA periods or volume threshold

### "Error getting LTP" Message
- **Cause:** Zerodha API permission issue (not critical)
- **Fix:** Use Yahoo Finance data (already implemented)

### "Insufficient permission" Error
- **Cause:** Live price permission not granted
- **Fix:** Not needed - we use Yahoo Finance

### Bot Not Executing Trades
- **Cause:** API authentication expired, wrong IP whitelisted
- **Fix:** Run `python auth_helper.py` to re-authenticate

---

## 📞 Quick Checklist

- [ ] Downloaded both bot files
- [ ] Ran backtest - win rate > 50%? ✓
- [ ] config.json has API key & secret ✓
- [ ] IP is whitelisted on Zerodha ✓
- [ ] Ran bot_simple.py - no errors ✓
- [ ] Got trading signals ✓
- [ ] Ready to paper trade ✓

---

## 🎓 Next Steps

1. **Backtest** - See if strategy works historically
   ```bash
   python backtest_simple.py
   ```

2. **Test Single Stock** - Verify signals look good
   ```bash
   python bot_simple.py
   ```

3. **Paper Trade** - Run with virtual money for 2-4 weeks

4. **Live Trade** - Once confident, trade with real capital (START SMALL!)

5. **Monitor & Refine** - Check logs daily, adjust as needed

---

## 💡 Tips for Success

1. **Keep it simple** - MA crossover is proven to work
2. **Backtest before trading** - Historical data tells the story
3. **Paper trade first** - Verify signals with real market
4. **Risk management** - 2% per trade, always
5. **Monitor logs** - Check `trading_bot_simple.log` daily
6. **Don't overtrade** - Quality > Quantity
7. **Be patient** - Good trades take time
8. **Have discipline** - Follow your stop loss ALWAYS

---

## 📖 Educational Resources

- **Moving Averages:** https://school.stockcharts.com/doku.php?id=technical_indicators:moving_averages
- **Crossover Strategies:** https://www.investopedia.com/terms/c/crossover.asp
- **Risk Management:** https://www.investopedia.com/terms/r/risk-management.asp
- **Trading Psychology:** Mark Douglas - "Trading in the Zone"

---

**Good luck! You've got this! 🚀**

Questions? Check the logs or re-read this guide.
