import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = os.getenv("8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ")
CHAT_ID = os.getenv("-1004490031358")

# --- ANA SAYFA TESTİ (YENİ EKLEDİK) ---
@app.route('/')
def home():
    return "Sistem Çalışıyor! Bot Aktif. ✅", 200

# --- VERİ TABANI FONKSİYONLARI ---
def init_db():
    conn = sqlite3.connect('signals.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  symbol TEXT, signal TEXT, pattern TEXT, 
                  entry REAL, tp1 REAL, tp2 REAL, sl REAL, 
                  rsi REAL, time TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("INSERT INTO signals (symbol, signal, pattern, entry, tp1, tp2, sl, rsi, time, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (data.get('symbol'), data.get('signal'), data.get('pattern'), 
                   float(data.get('entry')), float(data.get('tp1')), float(data.get('tp2')), 
                   float(data.get('sl')), float(data.get('rsi')), 
                   datetime.now().strftime("%Y-%m-%d %H:%M"), "OPEN"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Veri tabanı hatası: {e}")

def send_telegram_msg(data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! HARMONİK SİNYAL*\n\n"
           f"📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n"
           f"💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n"
           f"🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n"
           f"📊 RSI: `{data.get('rsi')}`\n\n"
           f"⏰ Saat: {datetime.now().strftime('%H:%M')}")
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- WEBHOOK ENDPOINT ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        if data:
            save_to_db(data)
            send_telegram_msg(data)
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "no data"}), 400
    return jsonify({"status": "wrong method"}), 405

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
