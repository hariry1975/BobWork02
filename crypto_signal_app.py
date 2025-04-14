# crypto_signal_app.py
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Coin mapping
coin_ids = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "trumpcoin"
}

# Technical indicator functions
def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def calculate_sma(prices, length=5):
    if len(prices) < length:
        return None
    return round(pd.Series(prices[-length:]).mean(), 4)

# Get live price from CoinGecko
def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    try:
        response = requests.get(url).json()
        return response[coin]['usd']
    except:
        return None

# Save to Supabase
def save_to_supabase(coin, price, rsi, sma):
    data = {
        "coin": coin,
        "price": price,
        "rsi": rsi,
        "sma": sma,
        "timestamp": datetime.utcnow().isoformat()
    }
    supabase.table("prices").insert(data).execute()

# Load historical data from Supabase
def load_history(coin):
    response = supabase.table("prices").select("*").eq("coin", coin).order("timestamp", desc=True).limit(50).execute()
    return pd.DataFrame(response.data)

# Streamlit layout
st.set_page_config(page_title="🚀 Crypto Signal App", layout="wide")
st.title("📊 Real-time Crypto Signal Dashboard")

# Refresh every 30 seconds
st_autorefresh = st.empty()
st_autorefresh.markdown("⏳ Auto-refreshing every 30 seconds...")

# Display data for each coin
for name, coin_id in coin_ids.items():
    st.markdown(f"## 💰 {name}")
    col1, col2 = st.columns([1, 2])

    with col1:
        price = get_price(coin_id)
        if price is not None:
            history = load_history(name)
            prices = [price] + history['price'].tolist()
            rsi = calculate_rsi(prices)
            sma = calculate_sma(prices)
            save_to_supabase(name, price, rsi, sma)

            st.metric("Current Price (USD)", f"${price:.4f}")
            if rsi:
                st.metric("RSI", rsi)
            if sma:
                st.metric("SMA (5)", sma)

            if rsi and rsi < 30:
                st.success("✅ RSI suggests **BUY** 📈")
            elif rsi and rsi > 70:
                st.error("❌ RSI suggests **SELL** 📉")
            else:
                st.warning("😐 No strong signal. Hold position.")
        else:
            st.error("❌ Failed to fetch price data")

    with col2:
        chart_data = load_history(name).sort_values("timestamp")
        if not chart_data.empty:
            st.line_chart(chart_data.set_index("timestamp")["price"])

# Auto-refresh
st_autorefresh = st.empty()
time.sleep(30)
st.experimental_rerun()