"""
NSE Screener - All-in-One App
Run screener directly in the app and see results instantly!
No file uploads needed.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import time
import numpy as np
import os

# Page config
st.set_page_config(
    page_title="Stock Universal Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# TRADING CONFIGURATION - TIMEFRAME BASED PROFIT TARGETS
# ============================================================================
class TradingConfig:
    """Configuration for different trading timeframes and their target settings"""
    
    # Timeframe configurations: (holding_days, base_profit, max_profit)
    TIMEFRAMES = {
        'intraday_15min': {
            'holding_days': 1,
            'base_profit': 0.015,      # 1.5% base
            'max_profit': 0.30,         # 30% max
            'description': 'Intraday (15min-1hour)'
        },
        'intraday_1hour': {
            'holding_days': 1,
            'base_profit': 0.020,       # 2% base
            'max_profit': 0.25,         # 25% max
            'description': 'Intraday (1 hour)'
        },
        'short_swing_1d': {
            'holding_days': 1,
            'base_profit': 0.05,        # 5% base
            'max_profit': 0.18,         # 18% max
            'description': 'Short swing (1 day)'
        },
        'short_swing_3d': {
            'holding_days': 3,
            'base_profit': 0.08,        # 8% base
            'max_profit': 0.25,         # 25% max
            'description': 'Short swing (3 days)'
        },
        'swing_5d': {
            'holding_days': 5,
            'base_profit': 0.10,        # 10% base
            'max_profit': 0.20,         # 20% max
            'description': 'Swing trade (5 days)'
        },
        'swing_7d': {
            'holding_days': 7,
            'base_profit': 0.12,        # 12% base
            'max_profit': 0.20,         # 20% max
            'description': 'Swing trade (7 days)'
        },
        'positional_2w': {
            'holding_days': 14,
            'base_profit': 0.08,        # 8% base
            'max_profit': 0.15,         # 15% max
            'description': 'Positional (2 weeks)'
        },
        'positional': {
            'holding_days': 30,
            'base_profit': 0.10,        # 10% base
            'max_profit': 0.15,         # 15% max
            'description': 'Positional (1 month)'
        },
    }
    
    # Current selected timeframe (change this to switch strategies)
    CURRENT_TIMEFRAME = 'swing_5d'  # Default: 5-day swing trading

# ============================================================================
# STOCK LIST - LOAD FROM CSV
# ============================================================================
@st.cache_data
def load_stocks_from_csv():
    """Load stocks from CSV file, with fallback to hardcoded list"""
    try:
        csv_path = 'all_nse_bse_stocks.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Filter for active stocks only
            active_stocks = df[df['status'] == 'Active']['symbol'].tolist()
            return active_stocks if active_stocks else get_fallback_stocks()
        else:
            return get_fallback_stocks()
    except Exception as e:
        return get_fallback_stocks()

def get_fallback_stocks():
    """Fallback hardcoded list if CSV is not available"""
    return [
        # NIFTY 50
        'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
        'HCLTECH', 'TITAN', 'ITC', 'SUNPHARMA', 'AXISBANK', 'LT', 'ASIANPAINT',
        'ULTRACEMCO', 'BAJAJFINSV', 'MAHINDRA', 'WIPRO', 'MARUTI', 'BAJAJFLTSEC',
        'POWERGRID', 'GRASIM', 'HEROMOTOCO', 'JSWSTEEL', 'GMRINFRA', 'CUMMINSIND',
        'TATAMOTORS', 'TATASTEEL', 'SBILIFE', 'ICICIGI', 'INDHOTEL', 'NTPC',
        'APOLLOTYRE', 'TORNTPOWER', 'EICHERMOT', 'HINDPETRO', 'BPCL', 'GAIL',
        'ONGC', 'COALINDIA', 'TATAPOWER', 'IBREALEST', 'ADANIGREEN', 'AUBANK',
        'BANDHANBNK', 'CANBK', 'CHOLAFIN', 'CONCOR', 'DIVISLAB', 'LUPIN',
    ]

# Load stocks once at startup
NSE_STOCKS = load_stocks_from_csv()

# Custom CSS with Enhanced Styling
st.markdown("""
    <style>
    /* Main styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .header-container h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .header-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Signal badges */
    .buy-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    
    .sell-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    
    /* Signal container */
    .signal-container {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .signal-container:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    /* Strength indicator */
    .strength-high {
        color: #28a745;
        font-weight: bold;
    }
    
    .strength-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .strength-low {
        color: #dc3545;
        font-weight: bold;
    }
    
    /* Info box */
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        border-top: 1px solid #e0e0e0;
        margin-top: 3rem;
        font-size: 0.9rem;
    }
    
    /* Progress styling */
    .progress-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    /* Table styling */
    .dataframe {
        background-color: white;
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# Title with gradient header
st.markdown("""
    <div class="header-container">
        <h1>📊 Stock Market Screener</h1>
        <p>Real-time trading signals for NSE & BSE stocks (1600+) with Dynamic Profit Targets</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# NSE & BSE STOCK LIST - NOW LOADED FROM CSV IN load_stocks_from_csv()
# ============================================================================
# All stocks are loaded from all_nse_bse_stocks.csv with active status filter

# Helper function to get index name
def get_index_name(symbol):
    """Get index name from symbol (simplified - all loaded stocks are active)"""
    return 'NSE/BSE'

# ============================================================================
# ANALYZER FUNCTIONS
# ============================================================================
@st.cache_data
def get_stock_data(symbol, days=100):
    """Fetch stock data"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty or len(df) < 26:
            return None
        
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        
        return df
    except:
        return None

# ============================================================================
# VOLATILITY AND PROFIT TARGET CALCULATIONS
# ============================================================================
def calculate_volatility(df: pd.DataFrame) -> float:
    """Calculate stock volatility using standard deviation of returns"""
    try:
        if len(df) < 2:
            return 0.05  # Default 5%
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        return max(0.02, min(volatility, 0.50))  # Cap between 2% and 50%
    except:
        return 0.05

def calculate_dynamic_profit_target(current_price: float, volatility: float, 
                                   holding_days: int = None, timeframe: str = None) -> tuple:
    """
    Calculate profit target based on volatility, holding period, and timeframe
    Returns: (target_price, profit_pct, holding_days)
    """
    if timeframe is None:
        timeframe = TradingConfig.CURRENT_TIMEFRAME
    
    timeframe_config = TradingConfig.TIMEFRAMES.get(timeframe, TradingConfig.TIMEFRAMES['swing_5d'])
    
    if holding_days is None:
        holding_days = timeframe_config['holding_days']
    
    base_profit = timeframe_config['base_profit']
    max_profit = timeframe_config['max_profit']
    
    # Adjust base profit based on volatility
    volatility_adjustment = volatility * 0.5
    profit_pct = min(max_profit, max(base_profit + volatility_adjustment, 0.02))
    target_price = current_price * (1 + profit_pct)
    
    return target_price, profit_pct * 100, holding_days

def analyze_stock(symbol):
    """Analyze single stock using multiple indicators with dynamic profit targets"""
    result = {
        'symbol': symbol,
        'index': get_index_name(symbol),
        'signal': 'NO_SIGNAL',
        'score': 0,
        'entry': None,
        'entry_time': None,
        'exit_time': None,
        'target': None,
        'profit_pct': None,
        'stoploss': None,
        'reason': 'No data'
    }
    
    try:
        df = get_stock_data(symbol)
        
        if df is None or len(df) < 26:
            return result
        
        current_price = df['close'].iloc[-1]
        current_date = df['date'].iloc[-1]
        
        # Convert to datetime for proper formatting
        entry_datetime = pd.Timestamp(current_date)
        result['entry_time'] = entry_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate volatility for dynamic profit targets
        volatility = calculate_volatility(df)
        
        # ===== INDICATOR 1: EMA CROSSOVER =====
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        
        ema12_prev = ema12.iloc[-2]
        ema26_prev = ema26.iloc[-2]
        ema12_curr = ema12.iloc[-1]
        ema26_curr = ema26.iloc[-1]
        
        ema_bullish = (ema12_prev <= ema26_prev and ema12_curr > ema26_curr)
        ema_bearish = (ema12_prev >= ema26_prev and ema12_curr < ema26_curr)
        ema_score = 35 if ema_bullish or ema_bearish else 0
        
        # ===== INDICATOR 2: RSI (Relative Strength Index) =====
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_current = rsi.iloc[-1]
        
        # RSI: Overbought (>70) = strong signal, Oversold (<30) = strong signal
        rsi_score = 0
        if rsi_current > 70:  # Overbought (sell signal)
            rsi_score = 25
        elif rsi_current < 30:  # Oversold (buy signal)
            rsi_score = 25
        
        # ===== INDICATOR 3: MACD =====
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9).mean()
        histogram = macd - signal_line
        
        macd_prev = histogram.iloc[-2]
        macd_curr = histogram.iloc[-1]
        
        macd_bullish = (macd_prev < 0 and macd_curr > 0) or (macd_curr > 0 and histogram.iloc[-1] > histogram.iloc[-2])
        macd_bearish = (macd_prev > 0 and macd_curr < 0) or (macd_curr < 0 and histogram.iloc[-1] < histogram.iloc[-2])
        macd_score = 25 if (macd_bullish or macd_bearish) else 10
        
        # Volume check
        avg_vol = df['volume'].tail(20).mean()
        curr_vol = df['volume'].iloc[-1]
        volume_ok = curr_vol >= avg_vol
        
        if not volume_ok:
            result['reason'] = 'Low volume'
            return result
        
        # Price action vs MA
        sma50 = df['close'].rolling(50).mean().iloc[-1]
        price_vs_ma = (current_price - sma50) / sma50 * 100
        
        # ===== GENERATE SIGNAL WITH DYNAMIC PROFIT TARGETS =====
        timeframe = st.session_state.get('selected_timeframe', TradingConfig.CURRENT_TIMEFRAME)
        
        if ema_bullish and (rsi_current < 70):
            result['signal'] = 'BUY'
            result['entry'] = current_price
            
            # Calculate dynamic profit target
            target_price, profit_pct, holding_days = calculate_dynamic_profit_target(
                current_price, volatility, timeframe=timeframe
            )
            result['target'] = target_price
            result['profit_pct'] = profit_pct
            result['exit_time'] = (entry_datetime + timedelta(days=holding_days)).strftime('%Y-%m-%d')
            
            support = df['low'].tail(20).min()
            result['stoploss'] = support * 0.99
            
            # Composite score from multiple indicators
            score = ema_score + rsi_score + macd_score
            if price_vs_ma > 0:
                score += 5
            vol_ratio = curr_vol / avg_vol
            if vol_ratio > 1.2:
                score += 5
            
            result['score'] = min(100, score)
            result['reason'] = f'Multiple bullish indicators aligned | Volatility: {volatility:.1%}'
        
        elif ema_bearish and (rsi_current > 30):
            result['signal'] = 'SELL'
            result['entry'] = current_price
            
            # Calculate dynamic profit target (for short selling)
            target_price, profit_pct, holding_days = calculate_dynamic_profit_target(
                current_price, volatility, timeframe=timeframe
            )
            # For SELL signals, profit is on the downside
            result['target'] = current_price * (1 - profit_pct / 100)
            result['profit_pct'] = profit_pct
            result['exit_time'] = (entry_datetime + timedelta(days=holding_days)).strftime('%Y-%m-%d')
            
            resistance = df['high'].tail(20).max()
            result['stoploss'] = resistance * 1.01
            
            score = ema_score + rsi_score + macd_score
            if price_vs_ma < 0:
                score += 5
            
            result['score'] = min(100, score)
            result['reason'] = f'Multiple bearish indicators aligned | Volatility: {volatility:.1%}'
        
        return result
    
    except Exception as e:
        result['reason'] = f'Error: {str(e)[:20]}'
        return result

# ============================================================================
# BACKTEST FUNCTION
# ============================================================================
def backtest_signals(symbol, days=365, holding_period=5):
    """Backtest strategy over historical data for X days with specified holding period"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty or len(df) < 50:
            return {
                'symbol': symbol,
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'profitable_signals': 0,
                'win_rate': 0,
                'avg_return': 0,
                'total_return': 0,
                'max_profit': 0,
                'max_loss': 0,
                'timeframe': f'{days} days'
            }
        
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        
        signals = []
        buy_count = 0
        sell_count = 0
        winning_trades = 0
        losing_trades = 0
        total_profits = 0
        
        # Iterate through historical data to find signals
        for i in range(50, len(df) - holding_period):
            window = df.iloc[:i+1]
            
            # Calculate indicators
            ema12 = window['close'].ewm(span=12).mean()
            ema26 = window['close'].ewm(span=26).mean()
            
            if i < 1:
                continue
            
            ema12_prev = ema12.iloc[-2]
            ema26_prev = ema26.iloc[-2]
            ema12_curr = ema12.iloc[-1]
            ema26_curr = ema26.iloc[-1]
            
            # RSI
            delta = window['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_current = rsi.iloc[-1] if len(rsi) > 0 else 50
            
            entry_price = window['close'].iloc[-1]
            
            # BUY Signal
            if ema12_prev <= ema26_prev and ema12_curr > ema26_curr and rsi_current < 70:
                # Check future price (next N days)
                future_window = df.iloc[i:i+holding_period+1]
                if len(future_window) >= 2:
                    future_price = future_window['close'].iloc[-1]
                    target = entry_price * 1.05
                    sl = entry_price * 0.95
                    
                    if future_price >= target:
                        profit = ((future_price - entry_price) / entry_price) * 100
                        winning_trades += 1
                    elif future_price <= sl:
                        profit = ((future_price - entry_price) / entry_price) * 100
                        losing_trades += 1
                    else:
                        profit = ((future_price - entry_price) / entry_price) * 100
                        if profit > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                    
                    total_profits += profit
                    buy_count += 1
                    signals.append({
                        'date': window['date'].iloc[-1].strftime('%Y-%m-%d'),
                        'signal': 'BUY',
                        'entry_price': entry_price,
                        'exit_price': future_price,
                        'profit': profit,
                        'days_held': holding_period
                    })
            
            # SELL Signal
            elif ema12_prev >= ema26_prev and ema12_curr < ema26_curr and rsi_current > 30:
                future_window = df.iloc[i:i+holding_period+1]
                if len(future_window) >= 2:
                    future_price = future_window['close'].iloc[-1]
                    target = entry_price * 0.95
                    sl = entry_price * 1.05
                    
                    if future_price <= target:
                        profit = ((entry_price - future_price) / entry_price) * 100
                        winning_trades += 1
                    elif future_price >= sl:
                        profit = ((entry_price - future_price) / entry_price) * 100
                        losing_trades += 1
                    else:
                        profit = ((entry_price - future_price) / entry_price) * 100
                        if profit > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                    
                    total_profits += profit
                    sell_count += 1
                    signals.append({
                        'date': window['date'].iloc[-1].strftime('%Y-%m-%d'),
                        'signal': 'SELL',
                        'entry_price': entry_price,
                        'exit_price': future_price,
                        'profit': profit,
                        'days_held': holding_period
                    })
        
        total_signals = buy_count + sell_count
        win_rate = (winning_trades / total_signals * 100) if total_signals > 0 else 0
        avg_return = (total_profits / total_signals) if total_signals > 0 else 0
        
        return {
            'symbol': symbol,
            'total_signals': total_signals,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_return': total_profits,
            'timeframe': f'{days} days',
            'holding_period': holding_period,
            'signals': signals
        }
    
    except Exception as e:
        return {
            'symbol': symbol,
            'total_signals': 0,
            'error': str(e)
        }

# ============================================================================
# MAIN APP
# ============================================================================

# Sidebar
st.sidebar.header("⚙️ SCANNER SETTINGS")

# Timeframe selection
st.sidebar.markdown("### ⏱️ Trading Timeframe")
selected_timeframe = st.sidebar.selectbox(
    "Select profit target strategy:",
    options=list(TradingConfig.TIMEFRAMES.keys()),
    format_func=lambda x: f"{x.replace('_', ' ').title()} - {TradingConfig.TIMEFRAMES[x]['description']}",
    index=list(TradingConfig.TIMEFRAMES.keys()).index('swing_5d'),
    help="Choose your trading timeframe to set appropriate profit targets"
)
st.session_state.selected_timeframe = selected_timeframe

st.divider()

# Info section
with st.sidebar:
    st.markdown("""
    ### 📖 How It Works
    - **Scans** 1600+ NSE & BSE stocks
    - **Finds** profitable trading signals
    - **Sets** dynamic profit targets based on volatility
    - **Ranks** by signal strength (0-100)
    - **Takes** ~5-10 minutes to complete
    """)
    
    st.divider()
    
    scan_button = st.sidebar.button(
        "🔍 START SCAN",
        key="scan",
        help="Scan all 1600+ NSE and BSE stocks for trading signals with dynamic profit targets",
        use_container_width=True
    )
    
    st.divider()
    
    st.markdown("### 📊 Backtest Strategy")
    
    # Backtest symbol input
    backtest_symbol = st.text_input(
        "Stock symbol to backtest:",
        value="RELIANCE",
        placeholder="Enter stock symbol (e.g., TCS, INFY)",
        help="Test the strategy on a single stock using 365 days of historical data"
    ).upper()
    
    # Holding period input
    holding_period = st.slider(
        "Holding Period (days):",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        help="Number of days to hold each position before exiting"
    )
    
    backtest_button = st.button(
        f"📈 BACKTEST (365 days, {holding_period}d hold)",
        key="backtest",
        help="Backtest the strategy on historical data for 365 days",
        use_container_width=True
    )

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Status:</b> Ready to scan | <b>Coverage:</b> 1600+ Stocks | <b>Markets:</b> NSE & BSE | <b>Targets:</b> Dynamic
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'scanning' not in st.session_state:
    st.session_state.scanning = False
if 'scan_time' not in st.session_state:
    st.session_state.scan_time = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
    st.session_state.scan_time = None

# Run screener
if scan_button:
    st.session_state.scanning = True
    scan_start_time = datetime.now()
    
    # Progress section
    with st.container():
        progress_header = st.markdown('<div class="progress-section">', unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        progress_footer = st.markdown('</div>', unsafe_allow_html=True)
    
    results_list = []
    stocks_to_scan = NSE_STOCKS  # Scan ALL stocks
    
    for idx, symbol in enumerate(stocks_to_scan):
        # Update progress
        progress = (idx + 1) / len(stocks_to_scan)
        progress_bar.progress(progress)
        status_text.text(f"📈 Scanning: {idx+1}/{len(stocks_to_scan)} stocks | Current: {symbol}")
        
        # Analyze
        result = analyze_stock(symbol)
        if result['signal'] in ['BUY', 'SELL']:
            results_list.append(result)
        
        time.sleep(0.1)  # Rate limit
    
    # Calculate elapsed time
    scan_end_time = datetime.now()
    elapsed_time = (scan_end_time - scan_start_time).total_seconds()
    
    # Store results
    st.session_state.results = pd.DataFrame(results_list)
    st.session_state.scanning = False
    st.session_state.scan_time = scan_end_time
    
    # Clear progress animation and show success
    progress_bar.empty()
    status_text.empty()
    
    st.success(f"✅ Scan complete in {elapsed_time:.1f}s | Found {len(results_list)} high-probability signals")

# ============================================================================
# BACKTEST EXECUTION
# ============================================================================

if backtest_button:
    if not backtest_symbol:
        st.error("❌ Please enter a stock symbol to backtest")
    else:
        # Validate symbol exists in our stock list
        if backtest_symbol not in NSE_STOCKS:
            st.warning(f"⚠️ Stock symbol '{backtest_symbol}' not found in active list. Attempting backtest anyway...")
        
        st.session_state.backtest_running = True
        
        # Run backtest
        with st.spinner(f'🔄 Backtesting {backtest_symbol} over 365 days with {holding_period}-day holding period... This may take a moment'):
            try:
                backtest_results = backtest_signals(backtest_symbol, days=365, holding_period=holding_period)
                st.session_state.backtest_results = backtest_results
                st.success(f"✅ Backtest complete for {backtest_symbol}!")
            except Exception as e:
                st.error(f"❌ Error running backtest: {str(e)}")
                st.session_state.backtest_results = None
        
        st.session_state.backtest_running = False

# ============================================================================
# DISPLAY BACKTEST RESULTS
# ============================================================================

if st.session_state.backtest_results is not None:
    backtest_result = st.session_state.backtest_results
    
    st.markdown("---")
    st.subheader(f"📈 Backtest Results - {backtest_result['symbol']}")
    st.text(f"Strategy tested over 365 days with {backtest_result['holding_period']}-day holding period")
    
    # Performance metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📊 Total Signals",
            backtest_result['total_signals'],
            delta=f"Buy: {backtest_result['buy_signals']}, Sell: {backtest_result['sell_signals']}"
        )
    
    with col2:
        win_rate = backtest_result['win_rate']
        st.metric(
            "✅ Win Rate",
            f"{win_rate:.1f}%",
            delta=f"Wins: {backtest_result['winning_trades']}, Losses: {backtest_result['losing_trades']}"
        )
    
    with col3:
        avg_return = backtest_result['avg_return']
        color = "normal" if avg_return >= 0 else "off"
        st.metric(
            "📈 Avg Return",
            f"{avg_return:+.2f}%",
            delta=None
        )
    
    with col4:
        total_return = backtest_result['total_return']
        color = "normal" if total_return >= 0 else "off"
        st.metric(
            "💰 Total Return",
            f"{total_return:+.2f}%",
            delta=None
        )
    
    with col5:
        expectancy = (backtest_result['avg_return'] * backtest_result['win_rate'] / 100) if backtest_result['total_signals'] > 0 else 0
        st.metric(
            "🎯 Expectancy",
            f"{expectancy:+.2f}%",
            delta="Per trade"
        )
    
    # Detailed trades table
    st.markdown("---")
    st.subheader("📋 Trade History")
    
    if len(backtest_result['signals']) > 0:
        # Create DataFrame for display
        trades_data = []
        for signal in backtest_result['signals']:
            trades_data.append({
                'Date': signal['date'],
                'Signal': signal['signal'],
                'Entry Price': f"₹{signal['entry_price']:.2f}",
                'Exit Price': f"₹{signal['exit_price']:.2f}",
                'Profit %': f"{signal['profit']:.2f}%",
                'Status': '✅ Win' if signal['profit'] > 0 else '❌ Loss',
                'Days Held': signal.get('days_held', '-')
            })
        
        trades_df = pd.DataFrame(trades_data)
        
        # Color-code the table
        def color_status(val):
            if '✅' in val:
                return 'background-color: rgba(0, 255, 0, 0.1)'
            elif '❌' in val:
                return 'background-color: rgba(255, 0, 0, 0.1)'
            return ''
        
        styled_df = trades_df.style.map(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download backtest results
        csv_backtest = trades_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Backtest Results",
            data=csv_backtest,
            file_name=f"backtest_{backtest_result['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No signals were generated during the backtest period.")
    
    # Summary analysis
    st.markdown("---")
    st.subheader("📊 Analysis Summary")
    
    if backtest_result['total_signals'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Signal Distribution:**
            - Total Signals: {backtest_result['total_signals']}
            - Buy Signals: {backtest_result['buy_signals']} ({backtest_result['buy_signals']/backtest_result['total_signals']*100:.1f}%)
            - Sell Signals: {backtest_result['sell_signals']} ({backtest_result['sell_signals']/backtest_result['total_signals']*100:.1f}%)
            """)
        
        with col2:
            st.info(f"""
            **Win/Loss Summary:**
            - Winning Trades: {backtest_result['winning_trades']} ({backtest_result['win_rate']:.1f}%)
            - Losing Trades: {backtest_result['losing_trades']} ({100 - backtest_result['win_rate']:.1f}%)
            - Average Return: {backtest_result['avg_return']:+.2f}%
            - Total Return: {backtest_result['total_return']:+.2f}%
            """)

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

if st.session_state.results is not None and len(st.session_state.results) > 0:
    df_results = st.session_state.results
    
    # Filter
    buy_signals = df_results[df_results['signal'] == 'BUY'].sort_values('score', ascending=False)
    sell_signals = df_results[df_results['signal'] == 'SELL'].sort_values('score', ascending=False)
    
    # ==================== STATISTICS ====================
    st.markdown("---")
    st.subheader("📊 Scan Summary")
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📍 Total Signals", len(df_results), delta=len(df_results))
    
    with col2:
        st.metric("🟢 Buy Signals", len(buy_signals))
    
    with col3:
        st.metric("🔴 Sell Signals", len(sell_signals))
    
    with col4:
        avg_score = df_results['score'].mean()
        st.metric("⭐ Avg Strength", f"{avg_score:.0f}/100")
    
    with col5:
        best_signal = df_results['score'].max()
        st.metric("🏆 Best Score", f"{best_signal:.0f}/100")
    
    # Show backtest results summary if available
    if st.session_state.backtest_results is not None:
        st.markdown("---")
        st.subheader("📈 Latest Backtest Results")
        
        backtest_result = st.session_state.backtest_results
        backtest_col1, backtest_col2, backtest_col3, backtest_col4 = st.columns(4)
        
        with backtest_col1:
            st.metric(
                "📊 Total Signals",
                backtest_result['total_signals'],
                delta=f"Win: {backtest_result['winning_trades']}"
            )
        
        with backtest_col2:
            st.metric(
                "✅ Win Rate",
                f"{backtest_result['win_rate']:.1f}%",
                delta=f"Hold: {backtest_result['holding_period']}d"
            )
        
        with backtest_col3:
            st.metric(
                "📈 Avg Return",
                f"{backtest_result['avg_return']:+.2f}%"
            )
        
        with backtest_col4:
            st.metric(
                "💰 Total Return",
                f"{backtest_result['total_return']:+.2f}%"
            )
    
    # Export data
    st.markdown("---")
    
    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
    
    with col_export1:
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_export2:
        if st.session_state.scan_time:
            scan_time_str = st.session_state.scan_time.strftime('%Y-%m-%d %H:%M:%S')
            st.info(f"Last scan: {scan_time_str}")
    
    with col_export3:
        if st.session_state.backtest_results is not None:
            backtest_result = st.session_state.backtest_results
            csv_backtest_data = pd.DataFrame(backtest_result['signals']).to_csv(index=False)
            st.download_button(
                label="📊 Download Backtest CSV",
                data=csv_backtest_data,
                file_name=f"backtest_{backtest_result['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # ==================== TOP SIGNALS ====================
    st.markdown("---")
    st.subheader("🎯 Top Trading Signals")
    
    # Buy signals
    st.markdown(f"#### 🟢 BUY Signals ({len(buy_signals)} signals)")
    if len(buy_signals) > 0:
        for idx, (i, row) in enumerate(buy_signals.head(20).iterrows(), 1):
            if row['score'] >= 85:
                strength_class = "strength-high"
                strength_label = "🔥 Strong"
            elif row['score'] >= 70:
                strength_class = "strength-medium"
                strength_label = "⚡ Medium"
            else:
                strength_class = "strength-low"
                strength_label = "⚠️ Weak"
            
            with st.container():
                st.markdown(f"""
                <div class="signal-container">
                <b>{idx}. {row['symbol']}</b> <span class="buy-badge">BUY</span> 
                <span class="{strength_class}">{strength_label}</span> ({row['score']:.0f}/100)
                </div>
                """, unsafe_allow_html=True)
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.caption(f"📍 Entry: {row['entry_time']}")
                with col_t2:
                    st.caption(f"🎯 Exit: {row['exit_time']}")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Entry ₹", f"{row['entry']:.2f}")
                with col_b:
                    profit_display = f"+{row['profit_pct']:.1f}%" if row['profit_pct'] else f"+{((row['target']/row['entry']-1)*100):.1f}%"
                    st.metric("Target ₹", f"{row['target']:.2f}", delta=profit_display)
                with col_c:
                    st.metric("SL ₹", f"{row['stoploss']:.2f}")
                
                rr = (row['target'] - row['entry']) / (row['entry'] - row['stoploss']) if row['entry'] != row['stoploss'] else 0
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("R:R Ratio", f"1:{rr:.2f}")
                with col_r2:
                    st.metric("Strength", f"{row['score']:.0f}/100")
                
                st.progress(row['score'] / 100)
                st.markdown("---")
    else:
        st.info("❌ No buy signals found in current scan")
    
    st.divider()
    
    # Sell signals
    st.markdown(f"#### 🔴 SELL Signals ({len(sell_signals)} signals)")
    if len(sell_signals) > 0:
        for idx, (i, row) in enumerate(sell_signals.head(20).iterrows(), 1):
            if row['score'] >= 85:
                strength_class = "strength-high"
                strength_label = "🔥 Strong"
            elif row['score'] >= 70:
                strength_class = "strength-medium"
                strength_label = "⚡ Medium"
            else:
                strength_class = "strength-low"
                strength_label = "⚠️ Weak"
            
            with st.container():
                st.markdown(f"""
                <div class="signal-container">
                <b>{idx}. {row['symbol']}</b> <span class="sell-badge">SELL</span> 
                <span class="{strength_class}">{strength_label}</span> ({row['score']:.0f}/100)
                </div>
                """, unsafe_allow_html=True)
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.caption(f"📍 Entry: {row['entry_time']}")
                with col_t2:
                    st.caption(f"🎯 Exit: {row['exit_time']}")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Entry ₹", f"{row['entry']:.2f}")
                with col_b:
                    profit_display = f"-{row['profit_pct']:.1f}%" if row['profit_pct'] else f"{((row['target']/row['entry']-1)*100):.1f}%"
                    st.metric("Target ₹", f"{row['target']:.2f}", delta=profit_display)
                with col_c:
                    st.metric("SL ₹", f"{row['stoploss']:.2f}")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("Reason", row['reason'][:50])
                with col_r2:
                    st.metric("Strength", f"{row['score']:.0f}/100")
                
                st.progress(row['score'] / 100)
                st.markdown("---")
    else:
        st.info("❌ No sell signals found in current scan")
    
    # ==================== CHARTS ====================
    st.markdown("---")
    st.subheader("📈 Analytics & Visualizations")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### Signal Distribution")
        
        signal_dist = pd.DataFrame({
            'Signal': ['Buy', 'Sell'],
            'Count': [len(buy_signals), len(sell_signals)]
        })
        
        fig = px.pie(
            signal_dist,
            values='Count',
            names='Signal',
            color='Signal',
            color_discrete_map={'Buy': '#27ae60', 'Sell': '#e74c3c'},
            hole=0.3
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### Strength Distribution")
        
        strength_data = pd.cut(df_results['score'], bins=[0, 70, 80, 90, 100],
                             labels=['<70', '70-79', '80-89', '90-100'])
        strength_dist = strength_data.value_counts().sort_index()
        
        fig = px.bar(
            x=strength_dist.index,
            y=strength_dist.values,
            labels={'x': 'Signal Strength', 'y': 'Number of Signals'},
            color=strength_dist.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    if not st.session_state.scanning:
        st.markdown("""
        <div class="info-box">
        👈 <b>Ready to scan?</b> Click the <b>"🔍 START SCAN"</b> button in the left sidebar to begin scanning 400+ stocks!
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ## 📖 How This Screener Works
        
        ### Three Simple Steps:
        
        1. **Click "START SCAN"** 
           - Scans all 400+ NSE and BSE stocks
           - Analyzes price and volume patterns
           - Checks market conditions
        
        2. **Wait for Results** 
           - Typically takes 3-5 minutes
           - Progress bar shows real-time scanning
           - Live stock-by-stock updates
        
        3. **Review Signals**
           - View buy and sell opportunities
           - See entry/exit times and prices
           - Download results as CSV
        
        ### What You'll See:
        
        | Feature | Details |
        |---------|---------|
        | 🟢 **Buy Signals** | Stocks with bullish setup |
        | 🔴 **Sell Signals** | Stocks with bearish setup |
        | ⭐ **Signal Strength** | 0-100 confidence score |
        | 💰 **Entry/Exit Times** | Exact timestamps for trading |
        | 📊 **Risk-Reward Ratio** | Position management metrics |
        | 📥 **Export Data** | Download results as CSV |
        
        ⚠️ **Disclaimer**: For educational purposes only. Always do your own research before trading.
        """)

# Footer Section
st.markdown("---")
st.markdown("""
<div class="footer">
<p><b>Stock Market Screener</b> | NSE & BSE Coverage | 400+ Stocks Daily</p>
<p>Last Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
<p>⚠️ <i>For educational and research purposes only. Always consult a financial advisor before trading.</i></p>
</div>
""", unsafe_allow_html=True)
