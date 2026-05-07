from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)

APP_NAME = "SNR Emergency AI"

EMERGENCY_NUMBERS = {
    "ambulance": "997",
    "fire": "998",
    "police": "999",
    "general": "997"
}

# -----------------------------
# Language detection
# -----------------------------
ARABIC_CHARS = re.compile(r'[\u0600-\u06FF]')

def detect_language(text):
    return "ar" if ARABIC_CHARS.search(text) else "en"

# -----------------------------
# Emergency database (EN + AR)
# -----------------------------
EMERGENCIES = {
    "fire": {
        "keywords": ["fire", "smoke", "burning", "flames", "gas leak", "حريق", "دخان", "احتراق"],
        "advice_en": "Evacuate immediately. Stay low under smoke.",
        "advice_ar": "غادر المكان فوراً. ابقَ منخفضاً تحت الدخان.",
        "extra_en": "Do not use elevators.",
        "extra_ar": "لا تستخدم المصاعد.",
        "number": "fire"
    },

    "heart_attack": {
        "keywords": ["heart attack", "chest pain", "tight chest", "نوبة قلبية", "ألم صدر"],
        "advice_en": "Call emergency services immediately.",
        "advice_ar": "اتصل بالإسعاف فوراً.",
        "extra_en": "Keep person calm.",
        "extra_ar": "حافظ على هدوء المصاب.",
        "number": "ambulance"
    },

    "bleeding": {
        "keywords": ["bleeding", "blood", "cut", "wound", "نزيف", "جرح", "دم"],
        "advice_en": "Apply strong pressure to stop bleeding.",
        "advice_ar": "اضغط بقوة لإيقاف النزيف.",
        "extra_en": "Do not remove cloth.",
        "extra_ar": "لا تنزع القماش.",
        "number": "ambulance"
    }
}

user_location = {}

# -----------------------------
# Helpers
# -----------------------------
def normalize(text):
    return text.lower()

def detect_emergency(text):
    best = None
    best_score = 0

    for cat, data in EMERGENCIES.items():
        score = sum(1 for k in data["keywords"] if k in text.lower())
        if score > best_score:
            best = cat
            best_score = score

    return best

# -----------------------------
# Core response engine
# -----------------------------
def get_response(text):
    lang = detect_language(text)
    cat = detect_emergency(text)

    maps_link = None
    if user_location:
        lat = user_location.get("lat")
        lon = user_location.get("lon")
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"

    if cat:
        data = EMERGENCIES[cat]

        return {
            "type": "emergency",
            "category": cat,
            "advice": data["advice_ar"] if lang == "ar" else data["advice_en"],
            "extra": data["extra_ar"] if lang == "ar" else data["extra_en"],
            "number": EMERGENCY_NUMBERS[data["number"]],
            "lang": lang,
            "maps": maps_link
        }

    return {
        "type": "unknown",
        "message": "لم يتم تحديد الحالة بوضوح" if lang == "ar"
                   else "Emergency not clearly identified.",
        "number": EMERGENCY_NUMBERS["general"],
        "maps": maps_link,
        "lang": lang
    }

# -----------------------------
# UI (SNR DESIGN)
# -----------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SNR Emergency AI</title>

<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="manifest" href="/manifest.json">

<style>
body {
    margin:0;
    font-family:Arial;
    background:linear-gradient(135deg,#0b1f3a,#020b18);
    color:white;
}

.container {
    max-width:800px;
    margin:30px auto;
    background:white;
    color:#0b1f3a;
    padding:20px;
    border-radius:15px;
}

h1 {text-align:center;color:#0077b6;}

input {
    width:100%;
    padding:15px;
    border-radius:10px;
    border:1px solid #ccc;
}

.btn {
    padding:12px;
    margin-top:10px;
    border:none;
    border-radius:10px;
    cursor:pointer;
}

.blue {background:#0077b6;color:white;}
.cyan {background:#90e0ef;color:#0b1f3a;}

.call {
    display:inline-block;
    margin:5px;
    padding:10px;
    background:#00b4d8;
    color:white;
    border-radius:8px;
    text-decoration:none;
}

.card {
    margin-top:20px;
    padding:15px;
    background:#e0f7ff;
    border-radius:10px;
}
</style>
</head>

<body>

<div class="container">

<h1>🚨 SNR Emergency AI</h1>

<form method="POST">
    <input name="message" placeholder="Describe emergency..." required>

    <button type="button" class="btn cyan" onclick="startVoice()">🎤 Voice</button>
    <button type="button" class="btn cyan" onclick="getGPS()">📍 GPS</button>
    <button type="submit" class="btn blue">Analyze</button>
</form>

<div>
<a class="call" href="tel:997">Ambulance</a>
<a class="call" href="tel:998">Fire</a>
<a class="call" href="tel:999">Police</a>
</div>

{% if response %}
<div class="card">

{% if response.type == "emergency" %}
<h3>{{ response.category }}</h3>
<p><b>Advice:</b> {{ response.advice }}</p>
<p>{{ response.extra }}</p>

<a class="call" href="tel:{{ response.number }}">CALL {{ response.number }}</a>

{% else %}
<p>{{ response.message }}</p>
{% endif %}

{% if response.maps %}
<br><br>
<a class="call" href="{{ response.maps }}" target="_blank">
📍 Open Location in Maps
</a>
{% endif %}

</div>
{% endif %}

</div>

<script>
function startVoice(){
    const r = new (window.SpeechRecognition||window.webkitSpeechRecognition)();
    r.lang="en-US";
    r.start();
    r.onresult=e=>{
        document.querySelector("input").value=e.results[0][0].transcript;
    }
}

function getGPS(){
    navigator.geolocation.getCurrentPosition(pos=>{
        fetch("/location",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                lat:pos.coords.latitude,
                lon:pos.coords.longitude
            })
        });
    });
}
</script>

<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}
</script>

</body>
</html>
"""

# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET","POST"])
def home():
    res = None
    if request.method == "POST":
        msg = request.form.get("message")
        res = get_response(normalize(msg))
    return render_template_string(HTML, response=res)

@app.route("/location", methods=["POST"])
def location():
    global user_location
    user_location = request.get_json()
    return jsonify({"ok": True})

@app.route("/manifest.json")
def manifest():
    return {
        "name": "SNR Emergency AI",
        "short_name": "SNR",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#0077b6",
        "background_color": "#0b1f3a"
    }

@app.route("/sw.js")
def sw():
    return """
self.addEventListener('install', e=>{
  e.waitUntil(caches.open('v1').then(c=>c.addAll(['/'])));
});
self.addEventListener('fetch', e=>{
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
""", 200, {"Content-Type": "text/javascript"}

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)