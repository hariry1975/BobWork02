

import streamlit as st
import requests
import pandas as pd
import datetime
from supabase import create_client, Client

# ---- Supabase Config ----
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---- Coin List ----
coin_ids = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "trump"
}

# ---- Fetch Live Price ----
def get_live_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usd']
    except:
        return None

# ---- Calculate RSI ----
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    delta = pd.Series(prices).diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

# ---- Calculate SMA ----
def calculate_sma(prices, length=5):
    clean_prices = [p for p in prices[-length:] if p is not None]
    if len(clean_prices) < length:
        return None
    return sum(clean_prices) / length

# ---- Save to Supabase ----
def save_data_to_supabase(symbol, price):
    now = datetime.datetime.now().isoformat()
    try:
        supabase.table("prices").insert({
            "symbol": symbol,
            "price": price,
            "timestamp": now
        }).execute()
    except Exception as e:
        st.error(f"❌ Failed to save {symbol} data: {e}")

# ---- UI ----
st.set_page_config(page_title="📊 Crypto Signal App", layout="wide")
st.title("📈 Real-Time Crypto Signal Dashboard")

# ---- Main Loop ----
for symbol, coin_id in coin_ids.items():
    with st.container():
        st.subheader(f"💰 {symbol}")

        # Fetch and store 14 price points (13 history + 1 live)
        prices = []
        for _ in range(13):
            price = get_live_price(coin_id)
            prices.append(price)
        latest_price = get_live_price(coin_id)
        prices.append(latest_price)

        if latest_price:
            st.metric(label="Current Price (USD)", value=f"${latest_price:.4f}")
            save_data_to_supabase(symbol, latest_price)
        else:
            st.error("⚠️ Could not retrieve price data.")
            continue

        # Calculate RSI
        rsi = calculate_rsi(prices)
        if rsi is not None:
            if rsi < 30:
                st.success(f"📉 RSI = {rsi:.2f} → **Buy Signal**")
            elif rsi > 70:
                st.warning(f"📈 RSI = {rsi:.2f} → **Sell Signal**")
            else:
                st.info(f"⏳ RSI = {rsi:.2f} → No strong signal yet.")
        else:
            st.info("⏳ RSI not available yet. Waiting for enough data.")

        # Calculate SMA
        sma = calculate_sma(prices)
        if sma is not None:
            st.write(f"📊 5-period SMA: ${sma:.4f}")
        else:
            st.write("📊 SMA not available.")

        # Price Chart
        df = pd.DataFrame({"Price": prices}, index=pd.date_range(end=pd.Timestamp.now(), periods=len(prices), freq="min"))
        st.line_chart(df)

# ---- Auto Refresh ----
st.experimental_autorefresh(interval=60 * 1000, key="refresh")
