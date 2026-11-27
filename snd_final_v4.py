import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="Pencari SnD", page_icon="📊", layout="wide")
st.title("📊 Pencari SnD + Pivot")
st.caption("DOT • POL • EMAS (XAU) - Tanpa Iklan - by Sugiharto-B")

# PILIHAN ASET
pilihan = st.selectbox("Pilih Aset:", ["DOT / USDT", "POL / USDT", "EMAS / XAUUSDT"])
symbol_map = {"DOT / USDT": "DOTUSDT", "POL / USDT": "POLUSDT", "EMAS / XAUUSDT": "XAUUSDT"}
symbol = symbol_map[pilihan]

tf = st.selectbox("Timeframe:", ["1h", "4h", "1d"], index=1)
tf_map = {"1h": "1h", "4h": "4h", "1d": "1d"}
interval = tf_map[tf]

jumlah = st.slider("Jumlah Candle:", 50, 500, 200)

@st.cache_data(ttl=60)
def ambil_data(symbol, interval, limit):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url, timeout=10)
    data = r.json()
    df = pd.DataFrame(data, columns=["open_time","open","high","low","close","volume","close_time","qav","trades","taker_base","taker_quote","ignore"])
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c])
    df["time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df

try:
    df = ambil_data(symbol, interval, jumlah)
    harga_now = float(df["close"].iloc[-1])
    st.metric(f"Harga {pilihan} Sekarang", f"{harga_now:,.4f} USDT")

    # PIVOT POINT (dari candle terakhir)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    H = float(prev["high"]); L = float(prev["low"]); C = float(prev["close"])
    pivot = (H + L + C) / 3
    r1 = 2*pivot - L
    s1 = 2*pivot - H
    r2 = pivot + (H - L)
    s2 = pivot - (H - L)

    st.subheader("🎯 Pivot Point (Candle Sebelumnya)")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("R2", f"{r2:,.4f}")
    c2.metric("R1", f"{r1:,.4f}")
    c3.metric("PIVOT", f"{pivot:,.4f}")
    c4.metric("S1", f"{s1:,.4f}")
    c5.metric("S2", f"{s2:,.4f}")

    # SUPPLY & DEMAND SEDERHANA
    st.subheader("📦 Zona Supply & Demand Terdekat")
    # Demand = Low terendah 20 candle terakhir
    low_20 = df.tail(20)["low"].min()
    high_20 = df.tail(20)["high"].max()
    # Cari zona
    st.success(f"🟢 DEMAND (Beli) di sekitar: {low_20:,.4f} - {low_20*1.005:,.4f}")
    st.error(f"🔴 SUPPLY (Jual) di sekitar: {high_20*0.995:,.4f} - {high_20:,.4f}")

    jarak_ke_demand = ((harga_now - low_20) / low_20) * 100
    jarak_ke_supply = ((high_20 - harga_now) / harga_now) * 100

    st.info(f"Jarak Harga ke Demand: {jarak_ke_demand:.2f}% | Jarak ke Supply: {jarak_ke_supply:.2f}%")

    if abs(harga_now - pivot) < (H-L)*0.05:
        st.warning("⚠️ Harga sedang di area PIVOT - Hati-hati, biasanya mantul / jebol!")
    elif harga_now > pivot:
        st.write("📈 Trend di atas Pivot - Cenderung Bullish")
    else:
        st.write("📉 Trend di bawah Pivot - Cenderung Bearish")

    st.subheader("📈 Grafik Harga Terakhir + Zona SnD")
import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["time"], y=df["close"], mode='lines', name='Harga', line=dict(color='white')))
fig.add_hrect(y0=low_20, y1=low_20*1.01, fillcolor="green", opacity=0.35, line_width=0, annotation_text="DEMAND")
fig.add_hrect(y0=high_20*0.99, y1=high_20, fillcolor="red", opacity=0.35, line_width=0, annotation_text="SUPPLY")
fig.add_hline(y=harga_now, line_dash="dash", line_color="yellow")
fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Data Terakhir")
    st.dataframe(df[["time","open","high","low","close","volume"]].tail(10).sort_values("time", ascending=False), use_container_width=True)

    if st.button("🔄 REFRESH / CARI LAGI"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Gagal ambil data: {e}")
    st.write("Coba ganti timeframe atau refresh lagi.")

st.markdown("---")
st.caption("Data dari Binance Public API - Gratis & Tanpa Iklan")
