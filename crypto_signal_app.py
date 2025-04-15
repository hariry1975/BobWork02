

import streamlit as st
import requests
import pandas as pd
import datetime
from supabase import create_client, Client

# ---- Supabase Config ----
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Crypto Signal App", layout="wide")

st.title("📈 Crypto Signal Dashboard")

# CoinGecko coin ID mapping
coin_ids = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "maga"
}

def fetch_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        res = requests.get(url).json()
        return res[coin_id]["usd"]
    except:
        return None

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None

    df = pd.DataFrame(prices, columns=["close"])
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

def save_price(symbol, price):
    try:
        supabase.table("crypto_data").insert({
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"🔄 Could not save {symbol} to Supabase: {e}")

# Auto-refresh workaround using meta tag
st.markdown(
    '<meta http-equiv="refresh" content="60">',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

for i, (symbol, coin_id) in enumerate(coin_ids.items()):
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"## 💰 {symbol}")
        prices = []
        for _ in range(14):
            price = fetch_price(coin_id)
            if price:
                prices.append(price)

        live_price = fetch_price(coin_id)
        if live_price is None:
            st.error("❌ Could not retrieve price data.")
            continue

        prices.append(live_price)
        save_price(symbol, live_price)

        st.metric(label="Current Price (USD)", value=f"${live_price:.4f}")

        sma = sum(prices[-5:]) / 5 if len(prices) >= 5 else None
        rsi = calculate_rsi(prices)

        if sma is not None:
            st.markdown(f"📉 **SMA-5 = {sma:.4f}**")
        else:
            st.markdown("📉 SMA-5 not available.")

        if rsi is not None:
            if rsi < 30:
                st.success(f"🟢 RSI = {rsi:.2f} → **Buy Signal**")
            elif rsi > 70:
                st.error(f"🔴 RSI = {rsi:.2f} → **Sell Signal**")
            else:
                st.info(f"⏳ RSI = {rsi:.2f} → No strong signal yet.")
        else:
            st.info("⏳ RSI not available yet. Waiting for enough data.")

        st.line_chart(prices, height=200)

