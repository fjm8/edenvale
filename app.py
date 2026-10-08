import os, sqlite3, datetime, random
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)
DB_PATH = "/tmp/edenvale.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, tracking TEXT UNIQUE, item_name TEXT, qty INTEGER, status TEXT, date_in TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS pickups (id INTEGER PRIMARY KEY, tracking TEXT, item_name TEXT, driver_id TEXT, driver_name TEXT, picked_at TEXT)")
    return conn

HTML = "<meta name='viewport' content='width=device-width, initial-scale=1'><style>body{font-family:Arial;padding:20px;background:#f8fafc}.card{background:white;padding:16px;border-radius:12px;margin:10px 0;border:1px solid #ddd}.btn{display:block;padding:15px;background:#2563eb;color:white;text-align:center;border-radius:10px;text-decoration:none;margin:10px 0;font-weight:bold}input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #ddd;box-sizing:border-box}</style>"

@app.route('/')
def home():
    return render_template_string(HTML + "<h2>EDENVALE WMS LIVE ✅</h2><a class='btn' href='/driver'>🚚 DRIVER LINK - CLICK HERE</a><a class='btn' style='background:black' href='/inbound'>📥 Receive Stock</a><div class='card'>Driver link to share:<br><b>https://edenvale.onrender.com/driver</b></div>")

@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method == 'POST':
        t = (request.form.get('tracking') or f"EDV-{random.randint(1000,9999)}").upper()
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO stock VALUES (NULL,?,?,?,?,?)", (t, request.form['item'], int(request.form['qty']), 'IN STOCK', datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template_string(HTML + "<div class='card'><h3>Receive Stock</h3><form method='post'><input name='item' placeholder='Item name' required><input name='qty' type='number' placeholder='Qty' required><input name='tracking' placeholder='Box code EDV-1001 (auto if empty)'><button style='width:100%;padding:14px;background:black;color:white;border-radius:8px;margin-top:10px'>Save</button></form></div><a href='/'>Back</a>")

@app.route('/driver', methods=['GET','POST'])
def driver():
    msg = ""
    if request.method == 'POST':
        t = request.form['tracking'].strip().upper()
        did = request.form['driver_id'].strip()
        dname = request.form['driver_name'].strip()
        conn = get_db()
        item = conn.execute("SELECT item_name FROM stock WHERE tracking=?", (t,)).fetchone()
        if not item:
            msg = f"❌ Box {t} NOT FOUND"
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO pickups VALUES (NULL,?,?,?,?,?)", (t, item[0], did, dname, now))
            conn.execute("UPDATE stock SET status='PICKED UP' WHERE tracking=?", (t,))
            conn.commit()
            msg = f"✅ SUCCESS! {t} picked by {dname}"
        conn.close()
    conn = get_db()
    rows = conn.execute("SELECT * FROM pickups ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    rhtml = "".join([f"<div class='card'><b>{r[1]}</b> - {r[4]} ({r[3]}) at {r[5]}</div>" for r in rows])
    return render_template_string(HTML + f"<h2 style='background:#2563eb;color:white;padding:16px;border-radius:10px'>🚚 DRIVER PICKUP</h2><div class='card' style='border:2px solid #2563eb'><div style='background:#eff6ff;padding:10px;border-radius:8px'>{msg}</div><form method='post'><label>📦 Box Code</label><input name='tracking' placeholder='EDV-1234' required autofocus><label>🪪 Driver ID</label><input name='driver_id' required><label>👤 Name</label><input name='driver_name' required><button style='width:100%;padding:14px;background:#2563eb;color:white;border-radius:8px;font-weight:bold'>CONFIRM PICKUP</button></form></div>{rhtml}<a href='/'>← Home</a>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
