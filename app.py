from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "stock_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

stocks = load_data()
next_id = max([s.get('id',0) for s in stocks], default=0) + 1

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* {font-family: 'Inter', sans-serif; box-sizing: border-box; margin:0; padding:0}
body {background:#f5f7fb; color:#1e293b}
.header {background: linear-gradient(135deg,#2563eb 0%,#1e40af 100%); color:white; padding:22px 24px; display:flex; justify-content:space-between; align-items:center}
.header h1 {font-size:22px; font-weight:700}
.header span {background:rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:12px}
.container {max-width:1100px; margin:0 auto; padding:20px}
.cards {display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:24px}
.card {background:white; border-radius:16px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.05); border-left:5px solid}
.card.blue {border-color:#2563eb} .card.green {border-color:#10b981} .card.orange {border-color:#f59e0b}
.card h3 {font-size:12px; color:#64748b; letter-spacing:1px; margin-bottom:8px}
.card .val {font-size:32px; font-weight:700; color:#0f172a}
.buttons {display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:24px}
.btn {display:flex; align-items:center; justify-content:center; gap:8px; padding:16px; border-radius:12px; text-decoration:none; font-weight:600; color:white; transition:0.2s}
.btn:hover {transform:translateY(-2px); box-shadow:0 8px 20px rgba(0,0,0,0.15)}
.btn-receive {background:#2563eb} .btn-pickup {background:#f59e0b} .btn-stock {background:#10b981} .btn-reports {background:#8b5cf6}
.table-wrap {background:white; border-radius:16px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.05)}
table {width:100%; border-collapse:collapse}
th {background:#f8fafc; text-align:left; padding:14px 16px; font-size:12px; color:#64748b}
td {padding:14px 16px; border-top:1px solid #f1f5f9; font-size:14px}
.badge {padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700}
.badge.in {background:#dcfce7; color:#166534} .badge.out {background:#fef3c7; color:#92400e}
.form-wrap {background:white; border-radius:16px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,0.05); max-width:600px}
label {display:block; font-size:13px; font-weight:600; margin:16px 0 6px; color:#334155}
input, select {width:100%; padding:12px 14px; border:1px solid #e2e8f0; border-radius:10px; font-size:14px}
input:focus {outline:none; border-color:#2563eb}
.submit {margin-top:20px; width:100%; padding:14px; background:#2563eb; color:white; border:none; border-radius:10px; font-weight:700; font-size:15px; cursor:pointer}
.destination-highlight {background:#eff6ff; border:1px dashed #3b82f6; padding:10px 14px; border-radius:8px; font-weight:600; color:#1e40af}
</style>
"""

def layout(content, title="Edenvale System"):
    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title}</title>{BASE_CSS}</head><body>
    <div class="header"><h1>🏭 Edenvale Returnables</h1><span>LIVE • {datetime.now().strftime('%d %b %H:%M')}</span></div>
    <div class="container">{content}</div></body></html>
    """

@app.route('/')
def dashboard():
    total = len(stocks)
    in_stock = len([s for s in stocks if s['status']=='IN STOCK'])
    picked = len([s for s in stocks if s['status']=='PICKED UP'])
    content = f"""
    <div class="cards">
        <div class="card blue"><h3>TOTAL RECEIVED</h3><div class="val">{total}</div></div>
        <div class="card green"><h3>IN STOCK</h3><div class="val">{in_stock}</div></div>
        <div class="card orange"><h3>PICKED UP</h3><div class="val">{picked}</div></div>
    </div>
    <div class="buttons">
        <a href="/receive" class="btn btn-receive">📦 Receive Stock</a>
        <a href="/driver" class="btn btn-pickup">🚚 Driver Pickup</a>
        <a href="/stock" class="btn btn-stock">📊 View Stock</a>
        <a href="/reports" class="btn btn-reports">📈 Reports</a>
    </div>
    <div class="table-wrap">
    <table><tr><th>ID</th><th>Product</th><th>Qty</th><th>Supplier</th><th>Destination / Going To</th><th>Status</th><th>Date</th></tr>
    """
    for s in reversed(stocks[-10:]):
        badge = 'in' if s['status']=='IN STOCK' else 'out'
        content += f"<tr><td>#{s['id']}</td><td><b>{s['product']}</b></td><td>{s['qty']}</td><td>{s['supplier']}</td><td><span class='destination-highlight'>📍 {s.get('destination','-')}</span></td><td><span class='badge {badge}'>{s['status']}</span></td><td>{s['date'][:16]}</td></tr>"
    content += "</table></div><p style='margin-top:12px;color:#64748b;font-size:13px'>Showing last 10 - <a href='/stock'>View All</a></p>"
    return render_template_string(layout(content))

@app.route('/receive', methods=['GET','POST'])
def receive():
    global next_id
    if request.method=='POST':
        product = request.form.get('product','').strip()
        qty = request.form.get('qty','').strip()
        supplier = request.form.get('supplier','').strip()
        destination = request.form.get('destination','').strip()
        if product and qty:
            new_entry = {
                'id': next_id,
                'product': product,
                'qty': qty,
                'supplier': supplier or 'Unknown',
                'destination': destination or 'Not Specified',
                'status': 'IN STOCK',
                'driver': '',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            stocks.append(new_entry)
            save_data(stocks)
            next_id+=1
            return redirect('/')
    form = """
    <div class="form-wrap"><h2 style="margin-bottom:8px">📦 Receive New Stock</h2>
    <p style="color:#64748b;font-size:13px;margin-bottom:12px">Counter staff - enter where this stock is going</p>
    <form method="POST">
        <label>Product / Item Name *</label><input name="product" placeholder="e.g. 20L Bottle, Pallet, Gas Bottle" required>
        <label>Quantity *</label><input name="qty" type="number" placeholder="e.g. 10" required>
        <label>Supplier / From Who</label><input name="supplier" placeholder="e.g. Customer Name / Supplier">
        <label style="color:#2563eb">📍 Destination / Where is it going? *</label>
        <input name="destination" placeholder="e.g. Yard A, Customer - Spar Edenvale, Truck 2, Warehouse 3" required style="border-color:#3b82f6; background:#eff6ff">
        <button class="submit">✅ Save & Add to Stock</button>
    </form><br><a href="/" style="color:#64748b;text-decoration:none">← Back to Dashboard</a></div>
    """
    return render_template_string(layout(form, "Receive Stock"))

@app.route('/driver', methods=['GET','POST'])
def driver():
    if request.method=='POST':
        sid = int(request.form.get('stock_id','0'))
        driver_name = request.form.get('driver_name','').strip()
        for s in stocks:
            if s['id']==sid and s['status']=='IN STOCK':
                s['status']='PICKED UP'
                s['driver']=driver_name
                s['pickup_date']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_data(stocks)
                break
        return redirect('/driver')
    in_stock_items = [s for s in stocks if s['status']=='IN STOCK']
    content = """
    <div class="form-wrap" style="max-width:800px"><h2>🚚 Driver Pickup</h2>
    <p style="color:#64748b;font-size:13px;margin:8px 0 16px">Driver sees DESTINATION so no confusion where to take it</p>
    """
    if not in_stock_items:
        content += "<p style='padding:20px;background:#fef3c7;border-radius:10px'>No stock in yard. Receive stock first.</p>"
    else:
        for s in in_stock_items:
            content += f"""
            <div style="border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div><b>#{s['id']} {s['product']} x{s['qty']}</b><br>
                <span style="font-size:12px;color:#64748b">From: {s['supplier']} • {s['date'][:16]}</span><br>
                <span class="destination-highlight">📍 GOING TO: {s.get('destination','-')}</span>
                </div>
                <form method="POST" style="display:flex;gap:8px"><input type="hidden" name="stock_id" value="{s['id']}">
                <input name="driver_name" placeholder="Driver Name / PIN" required style="width:150px">
                <button style="background:#f59e0b;color:white;border:none;padding:10px 16px;border-radius:8px;font-weight:700;cursor:pointer">Pickup</button>
                </form>
            </div>
            """
    content += "<br><a href='/' style='color:#64748b;text-decoration:none'>← Back</a></div>"
    return render_template_string(layout(content, "Driver Pickup"))

@app.route('/stock')
def view_stock():
    content = """<div class="table-wrap"><div style="padding:16px 20px;display:flex;justify-content:space-between;align-items:center"><h2>📊 All Stock</h2><a href="/" style="text-decoration:none;color:#2563eb;font-weight:600">← Dashboard</a></div>
    <table><tr><th>ID</th><th>Product</th><th>Qty</th><th>From</th><th>📍 Destination</th><th>Status</th><th>Driver</th><th>Date</th></tr>"""
    for s in reversed(stocks):
        badge = 'in' if s['status']=='IN STOCK' else 'out'
        content += f"<tr><td>#{s['id']}</td><td><b>{s['product']}</b></td><td>{s['qty']}</td><td>{s['supplier']}</td><td><span class='destination-highlight'>{s.get('destination','-')}</span></td><td><span class='badge {badge}'>{s['status']}</span></td><td>{s.get('driver','-')}</td><td>{s['date'][:16]}</td></tr>"
    content += "</table></div>"
    return render_template_string(layout(content, "View Stock"))

@app.route('/reports')
def reports():
    total = len(stocks)
    in_stock = len([s for s in stocks if s['status']=='IN STOCK'])
    picked = len([s for s in stocks if s['status']=='PICKED UP'])
    dest_count = {}
    for s in stocks:
        if s['status']=='IN STOCK':
            dest_count[s.get('destination','Unknown')] = dest_count.get(s.get('destination','Unknown'),0)+1
    dest_html = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in dest_count.items()]) or "<tr><td colspan=2>No data</td></tr>"
    content = f"""
    <div class="cards">
        <div class="card blue"><h3>TOTAL</h3><div class="val">{total}</div></div>
        <div class="card green"><h3>IN STOCK</h3><div class="val">{in_stock}</div></div>
        <div class="card orange"><h3>PICKED UP</h3><div class="val">{picked}</div></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div class="table-wrap" style="padding:16px"><h3>📍 Stock by Destination</h3><table style="margin-top:12px"><tr><th>Destination</th><th>Count</th></tr>{dest_html}</table></div>
        <div class="table-wrap" style="padding:16px"><h3>🚚 Recent Pickups</h3><table style="margin-top:12px"><tr><th>Item</th><th>Driver</th><th>To</th></tr>
        {"".join([f"<tr><td>{s['product']}</td><td>{s.get('driver','-')}</td><td>{s.get('destination','-')}</td></tr>" for s in reversed([x for x in stocks if x['status']=='PICKED UP'][-5:])]) or "<tr><td colspan=3>No pickups yet</td></tr>"}
        </table></div>
    </div><br><a href="/" style="color:#64748b;text-decoration:none">← Back</a>
    """
    return render_template_string(layout(content, "Reports"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
