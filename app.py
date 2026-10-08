import os, sqlite3, datetime, random
from flask import Flask, request, render_template_string, redirect
app = Flask(__name__)
DB_PATH = "/tmp/edenvale.db"
def get_db():
    conn=sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, tracking TEXT UNIQUE, item_name TEXT, category TEXT, qty INTEGER, supplier TEXT, location TEXT, aisle TEXT, bay TEXT, shelf TEXT, status TEXT, date_in TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS pickups (id INTEGER PRIMARY KEY, tracking TEXT, item_name TEXT, driver_id TEXT, driver_name TEXT, picked_at TEXT)""")
    return conn
BASE="""<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial;margin:0;background:#f8fafc}.header{background:white;padding:16px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center}.container{max-width:600px;margin:auto;padding:16px}.card{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px}.btn{display:block;padding:16px;background:white;border:1px solid #e5e7eb;border-radius:12px;text-decoration:none;color:black;font-weight:600;margin-bottom:10px;text-align:center}.btn-driver{background:#2563eb;color:white;border:none}.primary{background:black;color:white;border:none;width:100%;padding:14px;border-radius:12px;font-weight:600} input,select{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;margin:6px 0;box-sizing:border-box}</style>"""
@app.route('/')
def home():
    conn=get_db(); total=conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]; conn.close()
    return render_template_string(BASE+"""<div style="padding:16px;background:white;border-bottom:1px solid #ddd;display:flex;justify-content:space-between"><b>📦 EDENVALE WMS</b><a href="/driver" style="background:#2563eb;color:white;padding:8px 12px;border-radius:8px;text-decoration:none">🚚 Driver</a></div><div class="container"><h2>Warehouse Control - LIVE ✅</h2><a class="btn" href="/inbound">📥 Receive Stock</a><a class="btn" href="/all">📋 All Stock</a><a class="btn btn-driver" href="/driver">🚚 DRIVER PICKUP LINK</a><div class="card" style="background:#eff6ff">Share with drivers:<br><b>https://edenvale.onrender.com/driver</b></div></div>""")
@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method=='POST':
        track=(request.form.get('tracking') or f"EDV-{random.randint(1000,9999)}").upper(); loc=f"{request.form['aisle']}-{request.form['bay']}-{request.form['shelf']}"
        conn=get_db(); conn.execute("INSERT OR REPLACE INTO stock VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)", (track, request.form['item'], 'General', int(request.form['qty']), request.form['supplier'], loc, request.form['aisle'], request.form['bay'], request.form['shelf'], 'IN STOCK', datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))); conn.commit(); conn.close(); return redirect('/')
    return render_template_string(BASE+"""<div class="container"><div class="card"><h3>Receive Stock</h3><form method="post"><input name="item" placeholder="Item Name" required><input name="qty" type="number" placeholder="Qty" required><input name="supplier" placeholder="Supplier"><input name="tracking" placeholder="Box Code e.g. EDV-1001"><div style="display:flex;gap:6px"><select name="aisle"><option>A1</option><option>A2</option></select><select name="bay"><option>01</option><option>02</option></select><select name="shelf"><option>S1</option><option>S2</option></select></div><button class="primary" style="margin-top:10px">Save</button></form></div><a href="/">Back</a></div>""")
@app.route('/driver', methods=['GET','POST'])
def driver():
    msg=""
    if request.method=='POST':
        t=request.form['tracking'].strip().upper(); did=request.form['driver_id'].strip(); dname=request.form['driver_name'].strip()
        conn=get_db(); item=conn.execute("SELECT item_name FROM stock WHERE tracking=?", (t,)).fetchone()
        if not item: msg=f"❌ Box {t} NOT FOUND"
        else:
            now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO pickups VALUES (NULL,?,?,?,?,?)", (t, item[0], did, dname, now)); conn.execute("UPDATE stock SET status='PICKED UP' WHERE tracking=?", (t,)); conn.commit(); msg=f"✅ {t} picked by {dname} ({did}) at {now}"
        conn.close()
    conn=get_db(); recent=conn.execute("SELECT * FROM pickups ORDER BY id DESC LIMIT 20").fetchall(); conn.close()
    rows="".join([f"<div class='card'><b>{r[1]}</b> - {r[2]}<br>👤 {r[4]} ({r[3]}) at {r[5]}</div>" for r in recent])
    return render_template_string(BASE+"""<div style="background:#2563eb;color:white;padding:16px;display:flex;justify-content:space-between"><b>🚚 DRIVER PICKUP</b><a href="/" style="color:white;text-decoration:none">← Home</a></div><div class="container"><div class="card" style="border:2px solid #2563eb"><h3>Scan Box</h3>{% if msg %}<div style="background:#f0f9ff;padding:10px;border-radius:8px;font-weight:600;margin-bottom:10px">{{msg}}</div>{% endif %}<form method="post"><label>📦 Box Code</label><input name="tracking" placeholder="EDV-1234" required autofocus style="font-size:18px;font-weight:700;border:2px solid #2563eb"><label>🪪 Driver ID</label><input name="driver_id" required><label>👤 Name</label><input name="driver_name" required><button class="primary" style="background:#2563eb;margin-top:10px">✅ CONFIRM PICKUP</button></form></div><h3>Recent Pickups</h3>"""+rows+"</div>", msg=msg)
@app.route('/all')
def allstock():
    conn=get_db(); rows=conn.execute("SELECT * FROM stock ORDER BY id DESC").fetchall(); picks=conn.execute("SELECT * FROM pickups ORDER BY id DESC").fetchall(); conn.close()
    html=BASE+"<div class='container'><h3>Stock</h3>"
    for r in rows: html+=f"<div class='card'><b>{r[2]}</b> - {r[1]} - {r[6]} - {r[10]}</div>"
    html+="<h3>Pickups</h3>"
    for p in picks: html+=f"<div class='card'>{p[1]} - {p[4]} at {p[5]}</div>"
    return html+"<a href='/'>Back</a></div>"
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
