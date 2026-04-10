import streamlit as st
import pandas as pd
import numpy as np
<<<<<<< HEAD

=======
import plotly.graph_objects as go
>>>>>>> e0a2c931a344d4375028807465cf68258c98a25c
from datetime import datetime, timedelta
import yfinance as yf
import concurrent.futures

# -------------------------------
# Page Config & Styling
# -------------------------------
st.set_page_config(page_title="NSE Advanced Screener", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .header {background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
             padding:20px;border-radius:10px;color:white;margin-bottom:20px;}
    .stMetric {background: linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);
               padding:15px;border-radius:8px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header">
<<<<<<< HEAD
        <h1>📊 Advanced Stock Screener</h1>
      <p>EMA 12/26 + vWAP + HLC3 + Volume Confirmation</p> 
        <p>🌍 Real-Time • 1000+ Stocks • Risk Management</p>
=======
        <h1>📊 NSE Advanced Stock Screener</h1>
        <p>EMA 12/26 + vWAP + HLC3 + Volume Confirmation</p>
        <p>🌍 Real-Time • 100+ Stocks • Risk Management</p>
>>>>>>> e0a2c931a344d4375028807465cf68258c98a25c
    </div>
""", unsafe_allow_html=True)

# -------------------------------
# Stock Universe
# -------------------------------
NSE_STOCKS = ['RELIANCE','TCS','INFY','HDFC','ICICIBANK','SBIN','BHARTIARTL',
              'HCLTECH','TITAN','ITC','SUNPHARMA','AXISBANK','LT','ASIANPAINT',
              'ULTRACEMCO','BAJAJFINSV','MARUTI','TATAMOTORS','TATASTEEL','WIPRO']

# -------------------------------
# Data Fetch & Indicators
# -------------------------------
@st.cache_data
def get_stock_data(symbol, days=100):
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        df = yf.Ticker(f"{symbol}.NS").history(start=start_date, end=end_date)
        if df.empty or len(df) < 26: return None
        df = df.reset_index()
        df.rename(columns={"Date":"date","Open":"open","High":"high",
                           "Low":"low","Close":"close","Volume":"volume"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")
        return None

def calculate_vwap(df):
    df['hlc3'] = (df['high']+df['low']+df['close'])/3
    df['vwap'] = (df['volume']*df['hlc3']).cumsum()/df['volume'].cumsum()
    return df

def position_size(entry, stoploss, capital, risk_pct):
    risk_amount = capital*(risk_pct/100)
    per_share_risk = entry-stoploss
    return int(risk_amount/per_share_risk) if per_share_risk>0 else 0

# -------------------------------
# Signal Analysis
# -------------------------------
def analyze_stock(symbol, capital=None, risk_pct=None):
    result = {"symbol":symbol,"signal":"NO_SIGNAL","score":0,"entry":None,
              "target":None,"stoploss":None,"reason":"No data","vwap":None,
              "hlc3":None,"profit_pct":None,"risk_pct":None,"position_size":None}
    df = get_stock_data(symbol)
    if df is None: return result
    df = calculate_vwap(df)

    price = df['close'].iloc[-1]
    hlc3 = df['hlc3'].iloc[-1]
    vwap = df['vwap'].iloc[-1]
    ema12, ema26 = df['close'].ewm(span=12).mean(), df['close'].ewm(span=26).mean()
    ema12_prev, ema26_prev = ema12.iloc[-2], ema26.iloc[-2]
    ema12_curr, ema26_curr = ema12.iloc[-1], ema26.iloc[-1]
    avg_vol, curr_vol = df['volume'].tail(20).mean(), df['volume'].iloc[-1]
    if curr_vol<avg_vol: return result

    sma50 = df['close'].rolling(50).mean().iloc[-1]
    bullish = ema12_prev<=ema26_prev and ema12_curr>ema26_curr
    bearish = ema12_prev>=ema26_prev and ema12_curr<ema26_curr

    if bullish:
        result.update({"signal":"BUY","entry":price,"target":price*1.05,
                       "stoploss":df['low'].tail(20).min()*0.99,
                       "profit_pct":5,"risk_pct":((price-result['stoploss'])/price)*100})
    elif bearish:
        result.update({"signal":"SELL","entry":price,"target":price*0.95,
                       "stoploss":df['high'].tail(20).max()*1.01,
                       "profit_pct":5,"risk_pct":((result['stoploss']-price)/price)*100})
    else: return result

    score=60
    score+=10 if price>vwap else 0
    score+=10 if hlc3>vwap else 0
    score+=10 if price>sma50 else 0
    if curr_vol/avg_vol>1.2: score+=5
    result['score']=min(100,score)
    result['vwap'],result['hlc3']=vwap,hlc3

    if capital and risk_pct:
        result['position_size']=position_size(result['entry'],result['stoploss'],capital,risk_pct)
    return result

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.header("⚙️ Settings")
num_stocks=st.sidebar.slider("Stocks to scan:",10,len(NSE_STOCKS),20)
mode=st.sidebar.radio("Capital Mode:",["Unlimited","Fixed"])
capital=risk_pct=None
if mode=="Fixed":
    capital=st.sidebar.number_input("Capital (₹):",10000,1000000,100000,10000)
    risk_pct=st.sidebar.slider("Risk per trade %:",0.5,5.0,2.0,0.1)
scan=st.sidebar.button("🔍 Run Screener")

# -------------------------------
# Run Scan
# -------------------------------
if scan:
    with st.spinner("Scanning stocks..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures={ex.submit(analyze_stock,s,capital,risk_pct):s for s in NSE_STOCKS[:num_stocks]}
            results=[f.result() for f in concurrent.futures.as_completed(futures)]
    df=pd.DataFrame([r for r in results if r['signal']!="NO_SIGNAL"])
    if df.empty: st.warning("No signals found.")
    else:
        st.success(f"✅ Found {len(df)} signals")
        buy=df[df['signal']=="BUY"].sort_values("score",ascending=False)
        sell=df[df['signal']=="SELL"].sort_values("score",ascending=False)

        # Summary
        st.metric("Total Signals",len(df))
        st.metric("🟢 Buy",len(buy))
        st.metric("🔴 Sell",len(sell))
        st.metric("Avg Strength",f"{df['score'].mean():.0f}/100")

        # Top Opportunities
        st.header("🎯 Top Opportunities")
        for subset,label in [(buy,"Buy"),(sell,"Sell")]:
            st.subheader(f"{label} Signals")
            for _,row in subset.head(5).iterrows():
                st.metric("Entry",f"₹{row['entry']:.2f}")
                st.metric("Target",f"₹{row['target']:.2f}")
                st.metric("Stoploss",f"₹{row['stoploss']:.2f}")
                if row['position_size']: st.metric("Position Size",f"{row['position_size']} shares")
                st.progress(row['score']/100)

        # Detailed Table
        st.header("📋 All Signals")
        st.dataframe(df,use_container_width=True)

        # Download
        st.download_button("📥 Download CSV",df.to_csv(index=False),
                           f"screener_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv","text/csv")
