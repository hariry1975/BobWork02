

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# ---------------------- Configuration ----------------------
COINS = {
    'DOGE': 'dogecoin',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'TRUMP': 'maga'
}

REFRESH_INTERVAL = 60  # seconds
DATA_POINTS = 14  # for RSI/SMA

# === Supabase Setup ===
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------- Utility Functions ----------------------

def get_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usd']
    except:
        return None

def calculate_rsi(prices, period=14):
    df = pd.Series(prices)
    delta = df.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calculate_sma(prices, length=5):
    if len(prices) < length:
        return None
    return sum(prices[-length:]) / length

def save_data_to_supabase(symbol, price):
    now = datetime.utcnow().isoformat()
    supabase.table("prices").insert({
        "coin": symbol,
        "price": price,
        "timestamp": now
    }).execute()

# ---------------------- App UI ----------------------

st.set_page_config("Crypto Signal App", layout="wide")
st.title("📈 Crypto Signal App")

for symbol, coin_id in COINS.items():
    with st.container():
        st.subheader(f"{symbol} - {coin_id.capitalize()}")

        history = []
        while len(history) < DATA_POINTS:
            price = get_price(coin_id)
            if price:
                history.append(price)
                save_data_to_supabase(symbol, price)
                time.sleep(1)
            else:
                st.error("❌ Could not retrieve price data.")
                break

        latest_price = history[-1] if history else None
        rsi = calculate_rsi(history)
        sma = calculate_sma(history)

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Price (USD)", f"${latest_price:.4f}" if latest_price else "N/A")
        col2.metric("📊 RSI", f"{rsi:.2f}" if rsi else "N/A")
        col3.metric("📈 SMA", f"{sma:.4f}" if sma else "N/A")

        # Signal Section
        if rsi and rsi < 30:
            st.success(f"✅ RSI = {rsi:.2f} → BUY Signal!")
        elif rsi and rsi > 70:
            st.warning(f"⚠️ RSI = {rsi:.2f} → SELL Signal!")
        else:
            st.info(f"⏳ RSI = {rsi:.2f} → No strong signal yet.")

        # Plot chart
        st.line_chart(history)

st.caption(f"⏱️ Auto-refreshes every {REFRESH_INTERVAL} seconds")

# Refresh
time.sleep(REFRESH_INTERVAL)
st.experimental_rerun()
