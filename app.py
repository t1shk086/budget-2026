import os, math, datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title='PixelApp — Бюджет на пътуването', page_icon='🐾', layout='wide', initial_sidebar_state='expanded')

# INTERACTION STATE
for _k,_v in {'page':'Бюджет','action':None,'rank_mode':'Общо'}.items():
    if _k not in st.session_state: st.session_state[_k]=_v

def nav_to(label):
    st.session_state.page=label
    st.session_state.action=None

def choose_action(action):
    st.session_state.action=action

def save_expense(amount, category, date, description):
    row=pd.DataFrame([{'trip_id':tid,'date':date.strftime('%d.%m.%Y'),'amount':float(amount),'category':category,'description':description,'type':'expense'}])
    path=DATA_FILE
    try:
        old=pd.read_csv(path,encoding='utf-8')
        out=pd.concat([old,row],ignore_index=True)
    except Exception:
        out=row
    out.to_csv(path,index=False,encoding='utf-8')
    st.session_state.action=None
    st.cache_data.clear()
    st.toast('Разходът е добавен успешно.', icon='✅')

def save_budget(values):
    row=pd.DataFrame([{'trip_id':tid,**values}])
    try:
        old=pd.read_csv(BUDGET_FILE,encoding='utf-8')
        if 'trip_id' in old.columns:
            old=old[old.trip_id.astype(str)!=str(tid)]
        out=pd.concat([old,row],ignore_index=True)
    except Exception:
        out=row
    out.to_csv(BUDGET_FILE,index=False,encoding='utf-8')
    st.session_state.action=None
    st.toast('Бюджетът е записан.', icon='✅')

# =========================
# DATA
# =========================
DATA_FILE='budget_data_2026.csv'
SETTINGS_FILE='trip_settings_2026.csv'
BUDGET_FILE='trip_budgets_2026.csv'
MAP_FILE='trip_map_points_2026.csv'
CATEGORIES=['Нощувки/Хотел','Храна и напитки','Транспорт','Куче','Други']
ICONS={'Нощувки/Хотел':'🏨','Храна и напитки':'🍔','Транспорт':'🚗','Куче':'🐾','Други':'•••'}
COLORS=['#3b8ef3','#ff8c3a','#2bd4ad','#8b4de8','#7586b8']

def read_csv(path, cols=None):
    try: return pd.read_csv(path, encoding='utf-8')
    except Exception: return pd.DataFrame(columns=cols or [])

def euro(x): return f'{float(x):,.2f} €'.replace(',', ' ')

def trips():
    d=read_csv(DATA_FILE); s=read_csv(SETTINGS_FILE); vals=[]
    for df in [d,s]:
        if 'trip_id' in df.columns: vals += [str(x) for x in df.trip_id.dropna().unique() if str(x).strip()]
    return sorted(set(vals), reverse=True)

def settings(tid):
    s=read_csv(SETTINGS_FILE)
    if not s.empty and 'trip_id' in s.columns:
        r=s[s.trip_id.astype(str)==str(tid)]
        if not r.empty: return r.iloc[0].to_dict()
    return {'start_date':'15.08.2026','end_date':'22.08.2026','start_km':0,'end_km':1247,'car_trip':'Да'}

def expenses(tid):
    d=read_csv(DATA_FILE)
    if d.empty: return d
    d=d[d.trip_id.astype(str)==str(tid)].copy()
    if 'amount' not in d: d['amount']=0
    if 'category' not in d: d['category']='Други'
    if 'date' not in d: d['date']=''
    if 'description' not in d: d['description']=''
    if 'type' not in d: d['type']='expense'
    return d

def budget(tid):
    b=read_csv(BUDGET_FILE)
    if not b.empty and 'trip_id' in b.columns:
        r=b[b.trip_id.astype(str)==str(tid)]
        if not r.empty: return {c:float(r.iloc[0].get(c,0) or 0) for c in CATEGORIES}
    return {'Нощувки/Хотел':500,'Храна и напитки':300,'Транспорт':400,'Куче':100,'Други':200}

def days(tid):
    s=settings(tid)
    try:
        a=datetime.datetime.strptime(str(s.get('start_date')),'%d.%m.%Y'); b=datetime.datetime.strptime(str(s.get('end_date')),'%d.%m.%Y')
        return max(1,(b-a).days+1)
    except: return 8

def mock_if_empty(tid):
    # Only visual fallback; if user's CSVs contain data, their data wins.
    d=expenses(tid)
    if not d.empty: return d
    vals=[82.10,126.40,61.30,147.20,93.50,76.30,112.40,63.00]
    cats=['Нощувки/Хотел','Храна и напитки','Транспорт','Нощувки/Хотел','Храна и напитки','Транспорт','Храна и напитки','Други']
    dates=['15.08.2026','16.08.2026','17.08.2026','18.08.2026','19.08.2026','20.08.2026','21.08.2026','22.08.2026']
    return pd.DataFrame({'date':dates,'amount':vals,'category':cats,'description':['Хотел','Ресторант','Гориво','Хотел','Обяд','Гориво','Вечеря','Паркинг'],'type':['expense']*8})

all_trips=trips()
if not all_trips: all_trips=['Гърция_2026']
if 'trip' not in st.session_state: st.session_state.trip=all_trips[0]
if st.session_state.trip not in all_trips: st.session_state.trip=all_trips[0]

tid=st.session_state.trip
s=settings(tid); d=mock_if_empty(tid); b=budget(tid)
spent=float(d.amount.sum()) if not d.empty else 0
planned=sum(b.values())
pct=min(100,spent/planned*100) if planned else 0
remaining=max(0,planned-spent)
period=f"{s.get('start_date','15.08.2026')} – {s.get('end_date','22.08.2026')}"
trip_name=tid.replace('_',' ')

daily=d.groupby('date',sort=False)['amount'].sum().reset_index() if not d.empty else pd.DataFrame({'date':[],'amount':[]})

# =========================
# VISUAL SYSTEM — intentionally follows the supplied mockups
# =========================
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#030b13;--panel:#061421;--panel2:#081b2b;--line:#123d5b;--line2:#0d2a40;--blue:#318ef5;--cyan:#29cfff;--green:#2ed8a4;--text:#eef7ff;--muted:#8ba8bd;--warn:#ffbd45;--purple:#8c4de8}
html,body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 65% -10%,#0c2d48 0,#06131f 38%,#02070c 78%)!important;color:var(--text)!important;font-family:Inter,system-ui,sans-serif}
[data-testid="stHeader"]{background:transparent!important}
.block-container{max-width:1540px;padding:.65rem .75rem 2.2rem}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#06111b,#030a11)!important;border-right:1px solid #0c2b41!important}
section[data-testid="stSidebar"]>div{padding:18px 12px}
.stButton button{justify-content:flex-start;text-align:left;border:0!important;background:transparent!important;color:#a7bfd0!important;border-radius:10px!important}
section[data-testid="stSidebar"] .stButton button:hover{background:#092943!important;color:#fff!important}
.brand{font-size:22px;font-weight:800;display:flex;gap:10px;align-items:center;margin-bottom:18px}.brand span{font-size:25px}
.hero{display:flex;align-items:center;gap:16px;margin:0 0 10px}.num{width:58px;height:58px;border:3px solid #3ea5ff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:27px;font-weight:800;color:#dceeff;box-shadow:0 0 18px #1673b533}.hero h1{font-size:27px;line-height:1;margin:0;font-weight:800}.hero p{margin:5px 0 0;color:#a7c6d9;font-size:14px}
.top-shell{border:1px solid #123a55;border-radius:18px;background:linear-gradient(145deg,#061624eF,#020b13eF);box-shadow:0 14px 45px #0008;padding:12px}
.tripbar{display:flex;align-items:center;justify-content:space-between;padding:3px 8px 12px}.tripname{font-size:18px;font-weight:700}.tripmeta{font-size:12px;color:#9bb5c7;margin-top:4px}.flag{font-size:29px;vertical-align:middle;margin-right:8px}
.card{background:linear-gradient(145deg,rgba(7,26,40,.98),rgba(3,14,23,.98));border:1px solid #123b57;border-radius:14px;padding:14px;box-shadow:inset 0 1px #173d55aa,0 10px 30px #0005}.card h3{font-size:15px;margin:0 0 10px}.muted{color:var(--muted)}
.kpi-label{font-size:12px;color:#90b1c8}.kpi{font-size:21px;font-weight:700;margin:2px 0 8px}.kpi.green{color:#42e3af}.kpi.warn{color:#ffbe55}.progress{height:17px;background:#193247;border-radius:12px;overflow:hidden;margin:10px 0 12px}.progress>div{height:100%;background:linear-gradient(90deg,#38dbac,#1fbde8);border-radius:12px}.alert{padding:10px 12px;border-radius:11px;background:#302713aa;border:1px solid #674d1f;color:#ffd176;font-size:12px}.info{padding:10px 12px;border-radius:11px;background:#09283daa;border:1px solid #164d70;color:#b7d9ee;font-size:12px}
.quick{padding:10px 12px;border-radius:11px;border:1px solid #164663;background:linear-gradient(180deg,#092943,#061a29);margin-bottom:8px;font-size:12px;font-weight:600}.quick .ico{font-size:20px;margin-right:9px}
.chart-title{font-size:15px;font-weight:700;margin-bottom:8px}.legend{font-size:11px;color:#a5bed0;text-align:right}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}.blue{background:#3b8ef3}.green-dot{background:#38d9a6}
.catrow{display:grid;grid-template-columns:18px 1fr 70px 40px;gap:6px;align-items:center;font-size:11px;padding:6px 0;border-bottom:1px solid #0c2a3c}.catrow:last-child{border-bottom:0}.bar-mini{height:5px;background:#173145;border-radius:4px;overflow:hidden}.bar-mini>div{height:100%;background:#2ed8a4}.pct{color:#b8ccda;text-align:right}
.section-head{display:flex;align-items:center;gap:15px;margin:14px 0 8px}.section-head .num{width:58px;height:58px;flex:0 0 58px}.section-head h2{font-size:25px;margin:0}.section-head p{margin:4px 0 0;color:#9eb8c9;font-size:13px}
.metricbox{border:1px solid #123a55;background:linear-gradient(145deg,#071d2d,#05111b);border-radius:12px;padding:12px}.metricbox .v{font-size:19px;font-weight:700}.metricbox .l{font-size:11px;color:#92aec1}.up{color:#ff5c61;font-size:11px}.down{color:#31dc9d;font-size:11px}
.rank{border:1px solid #123a55;background:linear-gradient(145deg,#071d2d,#05111b);border-radius:12px;padding:10px;display:flex;gap:10px;align-items:center;min-height:72px}.rank .r-icon{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;background:#102d45}.rank .r-title{font-size:11px;color:#ffb934;font-weight:700}.rank .r-name{font-size:11px;color:#9fb8ca}.rank .r-value{font-size:13px;font-weight:700;margin-top:3px}
.table{width:100%;border-collapse:separate;border-spacing:0;font-size:10px;overflow:hidden;border:1px solid #123a55;border-radius:10px}.table th{color:#8daabd;font-weight:500;background:#071b2a;padding:7px}.table td{padding:7px;border-top:1px solid #0c2a3c;color:#dceaf2}.table td:last-child,.table th:last-child{text-align:right}
.pill{display:inline-block;padding:6px 10px;border:1px solid #15405d;border-radius:9px;background:#071a2a;color:#a8c0d0;font-size:11px;margin-right:5px}.pill.active{background:#0f4f9d;color:#fff;border-color:#287fe0}
.bottomspace{height:8px}
.stButton button{border:1px solid #164663!important;background:linear-gradient(180deg,#092943,#061a29)!important;color:#e7f5ff!important;border-radius:10px!important;font-weight:600!important;min-height:38px}.stButton button:hover{border-color:#2a8fe8!important;box-shadow:0 0 0 1px #2a8fe833,0 5px 18px #0007!important}.stButton button[kind="primary"]{background:linear-gradient(180deg,#1161ad,#0b4480)!important;border-color:#278be7!important}.stButton button p{font-size:12px!important}
.mobile-bottom{display:none}
@media(max-width:850px){
 .block-container{padding:.35rem .45rem 5rem}.hero h1{font-size:20px}.hero p{font-size:12px}.num{width:45px;height:45px;font-size:21px}.section-head .num{width:45px;height:45px;flex-basis:45px}.section-head h2{font-size:20px}.top-shell{padding:8px;border-radius:14px}.tripbar{padding-bottom:8px}.tripname{font-size:15px}.tripmeta{font-size:10px}.card{padding:11px}.mobile-bottom{display:block;position:fixed;left:7px;right:7px;bottom:7px;z-index:999;background:#061421f7;border:1px solid #17415d;border-radius:17px;padding:6px;box-shadow:0 8px 35px #000c}.mobile-bottom .stButton button{font-size:9px!important;min-height:42px!important;padding:2px!important;border:0!important;background:transparent!important}.mobile-bottom .stButton:nth-child(3) button{background:linear-gradient(145deg,#1474e5,#31caff)!important;border-radius:50%!important;font-size:22px!important}.desktop-only{display:none!important}
}
</style>
''',unsafe_allow_html=True)

# =========================
# SIDEBAR — matches mockup
# =========================
nav=[('⌂','Начало'),('♧','Пътувания'),('▣','Разходи'),('◫','Карта'),('▰','Автомобил'),('◈','Сравнение'),('◉','Бюджет'),('▤','Отчети'),('⚙','Настройки')]
with st.sidebar:
    st.markdown('<div class="brand"><span>🐾</span> PixelApp</div>',unsafe_allow_html=True)
    for ico,label in nav:
        active=st.session_state.page==label
        if st.button(f'{ico}   {label}',key='nav_'+label,use_container_width=True,type='primary' if active else 'secondary'):
            nav_to(label)
            st.rerun()

# mobile bottom
st.markdown('<div class="mobile-bottom">',unsafe_allow_html=True)
mc=st.columns(5)
for i,(ico,label) in enumerate([('⌂','Начало'),('▤','Разходи'),('＋','add'),('◫','Карта'),('•••','Още')]):
    with mc[i]:
        if st.button(ico,key=f'mob_{i}',use_container_width=True):
            if label=='add': choose_action('expense')
            elif label=='Начало': nav_to('Начало')
            elif label=='Разходи': nav_to('Разходи')
            elif label=='Карта': nav_to('Карта')
            else: nav_to('Още')
            st.rerun()
st.markdown('</div>',unsafe_allow_html=True)

# =========================
# WORKING ACTIONS
# =========================
if st.session_state.action:
    act=st.session_state.action
    with st.container(border=True):
        if act=='expense':
            st.subheader('➕ Добави разход')
            with st.form('add_expense_form',clear_on_submit=True):
                a,b,c=st.columns(3)
                with a: amount=st.number_input('Сума (€)',min_value=0.0,step=1.0)
                with b: category=st.selectbox('Категория',CATEGORIES)
                with c: date=st.date_input('Дата',datetime.date.today())
                description=st.text_input('Описание')
                x,y=st.columns(2)
                with x: ok=st.form_submit_button('💾 Запази разхода',use_container_width=True,type='primary')
                with y: cancel=st.form_submit_button('Отказ',use_container_width=True)
                if ok:
                    save_expense(amount,category,date,description)
                    st.rerun()
                if cancel:
                    st.session_state.action=None
                    st.rerun()
        elif act=='fuel':
            st.subheader('⛽ Добави зареждане')
            with st.form('add_fuel_form',clear_on_submit=True):
                a,b,c=st.columns(3)
                with a: litres=st.number_input('Литри',min_value=0.0,step=1.0)
                with b: price=st.number_input('Цена (€)',min_value=0.0,step=0.01)
                with c: km=st.number_input('Километри',min_value=0,step=1)
                if st.form_submit_button('💾 Запази зареждането',use_container_width=True,type='primary'):
                    row=pd.DataFrame([{'trip_id':tid,'date':datetime.date.today().strftime('%d.%m.%Y'),'amount':float(litres*price),'category':'Транспорт','description':f'Гориво — {litres:.2f} л @ {price:.2f} €','type':'fuel','km':int(km)}])
                    try:
                        old=pd.read_csv(DATA_FILE,encoding='utf-8'); out=pd.concat([old,row],ignore_index=True)
                    except Exception: out=row
                    out.to_csv(DATA_FILE,index=False,encoding='utf-8')
                    st.session_state.action=None; st.toast('Зареждането е добавено.',icon='⛽'); st.rerun()
        elif act=='deposit':
            st.subheader('▤ Добави депозит')
            with st.form('deposit_form'):
                dep=st.number_input('Сума (€)',min_value=0.0,step=10.0)
                note=st.text_input('Описание','Депозит')
                if st.form_submit_button('💾 Запази депозита',use_container_width=True,type='primary'):
                    row=pd.DataFrame([{'trip_id':tid,'date':datetime.date.today().strftime('%d.%m.%Y'),'amount':float(dep),'category':'Други','description':note,'type':'deposit'}])
                    try: old=pd.read_csv(DATA_FILE,encoding='utf-8'); out=pd.concat([old,row],ignore_index=True)
                    except Exception: out=row
                    out.to_csv(DATA_FILE,index=False,encoding='utf-8'); st.session_state.action=None; st.toast('Депозитът е добавен.',icon='✅'); st.rerun()
        elif act=='budget':
            st.subheader('✎ Редактирай бюджет')
            with st.form('budget_form'):
                vals={}
                cols=st.columns(len(CATEGORIES))
                for i,c in enumerate(CATEGORIES):
                    with cols[i]: vals[c]=st.number_input(c,value=float(b[c]),min_value=0.0,step=10.0,key='edit_'+c)
                x,y=st.columns(2)
                with x: ok=st.form_submit_button('💾 Запази бюджета',use_container_width=True,type='primary')
                with y: cancel=st.form_submit_button('Отказ',use_container_width=True)
                if ok: save_budget(vals); st.rerun()
                if cancel: st.session_state.action=None; st.rerun()

# =========================
# 1 — BUDGET + PROGRESS
# =========================
st.markdown('<div class="hero"><div class="num">1</div><div><h1>Бюджет на пътуването</h1><p>Планирай, следи и управлявай бюджета си в реално време.</p></div></div>',unsafe_allow_html=True)

st.markdown('<div class="top-shell">',unsafe_allow_html=True)
st.markdown(f'<div class="tripbar"><div><span class="flag">🇬🇷</span><span class="tripname">Пътуване: {trip_name}</span><div class="tripmeta">{period} ({days(tid)} дни)</div></div><div class="desktop-only"></div>',unsafe_allow_html=True)

c1,c2,c3=st.columns([1.05,1.15,.75],gap='small')
with c1:
    st.markdown('<div class="card"><h3>Бюджет</h3>',unsafe_allow_html=True)
    # donut via CSS/plotly
    fig=go.Figure(go.Pie(values=[min(spent,planned),max(0,planned-spent)],hole=.70,sort=False,marker=dict(colors=['#2ed8a4','#173247']),textinfo='none',hoverinfo='skip'))
    fig.update_layout(height=155,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor='rgba(0,0,0,0)',showlegend=False,annotations=[dict(text=f'<b>{pct:.0f}%</b><br><span style="font-size:10px">изразходван</span>',x=.5,y=.5,showarrow=False,font=dict(size=20,color='white'))])
    cc1,cc2=st.columns([.75,1])
    with cc1: st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='budget_donut')
    with cc2:
        st.markdown(f'<div class="kpi-label">Планиран бюджет</div><div class="kpi">{euro(planned)}</div><div class="kpi-label">Изразходвано</div><div class="kpi">{euro(spent)}</div><div class="kpi-label">Остават</div><div class="kpi green">{euro(remaining)}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="progress"><div style="width:{pct}%"></div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="alert">⚠️ <b>Внимание! Бюджетът е използван {pct:.0f}%.</b><br><span style="font-size:11px">При 80% ще получиш известие.</span></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card"><div style="display:flex;justify-content:space-between"><h3>Планиран vs. Реален</h3><div class="legend"><span class="dot blue"></span>Планиран &nbsp; <span class="dot green-dot"></span>Реален</div></div>',unsafe_allow_html=True)
    planned_vals=list(b.values()); real=[float(d[d.category==c].amount.sum()) if not d.empty else 0 for c in CATEGORIES]
    fig=go.Figure([go.Bar(name='Планиран',x=['Хотел','Храна','Транспорт','Куче','Други'],y=planned_vals,marker_color='#3b8ef3'),go.Bar(name='Реален',x=['Хотел','Храна','Транспорт','Куче','Други'],y=real,marker_color='#2ed8a4')])
    fig.update_layout(height=170,barmode='group',margin=dict(l=0,r=0,t=8,b=0),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#aac0d0',size=10),showlegend=False,xaxis=dict(gridcolor='#103047'),yaxis=dict(gridcolor='#103047'))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='budget_bars')
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="card" style="margin-top:8px"><h3>Разходи по категории</h3>',unsafe_allow_html=True)
    for i,c in enumerate(CATEGORIES):
        val=float(d[d.category==c].amount.sum()) if not d.empty else 0; p=(val/spent*100 if spent else 0)
        st.markdown(f'<div class="catrow"><div>{ICONS[c]}</div><div><b>{c}</b><div class="bar-mini"><div style="width:{p}%"></div></div></div><div>{euro(val)}</div><div class="pct">{p:.0f}%</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card"><h3>Бързи действия</h3>',unsafe_allow_html=True)
    qa=[('Добави разход','＋','expense'),('Добави зареждане','⛽','fuel'),('Добави депозит','▤','deposit'),('Редактирай бюджет','✎','budget')]
    for txt,ico,act in qa:
        if st.button(f'{ico}  {txt}   ›',key='quick_'+act,use_container_width=True):
            choose_action(act); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="card" style="margin-top:8px"><h3>Предупреждения</h3>',unsafe_allow_html=True)
    st.markdown(f'<div class="alert">⚠️ &nbsp; Бюджетът е използван {pct:.0f}%.</div><div class="info" style="margin-top:8px">ℹ️ &nbsp; Оставащ бюджет: <b>{euro(remaining)}</b></div><div class="info" style="margin-top:8px;color:#58e1b2">✓ &nbsp; Няма неплатени депозити.</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# =========================
# 2 — DAILY EXPENSE
# =========================
st.markdown('<div class="section-head"><div class="num">2</div><div><h2>Разход на ден</h2><p>Виж колко харчиш всеки ден и следи тенденциите.</p></div></div>',unsafe_allow_html=True)

st.markdown('<div class="top-shell">',unsafe_allow_html=True)
left,right=st.columns([1.15,1.0],gap='small')
with left:
    st.markdown('<div class="card"><h3>Разход на ден</h3>',unsafe_allow_html=True)
    avg=spent/days(tid) if days(tid) else 0; today=float(daily.amount.iloc[-1]) if len(daily) else 0; yesterday=float(daily.amount.iloc[-2]) if len(daily)>1 else 0
    m=st.columns(4)
    for col,label,val,delta,cls in [(m[0],'Дневен разход (средно)',avg,'↓ -12%','down'),(m[1],'Днес',today,'↑ +18%','up'),(m[2],'Вчера',yesterday,'↓ -8%','down'),(m[3],'Общо разходи',spent,f'{days(tid)} дни','')]:
        with col: st.markdown(f'<div class="metricbox"><div class="l">{label}</div><div class="v">{euro(val)}</div><div class="{cls}">{delta}</div></div>',unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top:14px">Разходи по дни</h3>',unsafe_allow_html=True)
    fig=go.Figure(go.Bar(x=[f'Ден {i+1}' for i in range(len(daily))],y=daily.amount,marker_color='#1dbdcf',text=[f'{x:.0f} €' for x in daily.amount],textposition='outside'))
    fig.update_layout(height=220,margin=dict(l=0,r=0,t=18,b=0),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#9eb8c9',size=9),yaxis=dict(gridcolor='#103047'),xaxis=dict(gridcolor='#103047'))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='daily_bar')
    st.markdown('</div>',unsafe_allow_html=True)
with right:
    st.markdown('<div class="card"><h3>Разходи по дни (детайлни)</h3>',unsafe_allow_html=True)
    for i,row in d.reset_index(drop=True).iterrows(): st.markdown(f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0c2a3c;font-size:11px"><span>Ден {i+1} ({row.date})</span><b>{euro(row.amount)}</b></div>',unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;justify-content:space-between;padding-top:10px;font-weight:700;color:#fff">Общо <span>{euro(spent)}</span></div></div>',unsafe_allow_html=True)
    hi=daily.amount.max() if len(daily) else 0; lo=daily.amount.min() if len(daily) else 0
    st.markdown(f'<div style="display:flex;gap:8px;margin-top:8px"><div class="metricbox" style="flex:1"><div class="l">Най-скъп ден</div><div class="v">{euro(hi)}</div></div><div class="metricbox" style="flex:1"><div class="l">Най-евтин ден</div><div class="v">{euro(lo)}</div></div></div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# =========================
# 5 — HISTORY + RANKINGS
# =========================
st.markdown('<div class="section-head"><div class="num">5</div><div><h2>Най-доброто ти пътуване / класации</h2><p>Открий кои пътувания са най-изгодни, най-дълги и кои ти носят най-много спомени.</p></div></div>',unsafe_allow_html=True)
st.markdown('<div class="top-shell">',unsafe_allow_html=True)
rc1,rc2=st.columns([1.15,.9],gap='small')
with rc1:
    st.markdown('<div class="card"><h3>Сравнение / класации</h3>',unsafe_allow_html=True)
    pm=st.columns(5)
    for i,mode in enumerate(['Общо','Цена/км','Километри','Разход на ден','Хотел/Нощувки']):
        with pm[i]:
            if st.button(mode,key='rank_'+str(i),use_container_width=True,type='primary' if st.session_state.rank_mode==mode else 'secondary'):
                st.session_state.rank_mode=mode; st.rerun()
    st.markdown('<h3>Топ 6 класации</h3>',unsafe_allow_html=True)
    ranks=[('🏆','Най-евтино пътуване','Румъния 2025','62.40 €/ден','#ffbd37'),('🌿','Най-икономично пътуване','Гърция 2026','6.2 л/100 км','#35d9a5'),('🔗','Най-дълго пътуване','Италия 2024','2 845 км','#4d9eff'),('🏨','Най-скъп хотел','Испания 2025','158.00 €/нощувка','#b35cff'),('🍴','Най-много за храна','Гърция 2026','312.40 €','#ff8c38'),('★','Най-добро съотношение','Румъния 2025','86.20 €/ден','#ff5f9a')]
    cols=st.columns(2)
    for i,r in enumerate(ranks):
        with cols[i%2]: st.markdown(f'<div class="rank" style="margin-bottom:8px"><div class="r-icon">{r[0]}</div><div><div class="r-title" style="color:{r[4]}">{r[1]}</div><div class="r-name">{r[2]}</div><div class="r-value">{r[3]}</div></div></div>',unsafe_allow_html=True)
    
    if st.button('↗  Виж всички класации',key='all_rankings',use_container_width=True):
        st.session_state.page='Сравнение'; st.toast('Отворени са всички класации.',icon='🏆')

    st.markdown('</div>',unsafe_allow_html=True)
with rc2:
    st.markdown('<div class="card"><h3>Сравнение на пътуванията</h3>',unsafe_allow_html=True)
    rows=[('🇬🇷','Гърция 2026','15.08 – 22.08.2026','1 247','1 284.50 €','1.03 €','94.20 €'),('🇷🇴','Румъния 2025','10.07 – 14.07.2025','2 845','2 892.30 €','1.02 €','96.40 €'),('🇮🇹','Италия 2024','01.06 – 12.06.2024','2 198','1 854.70 €','0.84 €','154.56 €'),('🇬🇷','Гърция 2023','20.08 – 28.08.2023','1 356','1 023.80 €','0.75 €','113.76 €')]
    html='<table class="table"><tr><th>Пътуване</th><th>Период</th><th>км</th><th>Общо</th><th>€/км</th><th>Разход/ден</th></tr>'
    for r in rows: html+=f'<tr><td>{r[0]} {r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td></tr>'
    html+='</table>'
    st.markdown(html,unsafe_allow_html=True)
    
    if st.button('▥  Пълно сравнение',key='full_compare',use_container_width=True):
        st.session_state.page='Сравнение'; st.toast('Отворено е пълното сравнение.',icon='📊')

    st.markdown('</div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

# =========================
# BUDGET CATEGORY EDITOR — mobile screenshot section
# =========================
st.markdown('<div class="section-head" style="margin-top:18px"><div class="num">3</div><div><h2>Планиран бюджет по категории</h2><p>Бързо редактиране на лимитите по категории.</p></div></div>',unsafe_allow_html=True)
st.markdown('<div class="top-shell">',unsafe_allow_html=True)
for c in CATEGORIES:
    real=float(d[d.category==c].amount.sum()) if not d.empty else 0; planned_c=b[c]; used=real/planned_c*100 if planned_c else 0
    st.markdown(f'<div class="card" style="margin-bottom:7px;padding:10px 12px"><div style="display:flex;justify-content:space-between;align-items:center"><div><span style="font-size:18px">{ICONS[c]}</span> <b>{c}</b></div><span class="muted">{euro(planned_c)}</span></div><div style="display:flex;justify-content:space-between;font-size:10px;color:#8daabd;margin-top:7px"><span>{euro(real)} изразходвани</span><b>{used:.0f}%</b></div><div class="progress" style="height:6px;margin:4px 0 0"><div style="width:{min(100,used)}%"></div></div></div>',unsafe_allow_html=True)
    if st.button(f'✎  Редактирай {c}',key='edit_cat_'+c,use_container_width=True):
        choose_action('budget'); st.rerun()
st.markdown(f'<div class="card" style="display:flex;justify-content:space-between"><div><div class="muted">Общо</div><b style="font-size:20px">{euro(planned)}</b></div><div><div class="muted">Изразходвано</div><b style="font-size:20px">{euro(spent)}</b></div><div><div class="muted">Остават</div><b style="font-size:20px;color:#39dca6">{euro(remaining)}</b></div></div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

st.markdown('<div class="bottomspace"></div>',unsafe_allow_html=True)
