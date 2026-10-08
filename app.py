import os, sqlite3, datetime, random
from flask import Flask, request

app = Flask(__name__)
DB = "/tmp/edenvale.db"

def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS stock (tracking TEXT PRIMARY KEY, item TEXT, qty INTEGER, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pickups (id INTEGER PRIMARY KEY, tracking TEXT, driver_id TEXT, driver_name TEXT, time TEXT)")
    return c

@app.route('/')
def home():
    return '<h2>EDENVALE WMS LIVE ✅</h2><a href="/driver" style="background:blue;color:white;padding:20px;display:block;text-align:center;font-weight:bold;text-decoration:none;border-radius:10px">🚚 DRIVER LINK</a><br>Link: https://edenvale.onrender.com/driver<br><br><a href="/inbound">Receive Stock</a>'

@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method == 'POST':
        t = request.form.get('tracking','EDV-'+str(random.randint(1000,9999))).upper()
        conn = db()
        conn.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?)", (t, request.form['item'], request.form['qty'], 'IN STOCK'))
        conn.commit()
        conn.close()
        return '<h2>Saved: '+t+'</h2><a href="/">Home</a>'
    return '<form method="post"><input name="item" placeholder="Item" required><input name="qty" placeholder="Qty" required><input name="tracking" placeholder="Box Code EDV-1001"><button>Save</button></form><a href="/">Home</a>'

@app.route('/driver', methods=['GET','POST'])
def driver():
    msg=''
    if request.method=='POST':
        t=request.form['tracking'].upper().strip()
        d_id=request.form['driver_id']
        d_name=request.form['driver_name']
        conn=db()
        item=conn.execute("SELECT * FROM stock WHERE tracking=?", (t,)).fetchone()
        if not item:
            msg='❌ Box '+t+' NOT FOUND'
        else:
            now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO pickups (tracking, driver_id, driver_name, time) VALUES (?,?,?,?)", (t,d_id,d_name,now))
            conn.execute("UPDATE stock SET status='PICKED UP' WHERE tracking=?", (t,))
            conn.commit()
            msg='✅ SUCCESS '+t+' picked by '+d_name
        conn.close()
    return f'<h2 style="background:blue;color:white;padding:15px">🚚 DRIVER PICKUP</h2><p><b>{msg}</b></p><form method="post"><input name="tracking" placeholder="Box Code EDV-1234" required><br><input name="driver_id" placeholder="Driver ID" required><br><input name="driver_name" placeholder="Name" required><br><button style="background:blue;color:white;padding:10px">CONFIRM PICKUP</button></form><br><a href="/">Home</a>'

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
