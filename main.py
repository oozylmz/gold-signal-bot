import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = os.getenv("8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ")
CHAT_ID = os.getenv("-1004490031358")

# --- VERİ TABANI FONKSİYONLARI (SÜPER GÜNCELLEME) ---
def init_db():
    conn = sqlite3.connect('signals.db')
    c = conn.cursor()
    # Tabloyu oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, signal TEXT, pattern TEXT, 
                  entry REAL, tp1 REAL, tp2 REAL, sl REAL, rsi REAL, time TEXT, status TEXT)''')
    
    # KRİTİK NOKTA: Eksik sütunları kontrol et ve ekle (Sürüm yükseltme)
    try:
        c.execute("ALTER TABLE signals ADD COLUMN exit_price REAL")
    except sqlite3.OperationalError:
        pass # Sütun zaten varsa hata vermez, geçer.
        
    try:
        c.execute("ALTER TABLE signals ADD COLUMN exit_time TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def save_to_db(data):
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        # Veri ekleme (Sütun sayısı dinamik kontrol edilmeli)
        c.execute("INSERT INTO signals (symbol, signal, pattern, entry, tp1, tp2, sl, rsi, time, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (data.get('symbol'), data.get('signal'), data.get('pattern'), 
                   float(data.get('entry')), float(data.get('tp1')), float(data.get('tp2')), 
                   float(data.get('sl')), float(data.get('rsi')), 
                   datetime.now().strftime("%Y-%m-%d %H:%M"), "OPEN"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Kayıt Hatası: {e}")

def send_telegram_msg(data):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! SİNYAL*\n\n📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n📊 RSI: `{data.get('rsi')}`")
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- ROUTERLAR ---
@app.route('/')
def home():
    return "Sistem Canlı ve Güncel! ✅", 200

@app.route('/get_signals', methods=['GET'])
def get_signals():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("SELECT * FROM signals ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        # Sütun isimlerini dinamik olarak alalım
        columns = [description[0] for description in c.description] if 'c' in locals() else []
        # Eğer c.description çalışmazsa manuel isimler:
        columns = ['id', 'symbol', 'signal', 'pattern', 'entry', 'tp1', 'tp2', 'sl', 'rsi', 'time', 'status', 'exit_price', 'exit_time']
        
        signals = []
        for row in rows:
            signals.append(dict(zip(columns, row)))
        return jsonify(signals), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_trade', methods=['POST'])
def update_trade():
    data = request.json
    trade_id = data.get('id')
    new_status = data.get('status')
    exit_p = data.get('exit_price')
    
    if trade_id and new_status:
        try:
            conn = sqlite3.connect('signals.db')
            c = conn.cursor()
            c.execute("UPDATE signals SET status = ?, exit_price = ?, exit_time = ? WHERE id = ?", 
                      (new_status, exit_p, datetime.now().strftime("%Y-%m-%d %H:%M"), trade_id))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Eksik veri"}), 400

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "Webhook Aktif! ✅", 200
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
