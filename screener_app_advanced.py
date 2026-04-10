"""
NSE Screener - Advanced Strategy with vWAP & HLC3
Strategy: EMA Crossover + vWAP Confirmation + HLC3 Source
Run: streamlit run screener_app_advanced.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import time

# Page config
st.set_page_config(
    page_title="NSE Advanced Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 NSE Advanced Stock Screener")
st.markdown("**Strategy: EMA Crossover + vWAP Confirmation + HLC3 Source**")

# ============================================================================
# NSE STOCK LIST
# ============================================================================
NSE_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
    'HCLTECH', 'TITAN', 'ITC', 'SUNPHARMA', 'AXISBANK', 'LT', 'ASIANPAINT',
    'ULTRACEMCO', 'BAJAJFINSV', 'MAHINDRA', 'WIPRO', 'MARUTI', 'BAJAJFLTSEC',
    'POWERGRID', 'GRASIM', 'HEROMOTOCO', 'JSWSTEEL', 'GMRINFRA',
    'CUMMINSIND', 'TATAMOTORS', 'TATASTEEL', 'SBILIFE', 'ICICIGI',
    'INDHOTEL', 'NTPC', 'APOLLOTYRE', 'TORNTPOWER', 'EICHERMOT',
    'HINDPETRO', 'BPCL', 'GAIL', 'ONGC', 'COALINDIA',
    'TATAPOWER', 'IBREALEST', 'ADANIGREEN', 'AUBANK', 'BANDHANBNK',
    'CANBK', 'CHOLAFIN', 'CONCOR', 'DIVISLAB', 'LUPIN',
]

# ============================================================================
# TECHNICAL INDICATORS WITH vWAP & HLC3
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

def calculate_hlc3(df):
    """Calculate HLC3 - Average of High, Low, Close"""
    df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
    return df

def calculate_vwap(df):
    """Calculate vWAP - Volume Weighted Average Price using HLC3"""
    df = calculate_hlc3(df)
    
    # vWAP = Sum(Volume * HLC3) / Sum(Volume)
    df['vwap_cum_vol_hlc3'] = (df['volume'] * df['hlc3']).cumsum()
    df['vwap_cum_vol'] = df['volume'].cumsum()
    df['vwap'] = df['vwap_cum_vol_hlc3'] / df['vwap_cum_vol']
    
    return df

def analyze_stock_advanced(symbol):
    """Advanced analysis with vWAP and HLC3"""
    result = {
        'symbol': symbol,
        'signal': 'NO_SIGNAL',
        'score': 0,
        'entry': None,
        'target': None,
        'stoploss': None,
        'reason': 'No data',
        'vwap_level': None,
        'hlc3_level': None
    }
    
    try:
        df = get_stock_data(symbol)
        
        if df is None or len(df) < 26:
            return result
        
        # Calculate indicators
        df = calculate_vwap(df)
        
        current_price = df['close'].iloc[-1]
        current_hlc3 = df['hlc3'].iloc[-1]
        current_vwap = df['vwap'].iloc[-1]
        
        # Calculate EMA
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        
        # Check crossover
        ema12_prev = ema12.iloc[-2]
        ema26_prev = ema26.iloc[-2]
        ema12_curr = ema12.iloc[-1]
        ema26_curr = ema26.iloc[-1]
        
        # Volume check
        avg_vol = df['volume'].tail(20).mean()
        curr_vol = df['volume'].iloc[-1]
        volume_ok = curr_vol >= avg_vol
        
        if not volume_ok:
            result['reason'] = 'Low volume'
            return result
        
        # Price vs vWAP & HLC3
        price_above_vwap = current_price > current_vwap
        price_above_hlc3 = current_price > current_hlc3
        hlc3_above_vwap = current_hlc3 > current_vwap
        
        # SMA 50
        sma50 = df['close'].rolling(50).mean().iloc[-1]
        price_above_ma = current_price > sma50
        
        result['vwap_level'] = current_vwap
        result['hlc3_level'] = current_hlc3
        
        # ==================== BULLISH SIGNAL ====================
        # BUY: EMA crossover + Price above vWAP + Volume confirmation
        if ema12_prev <= ema26_prev and ema12_curr > ema26_curr:
            
            # Bullish conditions
            bullish_conditions = 0
            
            # Condition 1: EMA crossover (required)
            bullish_conditions += 1
            
            # Condition 2: Price above vWAP
            if price_above_vwap:
                bullish_conditions += 1
            
            # Condition 3: HLC3 above vWAP
            if hlc3_above_vwap:
                bullish_conditions += 1
            
            # Condition 4: Price above SMA50
            if price_above_ma:
                bullish_conditions += 1
            
            # If at least 2 conditions met (EMA + 1 more)
            if bullish_conditions >= 2:
                result['signal'] = 'BUY'
                result['entry'] = current_price
                
                support = df['low'].tail(20).min()
                result['stoploss'] = support * 0.99
                result['target'] = current_price * 1.05
                
                # Calculate score based on conditions
                score = 65  # Base
                
                # +10 for each bullish condition
                score += bullish_conditions * 8
                
                # +5 for volume
                vol_ratio = curr_vol / avg_vol
                if vol_ratio > 1.2:
                    score += 5
                
                # +5 for HLC3 position
                hlc3_distance = (current_price - current_hlc3) / current_hlc3 * 100
                if hlc3_distance > 0 and hlc3_distance < 1:
                    score += 5
                
                result['score'] = min(100, score)
                
                condition_text = []
                if ema12_curr > ema26_curr:
                    condition_text.append("EMA12>EMA26")
                if price_above_vwap:
                    condition_text.append("Price>vWAP")
                if hlc3_above_vwap:
                    condition_text.append("HLC3>vWAP")
                if price_above_ma:
                    condition_text.append("Price>SMA50")
                
                result['reason'] = f"Bullish | {', '.join(condition_text[:3])}"
        
        # ==================== BEARISH SIGNAL ====================
        # SELL: EMA crossover + Price below vWAP
        elif ema12_prev >= ema26_prev and ema12_curr < ema26_curr:
            
            # Bearish conditions
            bearish_conditions = 0
            
            # Condition 1: EMA crossover (required)
            bearish_conditions += 1
            
            # Condition 2: Price below vWAP
            if not price_above_vwap:
                bearish_conditions += 1
            
            # Condition 3: HLC3 below vWAP
            if not hlc3_above_vwap:
                bearish_conditions += 1
            
            # Condition 4: Price below SMA50
            if not price_above_ma:
                bearish_conditions += 1
            
            if bearish_conditions >= 2:
                result['signal'] = 'SELL'
                result['entry'] = current_price
                result['target'] = current_price * 0.95
                
                resistance = df['high'].tail(20).max()
                result['stoploss'] = resistance * 1.01
                
                score = 65
                score += bearish_conditions * 8
                
                vol_ratio = curr_vol / avg_vol
                if vol_ratio > 1.2:
                    score += 5
                
                result['score'] = min(100, score)
                
                condition_text = []
                if ema12_curr < ema26_curr:
                    condition_text.append("EMA12<EMA26")
                if not price_above_vwap:
                    condition_text.append("Price<vWAP")
                if not hlc3_above_vwap:
                    condition_text.append("HLC3<vWAP")
                if not price_above_ma:
                    condition_text.append("Price<SMA50")
                
                result['reason'] = f"Bearish | {', '.join(condition_text[:3])}"
        
        return result
    
    except Exception as e:
        result['reason'] = f'Error'
        return result

# ============================================================================
# MAIN APP
# ============================================================================

st.sidebar.header("⚙️ Settings")
st.sidebar.markdown("**Strategy Parameters:**")
st.sidebar.info("📊 **EMA 12/26 Crossover** + vWAP + HLC3")

scan_button = st.sidebar.button("🔍 RUN SCREENER NOW", key="scan", 
                               help="Scan all NSE stocks with advanced strategy")
num_stocks = st.sidebar.slider("Stocks to scan:", 10, 50, 30)

st.sidebar.divider()
st.sidebar.markdown("**Strategy Explanation:**")
st.sidebar.markdown("""
- **EMA 12/26**: Bullish when 12 crosses above 26
- **vWAP**: Volume-weighted average price
- **HLC3**: Average of High, Low, Close
- **Conditions**: Need EMA + 1 more condition
- **Score**: 0-100 based on alignment
""")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'scanning' not in st.session_state:
    st.session_state.scanning = False

# Run screener
if scan_button:
    st.session_state.scanning = True
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results_list = []
    stocks_to_scan = NSE_STOCKS[:num_stocks]
    
    for idx, symbol in enumerate(stocks_to_scan):
        progress = (idx + 1) / len(stocks_to_scan)
        progress_bar.progress(progress)
        status_text.text(f"Scanning: {idx+1}/{len(stocks_to_scan)} - {symbol}")
        
        result = analyze_stock_advanced(symbol)
        if result['signal'] in ['BUY', 'SELL']:
            results_list.append(result)
        
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    st.session_state.results = pd.DataFrame(results_list)
    st.session_state.scanning = False
    
    st.success(f"✅ Scan complete! Found {len(results_list)} signals")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

if st.session_state.results is not None and len(st.session_state.results) > 0:
    df_results = st.session_state.results
    
    buy_signals = df_results[df_results['signal'] == 'BUY'].sort_values('score', ascending=False)
    sell_signals = df_results[df_results['signal'] == 'SELL'].sort_values('score', ascending=False)
    
    # ==================== STATISTICS ====================
    st.header("📊 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Signals", len(df_results))
    with col2:
        st.metric("🟢 Buy Signals", len(buy_signals))
    with col3:
        st.metric("🔴 Sell Signals", len(sell_signals))
    with col4:
        avg_score = df_results['score'].mean()
        st.metric("Avg Strength", f"{avg_score:.0f}/100")
    
    # ==================== TOP SIGNALS ====================
    st.header("🎯 TOP TRADING SIGNALS")
    
    col_buy, col_sell = st.columns(2)
    
    with col_buy:
        st.subheader("🟢 BUY SIGNALS (Strong Bullish)")
        
        if len(buy_signals) > 0:
            for idx, (i, row) in enumerate(buy_signals.head(10).iterrows(), 1):
                with st.expander(f"{idx}. {row['symbol']} - {row['score']:.0f}/100"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Entry", f"₹{row['entry']:.2f}")
                        st.metric("Target", f"₹{row['target']:.2f}",
                                delta=f"+{((row['target']/row['entry']-1)*100):.2f}%")
                    with col_b:
                        st.metric("SL", f"₹{row['stoploss']:.2f}",
                                delta=f"-{((1-row['stoploss']/row['entry'])*100):.2f}%")
                        rr = (row['target'] - row['entry']) / (row['entry'] - row['stoploss']) if row['entry'] != row['stoploss'] else 0
                        st.metric("RR", f"1:{rr:.2f}")
                    
                    # vWAP info
                    st.markdown(f"""
                    **Technical Levels:**
                    - vWAP: ₹{row['vwap_level']:.2f}
                    - HLC3: ₹{row['hlc3_level']:.2f}
                    - Entry vs vWAP: {((row['entry']/row['vwap_level']-1)*100):+.2f}%
                    
                    **Signal:** {row['reason']}
                    """)
                    
                    st.progress(row['score'] / 100)
        else:
            st.info("No buy signals")
    
    with col_sell:
        st.subheader("🔴 SELL SIGNALS (Strong Bearish)")
        
        if len(sell_signals) > 0:
            for idx, (i, row) in enumerate(sell_signals.head(10).iterrows(), 1):
                with st.expander(f"{idx}. {row['symbol']} - {row['score']:.0f}/100"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Entry", f"₹{row['entry']:.2f}")
                        st.metric("Target", f"₹{row['target']:.2f}",
                                delta=f"{((row['target']/row['entry']-1)*100):.2f}%")
                    with col_b:
                        st.metric("SL", f"₹{row['stoploss']:.2f}")
                        st.metric("Strength", f"{row['score']:.0f}/100")
                    
                    st.markdown(f"""
                    **Technical Levels:**
                    - vWAP: ₹{row['vwap_level']:.2f}
                    - HLC3: ₹{row['hlc3_level']:.2f}
                    - Entry vs vWAP: {((row['entry']/row['vwap_level']-1)*100):+.2f}%
                    
                    **Signal:** {row['reason']}
                    """)
                    
                    st.progress(row['score'] / 100)
        else:
            st.info("No sell signals")
    
    # ==================== CHARTS ====================
    st.header("📈 Analytics")
    
    col_chart1, col_chart2, col_chart3 = st.columns(3)
    
    with col_chart1:
        st.subheader("Signal Distribution")
        
        signal_dist = pd.DataFrame({
            'Signal': ['Buy', 'Sell'],
            'Count': [len(buy_signals), len(sell_signals)]
        })
        
        fig = px.pie(
            signal_dist,
            values='Count',
            names='Signal',
            color='Signal',
            color_discrete_map={'Buy': '#27ae60', 'Sell': '#e74c3c'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.subheader("Signal Strength")
        
        strength_data = pd.cut(df_results['score'], bins=[0, 70, 80, 90, 100],
                             labels=['<70', '70-79', '80-89', '90-100'])
        strength_dist = strength_data.value_counts().sort_index()
        
        fig = px.bar(
            x=strength_dist.index,
            y=strength_dist.values,
            labels={'x': 'Strength', 'y': 'Count'},
            color=strength_dist.values,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart3:
        st.subheader("Buy vs Sell Signals")
        
        signal_type = pd.DataFrame({
            'Type': ['Buy Signals', 'Sell Signals'],
            'Count': [len(buy_signals), len(sell_signals)]
        })
        
        fig = px.bar(
            signal_type,
            x='Type',
            y='Count',
            color='Type',
            color_discrete_map={'Buy Signals': '#27ae60', 'Sell Signals': '#e74c3c'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ==================== DETAILED TABLE ====================
    st.header("📋 All Signals - Detailed")
    
    sort_by = st.selectbox("Sort by:", ["Score (High)", "Entry Price", "Symbol"])
    
    if sort_by == "Score (High)":
        df_display = df_results.sort_values('score', ascending=False)
    elif sort_by == "Entry Price":
        df_display = df_results.sort_values('entry', ascending=False)
    else:
        df_display = df_results.sort_values('symbol')
    
    display_df = df_display[[
        'symbol', 'signal', 'entry', 'vwap_level', 'hlc3_level', 'target', 'stoploss', 'score'
    ]].copy()
    
    display_df.columns = ['Symbol', 'Signal', 'Entry (₹)', 'vWAP (₹)', 'HLC3 (₹)', 'Target (₹)', 'SL (₹)', 'Strength']
    display_df['Entry (₹)'] = display_df['Entry (₹)'].apply(lambda x: f"₹{x:.2f}")
    display_df['vWAP (₹)'] = display_df['vWAP (₹)'].apply(lambda x: f"₹{x:.2f}")
    display_df['HLC3 (₹)'] = display_df['HLC3 (₹)'].apply(lambda x: f"₹{x:.2f}")
    display_df['Target (₹)'] = display_df['Target (₹)'].apply(lambda x: f"₹{x:.2f}")
    display_df['SL (₹)'] = display_df['SL (₹)'].apply(lambda x: f"₹{x:.2f}")
    display_df['Strength'] = display_df['Strength'].apply(lambda x: f"{x:.0f}/100")
    
    st.dataframe(display_df, use_container_width=True)
    
    # ==================== RECOMMENDATIONS ====================
    st.header("💡 TOP RECOMMENDATIONS")
    
    rec_col1, rec_col2 = st.columns(2)
    
    with rec_col1:
        st.subheader("🟢 Best Buy (Highest Score)")
        if len(buy_signals) > 0:
            top_buy = buy_signals.iloc[0]
            st.success(f"""
            **{top_buy['symbol']}**
            
            **Entry:** ₹{top_buy['entry']:.2f}
            **Target:** ₹{top_buy['target']:.2f} (+{((top_buy['target']/top_buy['entry']-1)*100):.2f}%)
            **SL:** ₹{top_buy['stoploss']:.2f}
            **Strength:** {top_buy['score']:.0f}/100
            
            **vWAP:** ₹{top_buy['vwap_level']:.2f}
            **HLC3:** ₹{top_buy['hlc3_level']:.2f}
            
            **Signal:** {top_buy['reason']}
            """)
    
    with rec_col2:
        st.subheader("🔴 Best Sell (Highest Score)")
        if len(sell_signals) > 0:
            top_sell = sell_signals.iloc[0]
            st.error(f"""
            **{top_sell['symbol']}**
            
            **Entry:** ₹{top_sell['entry']:.2f}
            **Target:** ₹{top_sell['target']:.2f} ({((top_sell['target']/top_sell['entry']-1)*100):.2f}%)
            **SL:** ₹{top_sell['stoploss']:.2f}
            **Strength:** {top_sell['score']:.0f}/100
            
            **vWAP:** ₹{top_sell['vwap_level']:.2f}
            **HLC3:** ₹{top_sell['hlc3_level']:.2f}
            
            **Signal:** {top_sell['reason']}
            """)
    
    # Download
    st.divider()
    csv = df_results.to_csv(index=False)
    st.download_button(
        label="📥 Download Results (CSV)",
        data=csv,
        file_name=f"nse_screener_advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    if not st.session_state.scanning:
        st.info("👈 Click **RUN SCREENER NOW** to scan NSE stocks!")
        
        st.markdown("""
        ## Advanced Strategy Details:
        
        ### 📊 Indicators Used:
        
        **1. EMA 12/26 Crossover**
        - Bullish: EMA12 crosses above EMA26
        - Bearish: EMA12 crosses below EMA26
        
        **2. vWAP (Volume Weighted Average Price)**
        - Calculated from HLC3 (High+Low+Close)/3
        - Formula: Sum(Volume × HLC3) / Sum(Volume)
        - Price above vWAP = Bullish
        - Price below vWAP = Bearish
        
        **3. HLC3 (High-Low-Close Average)**
        - More accurate than close price alone
        - Used as price source for vWAP
        - Reduces false signals
        
        **4. SMA 50 Filter**
        - Trend confirmation
        - Additional signal strength
        
        ### ✅ Signal Conditions:
        
        **BUY Signals (All required):**
        - ✓ EMA12 > EMA26 (Moving Avg Crossover)
        - ✓ Price > vWAP (Volume Support)
        - ✓ HLC3 > vWAP (Price Strength)
        - ✓ High Volume Confirmation
        
        **SELL Signals:**
        - ✓ EMA12 < EMA26 (Trend Reversal)
        - ✓ Price < vWAP (Volume Resistance)
        - ✓ HLC3 < vWAP (Price Weakness)
        
        ### 🎯 Scoring (0-100):
        - Base: 65 points
        - +8 points per bullish condition met
        - +5 points for volume confirmation
        - +5 points for price positioning
        
        ### Example:
        - EMA crossover + Price>vWAP + HLC3>vWAP + Volume = **93/100** (Excellent)
        - EMA crossover only = **65/100** (Weak)
        
        Click **RUN SCREENER NOW** to start! 🚀
        """)

# Footer
st.divider()
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("⚠️ **Disclaimer:** For educational purposes only. Trade at your own risk.")
