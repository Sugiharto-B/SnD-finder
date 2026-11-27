import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
       # === SnD BENERAN TANPA DEF ===
    df['tutup'] = df['close']
    df['membuka'] = df['open']
    df['tinggi'] = df['high']
    df['rendah'] = df['low']
    df['body'] = df['tutup'] - df['membuka']
    df['body'] = df['body'].abs()    
    avg_body = df['body'].mean()
    demand_zones = []
    supply_zones = []
    for i in range(3, len(df)-1):
        is_up = df['tutup'].iloc[i] > df['membuka'].iloc[i] and df['body'].iloc[i] > 1.5 * avg_body
        is_down = df['tutup'].iloc[i] < df['membuka'].iloc[i] and df['body'].iloc[i] > 1.5 * avg_body
        base = df.iloc[i-3:i]
        base_kecil = (base['body'] < avg_body).all()
        if is_up and base_kecil:
            demand_zones.append((base['rendah'].min(), base['tinggi'].max()))
        if is_down and base_kecil:
            supply_zones.append((base['rendah'].min(), base['tinggi'].max()))
        rendah_20, tinggi_demand = demand_zones[-1] if demand_zones else (df['rendah'].min(), df['rendah'].min())
        rendah_supply, tinggi_20 = supply_zones[-1] if supply_zones else (df['tinggi'].max(), df['tinggi'].max()) 

    if abs(harga_now - pivot) < (H-L)*0.05:
        st.warning("⚠️ Harga sedang di area PIVOT - Hati-hati, biasanya mantul / jebol!")
    elif harga_now > pivot:
        st.write("📈 Trend di atas Pivot - Cenderung Bullish")
    else:
        st.write("📉 Trend di bawah Pivot - Cenderung Bearish")

    st.subheader("📈 Grafik Harga Terakhir + Zona SnD")
    # --- SnD OTOMATIS PINTER - Cari Demand Kuat Sendiri ---
    fig = go.Figure()
    df_100 = df.tail(100).copy()
    # Cari Swing Low: low paling rendah dibanding 5 kiri + 5 kanan
    df_100['swing_low'] = df_100['low'] == df_100['low'].rolling(11, center=True).min()
    swing_lows = df_100[df_100['swing_low'] == True]
    # Ambil Swing Low terakhir yang masih fresh (harga belum jebol ke bawahnya)
    demand_kuat = None
    for i in range(len(swing_lows)-1, -1, -1):
        low_c = swing_lows.iloc[i]['low']
        # Cek apakah harga sekarang masih di atas low ini (belum jebol)
        if df['close'].iloc[-1] > low_c:
            demand_kuat = swing_lows.iloc[i]
            break
    if demand_kuat is not None:
        kuat_low = demand_kuat['low']
        kuat_high = max(demand_kuat['open'], demand_kuat['close'])
        fig.add_hrect(y0=kuat_low, y1=kuat_high, fillcolor="green", opacity=0.3, line_width=0)
        fig.add_annotation(x=df["time"].iloc[-1], y=kuat_high, text=f"DEMAND KUAT OTOMATIS {kuat_low:.3f}", showarrow=False, font=dict(color="white", size=10), bgcolor="green")
    else:
        fig.add_annotation(x=df["time"].iloc[-1], y=df['close'].iloc[-1], text="SEMUA DEMAND JEBOL - WAIT!", showarrow=False, font=dict(color="white", size=10), bgcolor="red")
    # --- Supply OTOMATIS PINTER - Cari Supply Kuat Sendiri ---
    df_100_s = df.tail(100).copy()
    df_100_s['swing_high'] = df_100_s['high'] == df_100_s['high'].rolling(11, center=True).max()
    swing_highs = df_100_s[df_100_s['swing_high'] == True]
    supply_kuat = None
    for i in range(len(swing_highs)-1, -1, -1):
        high_c = swing_highs.iloc[i]['high']
        if df['close'].iloc[-1] < high_c:
            supply_kuat = swing_highs.iloc[i]
            break
    if supply_kuat is not None:
        s_high = supply_kuat['high']
        s_low = min(supply_kuat['open'], supply_kuat['close'])
        fig.add_hrect(y0=s_low, y1=s_high, fillcolor="red", opacity=0.3, line_width=0)
        fig.add_annotation(x=df["time"].iloc[-1], y=s_high, text=f"SUPPLY KUAT OTOMATIS {s_high:.3f}", showarrow=False, font=dict(color="white", size=10), bgcolor="red") 
            # --- ALARM OTOMATIS - Kalo Udah Deket Zone ---
    harga_skrg = df['close'].iloc[-1]
    pesan_alarm = ""
    warna_alarm = "gray"
    if supply_kuat is not None:
        jarak_supply = (supply_kuat['high'] - harga_skrg) / harga_skrg * 100
        if jarak_supply < 3:
            pesan_alarm = f"⚠️ DOT UDAH DEKET SUPPLY {supply_kuat['high']:.3f} - SIAP-SIAP JUAL / JANGAN FOMO!"
            warna_alarm = "red"
    if demand_kuat is not None and pesan_alarm == "":
        jarak_demand = (harga_skrg - demand_kuat['low']) / harga_skrg * 100
        if jarak_demand < 3:
            pesan_alarm = f"🔥 DOT UDAH DEKET DEMAND {demand_kuat['low']:.3f} - SIAP-SIAP SEROK!"
            warna_alarm = "green"
    if pesan_alarm != "":
        fig.add_annotation(x=df["time"].iloc[-1], y=harga_skrg, text=pesan_alarm, showarrow=True, arrowhead=2, font=dict(color="white", size=12), bgcolor=warna_alarm)
    fig.add_trace(go.Scatter(x=df["time"], y=df["close"], mode='lines', name='Harga', line=dict(color='black')))
    fig.add_hrect(y0=rendah_20, y1=tinggi_demand, fillcolor="green", opacity=0.35, line_width=0)
    fig.add_hrect(y0=rendah_supply, y1=tinggi_20, fillcolor="red", opacity=0.35, line_width=0) 
    # Garis tengah antara Demand & Supply
    tengah = (tinggi_demand + rendah_supply) / 2
    fig.add_trace(go.Scatter(x=[df["time"].iloc[0], df["time"].iloc[-1]], y=[(tinggi_demand + rendah_supply)/2, (tinggi_demand + rendah_supply)/2], mode="lines", line=dict(color="black", dash="dash", width=2), name="Tengah"))
# Split lines Demand to Mid

    d1 = tinggi_demand + (tengah - tinggi_demand) * 1/3
    d2 = tinggi_demand + (tengah - tinggi_demand) * 2/3
    fig.add_trace(go.Scatter(x=[df["time"].iloc[0], df["time"].iloc[-1]], y=[d1, d1], mode="lines", line=dict(color="green", dash="dot", width=1), showlegend=False))
    fig.add_trace(go.Scatter(x=[df["time"].iloc[0], df["time"].iloc[-1]], y=[d2, d2], mode="lines", line=dict(color="green", dash="dot", width=1), showlegend=False))

# Split lines Mid to Supply
    s1 = tengah + (rendah_supply - tengah) * 1/3
    s2 = tengah + (rendah_supply - tengah) * 2/3
    fig.add_trace(go.Scatter(x=[df["time"].iloc[0], df["time"].iloc[-1]], y=[s1, s1], mode="lines", line=dict(color="#2ca02c", dash="dot", width=1), showlegend=False))
    fig.add_trace(go.Scatter(x=[df["time"].iloc[0], df["time"].iloc[-1]], y=[s2, s2], mode="lines", line=dict(color="#2ca02c", dash="dot", width=1), showlegend=False))# Segitiga kuning harga sekarang
    fig.add_trace(go.Scatter(x=[df["time"].iloc[-1]], y=[harga_now], mode="markers", marker=dict(symbol="triangle-right", size=18, color="yellow", line=dict(color="black", width=1)), name="Harga Sekarang"))

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
