from flask import Flask, render_template_string, request, redirect, session
import json, os, datetime, random, string

app = Flask(__name__)
app.secret_key = "edenvale2026"
DB = "db_master.json"
MASTER_PASSWORD = "edenvale123"

def load_db():
    if os.path.exists(DB):
        with open(DB) as f:
            return json.load(f)
    return {"packages": [], "pickups": [], "logs": []}

def save_db(data):
    with open(DB, 'w') as f:
        json.dump(data, f, indent=2)

def gen_code(prefix):
    return f"{prefix}-{''.join(random.choices(string.digits, k=4))}"

HTML = """<!DOCTYPE html><html><head><meta name=viewport content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;padding:12px;max-width:650px;margin:auto} .card{border:1px solid #ddd;padding:12px;border-radius:10px;margin:8px 0} .btn{background:#111;color:white;padding:14px;border-radius:8px;width:100%;border:0;font-size:16px} input,select{width:100%;padding:14px;margin:6px 0;border-radius:8px;border:1px solid #ccc} .nav{background:#111;color:white;padding:10px;border-radius:8px;text-align:center} .nav a{color:white;margin:0 6px;text-decoration:none;font-weight:bold;font-size:13px} .green{background:#e8f5e9} .blue{background:#e3f2fd}</style></head><body><div class=nav><a href="/intake">INTAKE</a> | <a href="/master">MASTER</a> | <a href="/driver">DRIVER</a> | <a href="/track">TRACK</a></div><br>{{content}}</body></html>"""

@app.route("/")
def home():
    return redirect("/intake")

@app.route("/intake", methods=["GET","POST"])
def intake():
    db = load_db()
    if request.method=="POST":
        pkg = {"pkg_id": gen_code("PKG"), "qty": request.form["qty"], "item": request.form["item"], "origin": request.form["origin"], "dest": request.form["dest"], "client": request.form.get("client",""), "status": "IN_EDENVALE - Ready for Driver", "entered_by": request.form["employee"], "time": str(datetime.datetime.now())[:16]}
        db["packages"].append(pkg)
        save_db(db)
        return render_template_string(HTML, content=f"<div class='card green'><h2>Saved!</h2><h1>{pkg['pkg_id']}</h1><p>{pkg['qty']}x {pkg['item']}<br>{pkg['origin']} -> {pkg['dest']}</p><a href=/intake>Next Package</a></div>")
    return render_template_string(HTML, content="""<h2>INTAKE - Reception</h2><p>What came in, where it's going, what it is</p><form method=post><input name=employee placeholder="Your Name (receptionist)" required><input name=qty type=number placeholder="HOW MANY? e.g. 10" required><input name=item placeholder="WHAT IS IT? e.g. 20ft Container" required><input name=origin placeholder="FROM where? e.g. Durban" required><input name=dest placeholder="WHERE going to? e.g. JHB Client - MUST FILL" required><input name=client placeholder="Client Name (optional)"><button class=btn>SAVE PACKAGE</button></form>""")

@app.route("/master", methods=["GET","POST"])
def master():
    db = load_db()
    if request.args.get("logout"):
        session.clear()
        return redirect("/master")
    if "master" not in session:
        if request.method=="POST" and request.form.get("pwd")==MASTER_PASSWORD:
            session["master"]=True
        else:
            return render_template_string(HTML, content="<h2>MASTER - You Only</h2><form method=post><input type=password name=pwd placeholder='Password edenvale123'><button class=btn>Login</button></form>")
    html = f"<h2>MASTER Overview - You oversee all</h2><p>Total packages: {len(db['packages'])}</p>"
    for p in db["packages"][::-1]:
        pu = next((x for x in db["pickups"] if x["pkg_id"]==p["pkg_id"]), None)
        driver = f"DRV {pu['pickup_code']} - {pu['plate']}" if pu else "No driver yet"
        html+=f"<div class='card blue'><b>{p['pkg_id']}</b> | {p['qty']}x {p['item']}<br>From {p['origin']} To {p['dest']}<br>Status: {p['status']}<br><small>By {p['entered_by']} | {driver}</small></div>"
    return render_template_string(HTML, content=html+"<br><br><a href='/master?logout=1'>Logout</a>")

@app.route("/driver", methods=["GET","POST"])
def driver():
    db = load_db()
    if request.method=="POST":
        pkg_id = request.form["pkg_id"]
        pkg = next((x for x in db["packages"] if x["pkg_id"]==pkg_id), None)
        code = gen_code("DRV")
        pickup = {"pickup_code":code,"pkg_id":pkg_id,"driver_name":request.form["driver_name"],"driver_id":request.form["driver_id"],"plate":request.form["plate"],"time":str(datetime.datetime.now())[:16]}
        pkg["status"]=f"PICKED_UP {code}"
        db["pickups"].append(pickup)
        save_db(db)
        return render_template_string(HTML, content=f"<div class='card green'><h2>DRIVER CODE</h2><h1>{code}</h1><p>Package {pkg_id}<br>To {pkg['dest']}<br>Plate {pickup['plate']}</p><p>Give this DRV code to client for tracking</p><a href=/driver>Done</a></div>")
    avail = [p for p in db["packages"] if "Ready" in p["status"] or "IN_EDENVALE" in p["status"]]
    if not avail:
        return render_template_string(HTML, content="<h3>No packages ready. Intake first.</h3>")
    opts = "".join([f"<option value={p['pkg_id']}>{p['pkg_id']} - {p['origin']} -> {p['dest']}</option>" for p in avail])
    return render_template_string(HTML, content=f"<h3>DRIVER PICKUP</h3><form method=post><label>Select Package</label><select name=pkg_id>{opts}</select><input name=driver_name placeholder='Driver Full Name' required><input name=driver_id placeholder='Driver ID Number' required><input name=plate placeholder='Truck Plate e.g. CA 123' required><button class=btn>Generate DRV Code</button></form>")

@app.route("/track", methods=["GET","POST"])
def track():
    db = load_db()
    q = (request.args.get("q") or request.form.get("q") or "").upper().strip()
    res=""
    if q:
        for p in db["packages"]:
            if q in p["pkg_id"] or q in p["dest"].upper() or q in "".join([x["pickup_code"] for x in db["pickups"] if x["pkg_id"]==p["pkg_id"]]):
                pu = next((x for x in db["pickups"] if x["pkg_id"]==p["pkg_id"]), None)
                driver = f"On Road - Plate {pu['plate']} DRV {pu['pickup_code']}" if pu else "In Edenvale Warehouse - Ready"
                res+=f"<div class='card green'><b>{p['pkg_id']}</b><br>{p['qty']}x {p['item']}<br>{p['origin']} -> {p['dest']}<br><b>{p['status']}</b><br><br>{driver}</div>"
        if not res:
            res="<p>Not found</p>"
    return render_template_string(HTML, content=f"<h3>TRACK</h3><form method=post><input name=q value='{q}' placeholder='Enter PKG-xxxx or DRV-xxxx'><button class=btn>Track</button></form>{res}")

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)