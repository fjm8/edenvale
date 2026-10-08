import os, sqlite3, datetime, random
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)
DB_PATH = "/tmp/edenvale.db" # FIX for Render

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY,
        tracking TEXT UNIQUE,
        item_name TEXT,
        category TEXT,
        qty INTEGER,
        supplier TEXT,
        location TEXT,
        aisle TEXT,
        bay TEXT,
        shelf TEXT,
        status TEXT,
        date_in TEXT
    )""")
    return conn

BASE = """<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial;margin:0;background:#f8fafc}.header{background:white;padding:16px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between}.container{max-width:600px;margin:auto;padding:16px}.card{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px}.btn{display:block;padding:16px;background:white;border:1px solid #e5e7eb;border-radius:12px;text-decoration:none;color:black;font-weight:600;margin-bottom:10px}.primary{background:black;color:white;border:none;width:100%;padding:14px;border-radius:12px} input,select{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;margin:6px 0}</style>"""
def hdr(t): return f'<div class="header"><b>📦 EDENVALE WMS</b><span>{t}</span></div>'

@app.route('/')
def home():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    conn.close()
    return render_template_string(BASE + hdr("Live") + f"<div class='container'><h2>Warehouse Control - LIVE ✅</h2><div class='card'>Total Items: {total}</div><a class='btn' href='/inbound'>📥 Receive Stock</a><a class='btn' href='/locate'>🗺️ Find Item</a><a class='btn' href='/all'>📋 All Stock</a></div>")

@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method == 'POST':
        track = (request.form.get('tracking') or f"EDV-{random.randint(1000,9999)}").upper()
        loc = f"{request.form['aisle']}-{request.form['bay']}-{request.form['shelf']}"
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO stock VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)", (track, request.form['item'], request.form['category'], int(request.form['qty']), request.form['supplier'], loc, request.form['aisle'], request.form['bay'], request.form['shelf'], 'IN STOCK', datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit(); conn.close()
        return redirect('/')
    return render_template_string(BASE + hdr("Inbound") + "<div class='container'><div class='card'><h3>What Came In?</h3><form method='post'><input name='item' placeholder='Item Name' required><select name='category'><option>Electrical</option><option>Hardware</option><option>Other</option></select><input name='qty' type='number' placeholder='Qty' required><input name='supplier' placeholder='Supplier'><input name='tracking' placeholder='Barcode (auto if empty)'><div style='display:flex;gap:6px'><select name='aisle' required><option>A1</option><option>A2</option><option>B1</option></select><select name='bay' required><option>01</option><option>02</option><option>03</option></select><select name='shelf' required><option>S1</option><option>S2</option><option>S3</option></select></div><button class='primary' style='margin-top:10px'>Save</button></form></div><a href='/'>← Back</a></div>")

@app.route('/locate', methods=['GET','POST'])
def locate():
    res=[]
    if request.method=='POST':
        q="%"+request.form['q'].upper()+"%"
        conn=get_db(); res=conn.execute("SELECT * FROM stock WHERE tracking LIKE? OR item_name LIKE?", (q,q)).fetchall(); conn.close()
    return render_template_string(BASE + hdr("Find") + "<div class='container'><div class='card'><form method='post' style='display:flex;gap:6px'><input name='q' placeholder='Search' required><button class='primary' style='width:80px'>Find</button></form></div>{% for r in res %}<div class='card'><b>{{r[2]}}</b> - {{r[1]}} - 📍 {{r[6]}}</div>{% endfor %}</div>", res=res)

@app.route('/all')
def allstock():
    conn=get_db(); rows=conn.execute("SELECT * FROM stock ORDER BY id DESC").fetchall(); conn.close()
    html=BASE+hdr("All")+"<div class='container'><h3>All Stock</h3>"
    for r in rows: html+=f"<div class='card'><b>{r[2]}</b> - {r[1]} - 📍{r[6]}</div>"
    return html+"<a href='/'>← Back</a></div>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
