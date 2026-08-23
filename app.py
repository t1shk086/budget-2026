import os, io, math, datetime
import pandas as pd
import streamlit as st
import plotly.express as px

# Optional map dependencies
try:
    import folium
    from streamlit_folium import st_folium
except Exception:
    folium = None
    st_folium = None

st.set_page_config(page_title="PixelApp — Travel Manager", page_icon="🐾", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"
BUDGET_FILE = "trip_budgets_2026.csv"

CATEGORIES = ["Нощувки/Хотел", "Храна и напитки", "Транспорт", "Куче", "Други"]
CATEGORY_ICONS = {
    "Нощувки/Хотел": "🏨", "Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Други": "🪙",
    "Депозит/Резервация": "📌"
}
DEFAULT_BUDGETS = {"Нощувки/Хотел": 500.0, "Храна и напитки": 300.0, "Транспорт": 400.0, "Куче": 100.0, "Други": 200.0}

# ---------- Premium responsive styling ----------
st.markdown("""
<style>
:root { --bg:#06111c; --panel:#081b2a; --panel2:#0b2234; --line:#123a56; --blue:#2b91ff; --cyan:#24d5ff; --green:#32d59b; --orange:#ff9b3d; --text:#eef7ff; --muted:#88a4ba; }
html, body, [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 20% 0%, #0d2940 0%, #06111c 38%, #040b12 100%) !important; color:var(--text); }
[data-testid="stHeader"] { background:transparent !important; }
.block-container { max-width: 1500px; padding: 1.1rem 1.1rem 5rem; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#061522,#07101a) !important; border-right:1px solid #123a56; }
section[data-testid="stSidebar"] .stButton button { text-align:left; }
.stButton button, .stDownloadButton button { border-radius:12px !important; border:1px solid #164564 !important; background:linear-gradient(180deg,#0c2a42,#071a2a) !important; color:#eaf6ff !important; min-height:42px; }
.stButton button:hover { border-color:#2b91ff !important; box-shadow:0 0 18px rgba(43,145,255,.16); }
input, textarea, [data-baseweb="select"] > div { background:#071a29 !important; color:#fff !important; }
[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(10,37,57,.95),rgba(5,22,35,.95)); border:1px solid #123a56; border-radius:16px; padding:14px; }
.pixel-card { background:linear-gradient(145deg,rgba(9,34,52,.96),rgba(5,19,31,.96)); border:1px solid #123a56; border-radius:18px; padding:18px; box-shadow:0 10px 35px rgba(0,0,0,.25); }
.pixel-title { font-size:30px; font-weight:850; margin:0; letter-spacing:-.5px; }
.pixel-sub { color:var(--muted); margin-top:2px; }
.section-title { font-size:20px; font-weight:800; margin:8px 0 12px; }
.kpi-big { font-size:28px; font-weight:850; }
.progress { height:12px; background:#172d3d; border-radius:20px; overflow:hidden; }
.progress > div { height:100%; background:linear-gradient(90deg,#24d5ff,#32d59b); border-radius:20px; }
.alert { border-radius:14px; padding:12px 14px; background:rgba(255,164,59,.10); border:1px solid rgba(255,164,59,.25); color:#ffd18e; }
.badge { display:inline-block; border:1px solid #1a4867; background:#0a2437; border-radius:999px; padding:4px 9px; color:#a8c8de; font-size:12px; }
.mobile-nav { display:none; }
@media (max-width: 800px) {
  .block-container { padding:.6rem .55rem 6rem; }
  section[data-testid="stSidebar"] { display:none; }
  .pixel-title { font-size:24px; }
  .mobile-nav { display:block; position:fixed; left:8px; right:8px; bottom:8px; z-index:9999; background:rgba(5,18,29,.96); border:1px solid #164564; border-radius:18px; padding:7px; box-shadow:0 8px 30px rgba(0,0,0,.55); }
  .mobile-nav .stButton button { min-height:44px; font-size:11px; padding:2px 4px; }
  .mobile-nav .stButton button:nth-child(3) { background:linear-gradient(145deg,#1979ed,#2bd2ff) !important; border-radius:50% !important; min-height:48px; }
  [data-testid="stHorizontalBlock"] { gap:.55rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------- Data helpers ----------
def ensure_files():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"]).to_csv(DATA_FILE,index=False,encoding="utf-8")
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame(columns=["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"]).to_csv(SETTINGS_FILE,index=False,encoding="utf-8")
    if not os.path.exists(MAP_FILE):
        pd.DataFrame(columns=["trip_id","lat","lon","title","color"]).to_csv(MAP_FILE,index=False,encoding="utf-8")
    if not os.path.exists(BUDGET_FILE):
        pd.DataFrame(columns=["trip_id"] + CATEGORIES).to_csv(BUDGET_FILE,index=False,encoding="utf-8")

def read_csv(path, cols=None):
    try:
        return pd.read_csv(path, encoding="utf-8")
    except Exception:
        return pd.DataFrame(columns=cols or [])

def trips():
    d=read_csv(DATA_FILE)
    s=read_csv(SETTINGS_FILE)
    vals=set()
    if "trip_id" in d: vals.update([str(x) for x in d.trip_id.dropna().unique() if str(x).strip()])
    if "trip_id" in s: vals.update([str(x) for x in s.trip_id.dropna().unique() if str(x).strip()])
    return sorted(vals, reverse=True)

def settings(tid):
    s=read_csv(SETTINGS_FILE)
    if not s.empty and "trip_id" in s:
        r=s[s.trip_id.astype(str)==str(tid)]
        if not r.empty: return r.iloc[0].to_dict()
    return {"car_trip":"Не","start_km":0,"end_km":0,"manual_fuel":0,"start_date":"","end_date":""}

def trip_df(tid):
    d=read_csv(DATA_FILE)
    if d.empty: return d
    d=d[d.trip_id.astype(str)==str(tid)].copy()
    for c,default in [("amount",0),("liters",0),("current_km",0)]:
        if c not in d: d[c]=default
    return d

def budget(tid):
    b=read_csv(BUDGET_FILE)
    if not b.empty:
        r=b[b.trip_id.astype(str)==str(tid)]
        if not r.empty:
            return {c:float(r.iloc[0].get(c,DEFAULT_BUDGETS[c]) or 0) for c in CATEGORIES}
    return DEFAULT_BUDGETS.copy()

def save_budget(tid, vals):
    b=read_csv(BUDGET_FILE)
    b=b[b.trip_id.astype(str)!=str(tid)] if not b.empty and "trip_id" in b else b
    row={"trip_id":tid, **{c:float(vals.get(c,0)) for c in CATEGORIES}}
    pd.concat([b,pd.DataFrame([row])],ignore_index=True).to_csv(BUDGET_FILE,index=False,encoding="utf-8")

def add_expense(tid, amount, category, description, liters=0, km=0, typ="expense"):
    d=read_csv(DATA_FILE)
    row={"trip_id":tid,"date":datetime.datetime.now().strftime("%d.%m %H:%M"),"amount":float(amount),"category":category,"description":description or "Без описание","type":typ,"liters":float(liters),"current_km":float(km)}
    pd.concat([d,pd.DataFrame([row])],ignore_index=True).to_csv(DATA_FILE,index=False,encoding="utf-8")

def days_for(tid):
    s=settings(tid)
    try:
        a=datetime.datetime.strptime(str(s.get("start_date","")),"%d.%m.%Y")
        b=datetime.datetime.strptime(str(s.get("end_date","")),"%d.%m.%Y")
        return max(1,(b-a).days+1)
    except: return 1

def trip_total(tid):
    d=trip_df(tid)
    return float(d.amount.sum()) if not d.empty else 0

def euro(x): return f"{x:,.2f} €".replace(","," ")

ensure_files()
if "page" not in st.session_state: st.session_state.page="Бюджет"
if "current_trip" not in st.session_state: st.session_state.current_trip=None

all_trips=trips()
if not all_trips:
    st.session_state.current_trip="__new__"
else:
    if st.session_state.current_trip not in all_trips:
        st.session_state.current_trip=all_trips[0]

tid=st.session_state.current_trip

# ---------- Navigation ----------
nav=["Начало","Пътувания","Разходи","Карта","Автомобил","Сравнение","Бюджет","Отчети","Настройки"]
icons={"Начало":"⌂","Пътувания":"🧳","Разходи":"▤","Карта":"⌖","Автомобил":"🚗","Сравнение":"◈","Бюджет":"◉","Отчети":"▥","Настройки":"⚙"}
with st.sidebar:
    st.markdown("### 🐾 PixelApp")
    st.caption("Travel Manager")
    for p in nav:
        if st.button(f"{icons[p]}  {p}", key=f"side_{p}", use_container_width=True):
            st.session_state.page=p; st.rerun()

# mobile nav
st.markdown('<div class="mobile-nav">', unsafe_allow_html=True)
mcols=st.columns(5)
for i,(p,label) in enumerate([("Начало","⌂"),("Разходи","▤"),("__add__","＋"),("Карта","⌖"),("Сравнение","◈")]):
    with mcols[i]:
        if st.button(label,key=f"mob_{i}",use_container_width=True):
            if p=="__add__": st.session_state.page="Разходи"
            else: st.session_state.page=p
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Header ----------
if tid=="__new__":
    st.markdown('<div class="pixel-card"><div class="pixel-title">🐾 PixelApp</div><div class="pixel-sub">Създай първото си пътуване, за да започнеш.</div></div>',unsafe_allow_html=True)
    with st.form("new_trip"):
        name=st.text_input("Дестинация",placeholder="Гърция 2026")
        dates=st.date_input("Период",value=[datetime.date.today(),datetime.date.today()])
        car=st.checkbox("Пътувам със собствен автомобил")
        start_km=st.number_input("Начални км",min_value=0.0,step=1.0) if car else 0.0
        if st.form_submit_button("🚀 Създай пътуване",use_container_width=True) and name.strip():
            tid=name.strip().replace(" ","_")
            a=dates[0] if isinstance(dates,(list,tuple)) else dates; b=dates[-1] if isinstance(dates,(list,tuple)) else dates
            s=read_csv(SETTINGS_FILE)
            row={"trip_id":tid,"car_trip":"Да" if car else "Не","track_fuel":"Да" if car else "Добави впоследствие","start_km":start_km,"end_km":0,"manual_fuel":0,"start_date":a.strftime("%d.%m.%Y"),"end_date":b.strftime("%d.%m.%Y")}
            pd.concat([s,pd.DataFrame([row])],ignore_index=True).to_csv(SETTINGS_FILE,index=False,encoding="utf-8")
            save_budget(tid,DEFAULT_BUDGETS)
            st.session_state.current_trip=tid; st.session_state.page="Бюджет"; st.rerun()
    st.stop()

s=settings(tid); d=trip_df(tid); b=budget(tid)
site=d[d.type.astype(str)!="deposit"] if not d.empty and "type" in d else d
spent=float(site.amount.sum()) if not site.empty else 0.0
dep=float(d[d.type.astype(str)=="deposit"].amount.sum()) if not d.empty and "type" in d else 0.0
grand=spent+dep
planned=sum(b.values())
pct=min(100,grand/planned*100) if planned else 0
start_km=float(s.get("start_km",0) or 0); end_km=float(s.get("end_km",0) or 0)
if not end_km and not d.empty and "current_km" in d: end_km=float(d.current_km.max() or 0)
dist=max(0,end_km-start_km)
period=f"{s.get('start_date','')} – {s.get('end_date','')}"
trip_name=tid.replace("_"," ")

st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:end;gap:20px"><div><div class="pixel-title">{trip_name}</div><div class="pixel-sub">{period} · {days_for(tid)} дни</div></div><span class="badge">🐾 PixelApp</span></div>',unsafe_allow_html=True)
st.write("")

# ---------- Pages ----------
if st.session_state.page in ["Начало","Бюджет"]:
    c1,c2,c3=st.columns([1.05,1.1,.85])
    with c1:
        st.markdown('<div class="pixel-card">',unsafe_allow_html=True)
        st.markdown("### 💰 Бюджет")
        st.metric("Планиран бюджет",euro(planned))
        st.metric("Изразходвано",euro(grand),f"{pct:.0f}%")
        st.metric("Остават",euro(max(0,planned-grand)))
        st.markdown(f'<div class="progress"><div style="width:{pct:.1f}%"></div></div>',unsafe_allow_html=True)
        if pct>=80: st.markdown(f'<div class="alert" style="margin-top:14px">⚠️ <b>Внимание!</b> Бюджетът е използван {pct:.0f}%. При 80% получавате известие.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="pixel-card">',unsafe_allow_html=True)
        st.markdown("### 📊 Планиран vs. реален")
        rows=[]
        for cat in CATEGORIES:
            real=float(site[site.category==cat].amount.sum()) if not site.empty else 0
            rows.append({"Категория":cat,"Планиран":b[cat],"Реален":real})
        g=pd.DataFrame(rows)
        fig=px.bar(g,x="Категория",y=["Планиран","Реален"],barmode="group")
        fig.update_layout(height=310,margin=dict(l=10,r=10,t=20,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",legend_title_text="")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="pixel-card">',unsafe_allow_html=True)
        st.markdown("### ⚡ Бързи действия")
        if st.button("➕ Добави разход",use_container_width=True): st.session_state.page="Разходи"; st.rerun()
        if st.button("⛽ Добави зареждане",use_container_width=True): st.session_state.page="Автомобил"; st.rerun()
        if st.button("📌 Добави депозит",use_container_width=True): st.session_state.page="Разходи"; st.session_state.quick_deposit=True; st.rerun()
        if st.button("✏️ Редактирай бюджет",use_container_width=True): st.session_state.page="Бюджет"; st.session_state.edit_budget=True; st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="section-title">Разходи по категории</div>',unsafe_allow_html=True)
    cols=st.columns(5)
    for i,cat in enumerate(CATEGORIES):
        real=float(site[site.category==cat].amount.sum()) if not site.empty else 0
        with cols[i]:
            st.markdown(f'<div class="pixel-card"><div>{CATEGORY_ICONS[cat]} <b>{cat}</b></div><div class="kpi-big">{euro(real)}</div><div class="pixel-sub">{real/b[cat]*100:.0f}% от плана</div></div>',unsafe_allow_html=True)

    if st.session_state.get("edit_budget"):
        with st.expander("✏️ Редактиране на планирания бюджет",expanded=True):
            vals={}
            cc=st.columns(2)
            for i,cat in enumerate(CATEGORIES):
                with cc[i%2]: vals[cat]=st.number_input(cat,min_value=0.0,value=float(b[cat]),step=50.0,key=f"bud_{i}")
            if st.button("💾 Запази бюджета",type="primary",use_container_width=True):
                save_budget(tid,vals); st.session_state.edit_budget=False; st.rerun()

elif st.session_state.page=="Разходи":
    st.markdown('<div class="section-title">💳 Разход на ден</div>',unsafe_allow_html=True)
    today_spent=0
    if not d.empty:
        today=datetime.datetime.now().strftime("%d.%m")
        today_spent=float(d[d.date.astype(str).str.startswith(today)].amount.sum())
    avg=spent/days_for(tid) if days_for(tid) else 0
    a,bx,c=st.columns(3)
    a.metric("Днес",euro(today_spent)); bx.metric("Средно/ден",euro(avg)); c.metric("Общо",euro(grand))
    with st.form("expense_form",clear_on_submit=True):
        amount=st.number_input("Сума (EUR)",min_value=0.0,step=1.0)
        desc=st.text_input("Описание",placeholder="Вечеря, музей, паркинг...")
        cat=st.selectbox("Категория",CATEGORIES)
        deposit=st.checkbox("Това е депозит/резервация")
        if st.form_submit_button("💾 Запиши разхода",use_container_width=True) and amount>0:
            add_expense(tid,amount,"Депозит/Резервация" if deposit else cat,desc,typ="deposit" if deposit else "expense"); st.rerun()
    if not d.empty:
        x=d.copy(); x["date_only"]=x.date.astype(str).str[:5]
        daily=x.groupby("date_only",as_index=False).amount.sum().rename(columns={"date_only":"Дата","amount":"Разход"})
        fig=px.bar(daily,x="Дата",y="Разход",text_auto=".2f")
        fig.update_layout(height=330,margin=dict(l=10,r=10,t=20,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown("### Последни разходи")
        show=d.sort_index(ascending=False).head(20)[["date","category","description","amount"]].copy()
        show.columns=["Дата","Категория","Описание","Сума EUR"]
        st.dataframe(show,use_container_width=True,hide_index=True)

elif st.session_state.page=="Сравнение":
    st.markdown('<div class="section-title">🏆 История + класации</div>',unsafe_allow_html=True)
    metric=st.segmented_control("Критерий",["Общо","Цена/км","Километри","Разход/ден","Хотел/Нощувки"],default="Общо") if hasattr(st,"segmented_control") else "Общо"
    rows=[]
    all_d=read_csv(DATA_FILE); all_s=read_csv(SETTINGS_FILE)
    for t in trips():
        td=all_d[all_d.trip_id.astype(str)==t] if not all_d.empty else pd.DataFrame()
        ts=all_s[all_s.trip_id.astype(str)==t] if not all_s.empty else pd.DataFrame()
        total=float(td.amount.sum()) if not td.empty else 0
        sk=float(ts.iloc[0].get("start_km",0)) if not ts.empty else 0
        ek=float(ts.iloc[0].get("end_km",0)) if not ts.empty else 0
        if not ek and not td.empty and "current_km" in td: ek=float(td.current_km.max() or 0)
        km=max(0,ek-sk); days=days_for(t); hotel=float(td[td.category=="Нощувки/Хотел"].amount.sum()) if not td.empty else 0
        rows.append({"Пътуване":t.replace("_"," "),"Общо":total,"Цена/км":total/km if km else 0,"Километри":km,"Разход/ден":total/days,"Хотел/Нощувки":hotel})
    comp=pd.DataFrame(rows)
    if not comp.empty:
        ascending=metric in ["Цена/км","Разход/ден"]
        st.dataframe(comp.sort_values(metric,ascending=ascending).style.format({c:"{:.2f}" for c in comp.columns[1:]}),use_container_width=True,hide_index=True)
        best=comp.sort_values(metric,ascending=ascending).iloc[0]
        st.success(f"🏆 Най-добро по {metric}: **{best['Пътуване']}** — {best[metric]:.2f}")

elif st.session_state.page=="Автомобил":
    st.markdown('<div class="section-title">🚗 Автомобил</div>',unsafe_allow_html=True)
    fuel=float(d[d.category=="Транспорт"].liters.sum()) if not d.empty and "liters" in d else 0
    fuel_money=float(d[d.category=="Транспорт"].amount.sum()) if not d.empty else 0
    consumption=fuel/dist*100 if dist>0 and fuel>0 else 0
    a,bx,c=st.columns(3); a.metric("Изминати км",f"{dist:.0f} км"); bx.metric("Гориво",f"{fuel:.1f} л"); c.metric("Разход",f"{consumption:.1f} л/100 км" if consumption else "—")
    st.markdown('<div class="pixel-card">',unsafe_allow_html=True)
    with st.form("fuel_form",clear_on_submit=True):
        amount=st.number_input("Платено (EUR)",min_value=0.0,step=1.0)
        liters=st.number_input("Литри",min_value=0.0,step=0.1)
        km=st.number_input("Текущи километри",min_value=0.0,step=1.0,value=float(end_km or start_km))
        desc=st.text_input("Описание",value="Зареждане")
        if st.form_submit_button("⛽ Запиши зареждането",use_container_width=True) and amount>0:
            add_expense(tid,amount,"Транспорт",desc,liters,km); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

elif st.session_state.page=="Карта":
    st.markdown('<div class="section-title">🗺️ Карта на пътуването</div>',unsafe_allow_html=True)
    pts=read_csv(MAP_FILE)
    pts=pts[pts.trip_id.astype(str)==tid] if not pts.empty else pts
    if folium and st_folium:
        lat=float(pts.lat.mean()) if not pts.empty else 42.7; lon=float(pts.lon.mean()) if not pts.empty else 25.4
        m=folium.Map(location=[lat,lon],zoom_start=6,tiles="CartoDB dark_matter")
        for _,r in pts.iterrows(): folium.Marker([r.lat,r.lon],tooltip=str(r.title)).add_to(m)
        st_folium(m,use_container_width=True,height=520)
    else: st.info("Инсталирайте folium и streamlit-folium за картата.")

elif st.session_state.page=="Пътувания":
    st.markdown('<div class="section-title">🧳 Всички пътувания</div>',unsafe_allow_html=True)
    for t in trips():
        tt=trip_total(t); dd=days_for(t)
        c=st.container(border=True)
        with c:
            a,bx,cx=st.columns([2,1,1]); a.markdown(f"### 🌍 {t.replace('_',' ')}"); bx.metric("Общо",euro(tt)); cx.metric("€/ден",euro(tt/dd))
            if st.button("Отвори",key=f"open_{t}"): st.session_state.current_trip=t; st.session_state.page="Бюджет"; st.rerun()
    if st.button("➕ Ново пътуване",use_container_width=True): st.session_state.current_trip="__new__"; st.rerun()

elif st.session_state.page=="Отчети":
    st.markdown('<div class="section-title">📄 Отчети</div>',unsafe_allow_html=True)
    if not d.empty:
        csv=d.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 CSV на текущото пътуване",csv,f"PixelApp_{tid}.csv","text/csv",use_container_width=True)
        st.markdown("### Обобщение")
        st.dataframe(d.groupby("category",as_index=False).amount.sum().rename(columns={"amount":"EUR"}),use_container_width=True,hide_index=True)

elif st.session_state.page=="Настройки":
    st.markdown('<div class="section-title">⚙️ Настройки</div>',unsafe_allow_html=True)
    st.info("Това е тестова UI версия. Съществуващите CSV файлове се използват като база и не се презаписва основната логика на оригиналното приложение.")
    st.write("Текущо пътуване:",trip_name)
    if st.button("🗑️ Изтрий текущото пътуване",type="primary"):
        for f in [DATA_FILE,SETTINGS_FILE,MAP_FILE,BUDGET_FILE]:
            if os.path.exists(f):
                df=read_csv(f)
                if "trip_id" in df: df[df.trip_id.astype(str)!=tid].to_csv(f,index=False,encoding="utf-8")
        st.session_state.current_trip=trips()[0] if trips() else "__new__"; st.rerun()

# Footer
st.markdown('<div style="text-align:center;color:#5e7b91;font-size:12px;margin-top:30px">🐾 PixelApp · По-добри пътувания. По-умни решения.</div>',unsafe_allow_html=True)
