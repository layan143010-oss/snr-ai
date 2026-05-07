from flask import Flask, request, jsonify
import re, datetime, uuid
from difflib import SequenceMatcher, get_close_matches

app = Flask(__name__)

# =========================
# EMERGENCY CORE DATA
# =========================

NUMBERS = {
    "ambulance": "997",
    "fire": "998",
    "police": "999"
}

INCIDENT_LOGS = []

EMERGENCIES = {
    "fire": {
        "keywords": ["fire", "smoke", "burning", "explosion", "gas leak"],
        "level": 5,
        "actions": "Evacuate immediately. Do not inhale smoke. Call fire department."
    },
    "medical": {
        "keywords": ["heart", "chest pain", "unconscious", "bleeding", "not breathing", "injury"],
        "level": 5,
        "actions": "Call ambulance immediately. Keep patient stable and still."
    },
    "accident": {
        "keywords": ["car crash", "accident", "collision", "hit", "bike crash"],
        "level": 4,
        "actions": "Check injuries. Move to safe area if possible."
    },
    "danger": {
        "keywords": ["attack", "robbery", "danger", "threat", "weapon"],
        "level": 5,
        "actions": "Call police immediately. Move to safe location."
    }
}

# =========================
# AI ENGINE
# =========================

def normalize(t):
    t = t.lower()
    return re.sub(r"[^\w\s']", " ", t)

def score(text, keywords):
    s = 0
    for k in keywords:
        if k in text:
            s += 4
        if SequenceMatcher(None, text, k).ratio() > 0.75:
            s += 2
    return s

def detect(text):
    results = []
    for name, data in EMERGENCIES.items():
        sc = score(text, data["keywords"])
        if sc >= 3:
            results.append((name, sc, data))
    return sorted(results, key=lambda x: x[1], reverse=True)

def risk(text):
    high = ["dying", "not breathing", "unconscious", "fire", "blood"]
    return "HIGH" if any(w in text for w in high) else "MEDIUM"

def engine(msg, lat=None, lon=None):

    text = normalize(msg)
    matches = detect(text)
    r = risk(text)

    if matches:
        name, sc, data = matches[0]

        level = data["level"]
        action = data["actions"]

        if r == "HIGH" or level == 5:
            action = "🚨 CRITICAL: " + action

        incident = {
            "id": str(uuid.uuid4())[:8],
            "type": name,
            "risk": r,
            "score": sc,
            "time": str(datetime.datetime.utcnow()),
            "lat": lat,
            "lon": lon
        }

        INCIDENT_LOGS.append(incident)

        return {
            "status": "emergency",
            "type": name,
            "risk": r,
            "actions": action,
            "incident": incident
        }

    return {
        "status": "unknown",
        "risk": r,
        "actions": "Stay calm. If danger exists, call emergency services."
    }

# =========================
# SCI-FI UI
# =========================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>SNR Emergency Command Center</title>

<style>

body{
margin:0;
font-family:Arial;
background:#000;
color:#fff;
}

.header{
padding:20px;
text-align:center;
background:linear-gradient(90deg,#120000,#000,#001);
border-bottom:2px solid red;
box-shadow:0 0 30px red;
}

.header h1{
margin:0;
font-size:28px;
letter-spacing:2px;
}

.container{
display:grid;
grid-template-columns:2fr 1fr;
gap:15px;
padding:20px;
}

.panel{
background:#0a0a0a;
border:1px solid #222;
border-radius:12px;
padding:15px;
box-shadow:0 0 20px rgba(255,0,0,0.2);
}

input{
width:100%;
padding:12px;
background:#000;
border:1px solid #333;
color:#fff;
border-radius:8px;
margin-bottom:10px;
}

button{
width:100%;
padding:12px;
margin:5px 0;
border:none;
border-radius:8px;
cursor:pointer;
font-weight:bold;
}

.ai{background:red;color:white;}
.gps{background:#222;color:white;}
.call{background:#330000;color:white;}
.report{background:#111;color:white;}

.box{
margin-top:10px;
padding:10px;
background:#000;
border:1px solid #222;
min-height:120px;
white-space:pre-wrap;
}

.emergency{
color:red;
font-weight:bold;
}

.small{
font-size:12px;
opacity:0.6;
}

</style>

</head>

<body>

<div class="header">
<h1>🚨 SNR EMERGENCY COMMAND CENTER</h1>
<div class="small">AI DISPATCH SYSTEM • LIVE MONITORING</div>
</div>

<div class="container">

<!-- MAIN -->
<div class="panel">

<h3>⚡ AI Emergency Input</h3>

<input id="msg" placeholder="Describe emergency...">

<button class="ai" onclick="ask()">ANALYZE EMERGENCY</button>
<button class="gps" onclick="gps()">AUTO GPS LOCK</button>
<button class="call" onclick="sos()">SEND SOS REPORT</button>

<div class="box" id="out">System ready...</div>

</div>

<!-- SIDE -->
<div class="panel">

<h3>📞 Emergency Calls</h3>

<button class="call" onclick="window.location.href='tel:997'">Ambulance 997</button>
<button class="call" onclick="window.location.href='tel:998'">Fire 998</button>
<button class="call" onclick="window.location.href='tel:999'">Police 999</button>

<h3 style="margin-top:15px;">📊 Reports</h3>

<div class="box" id="reports">No incidents yet</div>

</div>

</div>

<script>

let lat=null, lon=null;

function ask(){

let msg=document.getElementById("msg").value;

fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,lat,lon})
})
.then(r=>r.json())
.then(d=>{

if(d.status==="emergency"){
document.getElementById("out").innerText =
"TYPE: "+d.type+"\nRISK: "+d.risk+"\n\n"+d.actions;
}else{
document.getElementById("out").innerText=d.actions;
}

loadReports();

});

}

function gps(){
navigator.geolocation.getCurrentPosition(p=>{
lat=p.coords.latitude;
lon=p.coords.longitude;
alert("GPS LOCKED: "+lat+", "+lon);
});
}

function sos(){
fetch("/sos",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({lat,lon})
});
alert("SOS SENT");
}

function loadReports(){
fetch("/reports")
.then(r=>r.json())
.then(d=>{
document.getElementById("reports").innerText =
JSON.stringify(d,null,2);
});
}

setInterval(loadReports,3000);

</script>

</body>
</html>
"""

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return HTML

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("message","")
    lat = data.get("lat")
    lon = data.get("lon")

    return jsonify(engine(msg,lat,lon))

@app.route("/sos", methods=["POST"])
def sos():
    data = request.json
    INCIDENT_LOGS.append({
        "type":"SOS",
        "time":str(datetime.datetime.utcnow()),
        "lat":data.get("lat"),
        "lon":data.get("lon")
    })
    return jsonify({"status":"logged"})

@app.route("/reports")
def reports():
    return jsonify(INCIDENT_LOGS[-10:])

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)