import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = "8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ"
CHAT_ID = "-1004490031358"

def init_db():
    conn = sqlite3.connect('signals.db')
    c = conn.cursor()
    # Sinyaller Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, signal TEXT, pattern TEXT, 
                  entry REAL, tp1 REAL, tp2 REAL, sl REAL, rsi REAL, time TEXT, status TEXT,
                  exit_price REAL, exit_time TEXT)''')
    # Kasa Tablosu (YENİ)
    c.execute('''CREATE TABLE IF NOT EXISTS balance 
                 (id INTEGER PRIMARY KEY, current_balance REAL, total_profit REAL)''')
    
    # Varsayılan kasa bakiyesi ekle (Eğer tablo boşsa 10,000$ ile başlat)
    c.execute("SELECT COUNT(*) FROM balance")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO balance (id, current_balance, total_profit) VALUES (1, 10000.0, 0.0)")
    
    try: c.execute("ALTER TABLE signals ADD COLUMN exit_price REAL")
    except: pass
    try: c.execute("ALTER TABLE signals ADD COLUMN exit_time TEXT")
    except: pass
    conn.commit()
    conn.close()

init_db()

# --- KASA YÖNETİM API'LERİ ---
@app.route('/get_balance', methods=['GET'])
def get_balance():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("SELECT current_balance, total_profit FROM balance WHERE id=1")
        row = c.fetchone()
        conn.close()
        return jsonify({"balance": row[0], "total_profit": row[1]}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    new_bal = data.get('balance')
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("UPDATE balance SET current_balance = ? WHERE id=1", (new_bal,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- DİĞER ROUTERLAR (Sinyal ve Webhook kısımları aynen kalıyor) ---
@app.route('/')
def home(): return "Quant Pro Sunucu Aktif ✅", 200

@app.route('/get_signals', methods=['GET'])
def get_signals():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("SELECT * FROM signals ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        columns = ['id', 'symbol', 'signal', 'pattern', 'entry', 'tp1', 'tp2', 'sl', 'rsi', 'time', 'status', 'exit_price', 'exit_time']
        return jsonify([dict(zip(columns, row)) for row in rows]), 200
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
            # save_to_db ve send_telegram_msg fonksiyonları yukarıdakiyle aynı kalacak
            save_to_db(data)
            send_telegram_msg(data)
            return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

def save_to_db(data):
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        def safe_float(val):
            try: return float(val)
            except: return 0.0
        c.execute("INSERT INTO signals (symbol, signal, pattern, entry, tp1, tp2, sl, rsi, time, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (str(data.get('symbol')), str(data.get('signal')), str(data.get('pattern')), 
                   safe_float(data.get('entry')), safe_float(data.get('tp1')), safe_float(data.get('tp2')), 
                   safe_float(data.get('sl')), safe_float(data.get('rsi')), 
                   datetime.now().strftime("%Y-%m-%d %H:%M"), "OPEN"))
        conn.commit()
        conn.close()
    except Exception as e: print(f"DB Hatası: {e}")

def send_telegram_msg(data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! SİNYAL*\n\n📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n📊 RSI: `{data.get('rsi')}`")
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
