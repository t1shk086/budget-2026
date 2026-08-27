import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io
import html
import streamlit.components.v1 as components

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

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

/* Единен шрифт за целия интерфейс */
html, body, [data-testid="stAppViewContainer"] {
    font-family: "Segoe UI", Roboto, sans-serif !important;
}

        /* Финална визия на картите: една карта = един бутон, текстът вляво. */
        div[class*="st-key-trip_card_"] { position:relative; margin-bottom:8px; }
        div[class*="st-key-trip_card_"] .tm-trip-card-visual {
            box-sizing:border-box; min-height:108px; padding:13px 16px 13px;
            border-radius:16px; border:1px solid rgba(255,255,255,.08);
            background:linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
            box-shadow:4px 4px 12px rgba(0,0,0,.24); color:#fff; text-align:left;
        }
        div[class*="st-key-trip_card_"] .tm-trip-card-title {
            display:flex; align-items:center; justify-content:space-between; width:100%;
            font-size:14px; line-height:1.35; font-weight:800; text-align:left;
        }
        div[class*="st-key-trip_card_"] .tm-trip-arrow { margin-left:auto; padding-left:10px; opacity:.85; }
        div[class*="st-key-trip_card_"] .tm-trip-card-status {
            margin-top:3px; font-size:12px; line-height:1.3; font-weight:700; text-align:left;
        }
        div[class*="st-key-trip_card_"] .tm-trip-card-budget { margin-top:7px; }
        div[class*="st-key-trip_card_"] .tm-trip-card-budget-text {
            margin-bottom:4px; font-size:11px; line-height:1.25; font-weight:800;
            color:rgba(255,255,255,.88); text-align:left;
        }
        div[class*="st-key-trip_card_"] .tm-trip-card-budget-track {
            width:100%; height:12px; padding:2px; box-sizing:border-box; overflow:hidden;
            border-radius:20px; background:rgba(0,0,0,.42);
            box-shadow:inset 2px 2px 5px rgba(0,0,0,.45);
        }
        div[class*="st-key-trip_card_"] .tm-trip-card-budget-fill {
            height:100%; border-radius:20px;
            background:linear-gradient(90deg,#4facfe 0%,#00f2fe 100%);
            box-shadow:inset 0 2px 2px rgba(255,255,255,.25);
        }
        @media(max-width:640px){
            div[class*="st-key-trip_card_"] .tm-trip-card-visual { min-height:102px; padding:12px 14px; }
            div[class*="st-key-trip_card_"] div[data-testid="stButton"] button { min-height:102px !important; }
        }

        /* No-budget card: keep it clean and compact. */
        div[class*="st-key-trip_card_"] .tm-trip-card-budget-text {
            text-align:left !important;
        }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"
TRIP_PLAN_FILE = "trip_plan_2026.csv"

DEFAULT_UI_LABELS = {
    "pet": "Куче",
    "hotel": "Нощувки/Хотел",
    "deposit": "Депозит/Резервация",
    "fuel_red_threshold": 1.80
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

def save_ui_labels(pet_label, hotel_label, deposit_label, fuel_red_threshold=1.80):
    try:
        try:
            fuel_red_threshold = float(fuel_red_threshold)
        except (TypeError, ValueError):
            fuel_red_threshold = 1.80
        fuel_red_threshold = max(0.01, fuel_red_threshold)
        pd.DataFrame([{
            "pet": pet_label,
            "hotel": hotel_label,
            "deposit": deposit_label,
            "fuel_red_threshold": fuel_red_threshold
        }]).to_csv(LABELS_FILE, index=False, encoding="utf-8")
        return True
    except:
        return False

UI_LABELS = get_ui_labels()

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

if not os.path.exists(TRIP_PLAN_FILE):
    pd.DataFrame(columns=["trip_id", "item_id", "title", "done", "created"]).to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")

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

CATEGORY_BUDGETS_FILE = "trip_category_budgets_2026.csv"

def get_category_budgets(t_id):
    result = {cat: 0.0 for cat in KATEGORII if cat != "Депозит/Резервация"}
    try:
        if not os.path.exists(CATEGORY_BUDGETS_FILE):
            return result
        df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
        if df.empty or not {"trip_id", "category", "budget"}.issubset(df.columns):
            return result
        rows = df[df["trip_id"].astype(str) == str(t_id)]
        for _, row in rows.iterrows():
            cat = str(row["category"])
            if cat in result:
                try:
                    result[cat] = max(0.0, float(row["budget"]))
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    return result

def get_global_budget(t_id):
    try:
        if not os.path.exists(CATEGORY_BUDGETS_FILE):
            return 0.0
        df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
        if df.empty or not {"trip_id", "category", "budget"}.issubset(df.columns):
            return 0.0
        rows = df[(df["trip_id"].astype(str) == str(t_id)) & (df["category"].astype(str) == "__GLOBAL__")]
        if rows.empty:
            return 0.0
        return max(0.0, float(rows.iloc[0]["budget"]))
    except Exception:
        return 0.0

def save_budget_config(t_id, mode, total_amount=None, budgets=None):
    try:
        columns = ["trip_id", "category", "budget"]
        if os.path.exists(CATEGORY_BUDGETS_FILE):
            df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
            if not set(columns).issubset(df.columns):
                df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(columns=columns)

        df = df[df["trip_id"].astype(str) != str(t_id)]
        new_rows = []

        if mode == "global":
            try:
                amount = float(total_amount) if total_amount is not None else 0.0
            except (TypeError, ValueError):
                amount = 0.0

            if amount <= 0:
                return False

            new_rows.append({
                "trip_id": str(t_id),
                "category": "__GLOBAL__",
                "budget": amount
            })

        elif mode == "category":
            budgets = budgets or {}
            for cat in KATEGORII:
                if cat == "Депозит/Резервация":
                    continue
                raw_value = budgets.get(cat)
                try:
                    amount = float(raw_value) if raw_value is not None else 0.0
                except (TypeError, ValueError):
                    amount = 0.0

                if amount > 0:
                    new_rows.append({
                        "trip_id": str(t_id),
                        "category": cat,
                        "budget": amount
                    })
        else:
            return False

        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        tmp_file = CATEGORY_BUDGETS_FILE + ".tmp"
        df.to_csv(tmp_file, index=False, encoding="utf-8")
        os.replace(tmp_file, CATEGORY_BUDGETS_FILE)
        return True

    except Exception:
        try:
            if os.path.exists(CATEGORY_BUDGETS_FILE + ".tmp"):
                os.remove(CATEGORY_BUDGETS_FILE + ".tmp")
        except:
            pass
        return False

def get_trip_plan(t_id):
    try:
        if not os.path.exists(TRIP_PLAN_FILE):
            return pd.DataFrame(columns=["trip_id", "item_id", "title", "done", "created"])
        df = pd.read_csv(TRIP_PLAN_FILE, encoding="utf-8")
        if df.empty:
            return df
        df = df[df["trip_id"].astype(str) == str(t_id)].copy()
        if "done" not in df.columns:
            df["done"] = False
        df["done"] = df["done"].astype(str).str.lower().isin(["true", "1", "yes", "да"])
        return df
    except Exception:
        return pd.DataFrame(columns=["trip_id", "item_id", "title", "done", "created"])

def add_trip_plan_item(t_id, title):
    try:
        if not title.strip():
            return False
        df = pd.read_csv(TRIP_PLAN_FILE, encoding="utf-8")
        if df.empty:
            df = pd.DataFrame(columns=["trip_id", "item_id", "title", "done", "created"])
        new_id = f"{t_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        row = {"trip_id": str(t_id), "item_id": new_id, "title": title.strip(), "done": False, "created": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def update_trip_plan(df_plan):
    try:
        df_plan.to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def delete_trip_plan_item(item_id):
    try:
        df = pd.read_csv(TRIP_PLAN_FILE, encoding="utf-8")
        df = df[df["item_id"].astype(str) != str(item_id)]
        df.to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")
        return True
    except Exception:
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

def _navigate_fuel(direction, trip_id):
    try:
        df_nav = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_nav = df_nav[(df_nav["trip_id"] == trip_id) & (df_nav["category"] == "Транспорт")].copy()
        manual_mask = df_nav["description"].astype(str).str.contains(
            r"(?:\[ПРОПУСНАТО\s+ГОРИВО\]|\[ГОРИВО\s+БЕЗ\s+СТОЙНОСТ\])", case=False, regex=True, na=False
        )
        fuel_mask = df_nav["liters"].fillna(0).astype(float).gt(0) | manual_mask
        rows = df_nav[fuel_mask]
        count = len(rows)
        if count <= 1:
            return

        key = f"fuel_history_index_{trip_id}"
        current = int(st.session_state.get(key, 0) or 0)
        current = max(0, min(current, count - 1))

        if direction == "prev":
            st.session_state[key] = min(count - 1, current + 1)
        else:
            st.session_state[key] = max(0, current - 1)
    except Exception:
        pass

def _toggle_plan_item(item_id):
    try:
        df_plan = pd.read_csv(TRIP_PLAN_FILE, encoding="utf-8")
        mask = df_plan["item_id"].astype(str) == str(item_id)
        if mask.any():
            current = bool(df_plan.loc[mask, "done"].iloc[0])
            df_plan.loc[mask, "done"] = not current
            update_trip_plan(df_plan)
    except Exception:
        pass

def _delete_plan_item(item_id):
    try:
        delete_trip_plan_item(str(item_id))
    except Exception:
        pass

def _add_plan_item_and_clear(t_id, widget_key):
    try:
        cleaned = str(st.session_state.get(widget_key, "") or "").strip()
        if not cleaned:
            return
        if add_trip_plan_item(t_id, cleaned):
            st.session_state[widget_key] = ""
    except Exception:
        pass

if "open_quick_expense" not in st.session_state:
    st.session_state["open_quick_expense"] = False

# =========================================================
# 1. НАЧАЛЕН ЕКРАН (СПИСЪК С ПЪТУВАНИЯ)
# =========================================================
if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: -8px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)

    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]

    st.markdown("""
    <style>
        .tm-home-action-space { margin-top: 2px; margin-bottom: 8px; }
        .tm-home-trips-title {
            color:#8b929e;
            font-size:12px;
            font-weight:800;
            letter-spacing:1px;
            margin:18px 0 9px 2px;
        }
        .tm-trip-card-wrap { margin-bottom:8px; }
        .tm-trip-budget-mini { margin-top:7px; }
        .tm-trip-budget-track { position:relative; height:12px; border-radius:20px; background:rgba(0,0,0,.42); padding:2px; overflow:hidden; box-shadow:inset 2px 2px 5px rgba(0,0,0,.45); }
        .tm-trip-budget-fill { height:100%; border-radius:20px; background:linear-gradient(90deg,#4facfe 0%,#00f2fe 100%); box-shadow:inset 0 2px 2px rgba(255,255,255,.25); }
        .tm-trip-budget-percent { position:absolute; right:6px; top:0; line-height:12px; font-size:8px; font-weight:900; color:rgba(255,255,255,.9); text-shadow:1px 1px 2px rgba(0,0,0,.8); }

        div[class*="st-key-trip_card_"] button {
            min-height:92px !important;
            padding:14px 16px !important;
            border-radius:16px !important;
            border:1px solid rgba(255,255,255,.08) !important;
            background:linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,.012)) !important;
            box-shadow:4px 4px 12px rgba(0,0,0,.24) !important;
            color:#fff !important;
            font-family:inherit !important;
            text-align:left !important;
            justify-content:flex-start !important;
            align-items:flex-start !important;
            white-space:pre-wrap !important;
            transition:all .2s ease !important;
        }
        div[class*="st-key-trip_card_"] button:hover {
            background:linear-gradient(135deg,rgba(255,255,255,.055),rgba(255,255,255,.018)) !important;
            border-color:rgba(0,242,254,.22) !important;
            box-shadow:4px 6px 16px rgba(0,0,0,.30),0 0 14px rgba(0,242,254,.05) !important;
            transform:translateY(-1px) !important;
        }
        div[class*="st-key-trip_card_"] button p {
            font-size:14px !important;
            line-height:1.45 !important;
            margin:0 !important;
        }
        @media(max-width:640px){
            div[class*="st-key-trip_card_"] button {
                min-height:88px !important;
                padding:13px 14px !important;
            }
        }

        div[class*="st-key-trip_card_"] div[data-testid="stButton"] > div {
            width:100% !important;
        }
        div[class*="st-key-trip_card_"] div[data-testid="stButton"] button {
            display:flex !important;
            flex-direction:row !important;
            align-items:flex-start !important;
            justify-content:flex-start !important;
            text-align:left !important;
        }
        div[class*="st-key-trip_card_"] div[data-testid="stButton"] button > div {
            width:100% !important;
            display:block !important;
            text-align:left !important;
        }
        div[class*="st-key-trip_card_"] div[data-testid="stButton"] button > div > div {
            width:100% !important;
            display:block !important;
            text-align:left !important;
        }
        div[class*="st-key-trip_card_"] div[data-testid="stButton"] button p {
            width:100% !important;
            display:block !important;
            margin:0 !important;
            padding:0 !important;
            text-align:left !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if st.button("➕  БЪРЗ РАЗХОД", use_container_width=True, type="primary", key="quick_expense_top_btn"):
        st.session_state["open_quick_expense"] = True
        st.rerun()

    @st.dialog("Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:",placeholder="Въведете име...").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---")
        st.write("🚗 Пътувате ли със собствен автомобил?")
        viber_car = st.radio("Изберете вариант:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        if st.button("✔️ Създай и Отвори", use_container_width=True, type="primary") and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"):
                s_d_str = d_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
            try:
                geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
                location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
                if location:
                    add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except:
                pass
            st.session_state["current_trip"] = target_id
            st.rerun()

    if st.button("✈️  НОВО ПЪТУВАНЕ", use_container_width=True, key="new_trip_home_btn"):
        create_trip_modal()

    if existing:
        st.markdown("<div class='tm-home-trips-title'>МОИТЕ ПЪТУВАНИЯ</div>", unsafe_allow_html=True)

        for _trip in existing:
            _trip_id = str(_trip)
            _trip_name = _trip_id.replace("_", " ")
            _settings = get_trip_settings(_trip_id)
            _finished = float(_settings.get("end_km", 0.0) or 0.0) > 0.0

            _status_dot = "🟢" if not _finished else "🔴"
            _status_text = "Активно" if not _finished else "Приключено"

            _df_home_trip = get_trip_data(_trip_id)

            _global = float(get_global_budget(_trip_id) or 0.0)
            _cat_budgets = get_category_budgets(_trip_id)
            _category_total = sum(
                float(v or 0.0)
                for v in _cat_budgets.values()
                if float(v or 0.0) > 0
            )

            if _global > 0:
                _budget_mode = "global"
                _budget = _global
            elif _category_total > 0:
                _budget_mode = "category"
                _budget = _category_total
            else:
                _budget_mode = "none"
                _budget = 0.0

            try:
                _spent = 0.0

                if not _df_home_trip.empty and "amount" in _df_home_trip.columns:
                    _type = (
                        _df_home_trip["type"].astype(str).str.strip().str.lower()
                        if "type" in _df_home_trip.columns
                        else pd.Series(["expense"] * len(_df_home_trip), index=_df_home_trip.index)
                    )

                    if _budget_mode == "global":
                        _spent = float(
                            _df_home_trip.loc[_type.isin(["expense", "deposit"]), "amount"]
                            .fillna(0)
                            .sum()
                        )

                    elif _budget_mode == "category":
                        _budgeted_categories = {
                            str(cat)
                            for cat, val in _cat_budgets.items()
                            if float(val or 0.0) > 0
                        }

                        _expense_rows = _df_home_trip.loc[
                            _type == "expense"
                        ].copy()

                        if "category" in _expense_rows.columns and not _expense_rows.empty:
                            _expense_rows["category_clean"] = _expense_rows["category"].astype(str).str.strip()
                            _spent_exp = float(
                                _expense_rows.loc[
                                    _expense_rows["category_clean"].isin(_budgeted_categories), "amount"
                                ]
                                .fillna(0)
                                .sum()
                            )
                        else:
                            _spent_exp = 0.0

                        _spent_dep = 0.0
                        if "Нощувки/Хотел" in _budgeted_categories:
                            _dep_rows = _df_home_trip.loc[_type == "deposit"].copy()
                            _spent_dep = float(_dep_rows["amount"].fillna(0).sum()) if not _dep_rows.empty else 0.0

                        _spent = _spent_exp + _spent_dep

                    else:
                        _spent = float(
                            _df_home_trip.loc[_type.isin(["expense", "deposit"]), "amount"]
                            .fillna(0)
                            .sum()
                        )
            except Exception:
                _spent = 0.0

            if _budget > 0:
                _pct = min(100.0, max(0.0, (_spent / _budget) * 100))
                _budget_line = f"💰 {_spent:,.2f} лв. от {_budget:,.2f} лв. ({_pct:.1f}%)"
            else:
                _budget_line = f"💰 Похарчени: {_spent:,.2f} лв."

            _card_text = f"📍  {_trip_name}\n{_status_dot}  {_status_text}   •   {_budget_line}"

            if st.button(_card_text, key=f"trip_card_{_trip_id}", use_container_width=True):
                st.session_state["current_trip"] = _trip_id
                st.rerun()

    # Диалог за Бърз разход
    if st.session_state.get("open_quick_expense", False):
        @st.dialog("➕ Бърз разход")
        def quick_expense_modal():
            if not existing:
                st.warning("Все още нямате създадени пътувания. Първо създайте пътуване.")
                if st.button("Затвори", use_container_width=True):
                    st.session_state["open_quick_expense"] = False
                    st.rerun()
                return

            selected_trip = st.selectbox("Изберете пътуване:", existing, format_func=lambda x: x.replace("_", " "))
            q_amt = st.number_input("Сума (лв.):", min_value=0.01, step=1.0, value=None, placeholder="0.00")
            q_cat_disp = st.selectbox("Категория:", [get_display_category(c) for c in KATEGORII])
            
            disp_to_canon = {get_display_category(c): c for c in KATEGORII}
            q_cat = disp_to_canon.get(q_cat_disp, q_cat_disp)
            
            q_desc = st.text_input("Описание (по желание):", placeholder="напр. Кафе, Закуска...")
            
            q_is_dep = False
            if q_cat == "Депозит/Резервация":
                q_is_dep = True

            q_liters = 0.0
            q_km = 0.0
            if q_cat == "Транспорт":
                q_liters = st.number_input("Литри гориво (ако е зареждане):", min_value=0.0, step=0.1, value=0.0)
                q_km = st.number_input("Текущи км по километраж (по желание):", min_value=0.0, step=1.0, value=0.0)

            c1, c2 = st.columns(2)
            if c1.button("Запази", type="primary", use_container_width=True):
                if q_amt and q_amt > 0:
                    if add_expense(selected_trip, q_amt, q_cat, q_desc, is_dep=q_is_dep, lit=q_liters, c_km=q_km):
                        st.success("Разходът е добавен!")
                        st.session_state["open_quick_expense"] = False
                        st.rerun()
                    else:
                        st.error("Грешка при запис.")
                else:
                    st.error("Моля въведете валидна сума.")
            if c2.button("Отказ", use_container_width=True):
                st.session_state["open_quick_expense"] = False
                st.rerun()

        quick_expense_modal()

# =========================================================
# 2. ЕКРАН НА АКТИВНО ПЪТУВАНЕ
# =========================================================
else:
    current_trip = st.session_state["current_trip"]
    trip_title = current_trip.replace("_", " ")

    col_back, col_title = st.columns([1, 4])
    if col_back.button("⬅️ Назад"):
        st.session_state["current_trip"] = None
        st.rerun()
    col_title.markdown(f"<h2 style='margin:0; padding:0; font-size: 24px;'>📍 {trip_title}</h2>", unsafe_allow_html=True)

    settings = get_trip_settings(current_trip)
    
    # Табове на приложението
    tab_expenses, tab_stats, tab_budget, tab_map, tab_plan, tab_settings = st.tabs([
        "💸 Разходи", "📊 Профил & Анализ", "🎯 Бюджет", "🗺️ Маршрут & Карта", "📋 Чеклист", "⚙️ Настройки"
    ])

    # ---------------------------------------------------------
    # ТАБ 1: РАЗХОДИ
    # ---------------------------------------------------------
    with tab_expenses:
        st.subheader("Добавяне на нов разход")
        with st.form(key=f"add_expense_form_{st.session_state['form_version']}"):
            f_amt = st.number_input("Сума (лв.):", min_value=0.01, step=1.0, value=None, placeholder="0.00")
            f_cat_disp = st.selectbox("Категория:", [get_display_category(c) for c in KATEGORII])
            disp_to_canon = {get_display_category(c): c for c in KATEGORII}
            f_cat = disp_to_canon.get(f_cat_disp, f_cat_disp)

            f_desc = st.text_input("Описание:", placeholder="Детайли за разхода...")
            
            f_is_dep = (f_cat == "Депозит/Резервация")

            f_liters = 0.0
            f_km = 0.0
            if f_cat == "Транспорт":
                f_liters = st.number_input("Литри (ако е гориво):", min_value=0.0, step=0.1, value=0.0)
                f_km = st.number_input("Километраж в момента (км):", min_value=0.0, step=1.0, value=0.0)

            btn_submit = st.form_submit_button("➕ Добави разход", type="primary", use_container_width=True)
            if btn_submit:
                if f_amt and f_amt > 0:
                    if add_expense(current_trip, f_amt, f_cat, f_desc, is_dep=f_is_dep, lit=f_liters, c_km=f_km):
                        st.success("Разходът бе добавен успешно!")
                        st.session_state["form_version"] += 1
                        st.rerun()
                    else:
                        st.error("Грешка при записа.")
                else:
                    st.error("Въведете сума.")

        st.write("---")
        st.subheader("История на разходите")
        df_exp = get_trip_data(current_trip)

        if not df_exp.empty:
            # Преобразуване за дисплей
            df_display = df_exp.copy()
            df_display["Категория"] = df_display["category"].apply(get_display_category)
            df_display["Емоджи"] = df_display["category"].apply(get_emoji)
            df_display["Сума"] = df_display["amount"].apply(lambda x: f"{x:,.2f} лв.")
            
            # Показваме най-новите разходи най-отгоре
            df_display = df_display.iloc[::-1]

            for idx, row in df_display.iterrows():
                with st.container():
                    c_icon, c_info, c_del = st.columns([1, 4, 1])
                    c_icon.markdown(f"<h3 style='text-align:center;'>{row['Емоджи']}</h3>", unsafe_allow_html=True)
                    
                    sub_txt = f"{row['date']} • {row['description']}"
                    if row['liters'] > 0:
                        sub_txt += f" • {row['liters']}л"
                    if row['current_km'] > 0:
                        sub_txt += f" • {row['current_km']}км"

                    c_info.markdown(f"**{row['Категория']}** - **{row['Сума']}**\n\n<small>{sub_txt}</small>", unsafe_allow_html=True)

                    if c_del.button("🗑️", key=f"del_exp_{idx}"):
                        try:
                            df_full = pd.read_csv(DATA_FILE, encoding="utf-8")
                            df_full = df_full.drop(idx)
                            df_full.to_csv(DATA_FILE, index=False, encoding="utf-8")
                            st.rerun()
                        except:
                            st.error("Грешка при изтриването.")
                st.write("<hr style='margin: 4px 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.info("Няма регистрирани разходи за това пътуване.")

    # ---------------------------------------------------------
    # ТАБ 2: ПРОФИЛ & АНАЛИЗ
    # ---------------------------------------------------------
    with tab_stats:
        st.subheader("📊 Анализ на пътуването")
        df_exp = get_trip_data(current_trip)

        if not df_exp.empty:
            tot_exp = df_exp[df_exp["type"] == "expense"]["amount"].sum()
            tot_dep = df_exp[df_exp["type"] == "deposit"]["amount"].sum()
            tot_all = tot_exp + tot_dep

            m1, m2, m3 = st.columns(3)
            m1.metric("Общо похарчени", f"{tot_all:,.2f} лв.")
            m2.metric("Преки разходи", f"{tot_exp:,.2f} лв.")
            m3.metric("Депозити", f"{tot_dep:,.2f} лв.")

            st.write("---")
            st.write("##### Разходи по категории")
            cat_summary = df_exp.groupby("category")["amount"].sum().reset_index()
            cat_summary["Визуална категория"] = cat_summary["category"].apply(get_display_category)
            cat_summary["Икона"] = cat_summary["category"].apply(get_emoji)

            for _, r in cat_summary.iterrows():
                pct = (r["amount"] / tot_all) * 100 if tot_all > 0 else 0
                st.write(f"{r['Икона']} **{r['Визуална категория']}**: {r['amount']:,.2f} лв. ({pct:.1f}%)")
                st.progress(min(1.0, pct / 100.0))

            # Автомобилен анализ ако е зададено пътуване с кола
            if settings.get("car_trip") == "Да":
                st.write("---")
                st.subheader("🚗 Автомобилен модул & Гориво")
                
                df_fuel = df_exp[(df_exp["category"] == "Транспорт") & (df_exp["liters"] > 0)].sort_values(by="current_km")
                start_km = settings.get("start_km", 0.0)
                end_km = settings.get("end_km", 0.0)

                if not df_fuel.empty or start_km > 0:
                    max_km = df_fuel["current_km"].max() if not df_fuel.empty else start_km
                    if end_km > 0: max_km = max(max_km, end_km)
                    
                    dist_driven = max(0.0, max_km - start_km) if start_km > 0 else 0.0
                    tot_liters = df_fuel["liters"].sum()
                    
                    fc1, fc2, fc3 = st.columns(3)
                    fc1.metric("Изминати км", f"{dist_driven:,.1f} км")
                    fc2.metric("Общо гориво", f"{tot_liters:,.1f} л")
                    
                    avg_con = (tot_liters / dist_driven * 100) if dist_driven > 0 and tot_liters > 0 else 0.0
                    fc3.metric("Ср. разход", f"{avg_con:.2f} л/100км" if avg_con > 0 else "N/A")

        else:
            st.info("Добавете разходи, за да видите статистиките.")

    # ---------------------------------------------------------
    # ТАБ 3: БЮДЖЕТ
    # ---------------------------------------------------------
    with tab_budget:
        st.subheader("🎯 Бюджетни настройки и дневни лимити")
        
        curr_global = get_global_budget(current_trip)
        curr_cats = get_category_budgets(current_trip)

        mode_option = st.radio("Изберете тип бюджет:", ["Без бюджет", "Общ глобален бюджет", "Бюджет по категории"], 
                               index=1 if curr_global > 0 else (2 if sum(curr_cats.values()) > 0 else 0))

        if mode_option == "Общ глобален бюджет":
            new_g = st.number_input("Общ бюджет (лв.):", min_value=0.0, value=float(curr_global), step=50.0)
            if st.button("Запази глобален бюджет", type="primary"):
                if save_budget_config(current_trip, mode="global", total_amount=new_g):
                    st.success("Глобалният бюджет е обновен!")
                    st.rerun()

        elif mode_option == "Бюджет по категории":
            new_cat_budgets = {}
            for cat in KATEGORII:
                if cat == "Депозит/Резервация": continue
                disp_name = get_display_category(cat)
                val = curr_cats.get(cat, 0.0)
                new_cat_budgets[cat] = st.number_input(f"Бюджет за {disp_name} (лв.):", min_value=0.0, value=float(val), step=10.0, key=f"b_in_{cat}")

            if st.button("Запази бюджети по категории", type="primary"):
                if save_budget_config(current_trip, mode="category", budgets=new_cat_budgets):
                    st.success("Бюджетите по категории са обновени!")
                    st.rerun()

        elif mode_option == "Без бюджет":
            if st.button("Изчисти всички бюджети"):
                save_budget_config(current_trip, mode="none")
                st.success("Бюджетите са премахнати.")
                st.rerun()

    # ---------------------------------------------------------
    # ТАБ 4: МАРШРУТ & КАРТА
    # ---------------------------------------------------------
    with tab_map:
        st.subheader("🗺️ Карта на дестинацията & Точки")
        
        # Добавяне на нова точка
        with st.expander("➕ Добави нова точка на картата"):
            mp_title = st.text_input("Име на мястото:", placeholder="напр. Хотел, Ресторант...")
            mp_lat = st.number_input("Ширина (Latitude):", format="%.6f", value=0.0)
            mp_lon = st.number_input("Дължина (Longitude):", format="%.6f", value=0.0)
            mp_color = st.selectbox("Цвят на маркера:", ["blue", "red", "green", "purple", "orange"])

            if st.button("Запази точката") and mp_title and mp_lat != 0:
                if add_map_point(current_trip, mp_lat, mp_lon, mp_title, mp_color):
                    st.success("Точката е добавена!")
                    st.rerun()

        pts = get_map_points(current_trip)
        if not pts.empty:
            avg_lat = pts["lat"].mean()
            avg_lon = pts["lon"].mean()
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

            for _, row in pts.iterrows():
                folium.Marker(
                    [row["lat"], row["lon"]], 
                    popup=row["title"], 
                    tooltip=row["title"],
                    icon=folium.Icon(color=row.get("color", "blue"))
                ).add_to(m)

            st_folium(m, width=700, height=400)
        else:
            st.info("Няма добавени GPS точки за това пътуване.")

    # ---------------------------------------------------------
    # ТАБ 5: ЧЕКЛИСТ & ПЛАН
    # ---------------------------------------------------------
    with tab_plan:
        st.subheader("📋 Чеклист за багаж и задачи")
        
        plan_key = f"new_plan_item_input_{current_trip}"
        st.text_input("Добави нова задача/вещ:", key=plan_key, placeholder="напр. Паспорти, Зарядни...", 
                      on_change=_add_plan_item_and_clear, args=(current_trip, plan_key))

        df_p = get_trip_plan(current_trip)
        if not df_p.empty:
            st.write("---")
            for idx, r in df_p.iterrows():
                col_ck, col_txt, col_del = st.columns([1, 5, 1])
                is_done = col_ck.checkbox("", value=r["done"], key=f"chk_{r['item_id']}")
                if is_done != r["done"]:
                    _toggle_plan_item(r["item_id"])
                    st.rerun()

                txt_style = f"~~{r['title']}~~" if r["done"] else r["title"]
                col_txt.markdown(txt_style)

                if col_del.button("🗑️", key=f"del_plan_{r['item_id']}"):
                    _delete_plan_item(r["item_id"])
                    st.rerun()
        else:
            st.info("Списъкът е празен. Добавете първата си задача по-горе.")

    # ---------------------------------------------------------
    # ТАБ 6: НАСТРОЙКИ
    # ---------------------------------------------------------
    with tab_settings:
        st.subheader("⚙️ Настройки на пътуването")
        
        car_mode = st.selectbox("Пътуване с кола:", ["Да", "Не"], index=0 if settings.get("car_trip") == "Да" else 1)
        s_km = st.number_input("Начален километраж:", value=float(settings.get("start_km", 0.0)))
        e_km = st.number_input("Краен километраж (за приключване):", value=float(settings.get("end_km", 0.0)))

        st.write("---")
        st.subheader("🎨 Персонализация на бутоните/етикетите")
        lbl_pet = st.text_input("Етикет за 'Куче':", value=UI_LABELS.get("pet", "Куче"))
        lbl_hotel = st.text_input("Етикет за 'Нощувки/Хотел':", value=UI_LABELS.get("hotel", "Нощувки/Хотел"))
        lbl_dep = st.text_input("Етикет за 'Депозит/Резервация':", value=UI_LABELS.get("deposit", "Депозит/Резервация"))

        if st.button("💾 Запази промените", type="primary"):
            save_trip_settings(current_trip, car_mode, settings.get("track_fuel", "Добави впоследствие"), s_km, e_km, settings.get("manual_fuel", 0.0), settings.get("start_date", ""), settings.get("end_date", ""))
            save_ui_labels(lbl_pet, lbl_hotel, lbl_dep)
            st.success("Настройките са обновени успешно!")
            st.rerun()

        st.write("---")
        if st.button("🔥 Изтрий това пътуване", type="secondary"):
            try:
                df_all = pd.read_csv(DATA_FILE)
                df_all[df_all["trip_id"] != current_trip].to_csv(DATA_FILE, index=False, encoding="utf-8")
                
                df_set = pd.read_csv(SETTINGS_FILE)
                df_set[df_set["trip_id"] != current_trip].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")

                st.session_state["current_trip"] = None
                st.rerun()
            except:
                st.error("Грешка при изтриването.")
