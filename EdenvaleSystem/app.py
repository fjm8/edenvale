from flask import Flask, render_template_string, request, redirect, session, url_for
import json, os, datetime, random, string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "edenvale2026-secure")
DB = os.path.join(os.path.dirname(__file__), "db_master.json")
MASTER_PASSWORD = "edenvale123"

def load_db():
    if os.path.exists(DB):
        try:
            with open(DB, 'r') as f:
                data = json.load(f)
                # Ensure all keys exist
                if "packages" not in data: data["packages"] = []
                if "pickups" not in data: data["pickups"] = []
                if "logs" not in data: data["logs"] = []
                return data
        except:
            pass
    return {"packages": [], "pickups": [], "logs": []}

def save_db(data):
    try:
        with open(DB, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def gen_code(prefix):
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

# --- HTML TEMPLATES ---

BASE_STYLE = """
<style>
body{font-family: Arial; background:#f4f6f9; margin:0; padding:20px;}
.container{max-width:900px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1);}
h1{color:#1a3c6e;} input, select, button{padding:10px; margin:5px 0; width:100%; border-radius:6px; border:1px solid #ccc; box-sizing:border-box;}
button{background:#1a3c6e; color:white; border:none; cursor:pointer; font-weight:bold;}
button:hover{background:#274f8a;} table{width:100%; border-collapse:collapse; margin-top:15px;}
th, td{border:1px solid #ddd; padding:8px; text-align:left; font-size:14px;} th{background:#1a3c6e; color:white;}
.nav{margin-bottom:20px;} .nav a{margin-right:15px; text-decoration:none; color:#1a3c6e; font-weight:bold;}
.success{background:#d4edda; color:#155724; padding:10px; border-radius:6px; margin:10px 0;}
</style>
"""

LOGIN_PAGE = BASE_STYLE + """
<div class="container">
<h1>Edenvale System - Master Login</h1>
<form method="post">
<input type="password" name="password" placeholder="Enter Master Password" required>
<button type="submit">Login</button>
</form>
<p style="font-size:12px; color:#888;">Default: edenvale123</p>
</div>
"""

DASHBOARD_PAGE = BASE_STYLE + """
<div class="container">
<div class="nav"><a href="/">Dashboard</a><a href="/intake">New Intake</a><a href="/pickup">Pickup</a><a href="/logout">Logout</a></div>
<h1>Edenvale Logistics Dashboard</h1>
<p>Total Packages: {{count}} | Pending: {{pending}} | Collected: {{collected}}</p>
<h3>Recent Packages</h3>
<table><tr><th>Code</th><th>Recipient</th><th>Phone</th><th>Date</th><th>Status</th></tr>
{% for p in packages[-20:][::-1] %}
<tr><td>{{p.code}}</td><td>{{p.name}}</td><td>{{p.phone}}</td><td>{{p.date}}</td><td>{{p.status}}</td></tr>
{% endfor %}
</table>
</div>
"""

INTAKE_PAGE = BASE_STYLE + """
<div class="container">
<div class="nav"><a href="/">Dashboard</a><a href="/intake">New Intake</a><a href="/pickup">Pickup</a><a href="/logout">Logout</a></div>
<h1>New Package Intake</h1>
{% if code %}<div class="success">Package saved! Code: <b>{{code}}</b></div>{% endif %}
<form method="post">
<input name="name" placeholder="Recipient Full Name" required>
<input name="phone" placeholder="Phone Number" required>
<input name="unit" placeholder="Unit / Address (e.g. Unit 12)" required>
<select name="courier"><option>Aramex</option><option>DHL</option><option>FedEx</option><option>Courier Guy</option><option>PAXI</option><option>Other</option></select>
<button type="submit">Save Package</button>
</form>
</div>
"""

PICKUP_PAGE = BASE_STYLE + """
<div class="container">
<div class="nav"><a href="/">Dashboard</a><a href="/intake">New Intake</a><a href="/pickup">Pickup</a><a href="/logout">Logout</a></div>
<h1>Pickup / Collection</h1>
<form method="post">
<input name="code" placeholder="Enter Package Code (e.g. EDN-ABC123)" required>
<button type="submit">Mark as Collected</button>
</form>
{% if msg %}<div class="success">{{msg}}</div>{% endif %}
<h3>Search</h3>
<form method="get">
<input name="q" placeholder="Search by Name or Phone" value="{{q or ''}}">
<button type="submit">Search</button>
</form>
{% if results %}
<table><tr><th>Code</th><th>Name</th><th>Phone</th><th>Status</th></tr>
{% for p in results %}<tr><td>{{p.code}}</td><td>{{p.name}}</td><td>{{p.phone}}</td><td>{{p.status}}</td></tr>{% endfor %}
</table>
{% endif %}
</div>
"""

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == MASTER_PASSWORD:
            session['auth'] = True
            return redirect('/')
    return render_template_string(LOGIN_PAGE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if not session.get('auth'):
        return redirect('/login')
    db = load_db()
    packages = db['packages']
    pending = len([p for p in packages if p['status']=='Pending'])
    collected = len([p for p in packages if p['status']!='Pending'])
    return render_template_string(DASHBOARD_PAGE, packages=packages, count=len(packages), pending=pending, collected=collected)

@app.route('/intake', methods=['GET','POST'])
def intake():
    if not session.get('auth'):
        return redirect('/login')
    code = None
    if request.method == 'POST':
        db = load_db()
        code = gen_code("EDN")
        pkg = {
            "code": code,
            "name": request.form.get('name'),
            "phone": request.form.get('phone'),
            "unit": request.form.get('unit'),
            "courier": request.form.get('courier'),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "Pending"
        }
        db['packages'].append(pkg)
        db['logs'].append({"action": f"Intake {code}", "time": pkg["date"]})
        save_db(db)
    return render_template_string(INTAKE_PAGE, code=code)

@app.route('/pickup', methods=['GET','POST'])
def pickup():
    if not session.get('auth'):
        return redirect('/login')
    msg = ""
    db = load_db()
    if request.method == 'POST':
        c = request.form.get('code','').strip().upper()
        found=False
        for p in db['packages']:
            if p['code'].upper() == c:
                p['status'] = "Collected - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                found=True
                msg=f"Package {c} marked as collected!"
                db['logs'].append({"action": f"Pickup {c}", "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})
                break
        if not found:
            msg=f"Code {c} not found!"
        save_db(db)

    q = request.args.get('q','').lower()
    results=[]
    if q:
        for p in db['packages']:
            if q in p['name'].lower() or q in p['phone'].lower() or q in p['code'].lower():
                results.append(p)

    return render_template_string(PICKUP_PAGE, msg=msg, results=results, q=request.args.get('q',''))

# Public tracking for residents
@app.route('/track', methods=['GET','POST'])
def track():
    result=None
    if request.method=='POST':
        code=request.form.get('code','').strip().upper()
        db=load_db()
        for p in db['packages']:
            if p['code'].upper()==code:
                result=p
                break
    return render_template_string(BASE_STYLE + """
    <div class="container"><h1>Track Your Package - Edenvale</h1>
    <form method="post"><input name="code" placeholder="Enter EDN-XXXXXX code" required><button>Track</button></form>
    {% if result %}<div class="success"><b>{{result.code}}</b> - {{result.name}} - Status: {{result.status}}</div>
    {% elif request.method=='POST' %}<p>Not found</p>{% endif %}
    <p><a href="/">Staff Login</a></p></div>
    """, result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
