import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Sayfa Ayarları
st.set_page_config(page_title="MGC1! Pro Quant Panel", layout="wide", page_icon="💰")

# Tasarım
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://gold-signal-bot.onrender.com/get_signals"
UPDATE_URL = "https://gold-signal-bot.onrender.com/update_trade"

st.title("🏆 MGC1! QUANTUM ANALYTICS DASHBOARD")
st.markdown("Sinyal performansı ve gerçek zamanlı işlem yönetimi.")

# --- VERİ ÇEKME FONKSİYONU (Yükleme Göstergeli) ---
def fetch_data():
    with st.spinner('🔄 Sunucuya bağlanılıyor, lütfen bekleyin (Sunucu uyanıyor olabilir)...'):
        try:
            # Timeout süresini artırdık çünkü Render'ın uyanması zaman alır
            response = requests.get(API_URL, timeout=30)
            if response.status_code == 200:
                json_data = response.json()
                if isinstance(json_data, list) and len(json_data) > 0:
                    return pd.DataFrame(json_data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
            return pd.DataFrame()

# Verileri çekmeye çalış
df = fetch_data()

# --- EKRANA BASMA MANTIĞI ---
if not df.empty:
    st.success("✅ Sunucuya başarıyla bağlanıldı ve veriler çekildi!")
    
    # KPI Metrikleri
    total_trades = len(df)
    wins = len(df[df['status'] == 'WIN'])
    losses = len(df[df['status'] == 'LOSS'])
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam İşlem", total_trades)
    col2.metric("Başarı Oranı", f"%{win_rate:.2f}")
    col3.metric("Kazanılan", wins)
    col4.metric("Kayıplar", losses)

    st.markdown("---")

    # Grafikler
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📈 Formasyon Dağılımı")
        fig_pie = px.pie(df, names='pattern', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📊 Sinyal Yönü Analizi")
        sig_counts = df['signal'].value_counts()
        fig_bar = px.bar(x=sig_counts.index, y=sig_counts.values, color=sig_counts.index)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("🛠️ Aktif İşlem Yönetimi")
    st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)

    with st.expander("📝 İşlem Durumunu Güncelle"):
        with st.form("update_form"):
            t_id = st.number_input("İşlem ID", step=1)
            t_status = st.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
            if st.form_submit_button("Güncelle"):
                requests.*
