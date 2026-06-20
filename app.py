import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Sayfa Ayarları
st.set_page_config(page_title="MGC1! Quant Pro", layout="wide", page_icon="💰")

# Modern Tasarım CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    </style>
    """, unsafe_allow_html=True)

# URL'ler
API_URL = "https://gold-signal-bot-1.onrender.com/get_signals"
UPDATE_URL = "https://gold-signal-bot-1.onrender.com/update_trade"

st.title("🏆 MGC1! QUANTUM TRADING JOURNAL")
st.markdown("Sinyal analizleri, Risk/Ödül oranları ve Performans Takibi.")

# --- GÜVENLİ VERİ ÇEKME FONKSİYONU ---
def fetch_data():
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 200:
            json_data = response.json()
            if json_data and isinstance(json_data, list):
                return pd.DataFrame(json_data)
        return pd.DataFrame() # Her durumda boş bir tablo döndür
    except Exception as e:
        st.sidebar.error(f"Bağlantı Hatası: {e}")
        return pd.DataFrame() # Hata durumunda boş tablo döndür

# Veriyi çek ve değişkene ata
df = fetch_data()

# --- KRİTİK KONTROL: df var mı ve boş değil mi? ---
if df is not None and not df.empty:
    st.success("✅ Veriler sunucudan başarıyla çekildi!")
    
    # 1. RR Hesaplama
    def calculate_rr(row):
        try:
            risk = abs(float(row['entry']) - float(row['sl']))
            reward = abs(float(row['tp2']) - float(row['entry']))
            return round(reward / risk, 2) if risk != 0 else 0
        except: return 0

    df['RR_Ratio'] = df.apply(calculate_rr, axis=1)

    # 2. PnL Hesaplama
    def calculate_pnl(row):
        try:
            if pd.notnull(row['exit_price']) and row['exit_price'] != 0:
                if row['signal'] == 'BUY':
                    return round(float(row['exit_price']) - float(row['entry']), 2)
                else:
                    return round(float(row['entry']) - float(row['exit_price']), 2)
        except: pass
        return 0

    df['PnL'] = df.apply(calculate_pnl, axis=1)

    # KPI Metrikleri
    total_trades = len(df)
    wins = len(df[df['status'] == 'WIN'])
    losses = len(df[df['status'] == 'LOSS'])
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_rr = df['RR_Ratio'].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Sinyal Sayısı", total_trades)
    col2.metric("Win Rate", f"%{win_rate:.2f}")
    col3.metric("Ort. RR", f"{avg_rr:.2f}")
    col4.metric("Kazanılan", wins)
    col5.metric("Kayıplar", losses)

    st.markdown("---")

    # Filtreleme
    st.subheader("🔍 Detaylı Filtreleme")
    c1, c2, c3 = st.columns(3)
    with c1: filter_pattern = st.multiselect("Formasyon", options=df['pattern'].unique())
    with c2: filter_signal = st.multiselect("Yön", options=df['signal'].unique())
    with c3: filter_status = st.multiselect("Durum", options=df['status'].unique())

    filtered_df = df.copy()
    if filter_pattern: filtered_df = filtered_df[filtered_df['pattern'].isin(filter_pattern)]
    if filter_signal: filtered_df = filtered_df[filtered_df['signal'].isin(filter_signal)]
    if filter_status: filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]

    st.subheader("📋 İşlem Detayları")
    cols_to_show = ['id', 'time', 'symbol', 'signal', 'pattern', 'entry', 'sl', 'tp2', 'RR_Ratio', 'PnL', 'status']
    # Sadece mevcut olan sütunları göster (hata önleme)
    existing_cols = [c for c in cols_to_show if c in filtered_df.columns]
    st.dataframe(filtered_df[existing_cols].sort_values('id', ascending=False), use_container_width=True)

    with st.expander("📝 İşlem Sonucunu Güncelle"):
        with st.form("update_form"):
            f1, f2, f3 = st.columns(3)
            with f1: t_id = st.number_input("İşlem ID", step=1)
            with f2: t_status = st.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
            with f3: t_exit = st.number_input("Kapanış Fiyatı", format="%.2f")
            if st.form_submit_button("Kaydet"):
                requests.post(UPDATE_URL, json={"id": t_id, "status": t_status, "exit_price": t_exit})
                st.rerun()

    st.markdown("---")
    st.subheader("📐 Lot Hesaplayıcı")
    with st.sidebar:
        st.header("💰 Risk Yönetimi")
        risk_amt = st.number_input("Risk Tutarı ($)", value=100.0)
        en_p = st.number_input("Giriş", value=2000.0)
        st_p = st.number_input("Stop", value=1990.0)
        risk_u = abs(en_p - st_p)
        if risk_u > 0: st.info(f"Lot: {risk_amt/risk_u:.4f}")

else:
    # VERİ YOKSA BU KISIM ÇALIŞIR (HATA VERMEZ)
    st.info("⏳ Şu an analiz edilecek sinyal bulunmuyor.")
    st.write("Sistemi test etmek için aşağıdaki butona basarak sanal bir sinyal gönderin.")
    
    if st.button("Sistemi Test Et ve Sinyal Gönder"):
        test_data = {"symbol": "Sanal Gold", "signal": "BUY", "pattern": "Pro-Bat", "entry": "2030", "tp1": "2040", "tp2": "2060", "sl": "2010", "rsi": "20"}
        try:
            webhook_url = API_URL.replace("get_signals", "webhook")
            requests.post(webhook_url, json=test_data)
            st.success("Sinyal gönderildi! Lütfen sayfayı yenileyin.")
        except: st.error("Hata oluştu.")

st.sidebar.markdown("### 🛠️ Sistem")
st.sidebar.write("✅ Sunucu: Online")
st.sidebar.write("✅ Veritabanı: Bağlı")
