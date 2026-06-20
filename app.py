import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="GOLD-MGC1 QUANT", layout="wide", page_icon="💰")

# --- MODERN NEON UI CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0b10; color: #e0e0e0; }
    div[data-testid="stMetric"] { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 12px; 
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 12px; }
    .stButton>button { 
        background-color: #f39c12 !important; 
        color: black !important; 
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #161b22; 
        border-radius: 8px 8px 0 0; 
        color: white !important; 
    }
    .stTabs [aria-selected="true"] { background-color: #f39c12 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://gold-signal-bot-1.onrender.com"
S_URL = f"{API_URL}/get_signals"
U_URL = f"{API_URL}/update_trade"
B_URL = f"{API_URL}/get_balance"
UB_URL = f"{API_URL}/update_balance"

st.title("🟡 GOLD — MGC1 HARMONIC")
st.markdown("✨ **Sinyal Takip ve Kasa Yönetim Sistemi**")

tab1, tab2 = st.tabs(["📡 SİNYALLER", "💰 KASA TAKİP"])

# ---------------------------------------------------------------------------
# SEKME 1: SİNYALLER
# ---------------------------------------------------------------------------
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
        
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.subheader("📜 Sinyal Geçmişi")
            display_df = df[['time', 'pattern', 'signal', 'entry', 'sl', 'tp2', 'status']].copy()
            st.dataframe(display_//df.sort_values('id', ascending=False), use_container_width=True) # Bu satırdaki / işaretlerini siliyorum

        with c_right:
            st.subheader("🎯 Son Sinyal Detayı")
            last = df.iloc[0]
            st.markdown(f"""
            <div style="background-color:#161b22; padding:20px; border-radius:15px; border:1px solid #f39c12">
                <h3 style="color:#f39c12; margin-bottom:10px;">{last['pattern']}</h3>
                <p><b>Yön:</b> {'<span style="color:green">BUY</span>' if last['signal']=='BUY' else '<span style="color:red">SELL</span>'}</p>
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
        st.info("Halen sinyal yok, piyasa bekleniyor...")

# ---------------------------------------------------------------------------
# SEKME 2: KASA TAKİP
# ---------------------------------------------------------------------------
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

    if daily_pnl <= -3000:
        st.error(f"🚨 KRİTİK: GÜNLÜK KAYIP LİMİTİ AŞILDI! (${daily_pnl:.2f})")
    elif daily_pnl >= 1000:
        st.success(f"✅ HEDEF TAMAMLANDI! (${daily_pnl:.2f} KAR) - DURUN!")
    else:
        st.info(f"Günlük Durum: ${daily_pnl:.2f}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("BAŞLANGIÇ KASASI", "$10,000")
    k2.metric("GÜNCEL KASA", f"${balance:,.2f}")
    k3.metric("TOPLAM K/Z", f"${total_p:,.2f}")
    k4.metric("GÜNLÜK K/Z", f"${daily_pnl:,.2f}")

    st.markdown("---")
    
    col_setup, col_chart = st.columns([1, 1])
    with col_setup:
        st.subheader("⚙️ Kasa Ayarları")
        with st.form("bal_form"):
            new_bal = st.number_input("Kasa Bakiyesi ($)", value=balance)
            if st.form_submit_button("Kaydet"):
                requests.post(UB_URL, json={"balance": new_bal})
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📐 Lot Hesaplayıcı")
        with st.container():
            r_usd = st.number_input("Risk ($)", value=100.0)
            en_p = st.number_input("Giriş", value=2000.0)
            st_p = st.number_input("Stop", value=1990.0)
            res_lot = r_usd / abs(en_p - st_p) if abs(en_p - st_p) != 0 else 0
            st.warning(f"Önerilen Lot: **{res_lot:.4f}**")

    with col_chart:
        st.subheader("📈 K/Z Grafiği")
        if not df.empty:
            df['cum_pnl'] = df['PnL'].cumsum()
            fig_line = px.line(df, x='time', y='cum_pnl', template="plotly_dark")
            fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.write("Grafik için veri bekleniyor...")
