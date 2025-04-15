import streamlit as st
import requests
import time
from datetime import datetime
from supabase import create_client, Client
import pandas as pd

# === Supabase Setup ===
SUPABASE_URL = "https://ncrxfifndtbinniykddg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jcnhmaWZuZHRiaW5uaXlrZGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2MjQ2NjEsImV4cCI6MjA2MDIwMDY2MX0.wvzWT-8IqCTcA4CauJCm8KCEtQXPoJqv_Lh3tzpF1Lg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Coins to track
coins = {
    "dogecoin": "Dogecoin",
    "ripple": "XRP",
    "cardano": "Cardano",
    "trump": "TrumpCoin"
}

# Helper to get live prices
def fetch_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        return data[coin_id]["usd"]
    except:
        return None

# Save to Supabase
def save_data_to_supabase(symbol, price):
    try:
        now = datetime.utcnow().isoformat()
        supabase.table("prices").insert({
            "symbol": symbol,
            "price": price,
            "timestamp": now
        }).execute()
    except Exception as e:
        st.error(f"Failed to save data: {e}")

# Calculate RSI
def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None
    deltas = pd.Series(prices).diff().dropna()
    gain = deltas.where(deltas > 0, 0.0)
    loss = -deltas.where(deltas < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

# App layout
st.set_page_config(page_title="Crypto Signal App", layout="wide")
st.title("📈 Real-Time Crypto Signal App")

# Main logic
for coin_id, coin_name in coins.items():
    with st.container():
        st.subheader(f"💰 {coin_name}")

        # Get last 13 historical prices
        prices = []
        while len(prices) < 13:
            price = fetch_price(coin_id)
            if price:
                prices.append(price)
                time.sleep(1)

        # Get live price
        live_price = fetch_price(coin_id)
        if live_price:
            prices.append(live_price)
            save_data_to_supabase(coin_id, live_price)
            st.metric(label="Live Price (USD)", value=f"${live_price:.4f}")
        else:
            st.error("Could not retrieve price data.")

        # RSI
        rsi = calculate_rsi(prices)
        if rsi is not None:
            if rsi < 30:
                st.success(f"📉 RSI = {rsi:.2f} → BUY Signal")
            elif rsi > 70:
                st.warning(f"📈 RSI = {rsi:.2f} → SELL Signal")
            else:
                st.info(f"⏳ RSI = {rsi:.2f} → No strong signal yet.")
        else:
            st.info("⏳ RSI data is not available yet. Waiting for more data...")

        # Chart
        df = pd.DataFrame({"Price": prices}, index=[datetime.utcnow().strftime("%H:%M:%S")] * len(prices))
        st.line_chart(df)

# Auto-refresh every 60s
st.caption("App will refresh every 60 seconds to fetch latest prices.")
st_autorefresh = st.empty()
st_autorefresh.markdown("<meta http-equiv='refresh' content='60'>", unsafe_allow_html=True)
