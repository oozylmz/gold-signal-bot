import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ"
CHAT_ID = "-1004490031358"

def init_db():
    conn = sqlite3.connect('signals.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, signal TEXT, pattern TEXT, 
                  entry REAL, tp1 REAL, tp2 REAL, sl REAL, rsi REAL, time TEXT, status TEXT,
                  exit_price REAL, exit_time TEXT)''')
    try:
        c.execute("ALTER TABLE signals ADD COLUMN exit_price REAL")
    except: pass
    try:
        c.execute("ALTER TABLE signals ADD COLUMN exit_time TEXT")
    except: pass
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
    except Exception as e: print(f"DB Hatası: {e}")

def send_telegram_msg(data):
    # HATA AYIKLAMA: Token ve ID kontrolü
    if not TELEGRAM_TOKEN:
        print("🚨 HATA: TELEGRAM_TOKEN bulunamadı! Render Environment Variables'ı kontrol edin.")
        return
    if not CHAT_ID:
        print("🚨 HATA: CHAT_ID bulunamadı! Render Environment Variables'ı kontrol edin.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! SİNYAL*\n\n📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n📊 RSI: `{data.get('rsi')}`")
    
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Mesaj başarıyla gönderildi!")
        else:
            # BURASI ÇOK ÖNEMLİ: Telegram'ın verdiği gerçek hata mesajını yazdırır
            print(f"❌ Telegram Hatası! Kod: {response.status_code} - Cevap: {response.text}")
    except Exception as e:
        print(f"🚨 Bağlantı Hatası: {e}")

@app.route('/')
def home():
    return "SÜRÜM 5.0 - KODLAR GÜNCELLENDİ! ✅ <br>Token Durumu: " + str(TELEGRAM_TOKEN)

@app.route('/get_signals', methods=['GET'])
def get_signals():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("SELECT * FROM signals ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        columns = ['id', 'symbol', 'signal', 'pattern', 'entry', 'tp1', 'tp2', 'sl', 'rsi', 'time', 'status', 'exit_price', 'exit_time']
        signals = [dict(zip(columns, row)) for row in rows]
        return jsonify(signals), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/update_trade', methods=['POST'])
def update_trade():
    data = request.json
    trade_id, new_status, exit_p = data.get('id'), data.get('status'), data.get('exit_price')
    if trade_id and new_status:
        try:
            conn = sqlite3.connect('signals.db')
            c = conn.cursor()
            c.execute("UPDATE signals SET status = ?, exit_price = ?, exit_time = ? WHERE id = ?", 
                      (new_status, exit_p, datetime.now().strftime("%Y-%m-%d %H:%M"), trade_id))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"}), 200
        except Exception as e: return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Eksik veri"}), 400

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET': return "Webhook Aktif! ✅", 200
    if request.method == 'POST':
        data = request.json
        if data:
            save_to_db(data)
            send_telegram_msg(data)
            return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
