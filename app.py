import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# Sayfa Ayarları
st.set_page_config(page_title="MGC1! Pro Quant Panel", layout="wide", page_icon="💰")

# Özel CSS ile tasarımı modernize etme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    </style>
    """, unsafe_allow_html=True)

# Sunucu Bilgileri (Sizin URL'leriniz)
API_URL = "https://gold-signal-bot.onrender.com/get_signals"
UPDATE_URL = "https://gold-signal-bot.onrender.com/update_trade"

st.title("🏆 MGC1! QUANTUM ANALYTICS DASHBOARD")
st.markdown("Sinyal performansı ve gerçek zamanlı işlem yönetimi.")

# --- VERİ ÇEKME FONKSİYONU ---
def fetch_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            if isinstance(json_data, list) and len(json_data) > 0:
                return pd.DataFrame(json_data)
        return pd.DataFrame() 
    except Exception as e:
        st.error(f"Sunucu bağlantı hatası: {e}")
        return pd.DataFrame()

# Verileri Çek
df = fetch_data()

# --- ANA MANTIK ---
if not df.empty:
    # --- ÜST METRİKLER (KPIs) ---
    total_trades = len(df)
    wins = len(df[df['status'] == 'WIN'])
    losses = len(df[df['status'] == 'LOSS'])
    
    # Win Rate hesaplama
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    # Metrikleri yan yana diz (Sizin hatanın olduğu kısım burasıydı, şimdi tertemiz)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam İşlem", total_trades)
    col2.metric("Başarı Oranı", f"%{win_rate:.2f}")
    col3.metric("Kazanılan", wins)
    col4.metric("Kayıplar", losses)

    st.markdown("---")

    # --- ANALİ*
