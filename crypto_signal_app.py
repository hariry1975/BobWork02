import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.graph_objects as go

# --- CONFIG ---
COINS = {
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "TRUMP": "maga"  # Note: CoinGecko might not list this as 'trump'
}

# --- FUNCTIONS ---
def fetch_last_1_hour_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'interval': 'minutely',
        'days': 1
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        prices = data["prices"][-60:]  # Last 60 minutes
        return [price[1] for price in prices], [datetime.datetime.fromtimestamp(price[0]/1000) for price in prices]
    except Exception as e:
        st.error(f"Error fetching price data for {coin_id}: {e}")
        return None, None

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
    return rsi.iloc[-1] if not rsi.empty else None

def calculate_sma(prices, length=5):
    if len(prices) < length:
        return None
    return sum(prices[-length:]) / length

def plot_chart(times, prices, symbol):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=prices, mode='lines', name=symbol))
    fig.update_layout(title=f"{symbol} Price (1 Hour)", xaxis_title="Time", yaxis_title="USD", height=300)
    return fig

# --- STREAMLIT APP ---
st.set_page_config(page_title="Crypto Signal App", layout="wide")
st.title("📈 Real-Time Crypto Signal Tracker")

for symbol, coin_id in COINS.items():
    with st.container():
        st.subheader(f"🔹 {symbol} ({coin_id})")
        prices, times = fetch_last_1_hour_prices(coin_id)

        if prices and times:
            current_price = prices[-1]
            rsi = calculate_rsi(prices)
            sma = calculate_sma(prices)

            st.metric(label="Current Price (USD)", value=f"${current_price:.4f}")
            if rsi is not None:
                st.info(f"RSI = {rsi:.2f}")
                if rsi < 30:
                    st.success("✅ Buy Signal")
                elif rsi > 70:
                    st.error("🚨 Sell Signal")
                else:
                    st.warning("😐 No strong signal")
            else:
                st.warning("RSI not available yet.")

            if sma is not None:
                st.markdown(f"**SMA (5-min avg):** ${sma:.4f}")

            st.plotly_chart(plot_chart(times, prices, symbol), use_container_width=True)
        else:
            st.error("Could not retrieve 1-hour price data.")
