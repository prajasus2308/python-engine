import os
import requests
import json
from flask import Flask, request, render_template_string, session

# 1. VERCEL ENTRY POINT
app = Flask(__name__)
app.secret_key = "vercel_ai_dashboard_key_2026"

# ===================== API LOGIC =====================
def fetch_serp(query, mode):
    params = {"engine": "google", "q": query, "api_key": "61170663fb882a93bda339ca9343f31638c5318f07077c14f2dfd426613107b4"}
    tbm_map = {"images": "isch", "news": "nws", "shopping": "shop"}
    if mode in tbm_map: params["tbm"] = tbm_map[mode]
    try:
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        return r.json()
    except: return {}

def fetch_ai(query, context):
    headers = {"Authorization": "Bearer 50812343-8406-4a84-be51-af87e847f58a", "Content-Type": "application/json"}
    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "Professional assistant summary."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]
    }
    try:
        r = requests.post("https://api.sambanova.ai/v1/chat/completions", json=payload, headers=headers)
        return r.json()['choices'][0]['message']['content']
    except: return "AI synthesis currently unavailable."

# ===================== PREMIUM UI =====================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>SearchQ AI | Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --primary: #2563eb; --bg: #f8fafc; --sidebar: #ffffff; }
        * { box-sizing: border-box; }
        body, html { margin: 0; height: 100%; width: 100%; font-family: 'Inter', sans-serif; background: var(--bg); overflow: hidden; }
        header { height: 70px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; padding: 0 25px; z-index: 100; }
        .logo { font-weight: 900; color: var(--primary); text-decoration: none; font-size: 1.6rem; }
        .search-area { flex: 1; display: flex; background: #f1f5f9; border-radius: 12px; padding: 8px 15px; margin-left: 30px; align-items: center; }
        .search-area input { background: transparent; border: none; flex: 1; outline: none; font-size: 1rem; color: #1e293b; }
        .dashboard { display: grid; grid-template-columns: 280px 1fr; height: calc(100vh - 70px); }
        .sidebar { background: var(--sidebar); border-right: 1px solid #e2e8f0; padding: 25px; overflow-y: auto; }
        .hist-item { display: block; padding: 12px; color: #475569; text-decoration: none; font-size: 0.95rem; border-radius: 10px; margin-bottom: 6px; }
        main { overflow-y: auto; padding: 40px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .tabs { display: flex; gap: 10px; margin-bottom: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; overflow-x: auto; }
        .tab { padding: 10px 22px; border-radius: 8px; text-decoration: none; color: #64748b; font-weight: 600; font-size: 0.9rem; }
        .tab.active { background: var(--primary); color: white; }
        .ai-panel { background: #0f172a; color: white; padding: 30px; border-radius: 20px; margin-bottom: 35px; border-left: 6px solid var(--primary); }
        .result-card { background: white; padding: 25px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        .img-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
        .img-card img { width: 100%; height: 200px; object-fit: cover; border-radius: 15px; }
        @media (max-width: 768px) { .dashboard { grid-template-columns: 1fr; } .sidebar { display: none; } }
    </style>
</head>
<body>
    <header>
        <a href="/" class="logo">SearchQ</a>
        <form class="search-area" action="/">
            <input name="q" placeholder="What would you like to know?" value="{{q}}" autocomplete="off">
            <input type="hidden" name="mode" value="{{mode}}">
        </form>
    </header>
    <div class="dashboard">
        <aside class="sidebar">
            <h5 style="color:#94a3b8; text-transform:uppercase; font-size:0.75rem; margin-bottom:20px;">History</h5>
            {% for item in history %}
            <a href="/?q={{item}}&mode={{mode}}" class="hist-item"><i class="far fa-clock"></i> {{item}}</a>
            {% endfor %}
            <div style="margin-top: auto;">
                <a href="/clear" style="color:#ef4444; text-decoration:none; font-size:0.85rem;">Reset Session</a>
                <div style="margin-top: 15px; font-size: 0.75rem; color: #94a3b8; font-weight: 500;">
                    {{ created_by }}
                </div>
            </div>
        </aside>
        <main>
            <div class="container">
                <div class="tabs">
                    {% for m in ['search', 'ai', 'images', 'news', 'shopping'] %}
                    <a href="/?q={{q}}&mode={{m}}" class="tab {{'active' if mode==m else ''}}">{{m.capitalize()}}</a>
                    {% endfor %}
                </div>
                {% if ai_answer %}
                <div class="ai-panel">
                    <h3>AI Synthesis</h3>
                    <div style="line-height:1.8;">{{ai_answer}}</div>
                </div>
                {% endif %}
                {% if mode == 'images' %}
                <div class="img-grid">
                    {% for img in images %}<div class="img-card"><img src="{{img}}"></div>{% endfor %}
                </div>
                {% else %}
                    {% for r in results %}
                    <div class="result-card">
                        <a href="{{r.link}}" target="_blank" style="color:var(--primary); font-weight:700; text-decoration:none;">{{r.title}}</a>
                        <p style="color:#475569; margin-top:12px;">{{r.snippet}}</p>
                    </div>
                    {% endfor %}
                {% endif %}
            </div>
        </main>
    </div>
</body>
</html>
"""

# ===================== ROUTES =====================
@app.route("/")
def home():
    q = request.args.get("q", "")
    mode = request.args.get("mode", "search")
    if 'history_json' not in session: session['history_json'] = json.dumps([])
    
    results, images, ai_answer = [], [], None
    history_list = json.loads(session['history_json'])
    
    if q:
        if q not in history_list:
            history_list.append(q)
            session['history_json'] = json.dumps(history_list[-15:])
        
        data = fetch_serp(q, mode)
        if mode == "ai":
            snippets = [f"{r.get('title')}: {r.get('snippet')}" for r in data.get("organic_results", [])[:5]]
            ai_answer = fetch_ai(q, " | ".join(snippets))
        elif mode == "images":
            images = [i.get("thumbnail") for i in data.get("images_results", [])[:20]]
        else:
            results = data.get("organic_results", [])[:10]

    created_by = "Created by Pratyush Raj"
    return render_template_string(HTML, q=q, mode=mode, results=results, images=images, ai_answer=ai_answer, history=reversed(history_list), created_by=created_by)

@app.route("/clear")
def clear():
    session['history_json'] = json.dumps([])
    return """<script>window.location.href="/";</script>"""

# 2. VERCEL PRODUCTION ENTRY POINT
# This ensures Vercel's WSGI server finds the 'app' object
app = app

if __name__ == "__main__":
    app.run(debug=True)
    print("Pratyush Raj")
