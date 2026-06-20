import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ"
CHAT_ID = "-1004490031358"

# =========================================================================
# KRİTİK DÜZELTME: Veri tabanı kurulumu artık Gunicorn tarafından da çalıştırılır.
# =========================================================================
def init_db():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        # Tabloyu oluştur
        c.execute('''CREATE TABLE IF NOT EXISTS signals 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, signal TEXT, pattern TEXT, 
                      entry REAL, tp1 REAL, tp2 REAL, sl REAL, rsi REAL, time TEXT, status TEXT,
                      exit_price REAL, exit_time TEXT)''')
        
        # Sütun güncellemeleri (Sürüm yükseltme)
        try:
            c.execute("ALTER TABLE signals ADD COLUMN exit_price REAL")
        except: pass
        try:
            c.execute("ALTER TABLE signals ADD COLUMN exit_time TEXT")
        except: pass
            
        conn.commit()
        conn.close()
        print("✅ Veri tabanı başarıyla kuruldu/güncellendi.")
    except Exception as e:
        print(f"🚨 Veri tabanı kurulum hatası: {e}")

# SUNUCU BAŞLADIĞI AN TABLOYU OLUŞTUR (if __name__'den bağımsız)
init_db() 
# =========================================================================

def save_to_db(data):
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        
        def safe_float(val):
            try: return float(val)
            except: return 0.0

        c.execute("INSERT INTO signals (symbol, signal, pattern, entry, tp1, tp2, sl, rsi, time, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (
                      str(data.get('symbol', 'Unknown')), 
                      str(data.get('signal', 'Unknown')), 
                      str(data.get('pattern', 'Unknown')), 
                      safe_float(data.get('entry')), 
                      safe_float(data.get('tp1')), 
                      safe_float(data.get('tp2')), 
                      safe_float(data.get('sl')), 
                      safe_float(data.get('rsi')), 
                      datetime.now().strftime("%Y-%m-%d %H:%M"), 
                      "OPEN"
                  ))
        conn.commit()
        conn.close()
        print("✅ Veri başarıyla kaydedildi!")
    except Exception as e: 
        print(f"🚨 DB KAYIT HATASI: {e}")

def send_telegram_msg(data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! SİNYAL*\n\n📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n📊 RSI: `{data.get('rsi')}`")
    
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200: print("✅ Telegram mesajı gönderildi!")
        else: print(f"❌ Telegram Hatası: {response.text}")
    except Exception as e: print(f"🚨 Bağlantı Hatası: {e}")

@app.route('/')
def home():
    return "SÜRÜM 7.0 - VERİ TABANI TAMİR EDİLDİ ✅", 200

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
    app.run(host='0.0.0.0', port=5000)
