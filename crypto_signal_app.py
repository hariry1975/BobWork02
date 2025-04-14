import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
import time
from supabase import create_client

# === Supabase Setup ===
url = "https://ncrxfifndtbinniykddg.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase = create_client(url, key)

# === Settings ===
st.set_page_config(layout="wide")
st.title("🚀 Live Crypto Signal App")

coin_ids = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "trumpcoin"  # make sure this ID is correct in CoinGecko
}

# === Utility Functions ===
def get_live_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    r = requests.get(url)
    data = r.json()
    return data.get(coin_id, {}).get("usd", None)

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None
    df = pd.DataFrame(prices, columns=["close"])
    rsi = RSIIndicator(close=df["close"], window=period)
    return rsi.rsi().iloc[-1]

def calculate_sma(prices, period=5):
    if len(prices) < period:
        return None
    df = pd.DataFrame(prices, columns=["close"])
    sma = SMAIndicator(close=df["close"], window=period)
    return sma.sma_indicator().iloc[-1]

def store_to_supabase(symbol, price, rsi, sma):
    supabase.table("crypto_data").insert({
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "sma": sma,
        "timestamp": int(time.time())
    }).execute()

# === Main Section ===
for coin, coin_id in coin_ids.items():
    with st.container():
        st.subheader(f"{coin} 🪙")

        prices = []
        for _ in range(13):
            price = get_live_price(coin_id)
            if price:
                prices.append(price)
            time.sleep(0.2)  # avoid hitting rate limits

        # Add current price as the 14th point
        live_price = get_live_price(coin_id)
        prices.append(live_price)

        if None in prices or not live_price:
            st.warning("❌ Could not retrieve price data.")
            continue

        latest_rsi = calculate_rsi(prices)
        latest_sma = calculate_sma(prices)

        store_to_supabase(coin, live_price, latest_rsi, latest_sma)

        st.metric(label=f"{coin} Price", value=f"${live_price:.4f}")
        if latest_rsi is not None:
            if latest_rsi < 30:
                st.success(f"✅ RSI = {latest_rsi:.2f} → Good time to BUY.")
            elif latest_rsi > 70:
                st.error(f"⚠️ RSI = {latest_rsi:.2f} → Consider SELLING.")
            else:
                st.warning(f"😐 RSI = {latest_rsi:.2f} → Neutral.")
        else:
            st.info("ℹ️ RSI not available yet.")

        if latest_sma:
            st.write(f"📈 SMA (5) = {latest_sma:.4f}")

        # Chart
        df_chart = pd.DataFrame(prices, columns=["Price"])
        st.line_chart(df_chart)

st.info("🔄 Auto-refreshes every 30 seconds.")
st.experimental_rerun()
time.sleep(30)
