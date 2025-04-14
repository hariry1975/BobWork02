import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta
import time
from supabase import create_client, Client
import os

# Supabase credentials (you can use st.secrets or os.getenv in production)
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Crypto Signal App", layout="wide")
st.title("🚀 Live Crypto Buy/Sell Signals")

# Coin list with CoinGecko IDs
coin_ids = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "maga"
}

refresh_interval = 30  # seconds

def get_live_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usd']
    except:
        return None

def calculate_rsi(prices, period=14):
    try:
        close_series = pd.Series(prices)
        rsi = ta.rsi(close_series, length=period)
        return rsi.iloc[-1] if not rsi.empty else None
    except:
        return None

def calculate_sma(prices, length=5):
    prices = [p for p in prices if p is not None]
    if len(prices) >= length:
        return sum(prices[-length:]) / length
    return None

def store_data_to_supabase(symbol, price, rsi, sma):
    supabase.table("crypto_signals").insert({
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "sma": sma,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }).execute()

for symbol, coin_id in coin_ids.items():
    with st.container():
        st.subheader(f"📈 {symbol} - {coin_id.title()}")

        prices = []
        for _ in range(13):
            price = get_live_price(coin_id)
            prices.append(price)
            time.sleep(0.2)  # To avoid hitting API rate limits

        live_price = get_live_price(coin_id)
        prices.append(live_price)

        rsi = calculate_rsi(prices)
        sma = calculate_sma(prices)

        col1, col2, col3 = st.columns(3)

        col1.metric("Live Price (USD)", f"${live_price:.4f}" if live_price else "N/A")
        col2.metric("RSI", f"{rsi:.2f}" if rsi else "Calculating...")
        col3.metric("SMA", f"{sma:.4f}" if sma else "Calculating...")

        if rsi and sma:
            if rsi < 30 and live_price > sma:
                st.success("✅ **BUY SIGNAL**: RSI is low and price is above SMA")
            elif rsi > 70 and live_price < sma:
                st.error("❌ **SELL SIGNAL**: RSI is high and price is below SMA")
            else:
                st.info("ℹ️ No strong buy/sell signal right now. Keep watching.")
        else:
            st.warning("⏳ Waiting for enough data to calculate indicators.")

        # Plot chart
        if all(p is not None for p in prices):
            df = pd.DataFrame({"Price": prices})
            st.line_chart(df)

        # Store to Supabase
        if live_price:
            store_data_to_supabase(symbol, live_price, rsi, sma)

st.caption(f"🔁 Auto-refreshes every {refresh_interval} seconds.")
st.experimental_rerun() if st.button("🔄 Refresh Now") else time.sleep(refresh_interval)
