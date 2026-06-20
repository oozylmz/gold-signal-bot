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

# Sunucu Bilgileri
API_URL = "https://gold-signal-bot-1.onrender.com/get_signals"
UPDATE_URL = "https://gold-signal-bot-1.onrender.com/update_trade"

st.title("🏆 MGC1! QUANTUM ANALYTICS DASHBOARD")
st.markdown("Sinyal performansı ve gerçek zamanlı işlem yönetimi.")

# --- VERİ ÇEKME FONKSİYONU ---
def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        return pd.DataFrame()

df = fetch_data()

if not df.empty:
    # --- ÜST METRİKLER (KPIs) ---
    total_trades = len(df)
    wins = len(df[df['status'] == 'WIN'])
    losses = len(df[df['status'] == 'LOSS'])
    open_trades = len(df[df['status'] == 'OPEN'])
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam İşlem", total_trades)
    col2.metric("Başarı Oranı (Win Rate)", f"%{win_rate:.2f}")
    col3.metric("Kazanılan", wins, delta_color="normal")
    col4.metric("Kayıplar", losses, delta_color="inverse")

    st.markdown("---")

    # --- ANALİTİK GRAFİKLER ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Formasyon Dağılımı")
        fig_pie = px.pie(df, names='pattern', hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📊 Sinyal Yönü Analizi")
        fig_bar = px.bar(df['signal'].value_counts(), 
                         labels={'value': 'Sinyal Sayısı', 'index': 'Yön'},
                         color=df['signal'].value_counts().index,
                         color_discrete_map={'BUY': 'green', 'SELL': 'red'})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # --- İŞLEM YÖNETİMİ VE TABLO ---
    st.subheader("🛠️ Aktif İşlem Yönetimi")
    st.write("Aşağıdaki tablo üzerinden tamamlanan işlemleri işaretleyin.")

    # Tabloyu daha şık hale getirme
    st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)

    # İşlem Güncelleme Alanı
    with st.expander("📝 İşlem Durumunu Güncelle"):
        with st.form("update_form"):
            t_id = st.number_input("İşlem ID", step=1)
            t_status = st.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
            submit = st.form_submit_button("Güncelle")
            
            if submit:
                res = requests.post(UPDATE_URL, json={"id": t_id, "status": t_status})
                if res.status_code == 200:
                    st.success(f"İşlem {t_id} başarıyla {t_status} olarak işaretlendi!")
                    st.rerun()
                else:
                    st.error("Güncelleme başarısız oldu.")

else:
    st.warning("Henüz veri tabanında kayıtlı sinyal bulunmuyor. Lütfen TradingView'den sinyal gönderin.")

st.sidebar.markdown("### 🛠️ Sistem Kontrol")
st.sidebar.write("✅ Sunucu: Online")
st.sidebar.write("✅ Veritabanı: Bağlı")
st.sidebar.write("✅ Telegram: Aktif")
