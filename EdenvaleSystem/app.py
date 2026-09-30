from flask import Flask, render_template_string, request, redirect, session
import json, os, random, string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'edenvale-super-secret-2026'
DB_FILE = 'db_master.json'
STATUS_FILE = 'system_status.json'
EMPLOYEE_PASSWORD = 'edenvale123'
SUPER_PASSWORD = 'Fjmunyai@2006'

def load_db():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return []

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=2)

def load_status():
    if not os.path.exists(STATUS_FILE): return {"enabled": True}
    try:
        with open(STATUS_FILE, 'r') as f: return json.load(f)
    except: return {"enabled": True}

def save_status(status):
    with open(STATUS_FILE, 'w') as f: json.dump(status, f)

def gen_code():
    return 'EDN-' + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))

BASE = """
<a href="/">Dashboard</a> | <a href="/intake">New Intake</a> | <a href="/pickup">Pickup</a> | <a href="/track">Track</a> | <a href="/driver">Driver Collect</a> | <a href="/logout">Logout</a><hr>
"""

OFFLINE_HTML = "<h1 style='text-align:center;margin-top:100px;color:red'>🔴 SYSTEM OFFLINE<br><small>Contact Building Management</small></h1>"

@app.before_request
def check_system_status():
    if request.path.startswith('/super'):
        return None
    status = load_status()
    if not status.get("enabled", True):
        if not session.get('is_super') and request.path not in ['/login', '/super/login']:
            return render_template_string(OFFLINE_HTML), 503

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == EMPLOYEE_PASSWORD:
            session['logged'] = True
            session['is_super'] = False
            return redirect('/')
        if pwd == SUPER_PASSWORD:
            session['logged'] = True
            session['is_super'] = True
            return redirect('/super')
    return render_template_string("<h2>Staff Login</h2><form method=post><input type=password name=password placeholder='Password' style='padding:10px;width:250px'><button type=submit style='padding:10px;background:blue;color:white'>Login</button></form>")

@app.route('/super/login', methods=['GET','POST'])
def super_login():
    if request.method == 'POST':
        if request.form.get('password') == SUPER_PASSWORD:
            session['logged'] = True
            session['is_super'] = True
            return redirect('/super')
    return render_template_string("<h2 style='color:red'>SUPER MASTER - OWNER ONLY</h2><form method=post><input type=password name=password placeholder='Super Password' style='padding:10px;width:300px'><button type=submit style='padding:10px;background:red;color:white'>ENTER</button></form>")

@app.route('/super')
def super_master():
    if not session.get('is_super'): return redirect('/super/login')
    data = load_db()
    status = load_status()
    enabled = status.get("enabled", True)
    state_text = "🟢 ONLINE" if enabled else "🔴 OFFLINE"
    btn = f"<a href='/super/toggle' style='background:red;color:white;padding:20px 40px;font-size:22px;text-decoration:none;border-radius:10px;display:inline-block'>🔴 SHUT DOWN</a>" if enabled else f"<a href='/super/toggle' style='background:green;color:white;padding:20px 40px;font-size:22px;text-decoration:none;border-radius:10px;display:inline-block'>🟢 TURN ON</a>"
    return render_template_string(f"<h1>👑 SUPER MASTER</h1><h2>{state_text}</h2><p>Total: {len(data)}</p>{btn}<br><br><a href='/'>Dashboard</a>")

@app.route('/super/toggle')
def toggle():
    if not session.get('is_super'): return redirect('/super/login')
    status = load_status()
    status['enabled'] = not status.get("enabled", True)
    save_status(status)
    return redirect('/super')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def dashboard():
    if not session.get('logged'): return redirect('/login')
    data = load_db()
    total = len(data); pending = len([x for x in data if x['status']=='Pending']); collected = total-pending
    html = BASE + f"<h2>Dashboard</h2>Total: {total} | Pending: {pending} | Collected: {collected}<h3>All Packages - Now Shows Driver Name</h3><table border=1 style='width:100%;border-collapse:collapse;font-size:14px'><tr style='background:navy;color:white'><th>Code</th><th>Recipient</th><th>Status</th><th>Collected By (Driver)</th><th>Date/Time</th></tr>"
    for p in reversed(data[-50:]):
        driver_info = p.get('collected_by', '-')
        time_info = p.get('collected_at', p.get('date','-'))
        # Make driver name bold and green when collected
        if p['status'] == 'Collected':
            driver_display = f"<b style='color:green'>{driver_info}</b>"
            status_display = f"<b style='color:green'>{p['status']}</b>"
        else:
            driver_display = driver_info
            status_display = f"<span style='color:orange'>{p['status']}</span>"
        
        html += f"<tr><td><b>{p['code']}</b></td><td>{p['recipient']}</td><td>{status_display}</td><td>{driver_display}</td><td>{time_info}</td></tr>"
    html += "</table>"
    return render_template_string(html)

@app.route('/intake', methods=['GET','POST'])
def intake():
    if not session.get('logged'): return redirect('/login')
    if request.method == 'POST':
        data = load_db(); code = gen_code()
        new_pkg = {"code":code,"recipient":request.form.get('recipient'),"phone":request.form.get('phone'),"unit":request.form.get('unit'),"courier":request.form.get('courier'),"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"status":"Pending", "collected_by": "-", "collected_at": "-"}
        data.append(new_pkg); save_db(data)
        return render_template_string(BASE + f"<h2>✅ Saved! Code: {code}</h2><a href='/intake'>Add Another</a>")
    return render_template_string(BASE + """<h2>New Intake</h2><form method=post><input name=recipient placeholder="Recipient" required style="width:100%;padding:10px"><br><input name=phone placeholder="Phone" required style="width:100%;padding:10px"><br><input name=unit placeholder="Unit" required style="width:100%;padding:10px"><br><select name=courier style="width:100%;padding:10px"><option>Aramex</option><option>DHL</option><option>Courier Guy</option><option>Other</option></select><br><button type=submit style="width:100%;padding:12px;background:blue;color:white">Save</button></form>""")

@app.route('/pickup', methods=['GET','POST'])
def pickup():
    if not session.get('logged'): return redirect('/login')
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        driver_name = request.form.get('driver_name') or "Staff"
        data = load_db()
        for p in data:
            if p['code'] == code:
                p['status']='Collected'
                p['collected_by']=driver_name
                p['collected_at']=datetime.now().strftime("%Y-%m-%d %H:%M")
                save_db(data)
                return render_template_string(BASE + f"<h2>✅ {code} Collected by <b style='color:green'>{driver_name}</b><br>Time: {p['collected_at']}</h2><a href='/'>Back to Dashboard</a>")
        return render_template_string(BASE + f"<h2>❌ {code} not found</h2>")
    return render_template_string(BASE + """<h2>Pickup (Staff)</h2><form method=post><input name=code placeholder="Package Code" required style="padding:10px;width:100%"><br><br><input name=driver_name placeholder="Driver/Collector Name - e.g. John Dhl" required style="padding:10px;width:100%"><br><br><button type=submit style="padding:12px;background:green;color:white;width:100%">✅ Mark as Collected</button></form>""")

@app.route('/driver', methods=['GET','POST'])
def driver_collect():
    msg = ""
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        driver_name = request.form.get('driver_name')
        data = load_db()
        found = False
        for p in data:
            if p['code'] == code:
                p['status'] = 'Collected'
                p['collected_by'] = driver_name
                p['collected_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                found = True
                break
        if found:
            save_db(data)
            msg = f"<div style='background:#d4edda;padding:15px;border-radius:10px;border:1px solid green'><h2>✅ COLLECTED</h2><p>Code: <b>{code}</b><br>Driver: <b style='color:green;font-size:18px'>{driver_name}</b><br>Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p><p>Recorded in Master Dashboard!</p></div>"
        else:
            msg = f"<div style='background:#ffcccc;padding:15px;border-radius:10px'><h2>❌ NOT FOUND - {code}</h2></div>"
    
    return render_template_string(f"""
    <div style="max-width:500px;margin:20px auto;font-family:sans-serif">
    <h1 style="text-align:center">🚚 DRIVER COLLECTION</h1>
    {msg}
    <form method=post style="border:1px solid #ccc;padding:20px;border-radius:10px;background:#f9f9f9">
        <label>Package Code *</label><br>
        <input name=code placeholder="EDN-A1B2C3" required style="width:100%;padding:15px;font-size:18px;margin:10px 0"><br>
        <label>Your Name (Driver) *</label><br>
        <input name=driver_name placeholder="Full Name" required style="width:100%;padding:15px;font-size:18px;margin:10px 0"><br>
        <button type=submit style="width:100%;padding:15px;background:green;color:white;font-size:20px;border:none;border-radius:10px">✅ CONFIRM & SHOW MY NAME</button>
    </form>
    </div>
    """)

@app.route('/track', methods=['GET','POST'])
def track():
    result=""
    if request.method == 'POST':
        code=request.form.get('code').strip().upper(); data=load_db(); found=[x for x in data if x['code']==code or code in x['phone']]
        if found:
            for p in found:
                driver = p.get('collected_by','-')
                when = p.get('collected_at', p.get('date'))
                if p['status'] == 'Collected':
                    result+=f"<div style='border:2px solid green;padding:10px;margin:5px;background:#eaffea'><b>{p['code']}</b> - {p['recipient']}<br>Status: <b style='color:green'>COLLECTED</b><br>Collected By: <b>{driver}</b><br>When: {when}</div>"
                else:
                    result+=f"<div style='border:1px solid orange;padding:10px;margin:5px'><b>{p['code']}</b> - {p['recipient']} - <b style='color:orange'>{p['status']}</b><br>Date: {p['date']}</div>"
        else: result="<p>❌ Not found</p>"
    return render_template_string(f"<h2>Track</h2><form method=post><input name=code placeholder='Code or Phone' style='padding:10px;width:300px' required><button type=submit>Track</button></form><hr>{result}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
