from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import random, math, os
from datetime import datetime, timedelta

app = FastAPI(title="AgriMind AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve static frontend ──────────────────────────────────────────
BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(BASE, "public")

if os.path.exists(PUBLIC):
    app.mount("/static", StaticFiles(directory=PUBLIC), name="static")

@app.get("/", include_in_schema=False)
def root():
    p = os.path.join(PUBLIC, "index.html")
    return FileResponse(p) if os.path.exists(p) else {"message": "AgriMind AI v2"}

@app.get("/{page}.html", include_in_schema=False)
def serve_page(page: str):
    p = os.path.join(PUBLIC, f"{page}.html")
    if os.path.exists(p):
        return FileResponse(p)
    raise HTTPException(404)

@app.get("/style.css", include_in_schema=False)
def serve_css():
    p = os.path.join(PUBLIC, "style.css")
    return FileResponse(p, media_type="text/css") if os.path.exists(p) else HTTPException(404)

# ── Schemas ────────────────────────────────────────────────────────
class CropInput(BaseModel):
    location:    str
    season:      str
    soil_ph:     float
    nitrogen:    float
    phosphorus:  float
    potassium:   float
    temperature: float
    humidity:    float
    soil_type:   Optional[str] = "Black Cotton"
    field_size:  Optional[float] = 5.0

class IrrigationInput(BaseModel):
    crop:          str
    growth_stage:  str
    field_size:    float
    soil_moisture: float
    temperature:   float
    humidity:      float
    rainfall:      float
    method:        Optional[str] = "Drip"

class RiskInput(BaseModel):
    crop:          str
    season:        str
    growth_stage:  str
    temperature:   float
    humidity:      float
    soil_moisture: float
    uv_index:      float
    wind_speed:    float

# ── Crop Database ──────────────────────────────────────────────────
CROP_DB = {
    "Kharif": [
        {"crop":"Soybean",   "icon":"🫘","ph_range":[6.0,7.5],"temp_range":[20,35],"hum_range":[55,90],"n_min":30,"growth_days":100,"water_need":"Medium","market_price":"₹3,800/quintal","profit_potential":"High",     "risk_level":"Low",   "base_score":88,"soil_fit":{"Black Cotton":6,"Alluvial":5,"Red Laterite":3,"Sandy Loam":4,"Clay":4}},
        {"crop":"Cotton",    "icon":"🌿","ph_range":[5.8,8.0],"temp_range":[25,40],"hum_range":[50,80],"n_min":25,"growth_days":165,"water_need":"Medium","market_price":"₹6,500/quintal","profit_potential":"Very High","risk_level":"Medium","base_score":84,"soil_fit":{"Black Cotton":7,"Alluvial":4,"Red Laterite":3,"Sandy Loam":3,"Clay":5}},
        {"crop":"Maize",     "icon":"🌽","ph_range":[5.8,7.0],"temp_range":[18,32],"hum_range":[50,80],"n_min":20,"growth_days":90, "water_need":"Medium","market_price":"₹1,900/quintal","profit_potential":"Medium",   "risk_level":"Low",   "base_score":78,"soil_fit":{"Black Cotton":4,"Alluvial":7,"Red Laterite":5,"Sandy Loam":6,"Clay":3}},
        {"crop":"Turmeric",  "icon":"🟡","ph_range":[5.5,7.0],"temp_range":[20,35],"hum_range":[65,90],"n_min":15,"growth_days":270,"water_need":"High",  "market_price":"₹12,000/quintal","profit_potential":"Very High","risk_level":"Medium","base_score":72,"soil_fit":{"Black Cotton":3,"Alluvial":5,"Red Laterite":6,"Sandy Loam":7,"Clay":3}},
        {"crop":"Groundnut", "icon":"🥜","ph_range":[6.0,7.0],"temp_range":[22,35],"hum_range":[45,75],"n_min":15,"growth_days":120,"water_need":"Low",   "market_price":"₹5,200/quintal","profit_potential":"High",     "risk_level":"Low",   "base_score":75,"soil_fit":{"Black Cotton":3,"Alluvial":6,"Red Laterite":7,"Sandy Loam":8,"Clay":2}},
    ],
    "Rabi": [
        {"crop":"Wheat",     "icon":"🌾","ph_range":[6.0,7.5],"temp_range":[10,25],"hum_range":[40,70],"n_min":30,"growth_days":120,"water_need":"Medium","market_price":"₹2,150/quintal","profit_potential":"High",     "risk_level":"Low",   "base_score":90,"soil_fit":{"Black Cotton":5,"Alluvial":8,"Red Laterite":3,"Sandy Loam":6,"Clay":5}},
        {"crop":"Chickpea",  "icon":"🟤","ph_range":[5.5,7.0],"temp_range":[15,30],"hum_range":[30,60],"n_min":10,"growth_days":100,"water_need":"Low",   "market_price":"₹5,440/quintal","profit_potential":"High",     "risk_level":"Low",   "base_score":82,"soil_fit":{"Black Cotton":7,"Alluvial":5,"Red Laterite":4,"Sandy Loam":6,"Clay":4}},
        {"crop":"Mustard",   "icon":"🌻","ph_range":[5.8,7.5],"temp_range":[10,28],"hum_range":[35,65],"n_min":20,"growth_days":110,"water_need":"Low",   "market_price":"₹5,650/quintal","profit_potential":"High",     "risk_level":"Low",   "base_score":80,"soil_fit":{"Black Cotton":4,"Alluvial":7,"Red Laterite":5,"Sandy Loam":7,"Clay":3}},
        {"crop":"Potato",    "icon":"🥔","ph_range":[5.0,6.5],"temp_range":[10,25],"hum_range":[50,80],"n_min":25,"growth_days":90, "water_need":"High",  "market_price":"₹1,500/quintal","profit_potential":"Medium",   "risk_level":"High",  "base_score":76,"soil_fit":{"Black Cotton":3,"Alluvial":7,"Red Laterite":5,"Sandy Loam":8,"Clay":2}},
    ],
    "Zaid": [
        {"crop":"Watermelon","icon":"🍉","ph_range":[6.0,7.0],"temp_range":[25,40],"hum_range":[40,70],"n_min":15,"growth_days":75, "water_need":"Medium","market_price":"₹1,200/quintal","profit_potential":"High",     "risk_level":"Medium","base_score":86,"soil_fit":{"Black Cotton":3,"Alluvial":7,"Red Laterite":5,"Sandy Loam":8,"Clay":2}},
        {"crop":"Moong",     "icon":"🟢","ph_range":[6.0,7.5],"temp_range":[25,40],"hum_range":[40,75],"n_min":10,"growth_days":65, "water_need":"Low",   "market_price":"₹7,755/quintal","profit_potential":"Very High","risk_level":"Low",   "base_score":78,"soil_fit":{"Black Cotton":5,"Alluvial":7,"Red Laterite":6,"Sandy Loam":7,"Clay":4}},
        {"crop":"Sunflower", "icon":"🌸","ph_range":[6.0,7.5],"temp_range":[20,35],"hum_range":[40,70],"n_min":20,"growth_days":90, "water_need":"Medium","market_price":"₹6,400/quintal","profit_potential":"High",     "risk_level":"Medium","base_score":74,"soil_fit":{"Black Cotton":5,"Alluvial":7,"Red Laterite":5,"Sandy Loam":6,"Clay":4}},
    ],
}

# ── Scoring ────────────────────────────────────────────────────────
def score_crop(crop, params):
    score = crop["base_score"]
    ph_mid = (crop["ph_range"][0]+crop["ph_range"][1])/2
    score += 5 if crop["ph_range"][0]<=params.soil_ph<=crop["ph_range"][1] else -abs(params.soil_ph-ph_mid)*2.5
    score += 4 if crop["temp_range"][0]<=params.temperature<=crop["temp_range"][1] else -4
    score += 3 if crop["hum_range"][0]<=params.humidity<=crop["hum_range"][1] else -2
    score += 3 if params.nitrogen>=crop["n_min"] else -(crop["n_min"]-params.nitrogen)*0.15
    score += crop["soil_fit"].get(params.soil_type, 3)
    return int(min(99, max(40, round(score))))

# ── Irrigation ─────────────────────────────────────────────────────
CROP_KC = {
    "Soybean":[0.40,0.80,1.15,0.50],"Cotton":[0.35,0.75,1.20,0.60],"Maize":[0.30,0.70,1.20,0.60],
    "Wheat":[0.40,0.70,1.10,0.40],"Turmeric":[0.50,0.90,1.10,0.70],"Groundnut":[0.40,0.70,1.05,0.60],
    "Watermelon":[0.40,0.75,1.00,0.75],"Chickpea":[0.40,0.70,1.05,0.30],"Sunflower":[0.35,0.75,1.15,0.55],
    "Moong":[0.40,0.70,1.00,0.45],"Potato":[0.50,0.75,1.15,0.75],"Mustard":[0.35,0.65,1.05,0.40],
}
STAGE_IDX  = {"Germination":0,"Vegetative":1,"Flowering":2,"Pod/Fruit Fill":2,"Maturity":3}
METHOD_EFF = {"Drip":0.90,"Sprinkler":0.78,"Flood":0.55,"Furrow":0.62}

def compute_eto(temp, hum):
    return round(0.0023*(temp+17.8)*math.sqrt(max(temp-10,1))*(1-hum/200), 2)

def compute_irrigation(params, offset):
    DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    dt         = datetime.now()+timedelta(days=offset)
    depletion  = 1.8+(params.temperature-25)*0.1
    rain_today = params.rainfall if offset==2 else (params.rainfall*0.4 if offset==6 else 0)
    soil_now   = params.soil_moisture-(offset*depletion)+(rain_today*0.35)
    needs      = soil_now<45 and rain_today<10
    kc_vals    = CROP_KC.get(params.crop,[0.5,0.8,1.1,0.55])
    kc         = kc_vals[min(STAGE_IDX.get(params.growth_stage,1), len(kc_vals)-1)]
    eto        = compute_eto(params.temperature, params.humidity)
    etc        = round(eto*kc, 2)
    eff        = METHOD_EFF.get(params.method, 0.75)
    gross      = round(max(0,round((50-soil_now)*0.9+etc*2))/eff) if needs else 0
    if   not needs and rain_today>=10: reason = f"Rain {round(rain_today)}mm forecast — skip"
    elif not needs and soil_now>=50:   reason = "Moisture adequate — skip"
    elif not needs:                    reason = "Rest day"
    elif offset==1:                    reason = "Below 45% threshold"
    elif offset==3:                    reason = f"ETc {etc}mm/day demand"
    elif offset==5:                    reason = "Heat stress prevention"
    else:                              reason = f"Deficit irrigation (Kc={kc})"
    return {"day":DAYS[dt.weekday()],"date":dt.strftime("%b %d"),"irrigate":needs,"amount_mm":gross,
            "method":params.method if needs else "—",
            "best_time":"6:00 AM" if params.temperature>32 else "6:30 AM",
            "eto":eto,"etc":etc,"kc":kc,"rain_mm":round(rain_today,1),"reason":reason}

# ── Risk Engine ────────────────────────────────────────────────────
def evaluate_risks(p):
    A = []
    def add(t,s,i,ti,d,im,ac,u): A.append({"type":t,"severity":s,"icon":i,"title":ti,"detail":d,"impact":im,"action":ac,"urgency":u})
    if p.humidity>60 and p.temperature>25:
        add("Pest","High","🦟","Whitefly Infestation Risk",f"Humidity {p.humidity}% and {p.temperature}°C ideal for breeding.","Yield loss up to 40%.","Apply neem oil (5ml/L) on leaf undersides. Yellow sticky traps.","Within 48 hours")
    if p.temperature>28 and p.humidity>55 and p.growth_stage in ["Flowering","Pod/Fruit Fill"]:
        add("Pest","High","🐛","Pod/Stem Borer Outbreak Risk",f"{p.temperature}°C during {p.growth_stage} increases borer activity.","30–50% yield loss.","Pheromone traps (5/acre). Chlorantraniliprole 0.4ml/L evening.","Within 24 hours")
    if 20<p.temperature<35 and p.humidity>50:
        add("Pest","Medium","🪲","Aphid Colony Risk",f"{p.temperature}°C and {p.humidity}% optimal for aphids.","15–25% yield loss.","Dimethoate 2ml/L or Chrysoperla carnea biocontrol.","Within 72 hours")
    if p.humidity>68 and p.temperature>22:
        add("Disease","High","🍄","Fungal Blight Early Warning",f"Humidity {p.humidity}% above 68% triggers spore germination.","Leaf defoliation, aflatoxin risk.","Mancozeb 75% WP 2g/L every 10 days.","Within 48 hours")
    if p.humidity>70 and 18<=p.temperature<=28:
        add("Disease","Medium","🌿","Downy Mildew Susceptibility",f"Cool {p.temperature}°C and {p.humidity}% favour mildew.","Up to 30% yield loss.","Metalaxyl + Mancozeb 2.5g/L. Remove infected debris.","Within 72 hours")
    if p.temperature>33 or p.uv_index>8:
        add("Weather","Medium","☀️","Heat & UV Stress Alert",f"Temp {p.temperature}°C UV {p.uv_index} exceed safe thresholds.","Pollen sterility, 10–25% yield loss.","Irrigate 6–8 AM. Kaolin clay spray 3%.","Today")
    if p.soil_moisture<30:
        add("Weather","High","🌵","Drought Stress — CRITICAL",f"Soil moisture {p.soil_moisture}% critically low.","40–70% yield loss if prolonged.","EMERGENCY IRRIGATION — Apply 30–40mm immediately.","IMMEDIATE")
    if p.temperature<8:
        add("Weather","High","❄️","Frost Risk Alert",f"Temp {p.temperature}°C frost risk tonight.","Possible total crop loss.","Overhead irrigation + agro-net cover.","IMMEDIATE — Tonight")
    if p.wind_speed>50:
        add("Weather","Medium","🌪️","High Wind Damage Risk",f"Wind {p.wind_speed}km/h causes lodging.","15–30% yield loss.","Windbreaks, stake crops, avoid spraying.","Before evening")
    if p.soil_moisture>80:
        add("Soil","Medium","🌊","Waterlogging Risk",f"Moisture {p.soil_moisture}% near saturation.","Root rot, 25–50% loss.","Open drainage. Trichoderma viride.","Within 24 hours")
    if p.temperature<15:
        add("Soil","Low","⚗️","Phosphorus Uptake Impaired",f"{p.temperature}°C reduces P solubility.","10–15% yield loss.","Foliar KH₂PO₄ 0.5%. PSB biofertilizer.","Within 1 week")
    if p.soil_moisture>70:
        add("Soil","Low","🌱","Nitrogen Leaching Risk",f"Moisture {p.soil_moisture}% causes N leaching.","15–20% lower yield.","Split urea 25kg/acre. Slow-release fertilizer.","Within 1 week")
    A.sort(key=lambda a: {"High":0,"Medium":1,"Low":2}.get(a["severity"],3))
    return A

# ── API Routes ─────────────────────────────────────────────────────
@app.get("/api/sensor-data")
def get_sensor_data():
    return {
        "temperature":   round(28+random.uniform(-2,3),1),
        "humidity":      round(65+random.uniform(-5,8),1),
        "soil_moisture": round(42+random.uniform(-4,5),1),
        "soil_ph":       round(6.4+random.uniform(-0.2,0.2),2),
        "nitrogen":      round(38+random.uniform(-3,4),1),
        "phosphorus":    round(22+random.uniform(-2,3),1),
        "potassium":     round(45+random.uniform(-3,5),1),
        "rainfall":      round(12+random.uniform(-2,3),1),
        "wind_speed":    round(14+random.uniform(-3,4),1),
        "uv_index":      7, "location":"Pune, Maharashtra", "season":"Kharif",
        "timestamp":     datetime.now().isoformat(),
    }

@app.post("/api/crop-recommendation")
def crop_recommendation(params: CropInput):
    crops = CROP_DB.get(params.season, CROP_DB["Kharif"])
    scored = []
    for c in crops:
        s = score_crop(c, params)
        reasons = []
        if c["ph_range"][0]<=params.soil_ph<=c["ph_range"][1]: reasons.append(f"pH {params.soil_ph} ideal")
        if c["temp_range"][0]<=params.temperature<=c["temp_range"][1]: reasons.append(f"{params.temperature}°C suits growth")
        if params.nitrogen>=c["n_min"]: reasons.append("nitrogen adequate")
        if c["soil_fit"].get(params.soil_type,3)>=6: reasons.append(f"{params.soil_type} soil excellent")
        if not reasons: reasons.append("manageable with good practices")
        scored.append({"crop":c["crop"],"icon":c["icon"],"suitability":s,
                        "reason":("; ".join(reasons[:2]).capitalize()+"."),
                        "growth_days":c["growth_days"],"water_need":c["water_need"],
                        "market_price":c["market_price"],"profit_potential":c["profit_potential"],"risk_level":c["risk_level"]})
    scored.sort(key=lambda x: x["suitability"], reverse=True)
    return {"status":"success","location":params.location,"season":params.season,
            "recommendations":scored[:4],"analyzed_at":datetime.now().isoformat()}

@app.post("/api/irrigation-plan")
def irrigation_plan(params: IrrigationInput):
    if params.field_size<=0: raise HTTPException(400,"Field size must be > 0")
    schedule  = [compute_irrigation(params,i) for i in range(7)]
    total_mm  = sum(d["amount_mm"] for d in schedule)
    flood_eq  = round(total_mm*1.45)
    savings   = round((1-total_mm/max(flood_eq,1))*100)
    total_L   = round(total_mm*params.field_size*404.7/10)
    irr_days  = sum(1 for d in schedule if d["irrigate"])
    return {"status":"success","crop":params.crop,"schedule":schedule,
            "summary":{"total_irrigation_days":irr_days,"total_water_mm":total_mm,"total_liters":total_L,
                       "flood_equivalent_mm":flood_eq,"water_savings_percent":savings,
                       "avg_eto_mm_day":round(sum(d["eto"] for d in schedule)/7,2)},
            "generated_at":datetime.now().isoformat()}

@app.post("/api/risk-alerts")
def risk_alerts(params: RiskInput):
    alerts = evaluate_risks(params)
    high,medium,low = [sum(1 for a in alerts if a["severity"]==s) for s in ["High","Medium","Low"]]
    score = min(99,high*28+medium*14+low*5)
    return {"status":"success","alerts":alerts,
            "risk_summary":{"total":len(alerts),"high":high,"medium":medium,"low":low,"risk_score":score,
                            "risk_level":"High" if score>60 else "Medium" if score>35 else "Low"},
            "scanned_at":datetime.now().isoformat()}

@app.get("/api/farm-summary")
def farm_summary():
    s = get_sensor_data()
    health = int(0.25*min(s["soil_moisture"]/50,1)*100+0.25*min(s["nitrogen"]/50,1)*100+
                 0.25*(1-abs(s["soil_ph"]-6.5)/3)*100+0.25*min(s["humidity"]/70,1)*100)
    return {"status":"success","top_crop":"Soybean","top_crop_score":88,"next_irrigation":"Tuesday",
            "active_alerts":4,"field_health_score":f"{health}/100","best_market_price":"₹3,800/quintal",
            "season":"Kharif 2025","location":"Pune, Maharashtra","last_updated":datetime.now().isoformat()}

@app.get("/api/health")
def health_check():
    return {"status":"healthy","version":"2.0.0","timestamp":datetime.now().isoformat()}

# ── Run locally ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
