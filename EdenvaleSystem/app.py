@app.route('/')
def home():
    conn=sqlite3.connect(DB)
    total=conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    today=conn.execute("SELECT COUNT(*) FROM stock WHERE date_in LIKE?", (f"%{datetime.datetime.now().strftime('%Y-%m-%d')}%",)).fetchone()[0]
    in_stock=conn.execute("SELECT COUNT(*) FROM stock WHERE status='IN STOCK'").fetchone()[0]
    conn.close()
    return render_template_string(BASE + """
<div style="background:linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color:white; padding:28px 20px 90px; border-radius:0 0 32px 32px">
  <div style="max-width:600px; margin:0 auto">
    <div style="display:flex; justify-content:space-between; align-items:center">
      <div style="font-weight:800; font-size:20px; letter-spacing:-0.5px">📦 EDENVALE</div>
      <div style="background:rgba(255,255,255,0.15); padding:6px 12px; border-radius:999px; font-size:12px">WMS v2.0 LIVE</div>
    </div>
    <h1 style="font-size:32px; line-height:1.1; margin:24px 0 8px; letter-spacing:-1px">Warehouse<br>under control.</h1>
    <p style="opacity:0.7; font-size:14px; margin:0">Track what came in • Label • Find in seconds</p>
  </div>
</div>

<div class="container" style="margin-top:-60px">
  <!-- STATS -->
  <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px">
    <div class="card" style="text-align:center; padding:16px 10px; margin:0"><b style="font-size:22px; display:block">{{total}}</b><span style="color:#64748b; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px">Total Items</span></div>
    <div class="card" style="text-align:center; padding:16px 10px; margin:0"><b style="font-size:22px; display:block">{{today}}</b><span style="color:#64748b; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px">Today In</span></div>
    <div class="card" style="text-align:center; padding:16px 10px; margin:0; background:#0f172a; color:white; border-color:#0f172a"><b style="font-size:22px; display:block">{{in_stock}}</b><span style="opacity:0.6; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px">In Stock</span></div>
  </div>

  <!-- MAIN ACTIONS -->
  <div style="margin-top:20px">
    <p style="font-size:12px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin:0 0 10px 4px">Quick Actions</p>

    <a class="btn" href="/inbound" style="background:linear-gradient(135deg, #2563eb, #1d4ed8); color:white; border:none; padding:20px">
      <div><div style="font-size:16px; font-weight:700">📥 Receive Stock</div><div style="opacity:0.8; font-size:12px; font-weight:400; margin-top:2px">What came in today?</div></div>
      <div style="background:rgba(255,255,255,0.2); width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center">+</div>
    </a>

    <a class="btn" href="/locate"><span>🗺️ Find Item Location</span><span style="color:#64748b">→</span></a>
    <a class="btn" href="/label"><span>🏷️ Print Label / Barcode</span><span style="color:#64748b">→</span></a>
  </div>

  <!-- SECONDARY -->
  <div style="margin-top:20px">
    <p style="font-size:12px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin:0 0 10px 4px">Warehouse</p>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px">
      <a class="card" href="/map" style="text-decoration:none; color:#0f172a; margin:0; text-align:center"><div style="font-size:24px">🏭</div><b style="font-size:13px">Map View</b><div style="font-size:11px; color:#64748b">Aisles & Bays</div></a>
      <a class="card" href="/all" style="text-decoration:none; color:#0f172a; margin:0; text-align:center"><div style="font-size:24px">📋</div><b style="font-size:13px">All Stock</b><div style="font-size:11px; color:#64748b">{{total}} items</div></a>
    </div>
  </div>

  <p style="text-align:center; color:#94a3b8; font-size:11px; margin-top:28px">Edenvale Logistics • Designed for speed</p>
</div>
    """, total=total, today=today, in_stock=in_stock)
