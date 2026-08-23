# Изтеглете файла от линка по-горе или копирайте целия код отдолу:
import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important;
        z-index: -1;
        pointer-events: none;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #252932, #16191f) !important; 
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; 
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        transition: all 0.25s ease !important; 
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        transform: translateY(-1px) !important; 
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
    }
    small { color: #7e8494 !important; }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"

# Настройки само за имената на бутоните. Каноничните категории в данните НЕ се променят.
DEFAULT_UI_LABELS = {
    "pet": "Куче",
    "hotel": "Нощувки/Хотел",
    "deposit": "Депозит/Резервация"
}

def get_ui_labels():
    labels = DEFAULT_UI_LABELS.copy()
    try:
        if os.path.exists(LABELS_FILE):
            df = pd.read_csv(LABELS_FILE, encoding="utf-8")
            if not df.empty:
                row = df.iloc[0]
                for key in labels:
                    value = str(row.get(key, labels[key]))
                    if value and value != "nan":
                        labels[key] = value
    except:
        pass
    return labels

def save_ui_labels(pet_label, hotel_label, deposit_label):
    try:
        pd.DataFrame([{
            "pet": pet_label,
            "hotel": hotel_label,
            "deposit": deposit_label
        }]).to_csv(LABELS_FILE, index=False, encoding="utf-8")
        return True
    except:
        return False

UI_LABELS = get_ui_labels()

# Визуалното име на категорията следва името на съответния бутон.
# Каноничните имена в DATA_FILE остават непроменени, за да не се чупят
# натрупаните данни и изчисленията. Ако канонично име участва в по-дълго
# име на категория, замяната се прави автоматично и за тази част.
def get_display_category(category):
    category_text = str(category)
    replacements = {
        "Куче": UI_LABELS.get("pet", "Куче"),
        "Нощувки/Хотел": UI_LABELS.get("hotel", "Нощувки/Хотел"),
        "Депозит/Резервация": UI_LABELS.get("deposit", "Депозит/Резервация")
    }
    for canonical, label in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        category_text = category_text.replace(canonical, label)
    return category_text

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        if "current_km" not in r.columns: r["current_km"] = 0.0
        return r
    except: 
        return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {
                "trip_id": t_id, 
                "car_trip": str(res.get("car_trip", "Не")), 
                "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), 
                "start_km": float(res.get("start_km", 0.0)), 
                "end_km": float(res.get("end_km", 0.0)), 
                "manual_fuel": float(res.get("manual_fuel", 0.0)), 
                "start_date": str(res.get("start_date", "")), 
                "end_date": str(res.get("end_date", ""))
            }
    except: 
        pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: 
        pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False

def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: 
        return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MAP_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

if st.session_state["current_trip"] is None:
    # ================================================================
    # PIXELAPP REDESIGN — REAL DATA DASHBOARD
    # Това НЕ е демо база. Всички пътувания и разходи се четат от
    # съществуващите budget_data_2026.csv / trip_settings_2026.csv.
    # ================================================================
    import math
    import plotly.express as px

    BUDGET_FILE = "trip_budgets_2026.csv"

    def _all_trip_ids():
        ids = []
        for fn in (DATA_FILE, SETTINGS_FILE):
            try:
                d = pd.read_csv(fn, encoding="utf-8")
                if "trip_id" in d.columns:
                    ids += [str(x) for x in d["trip_id"].dropna().tolist() if str(x).strip()]
            except Exception:
                pass
        return list(dict.fromkeys(ids))

    def _budget_df():
        cols = ["trip_id", "category", "planned"]
        try:
            d = pd.read_csv(BUDGET_FILE, encoding="utf-8")
            for c in cols:
                if c not in d.columns: d[c] = 0.0 if c == "planned" else ""
            return d[cols]
        except Exception:
            return pd.DataFrame(columns=cols)

    def _save_budget(trip_id, values):
        try:
            d = _budget_df()
            d = d[d["trip_id"].astype(str) != str(trip_id)]
            rows = [{"trip_id": trip_id, "category": k, "planned": float(v)} for k,v in values.items()]
            d = pd.concat([d, pd.DataFrame(rows)], ignore_index=True)
            d.to_csv(BUDGET_FILE, index=False, encoding="utf-8")
            return True
        except Exception:
            return False

    def _trip_metrics(tid):
        d = get_trip_data(tid)
        exp = d[d["type"] == "expense"].copy()
        dep = d[d["type"] == "deposit"].copy()
        actual = float(exp["amount"].sum())
        deposit = float(dep["amount"].sum())
        total = actual + deposit
        cats = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
        if not exp.empty:
            for _, r in exp.iterrows():
                if r["category"] in cats: cats[r["category"]] += float(r["amount"])
        settings = get_trip_settings(tid)
        sk = float(settings.get("start_km",0) or 0)
        ek = float(settings.get("end_km",0) or 0)
        maxkm = float(exp["current_km"].max()) if not exp.empty and "current_km" in exp.columns else 0
        endkm = ek if ek > 0 else maxkm
        dist = max(0.0, endkm-sk)
        liters = float(exp["liters"].sum()) + float(settings.get("manual_fuel",0) or 0)
        days = 1
        sd, ed = str(settings.get("start_date", "")), str(settings.get("end_date", ""))
        try:
            a=datetime.datetime.strptime(sd,"%d.%m.%Y"); b=datetime.datetime.strptime(ed,"%d.%m.%Y")
            days=max(1,(b-a).days+1)
        except: pass
        return {"data":d,"exp":exp,"deposit":deposit,"actual":actual,"total":total,"cats":cats,
                "settings":settings,"start":sd,"end":ed,"days":days,"dist":dist,"liters":liters,
                "per_day":total/days if days else total,"per_km":total/dist if dist else 0}

    def _trip_rows_for_history():
        rows=[]
        for tid in _all_trip_ids():
            m=_trip_metrics(tid)
            rows.append({"trip_id":tid,"name":tid.replace("_"," "),"total":m["total"],"per_day":m["per_day"],"dist":m["dist"],"per_km":m["per_km"],"hotel":m["cats"].get("Нощувки/Хотел",0),"start":m["start"],"end":m["end"]})
        return rows

    def _ensure_budget_for_trip(tid):
        d=_budget_df(); r=d[d["trip_id"].astype(str)==str(tid)]
        if not r.empty: return {str(x["category"]):float(x["planned"]) for _,x in r.iterrows()}
        # Без измислена стойност: ако бюджет още не е зададен, показваме 0 и потребителят го задава.
        return {k:0.0 for k in KATEGORII if k != "Депозит/Резервация"}

    trips=_trip_rows_for_history()
    if not trips:
        st.markdown("""
        <div class='px-empty'><div class='px-logo'>🐾</div><h1>PixelApp</h1>
        <p>Все още няма записани пътувания в budget_data_2026.csv / trip_settings_2026.csv.</p></div>
        """, unsafe_allow_html=True)
        if st.button("➕ Ново пътуване", use_container_width=True, type="primary"):
            st.session_state["open_create_trip"] = True
        if st.session_state.get("open_create_trip"):
            st.info("Използвай оригиналния екран за създаване на първото пътуване.")
        st.stop()

    # Последното пътуване по крайна дата; ако няма дата — първото налично.
    def _sort_key(r):
        try: return datetime.datetime.strptime(r["end"],"%d.%m.%Y")
        except: return datetime.datetime.min
    trips=sorted(trips,key=_sort_key,reverse=True)
    if "dashboard_trip" not in st.session_state or st.session_state["dashboard_trip"] not in [r["trip_id"] for r in trips]:
        st.session_state["dashboard_trip"]=trips[0]["trip_id"]
    selected_trip=st.session_state["dashboard_trip"]
    metric=_trip_metrics(selected_trip)
    planned=_ensure_budget_for_trip(selected_trip)
    planned_total=sum(planned.values())
    actual_total=metric["actual"]
    budget_pct=(actual_total/planned_total*100) if planned_total>0 else 0
    remaining=max(0,planned_total-actual_total) if planned_total>0 else 0

    # --- CSS: следва директно визуалната посока от предоставения desktop/mobile mockup ---
    st.markdown("""
    <style>
    .stApp{background:#020b14!important}.block-container{max-width:1540px!important;padding:18px 22px 50px!important}
    section[data-testid="stSidebar"]{background:#03111d!important;border-right:1px solid #123652}
    section[data-testid="stSidebar"] *{color:#dceeff!important}
    .px-title{display:flex;align-items:center;gap:16px;margin-bottom:12px}.px-step{width:54px;height:54px;border:3px solid #28a9ff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800;background:#09243b}.px-title h1{font-size:30px;margin:0;color:#f5fbff}.px-title p{margin:2px 0;color:#8ccfff}
    .px-panel{background:linear-gradient(145deg,#061522,#04101b);border:1px solid #123e61;border-radius:15px;padding:15px;box-shadow:0 10px 28px #0008;margin-bottom:12px}.px-panel h3{margin:0 0 10px;color:#f4f8ff;font-size:16px}.px-trip{display:flex;align-items:center;gap:10px;color:#fff;font-size:18px;font-weight:700}.px-trip small{display:block;color:#8eacc2;font-weight:400;font-size:12px}.px-kpi{background:#061827;border:1px solid #123b5a;border-radius:11px;padding:13px}.px-kpi .lbl{font-size:11px;color:#9bb7cd}.px-kpi .val{font-size:22px;font-weight:800;color:#fff;margin-top:3px}.px-kpi .delta{font-size:10px;color:#24d69a}.px-warning{background:#2a1d09;border:1px solid #5b3d12;border-radius:10px;padding:10px;color:#ffc34d}.px-cat{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0e273b;color:#d8e9f6;font-size:12px}.px-cat b{color:#fff}.px-table{width:100%;border-collapse:collapse}.px-table th,.px-table td{padding:8px;border-bottom:1px solid #113149;font-size:11px;text-align:left}.px-table th{color:#83b8dc}.px-table td{color:#dceeff}.px-rank{background:linear-gradient(145deg,#071b2a,#06131f);border:1px solid #123b59;border-radius:11px;padding:12px;height:100%}.px-rank .icon{font-size:27px}.px-rank .rtitle{font-size:11px;color:#1fe2a0;font-weight:700}.px-rank .rname{font-size:11px;color:#9ebbd0}.px-rank .rval{font-size:16px;color:#fff;font-weight:800}.px-navtitle{font-weight:800;color:#7fc8ff!important;font-size:17px;margin:8px 0 18px}.px-footer{text-align:center;color:#6186a1;font-size:11px;margin-top:15px}
    @media(max-width:800px){.block-container{padding:10px 10px 80px!important}.px-title h1{font-size:22px}.px-step{width:44px;height:44px;font-size:20px}.px-panel{padding:12px}.px-trip{font-size:15px}.px-rank{min-height:92px}.px-kpi .val{font-size:19px}section[data-testid="stSidebar"]{display:none}.px-mobile-nav{position:fixed;left:8px;right:8px;bottom:8px;z-index:999;background:#061421ee;border:1px solid #184766;border-radius:16px;padding:8px;backdrop-filter:blur(12px)}}
    </style>
    """, unsafe_allow_html=True)

    # Sidebar — функционална навигация
    st.sidebar.markdown("<div class='px-navtitle'>🐾 PixelApp</div>",unsafe_allow_html=True)
    nav=st.sidebar.radio("",["Начало","Пътувания","Разходи","Карта","Автомобил","Сравнение","Бюджет","Отчети","Настройки"],key="px_nav")
    if st.sidebar.button("➕ Ново пътуване",use_container_width=True):
        st.session_state["new_trip_from_dashboard"]=True
    if st.sidebar.button("↻ Презареди данните",use_container_width=True): st.rerun()

    @st.dialog("➕ Ново пътуване")
    def dashboard_create_trip():
        name=st.text_input("Дестинация")
        dr=st.date_input("Период",value=[datetime.date.today(),datetime.date.today()])
        car=st.radio("Автомобил",["Не","Да"])
        sk=st.number_input("Начални километри",min_value=0.0,step=1.0) if car=="Да" else 0.0
        if st.button("Създай и отвори",type="primary",use_container_width=True) and name.strip():
            target=name.strip().replace(" ","_")
            if isinstance(dr,(list,tuple)):
                sd=dr[0].strftime("%d.%m.%Y"); ed=(dr[-1] if len(dr)>1 else dr[0]).strftime("%d.%m.%Y")
            else: sd=ed=dr.strftime("%d.%m.%Y")
            save_trip_settings(target,car,"Да" if car=="Да" else "Добави впоследствие",sk,0,0,sd,ed)
            st.session_state["current_trip"]=target; st.rerun()
    if st.session_state.pop("new_trip_from_dashboard",False): dashboard_create_trip()

    @st.dialog("➕ Добави разход")
    def dashboard_add_expense():
        amount=st.number_input("Сума (€)",min_value=0.0,step=1.0)
        desc=st.text_input("Описание")
        cat=st.selectbox("Категория",[k for k in KATEGORII if k!="Депозит/Резервация"],format_func=get_display_category)
        if st.button("Запиши разхода",type="primary",use_container_width=True) and amount>0:
            add_expense(selected_trip,amount,cat,desc,False); st.rerun()

    @st.dialog("⛽ Добави зареждане")
    def dashboard_add_fuel():
        amount=st.number_input("Платена сума (€)",min_value=0.0,step=1.0)
        liters=st.number_input("Литри",min_value=0.0,step=0.1)
        km=st.number_input("Километри на таблото",min_value=0.0,step=1.0)
        full=st.checkbox("Пълен резервоар",value=True)
        if st.button("Запиши зареждането",type="primary",use_container_width=True) and amount>0 and liters>0:
            desc="[ПЪЛНО ЗАРЕЖДАНЕ] Зареждане" if full else "[ЧАСТИЧНО ЗАРЕЖДАНЕ] Зареждане"
            add_expense(selected_trip,amount,"Транспорт",desc,False,liters,km); st.rerun()

    @st.dialog("💰 Добави депозит")
    def dashboard_add_deposit():
        amount=st.number_input("Депозит (€)",min_value=0.0,step=1.0)
        desc=st.text_input("Описание",value="Депозит / резервация")
        if st.button("Запиши депозита",type="primary",use_container_width=True) and amount>0:
            add_expense(selected_trip,amount,"Депозит/Резервация",desc,True); st.rerun()

    @st.dialog("✏️ Редактирай бюджет")
    def dashboard_edit_budget():
        vals={}
        for k in [k for k in KATEGORII if k!="Депозит/Резервация"]:
            vals[k]=st.number_input(get_display_category(k),min_value=0.0,value=float(planned.get(k,0)),step=50.0,key="budget_"+k)
        if st.button("💾 Запази бюджета",type="primary",use_container_width=True):
            if _save_budget(selected_trip,vals): st.rerun()
            else: st.error("Неуспешно записване на бюджета.")

    # Избор на реално съществуващо пътуване
    options=[r["trip_id"] for r in trips]
    choice=st.selectbox("Активно пътуване",options,index=options.index(selected_trip),format_func=lambda x:x.replace("_"," "),key="dashboard_trip_select")
    if choice!=selected_trip:
        st.session_state["dashboard_trip"]=choice; selected_trip=choice; metric=_trip_metrics(choice); planned=_ensure_budget_for_trip(choice); planned_total=sum(planned.values()); actual_total=metric["actual"]; budget_pct=(actual_total/planned_total*100) if planned_total else 0; remaining=max(0,planned_total-actual_total) if planned_total else 0; st.rerun()

    # Header
    st.markdown("<div class='px-title'><div class='px-step'>1</div><div><h1>Бюджет на пътуването</h1><p>Планирай, следи и управлявай бюджета си в реално време.</p></div></div>",unsafe_allow_html=True)
    head1,head2=st.columns([3,1])
    with head1: st.markdown(f"<div class='px-panel'><div class='px-trip'>🇬🇷 Пътуване: {selected_trip.replace('_',' ')} <small>{metric['start']} – {metric['end']} ({metric['days']} дни)</small></div></div>",unsafe_allow_html=True)
    with head2:
        if st.button("✎ Редактирай бюджета",use_container_width=True): dashboard_edit_budget()

    if nav in ["Начало","Бюджет"]:
        left,mid,right=st.columns([1.2,1.35,.85])
        with left:
            st.markdown("<div class='px-panel'><h3>Бюджет</h3>",unsafe_allow_html=True)
            if planned_total>0:
                st.markdown(f"<div style='display:flex;gap:20px;align-items:center'><div style='width:118px;height:118px;border-radius:50%;background:conic-gradient(#22d69b {min(budget_pct,100)}%,#173044 0);display:flex;align-items:center;justify-content:center'><div style='width:92px;height:92px;border-radius:50%;background:#061521;display:flex;align-items:center;justify-content:center;flex-direction:column;color:white;font-weight:800;font-size:22px'>{budget_pct:.0f}%<small style='font-size:10px;color:#9db7ca'>изразходван</small></div></div><div><div class='px-kpi'><span class='lbl'>Планиран бюджет</span><div class='val'>{planned_total:,.2f} €</div></div><div class='px-kpi' style='margin-top:7px'><span class='lbl'>Изразходвано</span><div class='val'>{actual_total:,.2f} €</div></div><div class='px-kpi' style='margin-top:7px'><span class='lbl'>Остават</span><div class='val'>{remaining:,.2f} €</div></div></div></div>",unsafe_allow_html=True)
                st.progress(min(budget_pct/100,1.0))
                if budget_pct>=80: st.markdown(f"<div class='px-warning'>⚠️ <b>Внимание! Бюджетът е изразходван {budget_pct:.0f}%.</b><br>При 80% ще получиш известие.</div>",unsafe_allow_html=True)
            else:
                st.info("Бюджетът за това пътуване още не е зададен. Натисни „Редактирай бюджета“. Реалните разходи вече са заредени от твоите данни.")
            st.markdown("</div>",unsafe_allow_html=True)
        with mid:
            cats=list(planned.keys()); chart=pd.DataFrame({"Категория":cats,"Планиран":[planned[k] for k in cats],"Реален":[metric["cats"].get(k,0) for k in cats]})
            st.markdown("<div class='px-panel'><h3>Планиран vs. Реален</h3>",unsafe_allow_html=True)
            if chart["Планиран"].sum()+chart["Реален"].sum()>0:
                fig=px.bar(chart,x="Категория",y=["Планиран","Реален"],barmode="group")
                fig.update_layout(height=280,margin=dict(l=0,r=0,t=10,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",legend_title_text="")
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            else: st.info("Добави бюджет или разход, за да се появи графиката.")
            st.markdown("</div>",unsafe_allow_html=True)
            st.markdown("<div class='px-panel'><h3>Разходи по категории</h3>",unsafe_allow_html=True)
            for k,v in metric["cats"].items():
                pct=v/actual_total*100 if actual_total else 0
                st.markdown(f"<div class='px-cat'><span>{get_emoji(k)} {get_display_category(k)}</span><b>{v:,.2f} € &nbsp; {pct:.0f}%</b></div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        with right:
            st.markdown("<div class='px-panel'><h3>Бързи действия</h3>",unsafe_allow_html=True)
            if st.button("➕  Добави разход",use_container_width=True): dashboard_add_expense()
            if st.button("⛽  Добави зареждане",use_container_width=True): dashboard_add_fuel()
            if st.button("💰  Добави депозит",use_container_width=True): dashboard_add_deposit()
            if st.button("✎  Редактирай бюджет",use_container_width=True): dashboard_edit_budget()
            st.markdown("<hr><h3>Предупреждения</h3>",unsafe_allow_html=True)
            if planned_total==0: st.warning("Бюджетът не е зададен.")
            elif budget_pct>=80: st.warning(f"Бюджетът е изразходван {budget_pct:.0f}%.")
            else: st.success(f"Оставащ бюджет: {remaining:.2f} €")
            if metric["deposit"]>0: st.info(f"Депозити: {metric['deposit']:.2f} €")
            else: st.success("Няма платени депозити.")
            st.markdown("</div>",unsafe_allow_html=True)

    if nav in ["Начало","Разходи"]:
        st.markdown("<div class='px-title'><div class='px-step'>2</div><div><h1>Разход на ден</h1><p>Виж колко харчиш всеки ден и следи тенденциите.</p></div></div>",unsafe_allow_html=True)
        exp=metric["exp"].copy(); daily=[]
        if not exp.empty:
            exp["day"]=exp["date"].astype(str).str[:5]
            for day,g in exp.groupby("day",sort=False): daily.append({"Ден":day,"Разход":float(g["amount"].sum())})
        ddf=pd.DataFrame(daily)
        k1,k2,k3,k4=st.columns(4)
        avg=metric["actual"]/metric["days"] if metric["days"] else 0
        vals=[("Дневен разход (средно)",avg,"↘"),("Днес",float(ddf.iloc[-1]["Разход"]) if not ddf.empty else 0,""),("Вчера",float(ddf.iloc[-2]["Разход"]) if len(ddf)>1 else 0,""),("Общо разходи",metric["actual"],f"{metric['days']} дни")]
        for col,(lab,val,delta) in zip([k1,k2,k3,k4],vals):
            with col: st.markdown(f"<div class='px-kpi'><span class='lbl'>{lab}</span><div class='val'>{val:,.2f} €</div><div class='delta'>{delta}</div></div>",unsafe_allow_html=True)
        c1,c2=st.columns([1.6,1])
        with c1:
            st.markdown("<div class='px-panel'><h3>Разходи по дни</h3>",unsafe_allow_html=True)
            if not ddf.empty:
                fig=px.bar(ddf,x="Ден",y="Разход",text_auto='.0f'); fig.update_layout(height=310,margin=dict(l=0,r=0,t=10,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white")
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            else: st.info("Няма разходи.")
            st.markdown("</div>",unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='px-panel'><h3>Разходи по дни (детайлни)</h3><table class='px-table'><tr><th>Ден</th><th>Разход</th></tr>",unsafe_allow_html=True)
            for i,row in enumerate(daily,1): st.markdown(f"<tr><td>Ден {i} ({row['Ден']})</td><td>{row['Разход']:.2f} €</td></tr>",unsafe_allow_html=True)
            st.markdown("</table></div>",unsafe_allow_html=True)

    if nav in ["Начало","Сравнение","Пътувания"]:
        st.markdown("<div class='px-title'><div class='px-step'>5</div><div><h1>Най-доброто ти пътуване / класации</h1><p>Открий кои пътувания са най-изгодни, най-дълги и кои носят най-много спомени.</p></div></div>",unsafe_allow_html=True)
        metric_choice=st.segmented_control("",["Общо","Цена/км","Километри","Разход на ден","Хотел/Нощувки"],default="Общо",key="ranking_metric")
        rows=trips.copy()
        if metric_choice=="Цена/км": best=min(rows,key=lambda r:r["per_km"] if r["per_km"]>0 else 999999); title="Най-икономично пътуване"; value=f"{best['per_km']:.2f} €/км"; icon="🌿"
        elif metric_choice=="Километри": best=max(rows,key=lambda r:r["dist"]); title="Най-дълго пътуване"; value=f"{best['dist']:.0f} км"; icon="🔗"
        elif metric_choice=="Разход на ден": best=min(rows,key=lambda r:r["per_day"]); title="Най-евтино на ден"; value=f"{best['per_day']:.2f} €/ден"; icon="🏆"
        elif metric_choice=="Хотел/Нощувки": best=min(rows,key=lambda r:r["hotel"]); title="Най-малко за хотел"; value=f"{best['hotel']:.2f} €"; icon="🏨"
        else: best=min(rows,key=lambda r:r["total"]); title="Най-евтино пътуване"; value=f"{best['total']:.2f} €"; icon="🏆"
        rank_cols=st.columns(3)
        cards=[("🏆",title,best["name"],value),("🌿","Най-икономично",min(rows,key=lambda r:r["per_km"] if r["per_km"]>0 else 999999)["name"],f"{min(rows,key=lambda r:r['per_km'] if r['per_km']>0 else 999999)['per_km']:.2f} €/км"),("🔗","Най-дълго",max(rows,key=lambda r:r["dist"])["name"],f"{max(rows,key=lambda r:r['dist'])['dist']:.0f} км")]
        for col,card in zip(rank_cols,cards):
            with col: st.markdown(f"<div class='px-rank'><div class='icon'>{card[0]}</div><div class='rtitle'>{card[1]}</div><div class='rname'>{card[2]}</div><div class='rval'>{card[3]}</div></div>",unsafe_allow_html=True)
        table_rows=[]
        for r in rows: table_rows.append(r)
        st.markdown("<div class='px-panel'><h3>Сравнение на пътуванията</h3><table class='px-table'><tr><th>Пътуване</th><th>Период</th><th>Общо</th><th>€/ден</th><th>€/км</th><th>Км</th><th></th></tr>",unsafe_allow_html=True)
        for i,r in enumerate(table_rows):
            st.markdown(f"<tr><td>{r['name']}</td><td>{r['start']} – {r['end']}</td><td>{r['total']:.2f} €</td><td>{r['per_day']:.2f} €</td><td>{r['per_km']:.2f} €</td><td>{r['dist']:.0f}</td><td></td></tr>",unsafe_allow_html=True)
            if st.button("Виж",key=f"view_trip_{i}"):
                st.session_state["current_trip"]=r["trip_id"]; st.rerun()
        st.markdown("</table></div>",unsafe_allow_html=True)

    if nav=="Карта":
        st.markdown("<div class='px-panel'><h3>🗺️ Карта на пътуването</h3>",unsafe_allow_html=True)
        pts=get_map_points(selected_trip)
        if pts.empty: st.info("Няма запазени точки за това пътуване.")
        else:
            mm=folium.Map(location=[float(pts.lat.mean()),float(pts.lon.mean())],zoom_start=7)
            for _,pt in pts.iterrows(): folium.Marker([pt.lat,pt.lon],popup=pt.title,icon=folium.Icon(color=pt.color,icon="info-sign")).add_to(mm)
            st_folium(mm,width=None,height=480,key=f"dashboard_map_{selected_trip}")
        st.markdown("</div>",unsafe_allow_html=True)

    if nav=="Автомобил":
        s=metric["settings"]
        st.markdown("<div class='px-panel'><h3>🚗 Автомобил</h3>",unsafe_allow_html=True)
        a,b,c=st.columns(3)
        a.metric("Изминати",f"{metric['dist']:.0f} км"); b.metric("Гориво",f"{metric['liters']:.1f} л"); c.metric("€/км",f"{metric['per_km']:.2f}")
        st.info(f"Старт: {s.get('start_km',0):.0f} км • Край: {s.get('end_km',0):.0f} км")
        st.markdown("</div>",unsafe_allow_html=True)

    if nav=="Отчети":
        st.markdown("<div class='px-panel'><h3>📄 Отчети</h3>",unsafe_allow_html=True)
        csv_bytes=metric["data"].to_csv(index=False).encode("utf-8")
        st.download_button("📥 Експорт на текущото пътуване (CSV)",csv_bytes,file_name=f"PixelApp_{selected_trip}.csv",mime="text/csv",use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if nav=="Настройки":
        st.markdown("<div class='px-panel'><h3>⚙️ Настройки</h3>",unsafe_allow_html=True)
        st.info("Тук остават налични оригиналните административни инструменти и настройки от PixelApp, когато отвориш конкретното пътуване.")
        if st.button("Отвори оригиналния екран на пътуването",use_container_width=True): st.session_state["current_trip"]=selected_trip; st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("<div class='px-footer'>🐾 По-добри пътувания. По-добри решения. • PixelApp</div>",unsafe_allow_html=True)

else:
    trip_id = st.session_state["current_trip"]
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            st.write("Сигурни ли сте, че искате да изтриете този разход?")
            idx = st.session_state["delete_idx"]
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                r = df_all.loc[idx]
                display_category = get_display_category(r['category'])
                st.markdown(f"**{get_emoji(r['category'])} {display_category}** — <span style='color:#ff4b4b; font-weight:bold;'>{r['amount']:.2f} EUR</span><br><small>{r['description']}</small>", unsafe_allow_html=True)
            except: 
                pass
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try:
                        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                        df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                    except: 
                        pass
                    st.session_state["delete_idx"] = None
                    st.rerun()
            with c_del2:
                if st.button("✖️ ОТКАЗ", use_container_width=True): 
                    st.session_state["delete_idx"] = None
                    st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Изтриване на пътуването до {str(trip_id).replace('_', ' ')}?")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                try:
                    pd.read_csv(DATA_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                    pd.read_csv(SETTINGS_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                except: 
                    pass
                st.session_state["current_trip"] = None
                st.rerun()
        with c_tr2:
            if st.button("✖️ ОТКАЗ", use_container_width=True): 
                st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: 
            categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: 
                total_liters_sum += float(row["liters"])
                auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): 
                auto_fuel_money += float(row["amount"])
    
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

    progressive_avg_con, has_progressive_data = 0.0, False
    try:
        df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
        df_full_points = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
        if not df_full_points.empty:
            last_full_km = float(df_full_points.iloc[-1]["current_km"])
            total_dist = last_full_km - s_km
            total_liters = float(df_trans_fuel[df_trans_fuel["current_km"] <= last_full_km]["liters"].sum()) + m_fuel
            if total_dist > 0 and total_liters > 0:
                progressive_avg_con = (total_liters / total_dist * 100)
                has_progressive_data = True
    except: 
        pass

    date_html = f"<p style='font-size: 14px; color: #888; font-weight: 500; margin-top: 5px; margin-bottom: 0;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
    st.markdown(f"<div style='text-align: center; margin-top: -10px; margin-bottom: 10px; width: 100%;'><h2 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 500; font-size: 26px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; padding: 0;'>🌴 Дестинация: {str(trip_id).replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div id='trip_top_anchor' style='scroll-margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    ekran_za_kategorii = st.empty()

    if st.button("🔙 НАЗАД КЪМ НАЧАЛЕН ЕКРАН", use_container_width=True): 
        st.session_state["current_trip"] = None
        st.rerun()

    v_id = st.session_state["form_version"]
    st.markdown('<div id="target_sum_box" style="position: relative; scroll-margin-top: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: 
        s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Въведете разход...", format="%.2f", key=f"su_{v_id}")
    with col2: 
        o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")

    is_trip_finished = (e_km > 0.0)

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        if is_trip_finished: 
            st.error("🔒 Пътуването е приключено!")
            return
        liters = st.number_input("Литри:", value=None, placeholder="Напишете литри...", step=0.1)
        fuel_type = st.radio("Тип на зареждането:", ["Да, до горе (Пълен резервоар)", "Не, частично (за конкретна сума)"], index=0)
        
        df_f = get_trip_data(trip_id)[lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)].sort_index()
        last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
        km_input = st.number_input("Текущи километри на таблото (км):", value=None, placeholder="Въведете км...", step=1.0)
        
        total_segment_liters = 0.0
        segment_dist = 0.0
        
        if liters and km_input and km_input > last_km and "до горе" in fuel_type.lower():
            df_since_full = df_f[df_f["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
            if not df_since_full.empty:
                last_full_km = float(df_since_full.iloc[-1]["current_km"])
                partial_liters = float(df_f[df_f["current_km"] > last_full_km]["liters"].sum())
                total_segment_liters = partial_liters + liters
                segment_dist = km_input - last_full_km
            else:
                total_segment_liters = float(df_f["liters"].sum()) + liters + m_fuel
                segment_dist = km_input - s_km
            
            if segment_dist > 0 and total_segment_liters > 0:
                st.success(f"📊 Реален разход за етапа: **{(total_segment_liters / segment_dist * 100):.1f} л / 100 км**")
        
        if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
            lit, ckm = (float(liters) if liters is not None else 0.0), (float(km_input) if km_input is not None else 0.0)
            is_full = "ПЪЛНО" if "до горе" in fuel_type.lower() else "ЧАСТИЧНО"
            full_desc = f"[{is_full} ЗАРЕЖДАНЕ] {description}"
            
            if ckm > last_km and lit > 0 and is_full == "ПЪЛНО":
                df_since_full = df_f[df_f["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                if not df_since_full.empty:
                    last_full_km = float(df_since_full.iloc[-1]["current_km"])
                    partial_liters = float(df_f[df_f["current_km"] > last_full_km]["liters"].sum())
                    t_liters = partial_liters + lit
                    t_dist = ckm - last_full_km
                else:
                    t_liters = float(df_f["liters"].sum()) + lit + m_fuel
                    t_dist = ckm - s_km
                
                if t_dist > 0 and t_liters > 0:
                    full_desc += f" (Етап: {t_dist:.0f}км, Реален разход: {(t_liters / t_dist * 100):.1f}л/100км)"
            
            if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): 
                st.session_state["form_version"] += 1
                st.rerun()

    if o_input.strip() and s_input and s_input > 0:
        header_text = f"Записване на: <b>{s_input:.2f} EUR</b> за <i>\"{o_input.strip()}\"</i>"
        with ekran_za_kategorii.container():
            st.markdown(f"""
            <div style='text-align: center; margin: 10px 0 20px 0; animation: fadeIn 0.4s ease-in-out;'>
                <h3 style='color: #00f2fe; font-family: "Segoe UI", sans-serif; font-weight: 700; margin-bottom: 5px;'>🎯 ИЗБЕРЕТЕ КАТЕГОРИЯ</h3>
                <p style='color: #aaa; font-size: 14px; margin-bottom: 15px;'>{header_text}</p>
            </div>
            <style>
                @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            </style>
            """, unsafe_allow_html=True)
            
            grid = st.columns(3)
            display_categories = {
                "Куче": UI_LABELS["pet"],
                "Нощувки/Хотел": UI_LABELS["hotel"],
                "Депозит/Резервация": UI_LABELS["deposit"]
            }
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    is_disabled = is_trip_finished and (kat == "Транспорт")
                    button_label = display_categories.get(kat, kat)
                    if st.button(f"🔒 {button_label}" if is_disabled else button_label, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                        desc, is_d = o_input.strip(), (kat == "Депозит/Резервация")
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): 
                            fuel_modal(s_input, kat, desc, is_d)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, is_d): 
                                st.session_state["form_version"] += 1
                                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌ ОКОНЧАТЕЛЕН ОТКАЗ / НАЗАД", use_container_width=True):
                st.session_state["form_version"] += 1
                st.rerun()
            st.markdown("---")
            st.stop()

    if car_trip == "Да":
        # === 1. Изчисляване на прогреса за визуализацията на автомобила ===
        is_final_status = True if e_km > s_km else False
        km_progress_pct = 100 if is_final_status else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
        finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_progress_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"

        # === 2. ИЗЧИСЛЯВАНЕ НА ДВАТА ВИДА РАЗХОД ===
        val_real = 0.0      # Реалният разход (до горе)
        val_average = 0.0   # Средният разход (литри/км)
        
        # А) Изчисляване на Реалния разход (Етапен до горе)
        try:
            df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
            df_only_full = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
            if not df_only_full.empty:
                last_full_row = df_only_full.iloc[-1]["description"]
                import re
                match = re.search(r"(?:Реален разход:|Разход:)\s*([0-9.]+)", last_full_row)
                if match:
                    val_real = float(match.group(1))
        except:
            val_real = 0.0

        # Б) Изчисляване на Средния разход (Общо заредено спрямо изминато)
        try:
            current_dist = (eff_end_km - s_km) if is_trip_finished else (float(df_expenses["current_km"].max()) - s_km if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0)
            current_liters = float(df_expenses["liters"].sum()) + m_fuel
            if current_dist > 0 and current_liters > 0:
                val_average = (current_liters / current_dist * 100)
        except:
            val_average = 0.0

        # Цветове за двата уреда
        color_gauge_real = "#00f2fe" if val_real < 6.0 else ("#ffa500" if val_real < 8.5 else "#ff4b4b")
        color_gauge_avg = "#00f2fe" if val_average < 6.0 else ("#ffa500" if val_average < 8.5 else "#ff4b4b")
        
        transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel



        st.markdown(f"### ⏲ Данни за разход и пробег:")
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'><span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 СЛЕДЕНЕ НА ПРОБЕГА</span>{f'<span style=\"background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;\">🔒 ЗАКЛЮЧЕН</span>' if is_trip_finished else ''}</div><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'><div style='text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{s_km:.0f} км</b></div><div style='text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist:.0f} км</b></div><div style='text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>Краен</span><b style='color: white; font-size: 14px;'>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
        # Разделяме екрана на две основни колони: за уредите и за статистика на разходите
        box_col1, box_col2 = st.columns(2)
        
        with box_col1:
            # Ако пътуването е приключено, показваме двата уреда един до друг (вътрешна под-мрежа)
            if is_trip_finished:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; height: 100%; box-shadow: 4px 4px 12px rgba(0,0,0,0.3); margin-bottom: 20px;'>
                    <div style='display: flex; justify-content: space-around; align-items: center; gap: 20px; margin-top: 5px;'>
                        <!-- Уред 1: Реален разход -->
                        <div style='display: flex; flex-direction: column; align-items: center;'>
                            <div style='color: #00f2fe; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 12px;'>РЕАЛЕН РАЗХОД</div>
                            <div style='width: 95px; height: 95px; border-radius: 50%; border: 4px dashed {color_gauge_real}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 10px;'>
                                <div style='color: white; font-size: 24px; font-weight: 900; line-height: 1.1;'>{val_real:.1f}</div>
                                <div style='color: #666; font-size: 9px; font-weight: bold; margin-top: 2px;'>л/100км</div>
                            </div>
                            <div style='color: #666; font-size: 10px;'>Етап "до горе"</div>
                        </div>
                        <!-- Уред 2: Среден разход -->
                        <div style='display: flex; flex-direction: column; align-items: center;'>
                            <div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 12px;'>СРЕДЕН РАЗХОД</div>
                            <div style='width: 95px; height: 95px; border-radius: 50%; border: 4px dashed {color_gauge_avg}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 10px;'>
                                <div style='color: white; font-size: 24px; font-weight: 900; line-height: 1.1;'>{val_average:.1f}</div>
                                <div style='color: #666; font-size: 9px; font-weight: bold; margin-top: 2px;'>л/100км</div>
                            </div>
                            <div style='color: #666; font-size: 10px;'>Общо за трипа</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Ако пътуването ОЩЕ НЕ Е ПРИКЛЮЧЕНО, показваме само един динамичен уред
                val_active = val_real if val_real > 0.0 else val_average
                label_active = "последен етап до горе" if val_real > 0.0 else "среден до момента"
                color_active = color_gauge_real if val_real > 0.0 else color_gauge_avg
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; box-shadow: 4px 4px 12px rgba(0,0,0,0.3); margin-bottom: 20px;'>
                    <div style='color: #888; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 15px;'>ТЕКУЩ РАЗХОД</div>
                    <div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_active}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 15px;'>
                        <div style='color: white; font-size: 28px; font-weight: 900; line-height: 1.1;'>{val_active:.1f}</div>
                        <div style='color: #666; font-size: 10px; font-weight: bold; margin-top: 2px;'>л/100км</div>
                    </div>
                    <div style='color: #666; font-size: 11px;'>{label_active}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with box_col2:
            # Дясната кутия със заредените литри и общата сума за транспорт (добавено е отстояние отдолу за мобилни)
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; height: 100%; box-shadow: 4px 4px 12px rgba(0,0,0,0.3); margin-bottom: 20px;'>
                <div style='margin-bottom: 15px; width: 100%; text-align: center;'>
                    <div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 4px;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО</div>
                    <div style='color: white; font-size: 26px; font-weight: 800;'>{transport_liters:.1f} <span style='font-size: 13px; color: #666; font-weight: normal;'>литра</span></div>
                </div>
                <div style='padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.06); width: 100%; text-align: center;'>
                    <div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 4px;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ</div>
                    <div style='color: white; font-size: 26px; font-weight: 800;'>{auto_fuel_money:.2f} <span style='font-size: 13px; color: #666; font-weight: normal;'>EUR</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)


    
    @st.dialog("⚙️ Настройки за автомобил и период")
    def edit_car_modal():
        v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=is_trip_finished)
        new_sk = st.number_input("Начални километри (км):", value=None if s_km == 0.0 else s_km, placeholder="Въведете началните км...", disabled=is_trip_finished)
        
        # Полето приема само положителни числа за сигурност
        new_mf = st.number_input("Добави пропуснато гориво (л):", value=None, placeholder="Въведете литри...", min_value=0.0, disabled=is_trip_finished)
        
        has_cash_expense = st.checkbox("💵 Има ли финансов разход за добавеното гориво?") if (new_mf and new_mf > 0 and not is_trip_finished) else False
        manual_cash_amt = st.number_input("Въведете платена сума (EUR):", value=None, format="%.2f") if has_cash_expense else 0.0
        try:
            current_start = datetime.datetime.strptime(st_date, "%d.%m.%Y").date() if st_date and st_date != "nan" else datetime.date.today()
            current_end = datetime.datetime.strptime(en_date, "%d.%m.%Y").date() if en_date and en_date != "nan" else datetime.date.today() + datetime.timedelta(days=5)
        except: 
            current_start, current_end = datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)
        edit_range = st.date_input("Изберете нови дати:", value=[current_start, current_end], key="edit_dates_cal")
        
        # Показваме колко литра има натрупани в момента за информация
        if m_fuel > 0:
            st.info(f"📋 Текущо натрупано пропуснато гориво: {m_fuel:.1f} л.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Обнови настройките", use_container_width=True, type="primary", disabled=is_trip_finished):
            sk_val = float(new_sk) if new_sk is not None else 0.0
            added_liters = float(new_mf) if new_mf is not None else 0.0
            mf_val = max(0.0, m_fuel + added_liters)

            # БЕЗОПАСЕН ФИКС: Извикваме .strftime() САМО върху отделните обекти в списъка
            if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0:
                s_d_str = edit_range[0].strftime("%d.%m.%Y") if hasattr(edit_range[0], "strftime") else st_date
                e_d_str = edit_range[-1].strftime("%d.%m.%Y") if (len(edit_range) > 1 and hasattr(edit_range[-1], "strftime")) else s_d_str
            elif hasattr(edit_range, "strftime"):
                s_d_str = edit_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = st_date, en_date

            if has_cash_expense and manual_cash_amt and manual_cash_amt > 0 and added_liters > 0: 
                add_expense(trip_id, manual_cash_amt, "Транспорт", f"[ПРОПУСНАТО ГОРИВО] Добавени {added_liters:.1f} литра", False, 0.0, 0.0)
            
            save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, s_d_str, e_d_str)
            st.session_state["form_version"] += 1
            st.rerun()
            
        # Автоматизирано нулиране на литри И премахване на паричните записи от хронологията
        if m_fuel > 0 and not is_trip_finished:
            if st.button("🗑️ Изчисти натрупаните ръчни литри и разходи", use_container_width=True):
                # 1. Нулиране на литрите в SETTINGS_FILE
                save_trip_settings(trip_id, car_trip, "Да", s_km, e_km, 0.0, st_date, en_date)
                
                # 2. Изчистване на съответните финансови записи от DATA_FILE
                try:
                    df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                    mask_to_delete = (df_all["trip_id"] == trip_id) & (df_all["description"].astype(str).str.contains(r"\[ПРОПУСНАТО ГОРИВО\]"))
                    df_clean = df_all[~mask_to_delete]
                    df_clean.to_csv(DATA_FILE, index=False, encoding="utf-8")
                except:
                    pass
                
                st.session_state["form_version"] += 1
                st.rerun()

    @st.dialog("🏁 Край на пътуването")
    def finish_trip_modal():
        end_km_input = st.number_input("Финални километри от таблото (км):", value=None if e_km == 0.0 else e_km, step=1.0)
        if st.button("🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"):
            if end_km_input and end_km_input > s_km: 
                save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date)
                st.session_state["form_version"] += 1
                st.rerun()
            else: 
                st.error(f"Трябва да са над {s_km:.0f} км!")

    if car_trip == "Да":
        col_manage1, col_manage2 = st.columns(2)
        with col_manage1: 
            st.button("🔒 Заключени настройки" if is_trip_finished else "⚙️ Настройки автомобил", use_container_width=True, disabled=is_trip_finished, on_click=edit_car_modal)
        with col_manage2: 
            st.button("🏁 Пътуването е приключено 🔒" if is_trip_finished else "🏁 Край на пътуването", use_container_width=True, disabled=is_trip_finished, on_click=finish_trip_modal)
    else:
        if st.button("🚗 Добави автомобил към пътуването", use_container_width=True): 
            edit_car_modal()





    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Анализ на разходите:")
    
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        with stat_grid[idx % 2]:
            pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
            display_kat = get_display_category(kat)
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 500; font-size: 15px;">{get_emoji(kat)} {display_kat}</span>
                    <span style="font-weight: bold; color: #ff4b4b; font-size: 15px;">{s_value:.2f} EUR</span>
                </div>
                <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5), inset -1px -1px 2px rgba(255,255,255,0.05); position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 4px;">
                    <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 20px; box-shadow: 2px 2px 5px rgba(0, 242, 254, 0.4), inset 0 2px 2px rgba(255,255,255,0.3); transition: width 0.5s ease-in-out;"></div>
                    <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: rgba(255,255,255,0.85); text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{pct:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    @st.dialog("📊 Разходи по Категории", width="large")
    def разходи_по_категории_dialog():
        st.markdown("<p style='color: #888; margin-bottom: 20px;'>Преглед на направените разходи, групирани по категории:</p>", unsafe_allow_html=True)
        st.markdown("""
            <style>
                .category-expense-card {
                    background: rgba(255,255,255,0.02) !important;
                    padding: 10px 15px !important;
                    border-radius: 10px !important;
                    border: 1px solid rgba(250, 250, 250, 0.08) !important;
                    margin-bottom: 6px !important;
                    display: flex !important;
                    justify-content: space-between !important;
                    align-items: center !important;
                }
                .category-total-box {
                    background: rgba(255, 75, 75, 0.08) !important;
                    border: 1px dashed rgba(255, 75, 75, 0.3) !important;
                    padding: 12px !important;
                    border-radius: 10px !important;
                    margin-top: 5px !important;
                    margin-bottom: 25px !important;
                    text-align: right !important;
                    font-size: 16px !important;
                    font-weight: bold !important;
                    color: #ff4b4b !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_trip_rows = df_all[df_all["trip_id"] == trip_id]
            
            if df_trip_rows.empty:
                st.info("Няма регистрирани разходи за това пътуване.")
            else:
                записани_категории = df_trip_rows["category"].unique()
                
                for кат in KATEGORII:
                    if кат in записани_категории:
                        df_cat = df_trip_rows[df_trip_rows["category"] ==  кат]
                        cat_sum = float(df_cat["amount"].sum())
                        
                        display_кат = get_display_category(кат)
                        st.markdown(f"### {get_emoji(кат)} {display_кат}")
                        st.markdown("<hr style='margin-top:2px; margin-bottom:10px; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                        
                        for _, r in df_cat.iterrows():
                            l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                            st.markdown(f'''
                                <div class="category-expense-card">
                                    <div style="font-size: 14px; color: rgba(250,250,250,0.85);">
                                        📅 {r["date"].replace(" ", " / ")} — <span>{r["description"]}</span>{l_txt}
                                    </div>
                                    <div style="font-size: 14px; font-weight: 600; color: #fafafa;">
                                        {r["amount"]:.2f} EUR
                                    </div>
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        # Коригирано от {cat} на {кат}
                        st.markdown(f'''
                            <div class="category-total-box">
                                Общо за {display_кат}: {cat_sum:.2f} EUR
                            </div>
                        ''', unsafe_allow_html=True)
                        
        except Exception as e:
            st.error(f"Грешка при зареждане на категориите: {str(e)}")
            
        st.markdown("---")
        if st.button("❌ Затвори", use_container_width=True, key="close_cat_popup_btn"):
            st.rerun()

    if st.button("📊 Разходи по Категории", use_container_width=True, key="open_categories_popup_trigger"):
        разходи_по_категории_dialog()
    st.markdown("---")
    col_st1, col_st2 = st.columns(2)
    with col_st1:
        st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center; margin-bottom: 12px;'><small style='color:#aaa; font-weight:bold;'>🏨 ДЕПОЗИТ</small><h2 style='color:#ff4b4b; margin:5px 0;'>{depozit_hotel:.2f} <span style='font-size: 14px; font-weight: 500; color: #7e8494;'>EUR</span></h2></div>", unsafe_allow_html=True)
    with col_st2:
        st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>💰 НА МЯСТО</small><h2 style='color:#00f2fe; margin:5px 0;'>{total_on_site:.2f} <span style='font-size: 14px; font-weight: 500; color: #7e8494;'>EUR</span></h2></div>", unsafe_allow_html=True)

    
    @st.dialog("🔻 Хронология на разходите:", width="large")
    def hronologia_popup_dialog():
        st.markdown("<p style='color: #888; margin-bottom: 20px;'>Тук може да изтриете грешно въведен разход!</p>", unsafe_allow_html=True)
        st.markdown("""
            <style>
                .premium-expense-card {
                    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%) !important;
                    padding: 14px 18px !important;
                    border-radius: 12px !important;
                    border: 1px solid rgba(250, 250, 250, 0.2) !important;
                    box-shadow: 0px 4px 12px rgba(0,0,0,0.2) !important;
                    margin-bottom: 2px !important;
                    min-height: 52px !important;
                    display: flex !important;
                    flex-direction: column !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_trip_rows = df_all[df_all["trip_id"] == trip_id]
            
            if df_trip_rows.empty:
                st.info("Няма регистрирани разходи за това пътуване.")
            else:
                for idx in reversed(df_trip_rows.index.tolist()):
                    if idx not in df_all.index:
                        continue
                    r = df_all.loc[idx]
                    display_category = get_display_category(r["category"])
                    l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                    col_rec, col_del = st.columns([0.88, 0.12])
                    
                    with col_rec:
                        st.markdown(f'''
                            <div class="premium-expense-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                                    <div style="font-size: 16px; font-weight: 600; color: #fafafa;">
                                        <span>{get_emoji(r["category"])}</span> {display_category}
                                    </div>
                                    <div style="font-size: 16px; font-weight: 700; color: #ff4b4b; letter-spacing: 0.5px;">
                                        -{r["amount"]:.2f} EUR
                                    </div>
                                </div>
                                <div style="margin-top: 6px; font-size: 12.5px; color: rgba(250,250,250,0.5);">
                                    📅 {r["date"].replace(" ", " / ")} — <span style="color: rgba(250,250,250,0.75);">{r["description"]}</span>{l_txt}
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)
                        
                    with col_del:
                        st.markdown('<div class="expense-delete-wrapper">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"quick_del_{idx}", use_container_width=True):
                            df_fresh = pd.read_csv(DATA_FILE, encoding="utf-8")
                            target_row = df_fresh.loc[idx]
                            desc_str = str(target_row["description"])
                            
                            # Ако изтриваме ръчно добавено пропуснато гориво
                            if "[ПРОПУСНАТО ГОРИВО]" in desc_str:
                                import re
                                match = re.search(r"Добавени\s*([0-9.]+)\s*литра", desc_str)
                                if match:
                                    liters_to_subtract = float(match.group(1))
                                    new_m_fuel = max(0.0, m_fuel - liters_to_subtract)
                                    save_trip_settings(trip_id, car_trip, t_fuel, s_km, e_km, new_m_fuel, st_date, en_date)
                            
                            # Ако е нормално гориво от категория "Транспорт", .drop() автоматично
                            # ще намали сбора при следващото калкулиране на transport_liters
                            df_fresh = df_fresh.drop(idx)
                            df_fresh.to_csv(DATA_FILE, index=False, encoding="utf-8")
                            st.session_state["form_version"] += 1
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Грешка при зареждане на хронологията: {str(e)}")
        
        st.markdown("---")
        if st.button("❌ Затвори", use_container_width=True, key="close_hronologia_popup_btn"):
            st.rerun()



    
    avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км" if dist > 0 else (f"{progressive_avg_con:.1f} л / 100 км" if has_progressive_data else "Няма данни")
    grand_total = depozit_hotel + total_on_site
    period_html = f" • <b>Период:</b> {st_date} - {en_date}" if st_date and st_date != "nan" else ""
    dist_html = f" • <b>Общо изминати:</b> {dist:.0f} км" if dist > 0 else ""

    # === ДЕФИНИРАНЕ НА PDF HTML СТРУКТУРАТА ЗА ПЕЧАТ ===
    pdf_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Отчет за пътуване - {str(trip_id).replace('_', ' ')}</title>
        <style>
            @media print {{
                body {{ font-size: 11px; line-height: 1.4; color: #000; background: #fff; padding: 0; }}
                tr {{ page-break-inside: avoid; }}
                @page {{ size: A4; margin: 15mm; }}
            }}
            body {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                padding: 25px;
                color: #2f3542;
                background-color: #ffffff;
                max-width: 800px;
                margin: 0 auto;
            }}
            .header-container {{
                border-bottom: 3px solid #000000; 
                padding-bottom: 12px;
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
            }}
            .header-left h2 {{
                color: #2f3542;
                margin: 0 0 4px 0;
                font-size: 24px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .header-right {{
                text-align: right;
                font-weight: 900;
                color: #00a8ff; 
                font-size: 20px;
                letter-spacing: 0.5px;
            }}
            h3 {{
                color: #2f3542;
                border-bottom: 2px solid #e4e7eb;
                padding-bottom: 6px;
                margin-top: 30px;
                font-size: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .meta-info {{
                font-size: 12px;
                color: #747d8c;
                margin: 0;
            }}
            .summary-box {{
                background: #f4f7f9;
                border: 1px solid #dcdde1;
                border-left: 6px solid #2f3542; 
                padding: 18px;
                border-radius: 6px;
                margin-bottom: 25px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }}
            .summary-title {{
                font-size: 12px;
                color: #747d8c;
                text-transform: uppercase;
                margin-bottom: 4px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            .summary-amount {{
                font-size: 28px;
                color: #00a8ff; 
                font-weight: 800;
                margin: 0;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 25px;
            }}
            .stat-card {{
                background: #f8f9fa;
                border: 1px solid #e4e7eb;
                padding: 14px 16px;
                border-radius: 6px;
            }}
            .stat-card h4 {{
                margin: 0 0 10px 0;
                color: #2f3542;
                border-bottom: 1px solid #ced6e0;
                padding-bottom: 6px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .stats-grid ul {{
                list-style: none;
                padding: 0;
                margin: 0;
                font-size: 13px;
            }}
            .stat-card li {{
                margin-bottom: 6px;
                color: #57606f;
            }}
            .stat-card b {{
                color: #2f3542;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
                font-size: 12px;
            }}
            th {{
                background-color: #2f3542; 
                color: #ffffff;
                text-align: left;
                padding: 10px 12px;
                font-weight: 600;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #e4e7eb;
                color: #2f3542;
            }}
            tr:nth-child(even) {{
                background-color: #fcfcfc;
            }}
            .fuel-highlight {{
                color: #00a8ff;
                font-weight: 700;
            }}
            .badge-km {{
                background: #e4e7eb;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 11px;
                color: #2f3542;
                font-weight: 600;
            }}
            .text-right {{
                text-align: right;
            }}
            .total-row {{
                font-weight: bold;
                background-color: #f4f7f9 !important;
                font-size: 14px;
                border-top: 3px solid #000000; 
            }}
        </style>
    </head>
    <body>
        <div class='header-container'>
            <div class='header-left'>
                <h2>ОТЧЕТ ЗА ПЪТУВАНЕ: {str(trip_id).upper().replace('_', ' ')}</h2>
                <p class='meta-info'>Генериран на: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
            <div class='header-right'>
                🐾 PixelApp
            </div>
        </div>

        <div class='summary-box'>
            <div class='summary-title'>Финално салдо</div>
            <div class='summary-amount'>{grand_total:.2f} EUR</div>
            <p style='margin: 6px 0 0 0; font-size: 12px; color: #747d8c;'>
                (Депозит: {depozit_hotel:.2f} EUR | Разходи на място: {total_on_site:.2f} EUR)
            </p>
        </div>

        <div class='stats-grid'>
            <div class='stat-card'>
                <h4>Период и Пробег</h4>
                <ul>
                    <li>{period_html.replace(' • ', '')}</li>
                    <li><b>Начален километраж:</b> {s_km:.0f} км</li>
                    <li><b>Краен километраж:</b> {eff_end_km:.0f} км</li>
                    <li><b>Общо изминато разстояние:</b> {dist:.0f} км</li>
                </ul>
            </div>
            <div class='stat-card'>
                <h4>Автомобилна статистика</h4>
                <ul>
                    <li><b>Изразходено гориво:</b> {total_liters_calculated:.1f} литра</li>
                    <li><b>Обща стойност транспорт:</b> {auto_fuel_money:.2f} EUR</li>
                    <li><b>Среден теглен разход:</b> {avg_con_txt}</li>
                </ul>
            </div>
        </div>

        <h3>Хронология на разходите</h3>
        <table>
            <thead>
                <tr>
                    <th style='width: 18%;'>Дата и час</th>
                    <th style='width: 20%;'>Категория</th>
                    <th style='width: 37%;'>Описание</th>
                    <th style='width: 12%;'>Табло (км)</th>
                    <th style='width: 13%;' class='text-right'>Сума (EUR)</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, row in df_trip.iterrows():
        desc_val = str(row['description'])
        if "Моментен разход:" in desc_val:
            desc_val = desc_val.replace("Моментен разход:", "<span class='fuel-highlight'>Моментен разход:</span>")
        
        cur_km_val = float(row.get('current_km', 0.0))
        km_td_html = f"<span class='badge-km'>{cur_km_val:.0f} км</span>" if cur_km_val > 0 else "<span style='color:#bbb;'>—</span>"
        formatted_date = str(row['date']).replace(" ", " / ")
        display_category = get_display_category(row['category'])
        
        pdf_html += f"""
                <tr>
                    <td>{formatted_date}</td>
                    <td>{display_category}</td>
                    <td>{desc_val}</td>
                    <td>{km_td_html}</td>
                    <td class='text-right' style='font-weight: 500;'>{row['amount']:.2f} EUR</td>
                </tr>"""

    pdf_html += f"""
                <tr class='total-row'>
                    <td colspan='4' class='text-right' style='color: #2f3542;'>ОБЩА СУМА ЗА ПЛАЩАНЕ:</td>
                    <td class='text-right' style='color: #00a8ff;'>{grand_total:.2f} EUR</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>"""

    # === ИНТЕГРИРАНА МУЛТИФУНКЦИОНАЛНА ДИАЛОГОВА СИСТЕМА ===
    @st.dialog("💾 Действия с отчети", width="large")
    def download_and_compare_dialog():
        st.markdown("#### 📥 Изтегляне на текущото пътуване")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📄 Свали Отчет за Печат (PDF/HTML)",
                data=pdf_html,
                file_name=f"Otchet_{trip_id}_2026.html",
                mime="text/html",
                use_container_width=True,
                key="popup_download_pdf_btn"
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_excel = df_trip[['date', 'category', 'description', 'current_km', 'amount']].copy()
                df_excel.columns = ['Дата и час', 'Категория', 'Описание', 'Километраж (км)', 'Сума (EUR)']
                df_excel.to_excel(writer, index=False, sheet_name='Разходи')
                
            st.download_button(
                label="📊 Свали Таблица с разходи (Excel)",
                data=buffer.getvalue(),
                file_name=f"Razhodi_{trip_id}_2026.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="popup_download_excel_btn"
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        # БУТОН ЗА КРАЙНО ЗАТВАРЯНЕ НА ЦЕЛИЯ ПОПЪП ДИАЛОГ
        if st.button("❌ Затвори", use_container_width=True, type="primary", key="close_entire_popup_dialog_btn"):
            st.rerun()

    # === ПОДРЕДБА НА СТАНДАРТНИТЕ БУТОНИ НА ЕКРАНА ===
    st.markdown("<a id='click_scroll_trigger' href='#top_of_page' style='display:none;'></a>", unsafe_allow_html=True)
    
    if st.button("♾️ Хронология на Разходите", use_container_width=True, key="open_hronologia_popup_trigger"):
        hronologia_popup_dialog()

    if st.button("📥 Свали отчет", use_container_width=True, key="main_download_report_popup_trigger"):
        download_and_compare_dialog()








    

    st.markdown("---")



    st.subheader("🗺️ Карта на спирките и дестинациите:")
    df_points = get_map_points(trip_id)
    
    if "map_current_trip_id" not in st.session_state or st.session_state["map_current_trip_id"] != trip_id:
        st.session_state["map_current_trip_id"] = trip_id
        if not df_points.empty:
            st.session_state["stable_lat"] = float(df_points["lat"].mean())
            st.session_state["stable_lon"] = float(df_points["lon"].mean())
            st.session_state["stable_zoom"] = 8
        else:
            st.session_state["stable_lat"] = 42.7339
            st.session_state["stable_lon"] = 25.4858
            st.session_state["stable_zoom"] = 6

    m = folium.Map(
        location=[st.session_state["stable_lat"], st.session_state["stable_lon"]], 
        zoom_start=st.session_state["stable_zoom"]
    )
    m.get_root().html.add_child(folium.Element("<script>document.documentElement.lang = 'bg';</script>"))
    folium.LatLngPopup().add_to(m)
    
    for _, pt in df_points.iterrows(): 
        folium.Marker(
            location=[pt["lat"], pt["lon"]], 
            popup=pt["title"], 
            icon=folium.Icon(color=pt["color"], icon="info-sign")
        ).add_to(m)
    
    points_count = len(df_points)
    click_state = "active" if "active_click" in st.session_state and st.session_state["active_click"] is not None else "idle"
    dynamic_map_key = f"folium_map_{trip_id}_{points_count}_{click_state}"

    map_data = st_folium(
        m, 
        width=700, 
        height=400, 
        key=dynamic_map_key, 
        returned_objects=["last_clicked", "zoom"]
    )

    if map_data and map_data.get("last_clicked"):
        new_click = map_data["last_clicked"]
        if st.session_state.get("active_click") != new_click: 
            st.session_state["stable_lat"] = new_click["lat"]
            st.session_state["stable_lon"] = new_click["lng"]
            if map_data.get("zoom") is not None:
                st.session_state["stable_zoom"] = map_data["zoom"]
            st.session_state["active_click"] = new_click
            st.rerun()
            
    if "active_click" in st.session_state and st.session_state["active_click"] is not None and not is_trip_finished:
        click_coords = st.session_state["active_click"]
        st.markdown(f"📌 **Избрано място:** Ширина: `{click_coords['lat']:.4f}`, Дължина: `{click_coords['lng']:.4f}`")
        c_m1, c_m2 = st.columns([0.7, 0.3])
        with c_m1: 
            title_in = st.text_input("Име на новата спирка:", placeholder="напр. Хотел...", key="map_title_click")
        with c_m2: 
            color_in = st.selectbox("Цвят:", ["blue", "green", "red", "purple", "orange"], key="map_color_click")
        cb1, cb2 = st.columns([0.7, 0.3])
        with cb1:
            if st.button("💾 Запис", use_container_width=True, type="primary") and title_in:
                if add_map_point(trip_id, click_coords["lat"], click_coords["lng"], title_in, color_in): 
                    st.session_state["active_click"] = None
                    st.rerun()
        with cb2:
            if st.button("❌ Отказ", use_container_width=True): 
                st.session_state["active_click"] = None
                st.rerun()
    if not df_points.empty:
        st.markdown("#### 📍 Любими места от пътуването:")
        st.markdown("---")
        try:
            df_all_map = pd.read_csv(MAP_FILE, encoding="utf-8")
            color_emojis = {"blue": "🔵", "green": "🟢", "red": "🔴", "purple": "🟣", "orange": "🟠"}
            for idx in df_all_map[df_all_map["trip_id"] == trip_id].index.tolist():
                pt_row = df_all_map.loc[idx]
                col_p_txt, col_p_del = st.columns([0.85, 0.15])
                with col_p_txt:
                    st.markdown(f"{color_emojis.get(pt_row['color'], '🔵')} **{pt_row['title']}** <small>({pt_row['lat']:.4f}, {pt_row['lon']:.4f})</small>", unsafe_allow_html=True)
                with col_p_del:
                    if st.button("❌", key=f"del_pin_{idx}", use_container_width=True, disabled=is_trip_finished):
                        df_all_map.drop(idx).to_csv(MAP_FILE, index=False, encoding="utf-8")
                        st.rerun()
        except:
            pass
            
    st.markdown("---")
    if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True, key="delete_whole_trip_final_btn"):
        confirm_delete_trip_dialog()

    st.markdown("""
        <style>
            html { scroll-behavior: smooth !important; }
            .twin-premium-3d-btn {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important; 
                height: 38.4px !important;
                background: linear-gradient(to bottom, #262730 0%, #1a1c23 100%) !important;
                color: #ffffff !important; 
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                padding: 0.25rem 0.75rem !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                border-radius: 0.5rem !important;
                cursor: pointer !important;
                user-select: none !important;
                box-shadow: 0px 3px 0px #0e1117, 0px 5px 10px rgba(0,0,0,0.35) !important;
                transition: all 0.15s ease-in-out !important;
            }
            .twin-premium-3d-btn:hover {
                background: linear-gradient(to bottom, #31333e 0%, #22242d 100%) !important;
                border-color: rgba(255, 255, 255, 0.3) !important;
                box-shadow: 0px 3px 0px #0e1117, 0px 7px 14px rgba(0,0,0,0.45) !important;
            }
            .twin-premium-3d-btn:active {
                transform: translateY(2px) !important;
                box-shadow: 0px 1px 0px #0e1117, 0px 2px 4px rgba(0,0,0,0.2) !important;
                transition: all 0.05s ease !important;
            }
            .twin-grid-wrapper a {
                text-decoration: none !important;
                width: 100% !important;
                display: block !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    bottom_cols = st.columns(2)
    
    with bottom_cols[0]:
        if st.button("🔙 КЪМ ГЛАВНО МЕНЮ", use_container_width=True, key="fallback_home_trigger_btn"):
            st.session_state["current_trip"] = None
            st.rerun()
            
    with bottom_cols[1]:
        st.markdown("""
            <div class="twin-grid-wrapper">
                <a href="#trip_top_anchor" target="_self">
                    <button class="twin-premium-3d-btn">🔝КЪМ РАЗХОДИТЕ</button>
                </a>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    if "show_admin_panel" not in st.session_state:
        st.session_state["show_admin_panel"] = False

    if st.button("🛠️ Административни Инструменти", use_container_width=True, key="toggle_admin_panel_btn"):
        st.session_state["show_admin_panel"] = not st.session_state["show_admin_panel"]
        st.rerun()

    if st.session_state["show_admin_panel"]:
        st.markdown("""
            <div style="background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.15); padding: 15px; border-radius: 12px; margin-top: 10px;">
                <h4 style="margin-top:0; color:#00f2fe;">📦 Архивиране и Възстановяване на данни</h4>
                <p style="color: #aaa; font-size: 13px; margin-bottom: 15px;">Използвайте тази секция, за да свалите вашите данни локално или да ги качите обратно, ако сървърът се рестартира.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_backup1, col_backup2 = st.columns(2)
        
        with col_backup1:
            st.markdown("##### 📥 Сваляне на архив")
            try:
                import zipfile
                import io
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, LABELS_FILE]:
                        if os.path.exists(file_name):
                            zip_file.write(file_name, arcname=file_name)
                st.download_button(
                    label="📥 Свали всички CSV логове (.ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="PixelApp_Data_Backup.zip",
                    mime="application/octet-stream",
                    use_container_width=True,
                    key="download_all_csv_backup_btn"
                )
            except:
                st.error("Грешка при генериране на архива.")
                
        with col_backup2:
            st.markdown("##### 📤 Качване на архив")
            uploaded_zip = st.file_uploader(
                "Качете сваления по-горе .ZIP файл тук:", 
                type=["zip"], 
                key="restore_all_csv_backup_uploader",
                label_visibility="collapsed"
            )
            if uploaded_zip is not None:
                if st.button("🔄 ВЪЗСТАНОВИ ДАННИТЕ СЕГА", use_container_width=True, type="primary", key="trigger_restore_data_btn"):
                    success_extract = False
                    try:
                        import zipfile
                        with zipfile.ZipFile(uploaded_zip) as zip_file:
                            namelist = zip_file.namelist()
                            restored_count = 0
                            for f_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, LABELS_FILE]:
                                if f_name in namelist:
                                    with open(f_name, "wb") as f_out:
                                        f_out.write(zip_file.read(f_name))
                                    restored_count += 1
                            if restored_count > 0:
                                success_extract = True
                            else:
                                st.error("В ZIP архива не бяха открити валидни бази данни на PixelApp.")
                    except:
                        st.error("Конфликт при разархивирането. Уверете се, че качвате правилния файл.")
                    
                    if success_extract:
                        st.success("🎉 Данните са възстановени успешно!")
                        st.session_state["show_admin_panel"] = False
                        st.session_state["current_trip"] = None
                        st.rerun()

        st.markdown("---")
        st.markdown("##### 🏷️ Имена на категориите")
        st.caption("Тези настройки променят само текста на бутоните. Записаните разходи и статистиката остават непроменени.")

        pet_options = ["Куче", "Котка", "Домашен любимец"]
        accommodation_options = ["Нощувки/Хотел + Депозит/Резервация", "Хотелски такси + Депозит за резервация"]

        current_pet = UI_LABELS["pet"] if UI_LABELS["pet"] in pet_options else "Куче"
        current_accommodation = (
            "Хотелски такси + Депозит за резервация"
            if UI_LABELS["hotel"] == "Хотелски такси" and UI_LABELS["deposit"] == "Депозит за резервация"
            else "Нощувки/Хотел + Депозит/Резервация"
        )

        admin_col1, admin_col2 = st.columns(2)
        with admin_col1:
            new_pet_label = st.selectbox(
                "🐾 Име на бутона за домашен любимец:",
                pet_options,
                index=pet_options.index(current_pet),
                key="admin_pet_label"
            )
        with admin_col2:
            new_accommodation_labels = st.selectbox(
                "🏨 Имена на хотелските категории:",
                accommodation_options,
                index=accommodation_options.index(current_accommodation),
                key="admin_accommodation_labels"
            )

        if st.button("💾 Запази имената на категориите", use_container_width=True, type="primary", key="save_category_labels_btn"):
            if new_accommodation_labels == "Хотелски такси + Депозит за резервация":
                hotel_label = "Хотелски такси"
                deposit_label = "Депозит за резервация"
            else:
                hotel_label = "Нощувки/Хотел"
                deposit_label = "Депозит/Резервация"

            if save_ui_labels(new_pet_label, hotel_label, deposit_label):
                st.success("✅ Имената на категориите са запазени.")
                st.rerun()
            else:
                st.error("❌ Неуспешно запазване на имената на категориите.")
