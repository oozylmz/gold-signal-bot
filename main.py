import os
from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = os.getenv("8967758978:AAFfx1F7LJ9Fr2eerAn0Y0vnaUAIhOS8YjQ")
CHAT_ID = os.getenv("-1004490031358")

# --- RÖNTGEN SAYFASI (Hata tespiti için) ---
@app.route('/')
def home():
    # Sunucudaki tüm açık kapıları (rotaları) listeler
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(str(rule))
    
    return f"""
    <h1>Sistem Durumu: AKTİF ✅</h1>
    <p>Sunucunuz şu an çalışıyor. Aşağıdaki kapılar (rotalar) tanımlı:</p>
    <pre>{chr(10).join(routes)}</pre>
    <hr>
    <p><b>Test için şuna tıklayın:</b> <a href="/webhook">Webhook Kapısını Test Et</a></p>
    """

# --- WEBHOOK ENDPOINT ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "Webhook Kapısı Açık! Sadece POST ile sinyal gönderebilirsiniz. ✅", 200
        
    if request.method == 'POST':
        data = request.json
        if data:
            # Veritabanı ve Telegram işlemleri
            save_to_db(data)
            send_telegram_msg(data)
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "no data"}), 400
    return jsonify({"status": "wrong method"}), 405

# --- DİĞER FONKSİYONLAR (Aynen kalıyor) ---
def init_db():
    conn = sqlite3.connect('signals.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, signal TEXT, pattern TEXT, 
                  entry REAL, tp1 REAL, tp2 REAL, sl REAL, rsi REAL, time TEXT, status TEXT)''')
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
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("HATA: Token veya Chat ID eksik!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = (f"🎯 *MGC1! SİNYAL*\n\n📦 Formasyon: `{data.get('pattern')}`\n"
           f"🚀 Yön: *{data.get('signal')}*\n💰 Giriş: `{data.get('entry')}`\n"
           f"🎯 TP1: `{data.get('tp1')}`\n🎯 TP2: `{data.get('tp2')}`\n"
           f"🛑 Stop: `{data.get('sl')}`\n📊 RSI: `{data.get('rsi')}`")
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
# --- DASHBOARD VERİ API'Sİ ---
@app.route('/get_signals', methods=['GET'])
def get_signals():
    try:
        conn = sqlite3.connect('signals.db')
        c = conn.cursor()
        c.execute("SELECT * FROM signals ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        # Verileri JSON formatına çeviriyoruz
        signals = []
        for row in rows:
            signals.append({
                "id": row[0], "symbol": row[1], "signal": row[2], 
                "pattern": row[3], "entry": row[4], "tp1": row[5], 
                "tp2": row[6], "sl": row[7], "rsi": row[8], 
                "time": row[9], "status": row[10]
            })
        return jsonify(signals), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
