import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="MGC1! Quant Pro", layout="wide", page_icon="💰")

# Tasarım ve Renkler
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    .css-164fb9e { background-color: #1e222d; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://gold-signal-bot-1.onrender.com/get_signals"
UPDATE_URL = "https://gold-signal-bot-1.onrender.com/update_trade"

st.title("🏆 MGC1! QUANTUM TRADING JOURNAL")
st.markdown("Sinyal analizleri, Risk/Ödül oranları ve Performans Takibi.")

def fetch_data():
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except: return pd.DataFrame()

df = fetch_data()

if not df.empty:
    # --- PROFESYONEL HESAPLAMALAR ---
    # 1. Risk/Reward (RR) Oranı Hesaplama
    def calculate_rr(row):
        risk = abs(row['entry'] - row['sl'])
        reward = abs(row['tp2'] - row['entry'])
        return round(reward / risk, 2) if risk != 0 else 0

    df['RR_Ratio'] = df.apply(calculate_rr, axis=1)

    # 2. Kar/Zarar (PnL) Hesaplama (Sadece kapanan işlemler için)
    def calculate_pnl(row):
        if pd.notnull(row['exit_price']):
            if row['signal'] == 'BUY':
                return round(row['exit_price'] - row['entry'], 2)
            else:
                return round(row['entry'] - row['exit_price'], 2)
        return 0

    df['PnL'] = df.apply(calculate_pnl, axis=1)

    # --- ÜST METRİKLER ---
    total_trades = len(df)
    wins = len(df[df['status'] == 'WIN'])
    losses = len(df[df['status'] == 'LOSS'])
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_rr = df['RR_Ratio'].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Sinyal Sayısı", total_trades)
    col2.metric("Win Rate", f"%{win_rate:.2f}")
    col3.metric("Ort. RR Oranı", f"{avg_rr:.2f}")
    col4.metric("Net Win", wins)
    col5.metric("Net Loss", losses)

    st.markdown("---")

    # --- GELİŞMİŞ FİLTRELEME ---
    st.subheader("🔍 Detaylı Filtreleme")
    c1, c2, c3 = st.columns(3)
    with c1:
        filter_pattern = st.multiselect("Formasyon Seçin", options=df['pattern'].unique())
    with c2:
        filter_signal = st.multiselect("Yön Seçin", options=df['signal'].unique())
    with c3:
        filter_status = st.multiselect("Durum Seçin", options=df['status'].unique())

    # Filtreleri uygula
    filtered_df = df.copy()
    if filter_pattern: filtered_df = filtered_df[filtered_df['pattern'].isin(filter_pattern)]
    if filter_signal: filtered_df = filtered_df[filtered_df['signal'].isin(filter_signal)]
    if filter_status: filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]

    # --- DETAYLI TABLO ---
    st.subheader("📋 İşlem Detayları")
    # Tabloyu daha okunabilir yapalım
    display_cols = ['id', 'time', 'symbol', 'signal', 'pattern', 'entry', 'sl', 'tp2', 'RR_Ratio', 'PnL', 'status']
    st.dataframe(filtered_df[display_cols].sort_values('id', ascending=False), use_container_width=True)

    # --- PROFESYONEL İŞLEM GÜNCELLEME ---
    with st.expander("📝 İşlem Kapatma ve Sonuç Girişi"):
        with st.form("update_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1: t_id = st.number_input("İşlem ID", step=1)
            with f_col2: t_status = st.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
            with f_col3: t_exit = st.number_input("Kapanış Fiyatı", format="%.2f")
            
            if st.form_submit_button("İşlemi Kaydet"):
                res = requests.post(UPDATE_URL, json={"id": t_id, "status": t_status, "exit_price": t_exit})
                if res.status_code == 200:
                    st.success("İşlem başarıyla güncellendi!")
                    st.rerun()

    # --- RİSK HESAPLAMA ARACI (EKSTRA) ---
    st.markdown("---")
    st.subheader("📐 Risk Hesaplama Araçları")
    with st.sidebar:
        st.header("💰 Lot Hesaplayıcı")
        risk_amount = st.number_input("Risk Edilecek Tutar ($)", value=100.0)
        entry_p = st.number_input("Giriş Fiyatı", value=2000.0)
        stop_p = st.number_input("Stop Fiyatı", value=1990.0)
        
        risk_per_unit = abs(entry_p - stop_p)
        if risk_per_unit > 0:
            lot_size = risk_amount / risk_per_unit
            st.info(f"Önerilen İşlem Büyüklüğü: \n\n **{lot_size:.4f} Lot**")

else:
    st.info("Sinyaller bekleniyor...")
    if st.button("Sistemi Uyandır ve Test Sinyali Gönder"):
        test_data = {"symbol": "MGC1!", "signal": "BUY", "pattern": "Pro-Bat", "entry": "2030", "tp1": "2040", "tp2": "2060", "sl": "2010", "rsi": "20"}
        requests.post(API_URL.replace("get_signals", "webhook"), json=test_data)
        st.success("Sinyal gönderildi!")
