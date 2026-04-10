# Trading Bot - Complete Setup Guide

## Table of Contents
1. [Zerodha API Setup](#zerodha-api-setup)
2. [Local Installation](#local-installation)
3. [Configuration](#configuration)
4. [Testing (Backtest & Paper Trading)](#testing)
5. [VPS Deployment](#vps-deployment)
6. [Running the Bot](#running-the-bot)
7. [Troubleshooting](#troubleshooting)

---

## Zerodha API Setup

### Step 1: Create an API Application

1. Go to https://kite.zerodha.com/
2. Log in with your Zerodha credentials
3. Click your **Profile Icon** (top-right) → **Settings**
4. Navigate to **API Consoles** (or **Connected Apps**)
5. Click **"Create New App"**

### Step 2: Fill in App Details

```
App Name: TradingBot
Redirect URL: http://127.0.0.1:8080/
App Type: Web
```

After creation, you'll get:
- **API Key** (save this)
- **API Secret** (save this - keep it secret!)

### Step 3: Get Your Credentials

You need:
1. **User ID** - Your Zerodha username
2. **API Key** - From above
3. **API Secret** - From above

### Step 4: Authentication (enctoken)

The bot needs an `enctoken` to trade. There are two ways:

**Option A: Using Kite Connect SDK (Recommended for first time)**
```python
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="YOUR_API_KEY")
print(kite.login_url())
# Click the link, authorize, and copy the request token
# Then:
data = kite.request_access_token("REQUEST_TOKEN", api_secret="YOUR_API_SECRET")
print(data['access_token'])  # This is your enctoken
```

**Option B: Manual extraction from browser**
1. Log in to https://kite.zerodha.com/
2. Open Browser DevTools (F12)
3. Go to Application → Cookies → kite.zerodha.com
4. Find the cookie named `enctoken` and copy its value
5. Update config.json with this token

---

## Local Installation

### Step 1: Install Python 3.8+

```bash
# Check if Python is installed
python --version  # Should be 3.8 or higher

# If not, download from: https://www.python.org/downloads/
```

### Step 2: Create Project Directory

```bash
mkdir trading-bot
cd trading-bot
```

### Step 3: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `kiteconnect` - Zerodha Kite API
- `pandas` - Data analysis
- `numpy` - Numerical computing
- `yfinance` - Stock data
- `requests` - HTTP requests
- `newsapi` - News sentiment
- `ta` - Technical analysis library

---

## Configuration

### Step 1: Get Free API Keys

**NewsAPI (for sentiment analysis):**
1. Go to https://newsapi.org/
2. Sign up for free account
3. Get your API key
4. Copy to `config.json`

**Twitter API (optional, for social sentiment):**
- Go to https://developer.twitter.com/
- Create an app and get Bearer Token

### Step 2: Update config.json

Open `config.json` and fill in your credentials:

```json
{
  "zerodha": {
    "api_key": "YOUR_KITE_API_KEY",
    "api_secret": "YOUR_KITE_API_SECRET",
    "user_id": "YOUR_ZERODHA_USERNAME",
    "enctoken": "YOUR_ENCTOKEN_HERE"
  },
  "sentiment_analysis": {
    "news_api_key": "YOUR_NEWSAPI_KEY",
    "twitter_bearer_token": "OPTIONAL"
  },
  "trading_params": {
    "risk_per_trade": 0.02,
    "initial_capital": 100000,
    "max_daily_trades": 5,
    "max_open_positions": 3
  }
}
```

### Step 3: Add Your Watchlist

Edit the `watchlist` array in `config.json`:

```json
"watchlist": [
  "RELIANCE",
  "INFY",
  "TCS",
  "HDFC",
  "ICICIBANK",
  "WIPRO",
  "ITC",
  "BAJAJFINSV"
]
```

---

## Testing

### Test 1: Backtest Your Strategy

Run historical backtesting **before going live**:

```bash
python backtest.py
```

This will:
- Test your strategy on last 365 days of data
- Show win rate, profit/loss for each stock
- Generate `backtest_results.csv`

**Interpreting Results:**
```
Total Trades: 25
Win Rate: 65%
Average Return per Stock: 3.5%
```

This means: 65% of trades were winners, averaged 3.5% per trade.

### Test 2: Test Single Stock Analysis

```bash
python -c "
from bot import TradingBot
bot = TradingBot('config.json')
result = bot.analyze_stock('RELIANCE')
print(f'Signal: {result[\"final_signal\"]}')
print(f'Confidence: {result[\"confidence\"]}')
"
```

### Test 3: Paper Trading Mode

Before going live with real money:

1. Create a separate "Paper Trading" account in Zerodha (or use real account with small capital)
2. Run bot in paper trading
3. Monitor for 2-4 weeks
4. Check if results match backtest results

---

## VPS Deployment

### Why VPS?
- Bot runs 24/7 without your laptop being on
- More stable than local machine
- Always online during trading hours

### Step 1: Choose a VPS Provider

Recommended providers (India-based for low latency):
- **Linode** (US but cheap, ~$5/month)
- **Vultr** (India region available)
- **DigitalOcean** (Bangalore, ~$5/month)
- **AWS Lightsail** (India region)

### Step 2: Set Up VPS

**Create Droplet/Instance with:**
- OS: Ubuntu 22.04 LTS
- RAM: 1GB minimum (2GB recommended)
- Storage: 20GB
- Region: India (Mumbai/Bangalore preferred)

### Step 3: SSH into VPS

```bash
# Use SSH key (recommended) or password
ssh root@YOUR_VPS_IP

# On Windows, use PuTTY or Windows Terminal
```

### Step 4: Install Python and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3
sudo apt install python3-pip python3-venv -y

# Create project directory
mkdir trading-bot
cd trading-bot

# Copy your files to VPS
# Option 1: Using SCP
scp -r /path/to/local/bot/* root@YOUR_VPS_IP:/root/trading-bot/

# Option 2: Using SFTP or Git
git clone YOUR_REPO_URL .
```

### Step 5: Install Dependencies on VPS

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 6: Set Up Environment Variables

Never hardcode credentials! Use environment variables:

```bash
# Create .env file (DO NOT COMMIT THIS)
cat > .env << EOF
ZERODHA_API_KEY="your_key"
ZERODHA_API_SECRET="your_secret"
ZERODHA_USER_ID="your_user_id"
ZERODHA_ENCTOKEN="your_enctoken"
NEWSAPI_KEY="your_key"
EOF

# Make it secure
chmod 600 .env
```

Update `bot.py` to read from environment:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ZERODHA_API_KEY')
api_secret = os.getenv('ZERODHA_API_SECRET')
```

### Step 7: Run Bot with Screen or Tmux (persistent)

**Using Screen:**
```bash
# Start bot in background screen session
screen -S trading-bot
python bot.py

# Detach: Ctrl+A then D
# Reattach: screen -r trading-bot
```

**Using Tmux (better option):**
```bash
# Install tmux
sudo apt install tmux -y

# Create session
tmux new-session -d -s trading-bot -c ~/trading-bot
tmux send-keys -t trading-bot "source venv/bin/activate && python bot.py" Enter

# View logs: tmux capture-pane -t trading-bot -p
```

### Step 8: Set Up Logging

Bot creates `trading_bot.log` with all activity.

View logs:
```bash
tail -f trading_bot.log
```

### Step 9: Email Alerts (Optional)

Add to `bot.py` for trade notifications:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(symbol, signal, price):
    msg = MIMEText(f"{symbol}: {signal} @ {price}")
    msg['Subject'] = f"Trade Alert: {symbol}"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = "your_email@gmail.com"
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("your_email@gmail.com", "your_password")
        server.send_message(msg)
```

---

## Running the Bot

### Local Testing

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Run bot (remember to uncomment bot.run() in bot.py first)
python bot.py
```

### VPS Production

```bash
tmux send-keys -t trading-bot "python bot.py" Enter
```

### Monitoring

```bash
# Check if process is running
ps aux | grep python

# View logs in real-time
tail -f trading_bot.log

# Check CPU/Memory usage
top
```

### Stopping the Bot

```bash
# If using screen
screen -S trading-bot -X quit

# If using tmux
tmux kill-session -t trading-bot

# Or just Ctrl+C if running in foreground
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'kiteconnect'"

**Solution:**
```bash
pip install kiteconnect
```

### Issue: "Unauthorized: Invalid API key"

**Solution:**
1. Verify API key in config.json is correct
2. Regenerate enctoken (see [Zerodha API Setup](#zerodha-api-setup))
3. Check if Kite API is enabled in Zerodha settings

### Issue: "No data for symbol"

**Solution:**
1. Verify symbol name (use NSE format: RELIANCE, TCS, etc.)
2. Check if symbol is listed and trading

### Issue: Bot not executing trades

**Check:**
```bash
# Check logs
tail -f trading_bot.log

# Verify:
- API is connected
- Sentiment and fundamentals pass filter
- Capital is available
- Market is open (9:15 AM - 3:30 PM IST)
```

### Issue: High CPU usage on VPS

**Solution:**
- Reduce scan frequency (change 900 seconds to 1800 in bot.py)
- Reduce watchlist size
- Use lighter technical indicators

---

## Safety Checklist Before Going Live

- [ ] Backtest shows positive win rate (>50%)
- [ ] Paper traded for 2+ weeks
- [ ] Zerodha API credentials are secure
- [ ] Risk per trade is set to 2%
- [ ] Stop-loss and take-profit levels are configured
- [ ] VPS is up and running
- [ ] Logs are being created
- [ ] Email alerts are working (if configured)
- [ ] You can quickly stop the bot if needed
- [ ] You understand each trade the bot makes

---

## Next Steps

1. **Test backtest.py** - Run on historical data
2. **Paper trade** - Small capital with real signals
3. **Monitor for 2-4 weeks** - See results vs backtest
4. **Deploy to VPS** - Go live with full capital
5. **Monitor daily** - Check logs and trades
6. **Refine strategy** - Based on results

---

## Support & Resources

- **Zerodha Kite API Docs:** https://kite.trade/docs
- **Technical Analysis:** https://school.stockcharts.com/
- **Trading Psychology:** Mark Douglas "Trading in the Zone"

Good luck! 🚀
