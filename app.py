import os, sqlite3, datetime, random
from flask import Flask, request

app = Flask(__name__)
DB = "/tmp/edenvale.db"

def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS stock (tracking TEXT PRIMARY KEY, item TEXT, qty INTEGER, status TEXT, date_in TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pickups (id INTEGER PRIMARY KEY, tracking TEXT, item_name TEXT, driver_id TEXT, driver_name TEXT, time TEXT)")
    return c

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>body{font-family:'Inter',sans-serif}</style>
"""

@app.route('/')
def home():
    conn = db()
    stock = conn.execute("SELECT COUNT(*) FROM stock WHERE status='IN STOCK'").fetchone()[0]
    picked = conn.execute("SELECT COUNT(*) FROM stock WHERE status='PICKED UP'").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    conn.close()
    return f"""
    {STYLE}
    <body class="bg-slate-50 min-h-screen">
    <div class="bg-gradient-to-r from-blue-700 to-indigo-800 text-white p-6 shadow-lg">
        <h1 class="text-2xl font-bold">📦 EDENVALE WMS</h1>
        <p class="opacity-80 text-sm">Warehouse Management System • Live</p>
    </div>
    <div class="p-4 grid grid-cols-3 gap-3 max-w-4xl mx-auto -mt-4">
        <div class="bg-white rounded-xl shadow p-4 text-center"><div class="text-2xl font-bold text-blue-700">{total}</div><div class="text-xs text-slate-500">TOTAL</div></div>
        <div class="bg-white rounded-xl shadow p-4 text-center"><div class="text-2xl font-bold text-emerald-600">{stock}</div><div class="text-xs text-slate-500">IN STOCK</div></div>
        <div class="bg-white rounded-xl shadow p-4 text-center"><div class="text-2xl font-bold text-orange-600">{picked}</div><div class="text-xs text-slate-500">PICKED UP</div></div>
    </div>
    <div class="p-4 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4">
        <a href="/inbound" class="bg-white rounded-2xl shadow hover:shadow-lg p-6 border-l-4 border-emerald-500 transition"><div class="text-3xl">📥</div><h3 class="font-bold text-lg mt-2">Receive Stock</h3><p class="text-sm text-slate-500">Inbound • Generate box code</p></a>
        <a href="/driver" class="bg-blue-600 rounded-2xl shadow hover:shadow-lg p-6 text-white transition"><div class="text-3xl">🚚</div><h3 class="font-bold text-lg mt-2">Driver Pickup</h3><p class="text-sm opacity-80">Scan & confirm pickup</p></a>
        <a href="/stock" class="bg-white rounded-2xl shadow hover:shadow-lg p-6 border-l-4 border-blue-500 transition"><div class="text-3xl">📋</div><h3 class="font-bold text-lg mt-2">View Stock</h3><p class="text-sm text-slate-500">Check inventory</p></a>
        <a href="/report" class="bg-white rounded-2xl shadow hover:shadow-lg p-6 border-l-4 border-indigo-500 transition"><div class="text-3xl">📊</div><h3 class="font-bold text-lg mt-2">Reports</h3><p class="text-sm text-slate-500">Pickup history</p></a>
    </div>
    <div class="text-center p-6 text-xs text-slate-400">edenvale.onrender.com • v2.0</div>
    </body>
    """

@app.route('/driver', methods=['GET','POST'])
def driver():
    msg = ""; color="slate"
    if request.method == 'POST':
        t = request.form['tracking'].upper().strip()
        d_id = request.form['driver_id']
        d_name = request.form['driver_name']
        conn = db()
        item = conn.execute("SELECT item FROM stock WHERE tracking=?", (t,)).fetchone()
        if not item:
            msg = f"❌ Box {t} NOT FOUND in system"; color="red"
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO pickups (tracking, item_name, driver_id, driver_name, time) VALUES (?,?,?,?,?)", (t, item[0], d_id, d_name, now))
            conn.execute("UPDATE stock SET status='PICKED UP' WHERE tracking=?", (t,))
            conn.commit()
            msg = f"✅ SUCCESS! Box {t} picked up by {d_name} at {now}"; color="emerald"
        conn.close()
    return f"""
    {STYLE}
    <body class="bg-slate-50 min-h-screen">
    <div class="bg-blue-700 text-white p-4 flex items-center gap-2"><a href="/" class="bg-white/20 rounded-full w-8 h-8 flex items-center justify-center">‹</a><div><h1 class="font-bold">DRIVER PICKUP</h1><p class="text-xs opacity-80">Edenvale Logistics</p></div></div>
    <div class="max-w-md mx-auto p-4">
        {"<div class='bg-"+color+"-100 border border-"+color+"-300 text-"+color+"-800 p-4 rounded-xl mb-4 font-semibold'>"+msg+"</div>" if msg else ""}
        <div class="bg-white rounded-2xl shadow-xl p-6">
            <h2 class="font-bold text-lg mb-4">Confirm Pickup</h2>
            <form method="post" class="space-y-4">
                <div><label class="text-xs font-semibold text-slate-600">BOX CODE</label><input name="tracking" placeholder="EDV-1234" required class="w-full border-2 border-slate-200 rounded-xl p-3 mt-1 uppercase font-mono font-bold"></div>
                <div><label class="text-xs font-semibold text-slate-600">DRIVER ID</label><input name="driver_id" placeholder="DRV-001" required class="w-full border-2 border-slate-200 rounded-xl p-3 mt-1"></div>
                <div><label class="text-xs font-semibold text-slate-600">DRIVER NAME</label><input name="driver_name" placeholder="John Smith" required class="w-full border-2 border-slate-200 rounded-xl p-3 mt-1"></div>
                <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg transition">✅ CONFIRM PICKUP</button>
            </form>
        </div>
        <div class="mt-4 text-center"><a href="/" class="text-sm text-slate-500">← Back to Dashboard</a></div>
    </div>
    </body>
    """

@app.route('/inbound', methods=['GET','POST'])
def inbound():
    if request.method == 'POST':
        item = request.form['item']; qty = request.form['qty']
        t = request.form.get('tracking') or f"EDV-{random.randint(1000,9999)}"
        t = t.upper()
        conn = db(); conn.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?,?)", (t, item, qty, 'IN STOCK', datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit(); conn.close()
        return f"{STYLE}<body class='bg-slate-50 min-h-screen p-6'><div class='max-w-md mx-auto bg-white rounded-2xl shadow-xl p-6 text-center'><div class='text-5xl'>✅</div><h2 class='font-bold text-xl mt-2'>Saved!</h2><p class='font-mono bg-slate-100 p-2 rounded mt-2'>{t}</p><a href='/inbound' class='mt-4 inline-block bg-blue-600 text-white px-6 py-3 rounded-xl'>Add Another</a> <a href='/' class='ml-2 text-slate-500'>Home</a></div></body>"
    return f"""
    {STYLE}
    <body class="bg-slate-50 min-h-screen">
    <div class="bg-emerald-600 text-white p-4 flex items-center gap-2"><a href="/" class="bg-white/20 rounded-full w-8 h-8 flex items-center justify-center">‹</a><h1 class="font-bold">RECEIVE STOCK</h1></div>
    <div class="max-w-md mx-auto p-4"><div class="bg-white rounded-2xl shadow-xl p-6">
    <form method="post" class="space-y-4">
        <div><label class="text-xs font-semibold">ITEM NAME</label><input name="item" placeholder="Laptops Dell XPS" required class="w-full border-2 rounded-xl p-3 mt-1"></div>
        <div><label class="text-xs font-semibold">QUANTITY</label><input name="qty" type="number" placeholder="10" required class="w-full border-2 rounded-xl p-3 mt-1"></div>
        <div><label class="text-xs font-semibold">BOX CODE (optional)</label><input name="tracking" placeholder="EDV-1234 (auto if blank)" class="w-full border-2 rounded-xl p-3 mt-1 font-mono"></div>
        <button class="w-full bg-emerald-600 text-white font-bold py-4 rounded-xl">💾 SAVE TO STOCK</button>
    </form></div></div></body>
    """

@app.route('/stock')
def stock_view():
    conn = db(); rows = conn.execute("SELECT tracking, item, qty, status, date_in FROM stock ORDER BY date_in DESC").fetchall(); conn.close()
    rows_html = "".join([f"<tr class='border-b'><td class='p-3 font-mono font-bold'>{r[0]}</td><td class='p-3'>{r[1]}</td><td class='p-3'>{r[2]}</td><td class='p-3'><span class='px-2 py-1 rounded-full text-xs {"bg-emerald-100 text-emerald-700" if r[3]=="IN STOCK" else "bg-orange-100 text-orange-700"}'>{r[3]}</span></td></tr>" for r in rows]) or "<tr><td colspan=4 class='p-6 text-center text-slate-400'>No stock yet</td></tr>"
    return f"{STYLE}<body class='bg-slate-50'><div class='bg-blue-700 text-white p-4 flex gap-2 items-center'><a href='/' class='bg-white/20 w-8 h-8 rounded-full flex items-center justify-center'>‹</a><h1 class='font-bold'>STOCK LIST</h1></div><div class='p-4 max-w-4xl mx-auto bg-white rounded-2xl shadow mt-4 overflow-auto'><table class='w-full text-sm'><thead class='bg-slate-100'><tr><th class='p-3 text-left'>CODE</th><th class='p-3 text-left'>ITEM</th><th class='p-3'>QTY</th><th class='p-3'>STATUS</th></tr></thead><tbody>{rows_html}</tbody></table></div></body>"

@app.route('/report')
def report():
    conn = db(); rows = conn.execute("SELECT tracking, item_name, driver_id, driver_name, time FROM pickups ORDER BY time DESC LIMIT 50").fetchall(); conn.close()
    rows_html = "".join([f"<tr class='border-b'><td class='p-3 font-mono'>{r[0]}</td><td class='p-3'>{r[1]}</td><td class='p-3'>{r[3]}<div class='text-xs text-slate-400'>{r[2]}</div></td><td class='p-3 text-xs'>{r[4]}</td></tr>" for r in rows]) or "<tr><td colspan=4 class='p-6 text-center text-slate-400'>No pickups yet</td></tr>"
    return f"{STYLE}<body class='bg-slate-50'><div class='bg-indigo-700 text-white p-4 flex gap-2 items-center'><a href='/' class='bg-white/20 w-8 h-8 rounded-full flex items-center justify-center'>‹</a><h1 class='font-bold'>PICKUP REPORT</h1></div><div class='p-4 max-w-4xl mx-auto bg-white rounded-2xl shadow mt-4 overflow-auto'><table class='w-full text-sm'><thead class='bg-slate-100'><tr><th class='p-3'>BOX</th><th class='p-3'>ITEM</th><th class='p-3'>DRIVER</th><th class='p-3'>TIME</th></tr></thead><tbody>{rows_html}</tbody></table></div></body>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
