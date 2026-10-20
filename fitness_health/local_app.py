"""Local-only fitness dashboard using Python's standard-library HTTP server.

Run: python -m fitness_health.local_app
No Streamlit, remote assets, cookies or external network calls.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pandas as pd

from fitness_health.fitness_analysis import (
    load_mfp, load_withings, join_data, monthly_summary, forecast, lean_goal_table,
)
from fitness_health.quality import audit_frame

HOME = Path(__file__).resolve().parent
MAX_ROWS = 2000


def safe_number(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def series(frame, cols):
    return [
        {"date": d.strftime("%Y-%m-%d"), **{c: safe_number(row.get(c)) for c in cols}}
        for d, row in ((item.date, item._asdict()) for item in frame.itertuples(index=False))
    ]


def load_dashboard(root=HOME):
    daily, weights = load_mfp(root / "myfitnesspal" / "data")
    activity = load_withings(root / "withings" / "data")
    combined = join_data(daily, weights, activity)
    return daily, weights, activity, combined


def get_payload(root=HOME, start=None, end=None, tdee=2600, intake=1800):
    daily, weights, activity, combined = load_dashboard(root)
    if start:
        combined = combined.loc[combined.date >= pd.Timestamp(start)].copy()
    if end:
        combined = combined.loc[combined.date <= pd.Timestamp(end)].copy()
    if combined.empty:
        raise ValueError("No data for the selected date range.")
    if len(combined) > MAX_ROWS:
        raise ValueError("Too many daily observations.")
    summary = monthly_summary(combined)
    quality = audit_frame(combined)
    latest = combined.dropna(subset=["weight_kg"]).tail(1)
    latest_weight = float(latest.weight_kg.iloc[0]) if not latest.empty else 86.8
    latest_date = combined.date.max().strftime("%Y-%m-%d")
    scenarios = []
    for estimate in (tdee - 150, tdee, tdee + 150):
        path, milestones = forecast(
            start_weight=latest_weight, start_date=latest_date, tdee=estimate,
            baseline_intake=intake, days=365,
        )
        scenarios.append({
            "tdee": estimate,
            "trajectory": series(path.iloc[::7], ["weight_kg"]),
            "milestones": [
                {"goal_kg": safe_number(row.goal_kg),
                 "date": None if pd.isna(row.date) else row.date.strftime("%Y-%m-%d")}
                for row in milestones.itertuples(index=False)
            ],
        })
    return {
        "range": {"start": combined.date.min().strftime("%Y-%m-%d"), "end": latest_date},
        "summary": json.loads(summary.to_json(orient="records")),
        "quality": quality,
        "observations": series(combined, [
            "weight_kg", "weight_7d_mean", "calories", "protein_g", "carbs_g",
            "fat_g", "tdee_calories", "steps", "observed_deficit_kcal",
        ]),
        "scenarios": scenarios,
        "composition_goals": json.loads(lean_goal_table().to_json(orient="records")),
        "sources": {
            "food": "MyFitnessPal CSV (recorded, possibly partial)",
            "weight": "MyFitnessPal weight-history export (repeats may be carry-forwards)",
            "energy": "Withings totalcalories (device estimate; no active-energy double count)" if not activity.empty else "Withings unavailable",
            "forecast": "Illustrative energy-balance scenarios, not clinical predictions",
        },
    }


HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fitness &amp; Health | Local</title>
<style>
:root{color-scheme:dark;background:#101621;color:#eaf0f6;font:15px system-ui,Segoe UI,sans-serif}
*{box-sizing:border-box}body{max-width:1250px;margin:auto;padding:32px}
h1{font-size:32px;margin:0}h2{margin:0 0 14px;font-size:18px}
.subtitle,.note{color:#a5b5c9}header{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px}
.controls{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}
label{display:grid;gap:7px;font-size:13px;color:#b2c1d2}
input,button{padding:10px 12px;background:#192436;border:1px solid #40546b;color:#f2f7ff;border-radius:8px}
button{cursor:pointer;background:#2670d5;border:none;align-self:end}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:#192334;border:1px solid #2c4058;border-radius:14px;padding:20px;min-width:0}
.stat{font-size:28px;font-weight:700}section{margin:18px 0}canvas{width:100%;height:260px}
.error{color:#ffb5a7}.note{font-size:12px;line-height:1.6}
footer{margin-top:24px}table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:9px;border-bottom:1px solid #344255;text-align:left}
</style></head><body>
<header><div><h1>Fitness &amp; Health</h1><p class="subtitle">Private local analysis · Observed, estimated and scenario data kept separate</p></div><div class="note">127.0.0.1 only · No third-party assets</div></header>
<div class="controls">
<label>From<input id="start" type="date"></label><label>To<input id="end" type="date"></label>
<label>Assumed TDEE (kcal)<input id="tdee" type="number" min="1000" max="6000" value="2600"></label>
<label>Daily baseline intake (kcal)<input id="intake" type="number" min="600" max="6000" value="1800"></label>
<button id="refresh">Update dashboard</button>
</div><p id="error" class="error" role="alert"></p>
<section class="grid" id="metrics"></section>
<section class="grid">
<div class="card"><h2>Weight (kg) — recorded and 7-day mean</h2><canvas id="weight"></canvas></div>
<div class="card"><h2>Food intake (kcal) — recorded diary days</h2><canvas id="calories"></canvas></div>
<div class="card"><h2>Withings total daily expenditure (kcal)</h2><canvas id="tdeeChart"></canvas></div>
<div class="card"><h2>Weight scenario (kg) — 365 days</h2><canvas id="forecast"></canvas></div>
</section>
<section class="card"><h2>Monthly coverage &amp; summaries</h2><div style="overflow:auto"><table id="monthly"></table></div></section>
<section class="card"><h2>Methodology &amp; provenance</h2><div id="sources" class="note"></div></section>
<footer class="note">Missing diary days are unknown, not zero. A low logged calorie day may be incomplete. Consecutive equal weights may be chart carry-forwards. TDEE and forecasts are estimates, not clinical measurements.</footer>
<script>
const $=id=>document.getElementById(id), number=x=>x==null?'—':Number(x).toLocaleString(undefined,{maximumFractionDigits:1});
function chart(id,rows,lines){
 const el=$(id),dpi=devicePixelRatio||1,rect=el.getBoundingClientRect(),w=Math.max(200,rect.width),h=260;
 el.width=w*dpi;el.height=h*dpi;const ctx=el.getContext('2d');ctx.scale(dpi,dpi);
 ctx.clearRect(0,0,w,h); const pad={l:54,r:18,t:14,b:29}, plotW=w-pad.l-pad.r,plotH=h-pad.t-pad.b;
 const values=lines.flatMap(l=>rows.map(r=>r[l.key]).filter(v=>v!=null&&Number.isFinite(v)));
 if(!values.length){ctx.fillStyle='#9caec3';ctx.fillText('No data available',20,35);return}
 let lo=Math.min(...values),hi=Math.max(...values);if(hi===lo){lo-=1;hi+=1}
 const gap=(hi-lo)*.1;lo-=gap;hi+=gap;
 ctx.font='12px system-ui';ctx.strokeStyle='#34465d';ctx.fillStyle='#9eb1c9';
 for(let i=0;i<=4;i++){let y=pad.t+plotH*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();ctx.fillText(Math.round(hi-(hi-lo)*i/4).toLocaleString(),4,y+4)}
 const xx=i=>pad.l+i*plotW/Math.max(1,rows.length-1), yy=v=>pad.t+(hi-v)*plotH/(hi-lo);
 for(const line of lines){ctx.strokeStyle=line.color;ctx.lineWidth=2;ctx.beginPath();let open=false;
 rows.forEach((r,i)=>{let v=r[line.key];if(v==null){open=false;return}if(!open){ctx.moveTo(xx(i),yy(v));open=true}else ctx.lineTo(xx(i),yy(v))});ctx.stroke()}
 ctx.fillStyle='#9eb1c9';if(rows.length){ctx.fillText(rows[0].date,pad.l,h-7);ctx.textAlign='right';ctx.fillText(rows[rows.length-1].date,w-pad.r,h-7);ctx.textAlign='left'}
}
function fill(data){
 const rows=data.observations, q=data.quality, last=rows.filter(r=>r.weight_kg!=null).at(-1);
 const items=[['Latest recorded weight',last?number(last.weight_kg)+' kg':'—'],['Days with recorded food',q.logged_days+' / '+q.total_days],['Possibly partial food logs',q.possibly_partial_days],['Withings TDEE days',q.withings_tdee_days]];
 $('metrics').replaceChildren(...items.map(([title,value])=>{const c=document.createElement('div');c.className='card';const h=document.createElement('div');h.className='note';h.textContent=title;const v=document.createElement('div');v.className='stat';v.textContent=value;c.append(h,v);return c}));
 chart('weight',rows,[{key:'weight_kg',color:'#49a0ff'},{key:'weight_7d_mean',color:'#ffc06a'}]);
 chart('calories',rows,[{key:'calories',color:'#51c6a4'}]);
 chart('tdeeChart',rows,[{key:'tdee_calories',color:'#ffb56b'}]);
 const predicted=data.scenarios.map(s=>s.trajectory), dates=predicted[0].map(r=>r.date);
 chart('forecast',dates.map((date,i)=>({date,low:predicted[0][i]?.weight_kg,mid:predicted[1][i]?.weight_kg,high:predicted[2][i]?.weight_kg})),[{key:'low',color:'#628cad'},{key:'mid',color:'#54caa6'},{key:'high',color:'#ffc06a'}]);
 const cols=['month','days','days_logged','plausible_full_days','mean_logged_kcal','mean_withings_tdee','last_weight_kg'];
 const tbl=$('monthly');tbl.replaceChildren();const tr=document.createElement('tr');cols.forEach(k=>{let th=document.createElement('th');th.textContent=k.replaceAll('_',' ');tr.append(th)});tbl.append(tr);
 data.summary.forEach(r=>{let tr=document.createElement('tr');cols.forEach(k=>{let td=document.createElement('td');td.textContent=typeof r[k]==='number'?number(r[k]):r[k]??'—';tr.append(td)});tbl.append(tr)});
 const p=$('sources');p.replaceChildren(...Object.entries(data.sources).map(([k,v])=>{let line=document.createElement('p');line.textContent=k+': '+v;return line}));
}
async function refresh(){
 $('error').textContent='';try{
 const params=new URLSearchParams();['start','end','tdee','intake'].forEach(k=>{if($(k).value)params.set(k,$(k).value)});
 const res=await fetch('/api/dashboard?'+params);const data=await res.json();if(!res.ok)throw Error(data.error);fill(data)
 }catch(e){$('error').textContent=e.message}
}
$('refresh').addEventListener('click',refresh);window.addEventListener('resize',()=>{clearTimeout(window.redraw);window.redraw=setTimeout(refresh,180)});refresh();
</script></body></html>"""


def make_handler(root):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/":
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif url.path == "/api/dashboard":
                try:
                    qs = parse_qs(url.query)
                    get = lambda key, default="": qs.get(key, [default])[0]
                    tdee = int(get("tdee", "2600"))
                    intake = int(get("intake", "1800"))
                    if not (1000 <= tdee <= 6000 and 600 <= intake <= 6000):
                        raise ValueError("TDEE or intake is outside the supported range.")
                    data = get_payload(root, start=get("start"), end=get("end"), tdee=tdee, intake=intake)
                    body = json.dumps(data, allow_nan=False).encode("utf-8")
                    self.send_response(200)
                except (ValueError, FileNotFoundError, KeyError, pd.errors.ParserError) as exc:
                    body = json.dumps({"error": str(exc)}).encode("utf-8")
                    self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            else:
                self.send_error(404)
                return
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)
    return Handler


def main():
    parser = argparse.ArgumentParser(description="Launch a private local fitness dashboard")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    # Always bind loopback: never expose clinical data over LAN.
    with ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(HOME)) as server:
        print(f"Fitness & Health dashboard: http://127.0.0.1:{args.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
