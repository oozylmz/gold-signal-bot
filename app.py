import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="MGC1! QUANT TERMINAL", layout="wide", page_icon="💰")

# --- PROFESYONEL DARK MODE CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #3e4451; padding: 15px; border-radius: 15px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2c3e50; color: white; }
    .stDataFrame { border: 1px solid #3e4451; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://gold-signal-bot-1.onrender.com"
S_URL = f"{API_URL}/get_signals"
U_URL = f"{API_URL}/update_trade"
B_URL = f"{API_URL}/get_balance"
UB_URL = f"{API_URL}/update_balance"

st.title("🏆 MGC1! QUANTUM TERMINAL")

# --- SEKME YAPISI ---
tab1, tab2 = st.tabs(["📈 ANALİZ PANELİ", "💰 KASA YÖNETİMİ"])

# ---------------------------------------------------------------------------
# SEKME 1: ANALİZ PANELİ
# ---------------------------------------------------------------------------
with tab1:
    def fetch_data():
        try:
            r = requests.get(S_URL, timeout=10)
            return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
        except: return pd.DataFrame()

    df = fetch_data()

    if not df.empty:
        # Hesaplamalar
        df['RR'] = df.apply(lambda x: round(abs(x['tp2']-x['entry'])/abs(x['entry']-x['sl']), 2) if abs(x['entry']-x['sl'])!=0 else 0, axis=1)
        
        # KPI'lar
        total = len(df)
        win_rate = (len(df[df['status'] == 'WIN']) / (len(df[df['status'] == 'WIN']) + len(df[df['status'] == 'LOSS'])*100)) if (len(df[df['status'] == 'WIN']) + len(df[df['status'] == 'LOSS'])) > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Sinyal", total)
        m2.metric("Win Rate", f"%{win_rate:.2f}")
        m3.metric("Sistem Durumu", "LIVE ✅")

        st.markdown("---")
        
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.subheader("📋 Sinyal Takip Listesi")
            st.dataframe(df[['id', 'time', 'signal', 'pattern', 'entry', 'sl', 'tp2', 'RR', 'status']].sort_values('id', ascending=False), use_container_width=True)
        
        with c_right:
            st.subheader("📊 Dağılım")
            fig = px.pie(df, names='pattern', hole=0.5, color_discrete_sequence=px.colors.sequential.Bluered)
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📝 İşlem Kapat"):
            with st.form("update_form"):
                f1, f2, f3 = st.columns(3)
                tid = f1.number_input("ID", step=1)
                tstat = f2.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
                texit = f3.number_input("Çıkış Fiyatı", format="%.2f")
                if st.form_submit_button("Güncelle"):
                    requests.post(U_URL, json={"id": tid, "status": tstat, "exit_price": texit})
                    st.rerun()
    else:
        st.info("Sinyal bekleniyor...")

# ---------------------------------------------------------------------------
# SEKME 2: KASA YÖNETİMİ (NEW)
# ---------------------------------------------------------------------------
with tab2:
    # Kasa Verilerini Çek
    try:
        b_res = requests.get(B_URL).json()
        balance = b_res['balance']
        total_profit = b_res['total_profit']
    except:
        balance, total_profit = 10000.0, 0.0

    # GÜNLÜK HESAPLAMA (Sinyallerden bugünün karını bul)
    df_all = fetch_data()
    daily_pnl = 0
    if not df_all.empty:
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = df_all[df_all['time'].str.contains(today)]
        for _, row in today_trades.iterrows():
            if row['status'] == 'WIN': daily_pnl += (row['tp1'] - row['entry']) if row['signal'] == 'BUY' else (row['entry'] - row['tp1'])
            if row['status'] == 'LOSS': daily_pnl += (row['sl'] - row['entry']) if row['signal'] == 'BUY' else (row['entry'] - row['sl'])

    # --- UYARI SİSTEMİ ---
    if daily_pnl <= -3000:
        st.error(f"🚨 KRİTİK UYARI: GÜNLÜK KAYIP LİMİTİ AŞILDI! (${daily_pnl:.2f}) - İŞLEMLERİ DURDURUN!")
    elif daily_pnl >= 1000:
        st.success(f"✅ GÜNLÜK HEDEF TAMAMLANDI! (${daily_pnl:.2f} KAZANILDI) - BUGÜNLÜK YETERLİ!")
    else:
        st.info(f"Günlük Kasa Durumu: ${daily_pnl:.2f}")

    # Kasa Metrikleri
    k1, k2 = st.columns(2)
    k1.metric("Mevcut Kasa", f"${balance:,.2f}")
    k2.metric("Toplam Kar/Zarar", f"${total_profit:,.2f}")

    st.markdown("---")
    
    # Kasa Güncelleme
    with st.expander("💰 Kasayı Manuel Güncelle"):
        new_bal = st.number_input("Yeni Bakiye ($)", value=balance)
        if st.button("Bakiyeyi Kaydet"):
            requests.post(UB_URL, json={"balance": new_bal})
            st.rerun()

    # LOT HESAPLAYICI (Gelişmiş)
    st.markdown("---")
    st.subheader("📐 Profesyonel Lot Hesaplayıcı")
    with st.container():
        l1, l2, l3 = st.columns(3)
        with l1: risk_usd = st.number_input("İşlem Başı Risk ($)", value=100.0)
        with l2: entry_p = st.number_input("Giriş Fiyatı", value=2030.0)
        with l3: stop_p = st.number_input("Stop Fiyatı", value=2020.0)
        
        risk_per_unit = abs(entry_p - stop_p)
        if risk_per_unit > 0:
            final_lot = risk_usd / risk_per_unit
            st.warning(f"Sizin için ideal işlem büyüklüğü: **{final_lot:.4f} Lot**")
