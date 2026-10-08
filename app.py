import os, sqlite3, datetime, random
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)
DB_PATH = "/tmp/edenvale.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY, tracking TEXT UNIQUE, item_name TEXT,
        category TEXT, qty INTEGER, supplier TEXT, location TEXT,
        aisle TEXT, bay TEXT, shelf TEXT, status TEXT, date_in TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS pickups (
        id INTEGER PRIMARY KEY, tracking TEXT, item_name TEXT,
        driver_id TEXT, driver_name TEXT, picked_at TEXT)""")
    return conn

BASE = """<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial;margin:0;background:#f8fafc}.header{background:white;padding:16px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center}.container{max-width:600px;margin:auto;padding:16px}.card{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,0.05)}.btn{display:block;padding:16px;background:white;border:1px solid #e5e7eb;border-radius:12px;text-decoration:none;color:black;font-weight:600;margin-bottom:10px;text-align:center}.btn-driver{background:#2563eb;color:white;border:none}.primary{background:black;color:white;border:none;width:100%;padding:14px;border-radius:12px;font-weight:600} input,select{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;margin:6px 0;box-sizing:border-box}.badge{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}.in{background:#dcfce7;color:#166534}.out{background:#fee2e2;color:#991b1b}</style>"""
def hdr(t): return f'<div class="header"><b>📦 EDENVALE WMS</b><span>{t}</span><a href="/driver" style="background:#2563eb;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;font-size:13px">🚚 Driver Portal</a></div>'

@app.route('/')
def home():
    conn=get_db()
    total=conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    instock=conn.execute("SELECT COUNT(*) FROM stock WHERE status='IN STOCK'").fetchone()[0]
    picked=conn.execute("SELECT COUNT(*) FROM pickups").fetchone()[0]
    conn.close()
    return render_template_string(BASE+hdr("Live")+f"""
    <div class='container'>
    <h2>Warehouse Control - LIVE ✅</h2>
    <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px'>
      <div class='card' style='text-align:center'><b>{total}</b><br><small>Total</small></div>
      <div class='card' style='text-align:center'><b>{instock}</b><br><small>In Stock</small></div>
      <div class='card' style='text-align:center'><b>{picked}</b><br><small>Picked</small></div>
    </div>
    <a class='btn' href='/inbound'>📥 Receive Stock</a>
    <a class='btn' href='/locate'>🗺️ Find Item</a>
    <a class='btn' href='/all'>📋 All Stock</a>
    <a class='btn btn-driver' href='/driver'>🚚 DRIVER PICKUP LINK - Click Here</a>
    <div class='card' style='margin-top:16px;background:#eff6ff'><b>Driver Link to share:</b><br><small>https://edenvale.onrender.com/driver</small></div>
    </div>""")

@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method=='POST':
        track=(request.form.get('tracking') or f"EDV-{random.randint(1000,9999)}").upper()
        loc=f"{request.form['aisle']}-{request.form['bay']}-{request.form['shelf']}"
        conn=get_db(); conn.execute("INSERT OR REPLACE INTO stock VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)", (track, request.form['item'], request.form['category'], int(request.form['qty']), request.form['supplier'], loc, request.form['aisle'], request.form['bay'], request.form['shelf'], 'IN STOCK', datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))); conn.commit(); conn.close(); return redirect('/')
    return render_template_string(BASE+hdr("Inbound")+"""
    <div class='container'><div class='card'><h3>What Came In?</h3>
    <form method='post'><input name='item' placeholder='Item Name' required>
    <select name='category'><option>Electrical</option><option>Hardware</option><option>Other</option></select>
    <input name='qty' type='number' placeholder='Qty' required><input name='supplier' placeholder='Supplier'>
    <input name='tracking' placeholder='Barcode (auto if empty)'><div style='display:flex;gap:6px'>
    <select name='aisle' required><option>A1</option><option>A2</option><option>B1</option></select>
    <select name='bay' required><option>01</option><option>02</option><option>03</option></select>
    <select name='shelf' required><option>S1</option><option>S2</option><option>S3</option></select></div>
    <button class='primary' style='margin-top:10px'>Save Stock</button></form></div><a href='/'>← Back</a></div>""")

# ===== DRIVER SYSTEM - SEPARATE LINK =====
@app.route('/driver', methods=['GET','POST'])
def driver_portal():
    msg=""; found=None
    if request.method=='POST':
        tracking=request.form['tracking'].strip().upper()
        driver_id=request.form['driver_id'].strip()
        driver_name=request.form['driver_name'].strip()
        if not tracking or not driver_id:
            msg="⚠️ Enter Box Code + Driver ID"
        else:
            conn=get_db()
            item=conn.execute("SELECT item_name FROM stock WHERE tracking=?", (tracking,)).fetchone()
            if not item:
                msg=f"❌ Box Code {tracking} NOT FOUND in warehouse"
            else:
                now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT INTO pickups VALUES (NULL,?,?,?,?,?)", (tracking, item[0], driver_id, driver_name, now))
                conn.execute("UPDATE stock SET status='PICKED UP' WHERE tracking=?", (tracking,))
                conn.commit()
                msg=f"✅ SUCCESS! Box {tracking} picked up by Driver {driver_name} ({driver_id}) at {now}"
                found=tracking
            conn.close()
    conn=get_db(); recent=conn.execute("SELECT * FROM pickups ORDER BY id DESC LIMIT 10").fetchall(); conn.close()
    rows="".join([f"<div class='card'><b>{r[1]}</b> - {r[2]}<br><small>👤 {r[4]} ({r[3]}) at {r[5]}</small></div>" for r in recent])
    return render_template_string(BASE+"""
    <div style="background:#2563eb;color:white;padding:16px;display:flex;justify-content:space-between"><b>🚚 DRIVER PICKUP</b><a href="/" style="color:white;text-decoration:none">← Warehouse</a></div>
    <div class='container'>
    <div class='card' style="border:2px solid #2563eb">
      <h3>Scan Box to Pickup</h3>
      {% if msg %}<div class='card' style="background:#f0f9ff;font-weight:600">{{msg}}</div>{% endif %}
      <form method='post'>
        <label>📦 Box / Tracking Code (SCAN HERE)</label>
        <input name='tracking' placeholder='Scan barcode or type EDV-1234' required autofocus style="font-size:18px;font-weight:700;border:2px solid #2563eb">
        <label>🪪 Driver ID / Employee Code</label>
        <input name='driver_id' placeholder='e.g. DRV001 or ID number' required>
        <label>👤 Driver Name</label>
        <input name='driver_name' placeholder='Full name' required>
        <button class='primary' style="background:#2563eb;margin-top:10px">✅ CONFIRM PICKUP</button>
      </form>
    </div>
    <h3>Recent Pickups</h3>"""+rows+"""</div>""", msg=msg)

@app.route('/locate', methods=['GET','POST'])
def locate():
    res=[];
    if request.method=='POST':
        q="%"+request.form['q'].upper()+"%"; conn=get_db(); res=conn.execute("SELECT * FROM stock WHERE tracking LIKE? OR item_name LIKE?", (q,q)).fetchall(); conn.close()
    return render_template_string(BASE+hdr("Find")+"""
    <div class='container'><div class='card'><form method='post' style='display:flex;gap:6px'><input name='q' placeholder='Search Box Code' required><button class='primary' style='width:80px'>Find</button></form></div>
    {% for r in res %}<div class='card'><b>{{r[2]}}</b> - {{r[1]}} - 📍{{r[6]}} - <span class='badge {{'in' if r[10]=='IN STOCK' else 'out'}}'>{{r[10]}}</span></div>{% endfor %}</div>""", res=res)

@app.route('/all')
def allstock():
    conn=get_db(); rows=conn.execute("SELECT * FROM stock ORDER BY id DESC").fetchall(); picks=conn.execute("SELECT * FROM pickups ORDER BY id DESC").fetchall(); conn.close()
    html=BASE+hdr("All")+"<div class='container'><h3>All Stock</h3>"
    for r in rows:
        status_class="in" if r[10]=='IN STOCK' else "out"
        html+=f"<div class='card'><b>{r[2]}</b> - {r[1]} - 📍{r[6]} <span class='badge {status_class}'>{r[10]}</span></div>"
    html+="<h3 style='margin-top:20px'>🚚 Pickup Log</h3>"
    for p in picks: html+=f"<div class='card'><b>{p[1]}</b> picked by {p[4]} ({p[3]})<br><small>{p[5]}</small></div>"
    return html+"<a href='/'>← Back</a></div>"

if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
