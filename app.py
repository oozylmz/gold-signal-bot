import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="GOLD-MGC1 QUANT", layout="wide", page_icon="💰")

# --- ULTRA MODERN CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0b10; color: #e0e0e0; }
    div[data-testid="stMetric"] { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 15px; 
        padding: 20px;
        text-align: center;
    }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 15px; }
    
    /* Buton Genişletme ve Ortaya Hizalama */
    .stButton>button { 
        width: 100% !important;
        background-color: #f39c12 !important; 
        color: black !important; 
        font-weight: bold !important;
        border-radius: 10px !important;
        height: 3em !important;
    }
    
    /* Sekme (Tabs) Genişletme */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #161b22; 
        border-radius: 10px; 
        color: white !important; 
        padding: 10px 40px !important;
    }
    .stTabs [aria-selected="true"] { background-color: #f39c12 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://gold-//signal-bot-1.onrender.com" # // siliyorum
API_URL = "https://gold-signal-bot-1.onrender.com"
S_URL = f"{API_URL}/get_signals"
U_URL = f"{API_URL}/update_trade"
B_URL = f"{API_URL}/get_balance"

with st.sidebar:
    st.header("🛠️ Sistem Kontrol")
    st.write("✅ Sunucu: Online")
    st.markdown("---")
    if st.button("Sinyal Gönder (Test)"):
        test_data = {"symbol": "MGC1! TEST", "signal": "BUY", "pattern": "Sanal-Bat", "entry": "2030", "tp1": "2040", "tp2": "2060", "sl": "2010", "rsi": "20"}
        requests.post(f"{API_URL}/webhook", json=test_data)
        st.success("Gönderildi!")
    st.markdown("---")
    st.subheader("📐 Lot Hesaplayıcı")
    r_usd = st.number_input("Risk ($)", value=100.0)
    en_p = st.number_input("Giriş", value=2000.0)
    st_p = st.number_input("Stop", value=1990.0)
    res_lot = r_usd / abs(en_p - st_p) if abs(en_p - st_p) != 0 else 0
    st.info(f"Önerilen Lot: {res_lot:.4f}")

st.title("🟡 GOLD — MGC1 HARMONIC")
st.markdown("✨ **Sinyal Takip ve Otomatik Kasa Yönetimi**")

tab1, tab2 = st.tabs(["📡 SİNYALLER", "💰 KASA TAKİP"])

with tab1:
    def fetch_data():
        try:
            r = requests.get(S_URL, timeout=10)
            return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
        except: return pd.DataFrame()

    df = fetch_data()

    if not df.empty:
        total = len(df)
        buys = len(df[df['signal'] == 'BUY'])
        sells = len(df[df['signal'] == 'SELL'])
        opens = len(df[df['status'] == 'OPEN'])
        wins = len(df[df['status'] == 'WIN'])
        total_closed = len(df[df['status'] != 'OPEN'])
        win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("TOPLAM SİNYAL", total)
        col2.metric("BUY", buys)
        col3.metric("SELL", sells)
        col4.metric("AÇIK", opens)
        col5.metric("BAŞARI", f"%{win_rate:.1f}")
        col6.metric("DURUM", "CANLI ✅")

        st.markdown("---")
        st.subheader("📝 İşlemi Sonuçlandır")
        with st.expander("Sonucu girmek için tıklayın"):
            with st.form("update_form"):
                f1, f2, f3 = st.columns(3)
                with f1: tid = st.number_input("İşlem ID", step=1)
                with f2: tstat = st.selectbox("Sonuç", ["WIN", "LOSS", "OPEN"])
                with f3: texit = st.number_input("Çıkış Fiyatı", format="%.2f")
                if st.form_submit_button("SONUCU KAYDET"):
                    requests.post(U_URL, json={"id": tid, "status": tstat, "exit_//price": texit})
                    # // siliyorum
                    requests.post(U_URL, json={"id": tid, "status": tstat, "exit_price": texit})
                    st.rerun()

        st.markdown("---")
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.subheader("📜 Sinyal Geçmişi")
            # BAŞLIKLARI BÜYÜK HARF YAPMA
            cols_to_show = {'id': 'ID', 'time': 'ZAMAN', 'pattern': 'FORMASYON', 'signal': 'YÖN', 'entry': 'GİRİŞ', 'sl': 'STOP', 'tp2': 'TP2', 'status': 'DURUM'}
            display_df = df[list(cols_to_show.keys())].copy()
            display_df.columns = list(cols_to_show.values())
            st.dataframe(display_df.sort_values('ID', ascending=False), use_container_width=True)

        with c_right:
            st.subheader("🎯 Son Sinyal Detayı")
            last = df.iloc[0]
            st.markdown(f"""
            <div style="background-color:#161b22; padding:20px; border-radius:15px; border:1px solid #f39c12">
                <h3 style="color:#f39c12; margin-bottom:10px;">{last['pattern']}</h3>
                <p><b>Yön:</b> {'BUY' if last['signal']=='BUY' else 'SELL'}</p>
                <p><b>Giriş:</b> {last['entry']}</p>
                <p><b>Stop:</b> {last['sl']}</p>
                <p><b>TP2:</b> {last['tp2']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📊 Formasyon Dağılımı")
            fig = px.pie(df, names='pattern', hole=0.6, color_discrete_sequence=px.colors.sequential.YlOrRd)
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sinyal bekleniyor...")

with tab2:
    try:
        b_res = requests.get(B_URL).json()
        balance = b_res['balance']
        total_p = b_res['total_profit']
    except:
        balance, total_p = 0.0, 0.0

    df_all = fetch_data()
    daily_pnl = 0
    if not df_all.empty:
        today = datetime.now().strftime("%Y-%m-%d")
        today_trades = df_all[df_all['time'].str.contains(today)]
        for _, row in today_trades.iterrows():
            if row['status'] == 'WIN': daily_pnl += (row['tp1'] - row['entry']) if row['signal'] == 'BUY' else (row['entry'] - row['tp1'])
            if row['status'] == 'LOSS': daily_pnl += (row['sl'] - row['entry']) if row['signal'] == 'BUY' else (row['entry'] - row['sl'])

    # RENKLİ GÜNLÜK UYARI
    if daily_pnl <= -3000:
        st.markdown(f'<div style="background-color:#ff4b4b; color:white; padding:20px; border-radius:10px; text-align:center; font-weight:bold;">🚨 KRİTİK: GÜNLÜK KAYIP LİMİTİ AŞILDI! (${daily_pnl:.2f})</div>', unsafe_allow_html=True)
    elif daily_pnl >= 1000:

        st.markdown(f'<div style="background-color:#00c853; color:white; padding:20px; border-radius:10px; text-align:center; font-weight:bold;">✅ HEDEF TAMAMLANDI! (${daily_pnl:.2f} KAR)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background-color:#161b22; color:white; padding:20px; border-radius:10px; text-align:center;">Günlük Durum: ${daily_pnl:.2f}</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("BAŞLANGIÇ KASASI", "$100,000")
    k2.metric("GÜNCEL KASA", f"${balance:,.2f}")
    k3.metric("TOPLAM K/Z", f"${total_p:,.2f}")
    k4.metric("GÜNLÜK K/Z", f"${daily_pnl:,.2f}")

    st.markdown("---")
    col_setup, col_chart = st.columns([1, 1])
    with col_setup:
        st.subheader("⚙️ Kasa Yönetimi")
        st.write("Sistem, yaptığınız işlemlerin sonucuna göre kasanızı otomatik günceller.")
        st.info("Yeni bir işlem sonucu girdiğinizde Güncel Kasa anında değişecektir.")

    with col_chart:
        st.subheader("📈 K/Z Grafiği (Günlük)")
        if not df.empty:
            df['cum_pnl'] = df['PnL'].cumsum() if 'PnL' in df.columns else 0
            fig_line = px.line(df, x='time', y='cum_pnl', template="plotly_dark")
            # SAAT/DAKİKA KALDIRMA, SADECE GÜN
            fig_line.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
            fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.write("Grafik için veri bekleniyor...")
