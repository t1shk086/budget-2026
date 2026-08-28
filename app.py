# Изтеглете файла от линка по-горе или копирайте целия код отдолу:
import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
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

# Настройки само за имената на бутоните. Каноничните категории в данните НЕ се променят.
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


# =========================================================
# БЮДЖЕТИ ПО КАТЕГОРИИ
# =========================================================
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

def save_global_budget(t_id, amount):
    try:
        columns = ["trip_id", "category", "budget"]
        if os.path.exists(CATEGORY_BUDGETS_FILE):
            df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
            if not set(columns).issubset(df.columns):
                df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(columns=columns)
        df = df[~((df["trip_id"].astype(str) == str(t_id)) & (df["category"].astype(str) == "__GLOBAL__"))]
        amount = max(0.0, float(amount or 0.0))
        if amount > 0:
            df = pd.concat([df, pd.DataFrame([{
                "trip_id": str(t_id), "category": "__GLOBAL__", "budget": amount
            }])], ignore_index=True)
        df.to_csv(CATEGORY_BUDGETS_FILE, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def save_category_budgets(t_id, budgets):
    try:
        columns = ["trip_id", "category", "budget"]
        if os.path.exists(CATEGORY_BUDGETS_FILE):
            df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
            if not set(columns).issubset(df.columns):
                df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(columns=columns)

        # Премахваме само категориалните бюджети за това пътуване.
        # Глобалният ред __GLOBAL__ се запазва, докато не бъде изрично заменен.
        keep_mask = ~((df["trip_id"].astype(str) == str(t_id)) & (df["category"].astype(str) != "__GLOBAL__"))
        df = df[keep_mask]
        rows = []
        for cat in KATEGORII:
            if cat == "Депозит/Резервация":
                continue
            try:
                amount = max(0.0, float(budgets.get(cat, 0.0)))
            except (TypeError, ValueError):
                amount = 0.0
            if amount > 0:
                rows.append({"trip_id": str(t_id), "category": cat, "budget": amount})

        if rows:
            df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
        df.to_csv(CATEGORY_BUDGETS_FILE, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def save_budget_config(t_id, mode, total_amount=None, budgets=None):
    """
    Надеждно записва цялата бюджетна конфигурация за едно пътуване
    като една операция. Режимите са взаимно изключващи се:
    - "global" -> само общ бюджет
    - "category" -> бюджети по категории
    """
    try:
        columns = ["trip_id", "category", "budget"]
        if os.path.exists(CATEGORY_BUDGETS_FILE):
            df = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
            if not set(columns).issubset(df.columns):
                df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(columns=columns)

        # Премахваме цялата стара бюджетна конфигурация само за това пътуване.
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

# Временно отключване на заключването на приключено пътуване.
# end_km и статусът „Приключено“ НЕ се променят.
if "edit_unlocked_trip" not in st.session_state:
    st.session_state["edit_unlocked_trip"] = None

def trip_edit_unlocked(t_id):
    return st.session_state.get("edit_unlocked_trip") == str(t_id)

def lock_trip_editing(t_id=None):
    if t_id is None or st.session_state.get("edit_unlocked_trip") == str(t_id):
        st.session_state["edit_unlocked_trip"] = None

def get_finished_trip_ids():
    """Връща всички приключени пътувания по записания краен километраж."""
    result = []
    try:
        if os.path.exists(SETTINGS_FILE):
            df_settings = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
            if not df_settings.empty and "trip_id" in df_settings.columns and "end_km" in df_settings.columns:
                for _, row in df_settings.iterrows():
                    tid = str(row.get("trip_id", "")).strip()
                    if tid and float(row.get("end_km", 0.0) or 0.0) > 0:
                        result.append(tid)
    except Exception:
        pass
    return list(dict.fromkeys(result))

def _navigate_fuel(direction, trip_id):
    try:
        df_nav = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_nav = df_nav[(df_nav["trip_id"] == trip_id) & (df_nav["category"] == "Транспорт")].copy()

        # Зареждане е или нормален запис с литри, или ръчно добавено
        # пропуснато гориво, което се пази като [ПРОПУСНАТО ГОРИВО].
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

        # Индексът е обърнат, защото визуализираме последното зареждане като N/N.
        # Ляво: 6/6 -> 5/6 -> 4/6 ... -> 1/6
        # Дясно: 1/6 -> 2/6 -> 3/6 ... -> 6/6
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
    """Добавя текущата задача от session_state и изчиства полето след успех."""
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

if st.session_state["current_trip"] is None:
    st.session_state["edit_unlocked_trip"] = None
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: -8px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)

    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]

    # ---------------------------------------------------------
    # НАЧАЛЕН ЕКРАН — запазваме визуалния език на приложението.
    # Бърз разход е първи, след него Ново пътуване, после пътуванията.
    # ---------------------------------------------------------
    st.markdown("""
    <style>
        /* Големите действия използват същия визуален език като приложението */
        .tm-home-action-space { margin-top: 2px; margin-bottom: 8px; }
        .tm-home-trips-title {
            color:#9aa1ad;
            font-size:11px;
            font-weight:800;
            letter-spacing:0;
            margin:18px 0 9px 2px;
            padding-bottom:8px;
            border-bottom:1px solid rgba(255,255,255,0.08);
        }
        .tm-trip-card-wrap { margin-bottom:8px; }
        .tm-trip-budget-mini { margin-top:7px; }
        .tm-trip-budget-track { position:relative; height:12px; border-radius:20px; background:rgba(0,0,0,.42); padding:2px; overflow:hidden; box-shadow:inset 2px 2px 5px rgba(0,0,0,.45); }
        .tm-trip-budget-fill { height:100%; border-radius:20px; background:linear-gradient(90deg,#4facfe 0%,#00f2fe 100%); box-shadow:inset 0 2px 2px rgba(255,255,255,.25); }
        .tm-trip-budget-percent { position:absolute; right:6px; top:0; line-height:12px; font-size:8px; font-weight:900; color:rgba(255,255,255,.9); text-shadow:1px 1px 2px rgba(0,0,0,.8); }


        /* Самата Streamlit карта-бутон */
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

        /* FINAL LEFT ALIGNMENT — override Streamlit's internal flex centering. */
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

    # Бърз разход — първи и най-лесен за достигане.
    if st.button("➕ Бърз Разход", use_container_width=True, type="primary", key="quick_expense_top_btn"):
        st.session_state["open_quick_expense"] = True
        st.rerun()

    # Диалогът за ново пътуване е дефиниран преди бутона, за да няма нова страница.
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

    # Ново пътуване — над списъка, но след основното действие.
    if st.button("  Ново Пътуване", use_container_width=True, key="new_trip_home_btn"):
        create_trip_modal()

    if existing:
        st.markdown("<div class='tm-home-trips-title'>Избери Дестинация</div>", unsafe_allow_html=True)

        for _trip in existing:
            _trip_id = str(_trip)
            _trip_name = _trip_id.replace("_", " ")
            _settings = get_trip_settings(_trip_id)
            _finished = float(_settings.get("end_km", 0.0) or 0.0) > 0.0

            # Статус: активно = зелена точка, приключено = червена точка.
            _status_dot = "🟢" if not _finished else "🔴"
            _status_text = "Активно" if not _finished else "Приключено"

            _df_home_trip = get_trip_data(_trip_id)

            # ============================================================
            # НАЧАЛНА КАРТА — БЮДЖЕТ
            #
            # Важно: тук "изхарчено" означава реално похарчено за пътуването,
            # а не само това, което участва в ДНЕВНИЯ ЛИМИТ.
            #
            # Затова:
            #   expense  -> влиза
            #   deposit  -> влиза
            # Хотел/стаи и депозит НЕ се изключват тук. Те се изключват
            # само от малките карти за дневен лимит/темпо.
            # ============================================================

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

                    # При ОБЩ бюджет всичко платено за пътуването влиза:
                    # нормални разходи + депозити.
                    if _budget_mode == "global":
                        _spent = float(
                            _df_home_trip.loc[_type.isin(["expense", "deposit"]), "amount"]
                            .fillna(0)
                            .sum()
                        )

                    # При БЮДЖЕТ ПО КАТЕГОРИИ:
                    # броим разходите само за категориите, за които има бюджет.
                    # Депозитът е логически част от "Нощувки/Хотел", затова
                    # влиза само ако има зададен бюджет за хотел.
                    elif _budget_mode == "category":
                        _budgeted_categories = {
                            str(cat)
                            for cat, val in _cat_budgets.items()
                            if float(val or 0.0) > 0
                        }

                        _expense_rows = _df_home_trip.loc[
                            _type == "expense"
                        ].copy()

                        if "category" in _expense_rows.columns:
                            _expense_rows = _expense_rows[
                                _expense_rows["category"].astype(str).isin(_budgeted_categories)
                            ]
                            _spent += float(_expense_rows["amount"].fillna(0).sum())

                        # Deposit -> Hotel, но само когато Hotel има бюджет.
                        if "Нощувки/Хотел" in _budgeted_categories:
                            _spent += float(
                                _df_home_trip.loc[_type == "deposit", "amount"]
                                .fillna(0)
                                .sum()
                            )

            except Exception:
                _spent = 0.0

            if _budget > 0:
                _pct = max(0.0, min(100.0, (_spent / _budget) * 100.0))
                _budget_line = f"€{_spent:,.2f} / €{_budget:,.2f}  ·  {_pct:.0f}%"
            else:
                _pct = 0.0
                _budget_line = "Без Бюджет"

            # =========================================================
            # ПРОГРЕС ЛЕНТА — БЕЗОПАСЕН KEY ЗА КИРИЛИЦА И ЛАТИНИЦА
            # =========================================================
            # Името на пътуването никога не се използва директно в CSS.
            # Това премахва разликата между кирилица и латиница.
            _trip_id_text = str(_trip_id).strip()
            _safe_key = "trip_" + hashlib.sha256(
                _trip_id_text.encode("utf-8")
            ).hexdigest()[:16]

            # Реалният key на Streamlit бутона е ASCII и CSS класът му е:
            # .st-key-open_trip_card_<hash>
            _button_key = f"open_trip_card_{_safe_key}"
            _card_selector = f".st-key-{_button_key}"

            # Ако има бюджет, лентата винаги се показва, включително при 0%.
            _bar_pct = max(0.0, min(100.0, float(_pct))) if _budget > 0 else 0.0
            _bar_gradient = (
                f"linear-gradient(90deg, #4facfe 0%, #00f2fe {_bar_pct:.1f}%, "
                f"rgba(255,255,255,0.12) {_bar_pct:.1f}%, "
                f"rgba(255,255,255,0.12) 100%)"
            ) if _budget > 0 else (
                "linear-gradient(90deg, rgba(255,255,255,0.06) 0%, "
                "rgba(255,255,255,0.06) 100%)"
            )

            # Един контейнер и един бутон за всяко пътуване.
            with st.container():
                st.markdown(
                    f"""
                    <style>
                    {_card_selector} button {{
                        min-height:108px !important;
                        height:auto !important;
                        width:100% !important;
                        box-sizing:border-box !important;
                        padding:14px 0 24px 8px !important;
                        border-radius:16px !important;
                        border:1px solid rgba(255,255,255,.08) !important;
                        background:
                            {_bar_gradient} bottom / 100% 12px no-repeat,
                            linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,.012)) !important;
                        box-shadow:4px 4px 12px rgba(0,0,0,.24) !important;
                        color:#fff !important;
                        text-align:left !important;
                        justify-content:flex-start !important;
                        align-items:flex-start !important;
                        white-space:pre-wrap !important;
                        font-family:inherit !important;
                        line-height:1.45 !important;
                    }}
                    {_card_selector} button:hover {{
                        border-color:rgba(0,242,254,.22) !important;
                        background:
                            {_bar_gradient} bottom / 100% 12px no-repeat,
                            linear-gradient(135deg,rgba(255,255,255,.055),rgba(255,255,255,.018)) !important;
                        box-shadow:4px 6px 16px rgba(0,0,0,.30),0 0 14px rgba(0,242,254,.05) !important;
                        transform:translateY(-1px) !important;
                    }}
                    {_card_selector} button > div {{
                        width:100% !important;
                        display:flex !important;
                        justify-content:flex-start !important;
                        align-items:flex-start !important;
                        padding:0 !important;
                        margin:0 !important;
                    }}
                    {_card_selector} button > div > p {{
                        width:100% !important;
                        margin:0 !important;
                        padding:0 !important;
                        text-align:left !important;
                        white-space:pre-wrap !important;
                        align-self:flex-start !important;
                    }}
                    {_card_selector} button span {{
                        margin-left:0 !important;
                        padding-left:0 !important;
                    }}
                    @media(max-width:640px) {{
                        {_card_selector} button {{
                            min-height:102px !important;
                            padding:12px 0 23px 6px !important;
                        }}
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                _label = (
                    f"🚙  **{_trip_name}**    →\n"
                    f"{_status_dot}  {_status_text}\n"
                    f"{_budget_line}"
                )

                if st.button(
                    _label,
                    use_container_width=True,
                    key=_button_key
                ):
                    st.session_state["current_trip"] = _trip_id
                    st.rerun()
        st.markdown(
            """
            <div style="
                width:100%;
                border-bottom:1px solid rgba(255,255,255,0.08);
                margin-top:14px;
                margin-bottom:8px;
            "></div>
            """,
            unsafe_allow_html=True
        )                    
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-top:10px;'>Все още нямате записани почивки. Създайте първото си приключение по-горе!</div>", unsafe_allow_html=True)

    @st.dialog("➕ Бърз разход", width="large")
    def quick_expense_modal():
        # Използваме абсолютно същия списък като полето „Изберете пътуване до:“ на началния екран.
        existing_quick = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
        existing_quick = [t for t in existing_quick if pd.notna(t) and str(t).strip() != ""]

        if not existing_quick:
            st.info("Първо създайте поне едно пътуване.")
            return

        trip_display = [t.replace("_", " ") for t in existing_quick]
        selected_trip_display = st.selectbox(
            "Пътуване",
            trip_display,
            key="quick_expense_trip"
        )
        selected_trip = existing_quick[trip_display.index(selected_trip_display)]
        quick_settings = get_trip_settings(selected_trip)
        quick_car_trip = str(quick_settings.get("car_trip", "Не")) == "Да"
        quick_start_km = float(quick_settings.get("start_km", 0.0) or 0.0)
        quick_end_km = float(quick_settings.get("end_km", 0.0) or 0.0)
        quick_manual_fuel = float(quick_settings.get("manual_fuel", 0.0) or 0.0)
        quick_trip_finished = quick_end_km > 0.0

        c1, c2 = st.columns(2)
        with c1:
            amount = st.number_input(
                "Сума (EUR)", min_value=0.01, value=None, step=1.00,
                placeholder="Въведете сума...", format="%.2f", key="quick_expense_amount"
            )
        with c2:
            description = st.text_input(
                "Описание", placeholder="Например: обяд, паркинг...",
                key="quick_expense_description"
            )

        category_options = [cat for cat in KATEGORII if cat != "Депозит/Резервация"]
        selected_category = st.selectbox(
            "Категория",
            category_options,
            format_func=lambda cat: f"{get_emoji(cat)} {get_display_category(cat)}",
            key="quick_expense_category"
        )

        # Същото разпознаване на гориво като в основния екран.
        fuel_keywords = ["газ", "гориво", "зареждане", "бензин", "дизел"]
        is_quick_fuel = (
            selected_category == "Транспорт"
            and any(k in description.strip().lower() for k in fuel_keywords)
        )

        liters = 0.0
        km_input = 0.0
        fuel_type = "ЧАСТИЧНО"
        last_km = quick_start_km

        if is_quick_fuel:
            st.markdown("---")
            st.markdown(
                "<div style='color:#00f2fe;font-weight:700;font-size:14px;margin-bottom:10px;font-family:inherit;'>⛽ Данни за зареждането</div>",
                unsafe_allow_html=True
            )

            if not quick_car_trip:
                st.warning("🚗 За проследяване на горивото това пътуване трябва да е със собствен автомобил.")
            elif quick_trip_finished and not trip_edit_unlocked(selected_trip):
                st.error("🔒 Пътуването е приключено. Зареждането на гориво е заключено.")
            else:
                fuel_c1, fuel_c2 = st.columns(2)
                with fuel_c1:
                    liters_input = st.number_input(
                        "Литри", value=None, min_value=0.0, step=0.1,
                        placeholder="Напишете литри...", key="quick_fuel_liters"
                    )
                with fuel_c2:
                    fuel_type_choice = st.radio(
                        "Тип на зареждането",
                        ["Да, до горе (Пълен резервоар)", "Не, частично (за конкретна сума)"],
                        index=0, key="quick_fuel_type"
                    )
                km_input_value = st.number_input(
                    "Текущи километри на таблото (км)", value=None,
                    min_value=0.0, step=1.0, placeholder="Въведете км...",
                    key="quick_fuel_km"
                )

                df_qf = get_trip_data(selected_trip)
                if not df_qf.empty and "current_km" in df_qf.columns:
                    df_qf = df_qf[(df_qf["category"] == "Транспорт") & (df_qf["current_km"] > 0)].sort_index()
                    last_km = float(df_qf["current_km"].max()) if not df_qf.empty else quick_start_km
                else:
                    df_qf = pd.DataFrame(columns=["current_km", "liters", "description"])

                liters = float(liters_input) if liters_input is not None else 0.0
                km_input = float(km_input_value) if km_input_value is not None else 0.0
                fuel_type = "ПЪЛНО" if "до горе" in fuel_type_choice.lower() else "ЧАСТИЧНО"

                # Същото изчисление за етапен реален разход като в основния екран.
                if liters > 0 and km_input > last_km and fuel_type == "ПЪЛНО":
                    df_since_full = df_qf[df_qf["description"].astype(str).str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                    if not df_since_full.empty:
                        last_full_km = float(df_since_full.iloc[-1]["current_km"])
                        partial_liters = float(df_qf[df_qf["current_km"] > last_full_km]["liters"].sum())
                        total_segment_liters = partial_liters + liters
                        segment_dist = km_input - last_full_km
                    else:
                        total_segment_liters = float(df_qf["liters"].sum()) + liters + quick_manual_fuel
                        segment_dist = km_input - quick_start_km

                    if segment_dist > 0 and total_segment_liters > 0:
                        st.success(
                            f"📊 Реален разход за етапа: **{(total_segment_liters / segment_dist * 100):.1f} л / 100 км**"
                        )

        if st.button(
            "✔️ Запиши", use_container_width=True,
            type="primary", key="quick_expense_save"
        ):
            # Не допускаме float(None) при празно поле за сумата.
            if amount is None or float(amount) <= 0:
                st.warning("⚠️ Добавете разход или затворете полето.")
                return

            desc = description.strip() or "Бърз разход"

            # Ако е гориво, записваме със същия формат и литри/км полета.
            if is_quick_fuel:
                if not quick_car_trip:
                    st.error("❌ Това пътуване не е настроено за собствен автомобил.")
                    return
                if quick_trip_finished and not trip_edit_unlocked(selected_trip):
                    st.error("❌ Пътуването е приключено.")
                    return
                if liters <= 0:
                    st.error("❌ Въведете литри за зареждането.")
                    return
                if km_input <= 0:
                    st.error("❌ Въведете текущите километри на таблото.")
                    return

                df_qf = get_trip_data(selected_trip)
                if not df_qf.empty and "current_km" in df_qf.columns:
                    df_qf = df_qf[(df_qf["category"] == "Транспорт") & (df_qf["current_km"] > 0)].sort_index()
                else:
                    df_qf = pd.DataFrame(columns=["current_km", "liters", "description"])
                last_km_save = float(df_qf["current_km"].max()) if not df_qf.empty else quick_start_km

                full_desc = f"[{fuel_type} ЗАРЕЖДАНЕ] {desc}"

                if km_input > last_km_save and fuel_type == "ПЪЛНО":
                    df_since_full = df_qf[df_qf["description"].astype(str).str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                    if not df_since_full.empty:
                        last_full_km = float(df_since_full.iloc[-1]["current_km"])
                        partial_liters = float(df_qf[df_qf["current_km"] > last_full_km]["liters"].sum())
                        t_liters = partial_liters + liters
                        t_dist = km_input - last_full_km
                    else:
                        t_liters = float(df_qf["liters"].sum()) + liters + quick_manual_fuel
                        t_dist = km_input - quick_start_km

                    if t_dist > 0 and t_liters > 0:
                        full_desc += f" (Етап: {t_dist:.0f}км, Реален разход: {(t_liters / t_dist * 100):.1f}л/100км)"

                if add_expense(selected_trip, float(amount), "Транспорт", full_desc, False, liters, km_input):
                    st.success("✅ Зареждането е записано успешно.")
                    st.rerun()
                else:
                    st.error("❌ Зареждането не можа да бъде записано.")
                return

            if quick_trip_finished and not trip_edit_unlocked(selected_trip):
                st.error("🔒 Това пътуване е приключено. Отключете го от „Административни Инструменти“, ако искате да го редактирате.")
                return

            if add_expense(selected_trip, float(amount), selected_category, desc, False):
                st.success("✅ Разходът е записан успешно.")
                st.rerun()
            else:
                st.error("❌ Разходът не можа да бъде записан.")


    if st.session_state.get("open_quick_expense", False):
        st.session_state["open_quick_expense"] = False
        quick_expense_modal()

    if st.button("➖ Последни разходи", use_container_width=True, key="recent_expenses_home_btn"):
            @st.dialog("➖ Последни разходи", width="large")
            def recent_expenses_modal():
                st.markdown("""
                <style>
                    .recent-expenses-subtitle {
                        color: #8b929e;
                        font-size: 13px;
                        margin: -8px 0 18px 0;
                        font-family: inherit;
                    }
                    .recent-expense-card {
                        background: linear-gradient(135deg, rgba(255,255,255,.045), rgba(255,255,255,.018));
                        border: 1px solid rgba(255,255,255,.09);
                        border-radius: 16px;
                        padding: 14px 16px;
                        margin-bottom: 10px;
                        box-shadow: 0 6px 18px rgba(0,0,0,.18);
                        font-family: inherit;
                    }
                    .recent-expense-top {
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:12px;
                    }
                    .recent-expense-category {
                        font-size: 14px;
                        font-weight: 700;
                        color: #ffffff;
                        font-family: inherit;
                    }
                    .recent-expense-amount {
                        font-size: 18px;
                        font-weight: 800;
                        color: #ff6b6b;
                        white-space: nowrap;
                        font-family: inherit;
                    }
                    .recent-expense-trip {
                        margin-top: 8px;
                        color: #00d9ff;
                        font-size: 12px;
                        font-weight: 700;
                        font-family: inherit;
                    }
                    .recent-expense-meta {
                        margin-top: 4px;
                        color: #7e8494;
                        font-size: 11px;
                        line-height: 1.45;
                        font-family: inherit;
                    }
                    .recent-expense-desc {
                        margin-top: 8px;
                        color: #dce1e8;
                        font-size: 13px;
                        line-height: 1.4;
                        font-family: inherit;
                    }
                </style>
                """, unsafe_allow_html=True)
                try:
                    df_recent = pd.read_csv(DATA_FILE, encoding="utf-8")
                    if df_recent.empty:
                        st.info("Все още няма записани разходи.")
                    else:
                        recent = df_recent.tail(5).iloc[::-1]
                        st.markdown("<div class='recent-expenses-subtitle'>Последните 5 записани разхода от всички пътувания.</div>", unsafe_allow_html=True)
                        for _, row in recent.iterrows():
                            cat = str(row.get("category", "Други"))
                            trip_name = str(row.get("trip_id", "")).replace("_", " ")
                            desc = str(row.get("description", "Без описание"))
                            dt = str(row.get("date", ""))
                            amount = float(row.get("amount", 0) or 0)
                            emoji = get_emoji(cat)
                            display_cat = get_display_category(cat)
                            st.markdown(f"""
                            <div class='recent-expense-card'>
                                <div class='recent-expense-top'>
                                    <div class='recent-expense-category'>{emoji} {display_cat}</div>
                                    <div class='recent-expense-amount'>{amount:.2f} EUR</div>
                                </div>
                                <div class='recent-expense-trip'>✈️ {trip_name}</div>
                                <div class='recent-expense-meta'>🕒 {dt}</div>
                                <div class='recent-expense-desc'>{desc}</div>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception:
                    st.error("Неуспешно зареждане на последните разходи.")

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                if st.button("❌ Затвори", use_container_width=True, key="close_recent_expenses_btn"):
                    st.rerun()
            recent_expenses_modal()

    # 1. ЕЛЕГАНТЕН CSS: ПРЕМЕСТВА ФАБРИЧНИЯ НАДПИС ОТДЯСНО НА ТОГЪЛА С 1 ИНТЕРВАЛ РАЗСТОЯНИЕ
    st.html("""
    <style>
        /* Пренастройва контейнера на toggle бутона да подрежда елементите в линия */
        div[data-testid="stCheckbox"] > label {
            display: inline-flex !important;
            flex-direction: row-reverse !important; /* Мести оригиналния текст отдясно */
            align-items: center !important;
            gap: 10px !important; /* Разстояние точно колкото 1 интервал */
            width: auto !important;
            max-width: none !important;
            flex-shrink: 0 !important;
        }
        /* Подсигурява, че текстът няма да се пречупи на два реда на телефон */
        div[data-testid="stCheckbox"] p {
            white-space: nowrap !important;
            margin: 0 !important;
            font-size: 11px !important;
            font-weight: 800 !important;
            letter-spacing: 0 !important;
            color: #9aa1ad !important;
            font-family: inherit !important;
        }
        /* Streamlit понякога поставя текста в допълнителен span */
        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] label span {
            font-size: 11px !important;
            font-weight: 800 !important;
            letter-spacing: 0 !important;
            color: #9aa1ad !important;
            font-family: inherit !important;
        }
    </style>
    """)

    # 2. ОФИЦИАЛЕН TOGGLE БУТОН С ДИРЕКТЕН НАДПИС (БЕЗ ДОПЪЛНИТЕЛНИ КОЛОНИ И HTML)
    show_comparison = st.toggle(
        label="Сравнителен панел",
        value=False,
        key="stable_comparison_toggle"
    )
        
    # 3. НОВ ДИЗАЙН НА СРАВНИТЕЛНИЯ ПАНЕЛ — СЪЩИТЕ ДАННИ, ПО-ЧИСТ UX
    if show_comparison:
        @st.dialog("📊 Сравнителен панел", width="large")
        def show_global_analytics_dialog():
            st.markdown("""
            <style>
                .cmp-shell {
                    padding: 2px 0 4px 0;
                }
                .cmp-intro {
                    color:#8b929e;
                    font-size:12px;
                    margin:-6px 0 16px 0;
                    line-height:1.45;
                }
                .cmp-summary {
                    display:grid;
                    grid-template-columns:repeat(2,minmax(0,1fr));
                    gap:10px;
                    margin:4px 0 14px 0;
                }
                .cmp-card {
                    background:linear-gradient(135deg,rgba(255,255,255,.045),rgba(255,255,255,.018));
                    border:1px solid rgba(255,255,255,.08);
                    border-radius:14px;
                    padding:12px 13px;
                }
                .cmp-card-label {
                    color:#7e8494;
                    font-size:10px;
                    font-weight:700;
                    letter-spacing:.7px;
                    text-transform:uppercase;
                }
                .cmp-card-value {
                    color:#fff;
                    font-size:17px;
                    font-weight:900;
                    margin-top:3px;
                    line-height:1.2;
                }
                .cmp-card-note {
                    color:#9da5b1;
                    font-size:10px;
                    margin-top:3px;
                }
                .cmp-note {
                    background:rgba(0,242,254,.035);
                    border:1px solid rgba(0,242,254,.10);
                    border-radius:12px;
                    padding:10px 12px;
                    color:#b8c0cc;
                    font-size:11px;
                    line-height:1.45;
                    margin-top:10px;
                }
                @media (max-width: 600px) {
                    .cmp-summary { grid-template-columns:1fr 1fr; }
                }
            </style>
            <div class='cmp-shell'>
                <div style='font-size:12px;color:#fff;font-weight:800;letter-spacing:.8px;'>Сравнение на пътуванията</div>
                <div class='cmp-intro'>Избери показател и виж резултатите.</div>
            </div>
            """, unsafe_allow_html=True)

            chosen_criteria = st.segmented_control(
                label="Показател",
                options=["Цена / км", "€ / ден", "Общо", "Км", "Хотел"],
                default="Цена / км",
                key="modal_segmented_metric_selector"
            )

            criteria_map = {
                "Цена / км": "Цена за 1 км",
                "€ / ден": "Пари на Ден",
                "Общо": "Обща Стойност",
                "Км": "Изминати км",
                "Хотел": "Нощувки и Хотел",
            }
            chosen_criteria_internal = criteria_map.get(chosen_criteria, "Цена за 1 км")

            all_trips_computed = []
            try:
                df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
                df_all_settings = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                unique_trips = df_all_data["trip_id"].dropna().unique()

                for t in unique_trips:
                    if not t or str(t).strip() == "":
                        continue
                    df_t_data = df_all_data[df_all_data["trip_id"] == t]
                    df_t_sett = df_all_settings[df_all_settings["trip_id"] == t]

                    t_dep = float(df_t_data[df_t_data["type"] == "deposit"]["amount"].sum())
                    t_site = float(df_t_data[df_t_data["type"] == "expense"]["amount"].sum())
                    t_total = t_dep + t_site

                    t_hotel_only = float(df_t_data[df_t_data["category"] == "Нощувки/Хотел"]["amount"].sum())
                    t_deposit_only = float(df_t_data[df_t_data["category"] == "Депозит/Резервация"]["amount"].sum())
                    t_accommodation_total = t_hotel_only + t_deposit_only

                    t_dist, s_k, e_k = 0.0, 0.0, 0.0
                    days_count = 1

                    if not df_t_sett.empty:
                        s_k = float(df_t_sett["start_km"].iloc[0]) if "start_km" in df_t_sett.columns and not df_t_sett["start_km"].empty else 0.0
                        e_k = float(df_t_sett["end_km"].iloc[0]) if "end_km" in df_t_sett.columns and not df_t_sett["end_km"].empty else 0.0
                        st_d_str = str(df_t_sett["start_date"].iloc[0]) if "start_date" in df_t_sett.columns and not df_t_sett["start_date"].empty else ""
                        en_d_str = str(df_t_sett["end_date"].iloc[0]) if "end_date" in df_t_sett.columns and not df_t_sett["end_date"].empty else ""

                        max_k = float(df_t_data[df_t_data["type"] == "expense"]["current_km"].max()) if not df_t_data.empty else 0.0
                        eff_e = e_k if e_k > 0 else max_k
                        t_dist = eff_e - s_k if eff_e > s_k else 0.0

                        try:
                            d1 = datetime.datetime.strptime(st_d_str, "%d.%m.%Y")
                            d2 = datetime.datetime.strptime(en_d_str, "%d.%m.%Y")
                            days_count = max(1, (d2 - d1).days + 1)
                        except:
                            days_count = 1

                    all_trips_computed.append({
                        "Пътуване": str(t).replace("_", " "),
                        "Обща Стойност (EUR)": t_total,
                        "Цена за 1 км (EUR)": (t_total / t_dist) if t_dist > 0 else 0.0,
                        "Дневен Разход (EUR)": (t_total / days_count),
                        "Изминато разстояние (км)": t_dist,
                        "Нощувки и Хотел (EUR)": t_accommodation_total,
                        "DistValid": t_dist > 0
                    })
            except Exception:
                pass

            if all_trips_computed:
                df_pixel = pd.DataFrame(all_trips_computed)
                import plotly.express as px

                if chosen_criteria_internal == "Цена за 1 км":
                    x_col = "Цена за 1 км (EUR)"
                    t_format = "%{text:.2f} EUR/км"
                    df_filtered = df_pixel[df_pixel["DistValid"] == True]
                    if df_filtered.empty:
                        df_filtered = df_pixel
                    df_sorted = df_filtered.sort_values(by=x_col, ascending=True)
                    graph_title = "Цена за 1 км"
                    better_idx = df_sorted[x_col].idxmin() if not df_sorted.empty else None
                    worse_idx = df_sorted[x_col].idxmax() if not df_sorted.empty else None
                    better_label = "Най-икономично"
                    worse_label = "Най-скъпо"
                    fmt_value = lambda v: f"€{v:.2f}/км"
                elif chosen_criteria_internal == "Обща Стойност":
                    x_col = "Обща Стойност (EUR)"
                    t_format = "%{text:,.2f} EUR"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "Обща стойност"
                    better_idx = df_sorted[x_col].idxmin() if not df_sorted.empty else None
                    worse_idx = df_sorted[x_col].idxmax() if not df_sorted.empty else None
                    better_label = "Най-нисък разход"
                    worse_label = "Най-висок разход"
                    fmt_value = lambda v: f"€{v:,.2f}"
                elif chosen_criteria_internal == "Изминати км":
                    x_col = "Изминато разстояние (км)"
                    t_format = "%{text:.0f} км"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "Изминати километри"
                    better_idx = df_sorted[x_col].idxmax() if not df_sorted.empty else None
                    worse_idx = df_sorted[x_col].idxmin() if not df_sorted.empty else None
                    better_label = "Най-дълго пътуване"
                    worse_label = "Най-кратко пътуване"
                    fmt_value = lambda v: f"{v:.0f} км"
                elif chosen_criteria_internal == "Нощувки и Хотел":
                    x_col = "Нощувки и Хотел (EUR)"
                    t_format = "%{text:,.2f} EUR"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "Хотел и нощувки"
                    better_idx = df_sorted[x_col].idxmin() if not df_sorted.empty else None
                    worse_idx = df_sorted[x_col].idxmax() if not df_sorted.empty else None
                    better_label = "Най-нисък хотелски разход"
                    worse_label = "Най-висок хотелски разход"
                    fmt_value = lambda v: f"€{v:,.2f}"
                else:
                    x_col = "Дневен Разход (EUR)"
                    t_format = "%{text:.2f} EUR/ден"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "Среднодневен разход"
                    better_idx = df_sorted[x_col].idxmin() if not df_sorted.empty else None
                    worse_idx = df_sorted[x_col].idxmax() if not df_sorted.empty else None
                    better_label = "Най-нисък дневен разход"
                    worse_label = "Най-висок дневен разход"
                    fmt_value = lambda v: f"€{v:.2f}/ден"

                # СЕМПЪЛ + МОДЕРЕН ВИД:
                # запазваме стандартните хоризонтални колони,
                # но махаме тежкия градиент, излишните оси и визуалния шум.
                fig_pixel = px.bar(
                    df_sorted,
                    x=x_col,
                    y="Пътуване",
                    orientation="h",
                    text=x_col,
                    color_discrete_sequence=["#6f7cff"],
                )

                fig_pixel.update_traces(
                    marker=dict(
                        line=dict(width=0),
                        cornerradius=9,
                        opacity=0.92,
                    ),
                    texttemplate=f"<b>{t_format}</b>",
                    textposition="outside",
                    textfont=dict(
                        family="Segoe UI, Arial, sans-serif",
                        size=11,
                        color="#eef2f7",
                    ),
                    cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>" + f"{t_format}" + "<extra></extra>",
                )

                fig_pixel.update_layout(
                    title=dict(
                        text=f"<b>{graph_title}</b>",
                        font=dict(
                            family="Segoe UI, Arial, sans-serif",
                            color="#f2f4f7",
                            size=18,
                        ),
                        x=0,
                        y=0.98,
                        xanchor="left",
                        yanchor="top",
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(
                        family="Segoe UI, Arial, sans-serif",
                        color="#d8dde5",
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.075)",
                        gridwidth=1,
                        zeroline=False,
                        showline=False,
                        showticklabels=False,
                        title="",
                    ),
                    yaxis=dict(
                        showgrid=False,
                        showline=False,
                        zeroline=False,
                        title="",
                        tickfont=dict(
                            family="Segoe UI, Arial, sans-serif",
                            color="#dfe4eb",
                            size=11,
                        ),
                        automargin=True,
                    ),
                    margin=dict(l=10, r=105, t=58, b=10),
                    height=max(290, 58 * len(df_sorted) + 92),
                    bargap=0.28,
                    showlegend=False,
                    hoverlabel=dict(
                        bgcolor="#ffffff",
                        bordercolor="#d9dee6",
                        font=dict(
                            family="Segoe UI, Arial, sans-serif",
                            color="#202631",
                            size=11,
                        ),
                    ),
                )

                st.plotly_chart(
                    fig_pixel,
                    use_container_width=True,
                    config={"displayModeBar": False, "scrollZoom": False},
                )

                best_name = str(df_pixel.loc[better_idx, "Пътуване"]) if better_idx is not None else "—"
                best_value = float(df_pixel.loc[better_idx, x_col]) if better_idx is not None else 0.0
                worst_name = str(df_pixel.loc[worse_idx, "Пътуване"]) if worse_idx is not None else "—"
                worst_value = float(df_pixel.loc[worse_idx, x_col]) if worse_idx is not None else 0.0

                st.markdown(f"""
                <div class='cmp-summary'>
                    <div class='cmp-card'>
                        <div class='cmp-card-label'>🏆 {better_label}</div>
                        <div class='cmp-card-value'>{html.escape(best_name)}</div>
                        <div class='cmp-card-note'>{fmt_value(best_value)}</div>
                    </div>
                    <div class='cmp-card'>
                        <div class='cmp-card-label'>⚠️ {worse_label}</div>
                        <div class='cmp-card-value'>{html.escape(worst_name)}</div>
                        <div class='cmp-card-note'>{fmt_value(worst_value)}</div>
                    </div>
                </div>
                <div class='cmp-note'>💡 По-ниската стойност е по-добра при разходните показатели. При „Км“ по-високата стойност е по-добра.</div>
                """, unsafe_allow_html=True)
            else:
                st.info("Няма достатъчно база данни за сравнение.")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("❌ Затвори", key="bottom_modal_close_btn", use_container_width=True):
                st.session_state["stable_comparison_toggle"] = False
                st.rerun()

        show_global_analytics_dialog()






    # =========================================================
    # БЪРЗИ ДЕЙСТВИЯ НА НАЧАЛНИЯ ЕКРАН
    # =========================================================

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
                    if os.path.exists(TRIP_PLAN_FILE):
                        pd.read_csv(TRIP_PLAN_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")
                    if os.path.exists(CATEGORY_BUDGETS_FILE):
                        df_budget_delete = pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")
                        df_budget_delete[df_budget_delete["trip_id"].astype(str) != str(trip_id)].to_csv(
                            CATEGORY_BUDGETS_FILE, index=False, encoding="utf-8"
                        )
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
    # Платеният депозит е свързан с настаняването, затова го включваме
    # директно в "Нощувки/Хотел" за анализа и категорийния бюджет.
    categories_totals["Нощувки/Хотел"] = depozit_hotel
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
        df_full_points = df_trans_fuel[df_full_points["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
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
        st.session_state["edit_unlocked_trip"] = None
        st.rerun()

    v_id = st.session_state["form_version"]
    st.markdown('<div id="target_sum_box" style="position: relative; scroll-margin-top: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: 
        s_input = st.number_input("Сума (EUR)", value=None, placeholder="Въведете разход...", format="%.2f", key=f"su_{v_id}")
    with col2: 
        o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")

    is_trip_finished = (e_km > 0.0)
    is_edit_unlocked = trip_edit_unlocked(trip_id)
    trip_locked = is_trip_finished and not is_edit_unlocked

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        if trip_locked: 
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
                    is_disabled = trip_locked
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



        st.markdown("<div class='tm-section-title' style='margin-bottom:12px;'><span class='tm-section-number tm-n1'>1</span><span>Данни за разход и пробег</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'><span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 ПРОБЕГ</span>{f'<span style=\"background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;\">🔒 ЗАКЛЮЧЕН</span>' if is_trip_finished else ''}</div><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'><div style='text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{s_km:.0f} км</b></div><div style='text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist:.0f} км</b></div><div style='text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>Краен</span><b style='color: white; font-size: 14px;'>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
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
            
        # =========================================================
        # ⛽ АНАЛИЗ НА ЗАРЕЖДАНИЯТА — АДАПТИВНА МОБИЛНА КАРТА
        # =========================================================
        try:
            # Включваме и ръчно добавените пропуснати зареждания.
            # Те се записват с liters=0 в CSV, затова извличаме литрите
            # от описанието [ПРОПУСНАТО ГОРИВО] Добавени X.X литра.
            fuel_rows = df_expenses[
                (df_expenses["category"] == "Транспорт") &
                (
                    (df_expenses["liters"] > 0) |
                    (df_expenses["description"].astype(str).str.contains(r"(?:\[ПРОПУСНАТО\s+ГОРИВО\]|\[ГОРИВО\s+БЕЗ\s+СТОЙНОСТ\])", case=False, regex=True))
                )
            ].copy().sort_index()

            if not fuel_rows.empty:
                import re
                manual_mask = fuel_rows["description"].astype(str).str.contains(
                    r"(?:\[ПРОПУСНАТО\s+ГОРИВО\]|\[ГОРИВО\s+БЕЗ\s+СТОЙНОСТ\])", case=False, regex=True
                )
                for _idx in fuel_rows.index[manual_mask]:
                    _desc = str(fuel_rows.loc[_idx, "description"])
                    _match = re.search(r"Добавени\s*([0-9]+(?:\.[0-9]+)?)\s*литра", _desc, flags=re.IGNORECASE)
                    if _match:
                        fuel_rows.loc[_idx, "liters"] = float(_match.group(1))
                    fuel_rows.loc[_idx, "current_km"] = 0.0

                fuel_rows = fuel_rows.iloc[::-1].copy()  # последното първо
                fuel_count = len(fuel_rows)
                fuel_key = f"fuel_history_index_{trip_id}"
                if fuel_key not in st.session_state or st.session_state[fuel_key] >= fuel_count:
                    st.session_state[fuel_key] = 0

                fuel_idx = st.session_state[fuel_key]
                fr = fuel_rows.iloc[fuel_idx]
                liters_h = float(fr.get("liters", 0) or 0)
                amount_h = float(fr.get("amount", 0) or 0)
                km_h = float(fr.get("current_km", 0) or 0)
                ppl_h = (amount_h / liters_h) if liters_h > 0 else 0.0
                date_h = str(fr.get("date", ""))
                desc_h = str(fr.get("description", ""))
                amount_display_h = f"€{amount_h:.2f}" if amount_h > 0 else "—"
                ppl_display_h = f"€{ppl_h:.2f}" if amount_h > 0 and liters_h > 0 else "—"
                km_display_h = f"{km_h:.0f} км" if km_h > 0 else "—"
                # По-чисто визуално описание на зареждането. Данните в CSV остават непроменени.
                import re
                desc_display_h = desc_h
                fuel_match_h = re.match(r'^\[(?:\s*)ЧАСТИЧНО\s+ЗАРЕЖДАНЕ(?:\s*)\](.*)$', desc_h, flags=re.IGNORECASE)
                if fuel_match_h:
                    desc_display_h = f"Частично — {fuel_match_h.group(1).strip()}"
                else:
                    fuel_match_h = re.match(r'^\[(?:\s*)ПЪЛНО\s+ЗАРЕЖДАНЕ(?:\s*)\](.*)$', desc_h, flags=re.IGNORECASE)
                    if fuel_match_h:
                        desc_display_h = f"До горе — {fuel_match_h.group(1).strip()}"
                    else:
                        fuel_match_h = re.match(r'^\[ПРОПУСНАТО\s+ГОРИВО\]\s*Добавени\s*([0-9.]+)\s*литра\s*$', desc_h, flags=re.IGNORECASE)
                        if fuel_match_h:
                            desc_display_h = f"Добавено ръчно — {fuel_match_h.group(1)} л"
                        else:
                            fuel_match_h = re.match(r'^\[ГОРИВО\s+БЕЗ\s+СТОЙНОСТ\]\s*Добавени\s*([0-9.]+)\s*литра\s*$', desc_h, flags=re.IGNORECASE)
                            if fuel_match_h:
                                desc_display_h = f"Добавено ръчно — само {fuel_match_h.group(1)} л"

                compare_html = "⚪ Няма предишно зареждане за сравнение."
                compare_color = "#7e8494"
                if fuel_idx < fuel_count - 1:
                    prev_fr = fuel_rows.iloc[fuel_idx + 1]
                    prev_l = float(prev_fr.get("liters", 0) or 0)
                    prev_a = float(prev_fr.get("amount", 0) or 0)
                    prev_ppl = (prev_a / prev_l) if prev_l > 0 else 0.0
                    if prev_ppl > 0 and ppl_h > 0:
                        delta = ppl_h - prev_ppl
                        if delta < 0:
                            compare_html = f"🟢 €{abs(delta):.2f}/л по-евтино · предишно €{prev_ppl:.2f}/л → сега €{ppl_h:.2f}/л"
                            compare_color = "#63d391"
                        elif delta > 0:
                            compare_html = f"🟠 €{delta:.2f}/л по-скъпо · предишно €{prev_ppl:.2f}/л → сега €{ppl_h:.2f}/л"
                            compare_color = "#ffb348"
                        else:
                            compare_html = f"⚪ Същата цена · €{ppl_h:.2f}/л"
                            compare_color = "#aeb5c0"
                    elif ppl_h <= 0:
                        compare_html = "⚪ Няма цена за сравнение — въведени са само литрите."
                        compare_color = "#aeb5c0"

                # Цената е зелена до зададения праг и червена над него.
                fuel_red_threshold = float(UI_LABELS.get("fuel_red_threshold", 1.80) or 1.80)
                price_color_h = "#ff4b4b" if ppl_h > fuel_red_threshold else ("#63d391" if ppl_h > 0 else "#7e8494")

                st.markdown(f"""
                <div style='background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:20px;margin-top:2px;margin-bottom:20px;font-family:inherit;box-shadow:4px 4px 12px rgba(0,0,0,0.3);'>
                    <div style='display:flex;justify-content:center;align-items:center;gap:10px;'>
                        <div style='font-size:11px;color:#888;font-weight:bold;letter-spacing:1px;text-align:center;'>⛽ АНАЛИЗ НА ЗАРЕЖДАНИЯТА</div>
                    </div>
                    <div style='font-size:10px;color:#7e8494;margin-top:2px;'>{html.escape(date_h)}</div>
                    <div style='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:14px;'>
                        <div style='background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);padding:14px 16px;border-radius:16px;box-shadow:4px 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(0,242,254,0.12);'>
                            <div style='font-size:11px;color:#888;font-weight:bold;letter-spacing:0.5px;'>Литри</div>
                            <div style='font-size:24px;color:#00d9ff;font-weight:900;line-height:1.1;margin-top:4px;text-shadow:0 0 12px rgba(0,217,255,0.14);'>{liters_h:.1f} <span style='font-size:11px;color:#666;font-weight:normal;'>л</span></div>
                        </div>
                        <div style='background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);padding:14px 16px;border-radius:16px;box-shadow:4px 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,215,106,0.10);'>
                            <div style='font-size:11px;color:#888;font-weight:bold;letter-spacing:0.5px;'>Стойност</div>
                            <div style='font-size:24px;color:#ffd76a;font-weight:900;line-height:1.1;margin-top:4px;text-shadow:0 0 12px rgba(255,215,106,0.12);'>{amount_display_h}</div>
                        </div>
                        <div style='background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);padding:14px 16px;border-radius:16px;box-shadow:4px 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(46,189,89,0.10);'>
                            <div style='font-size:11px;color:#888;font-weight:bold;letter-spacing:0.5px;'>Цена / л</div>
                            <div style='font-size:24px;color:{price_color_h};font-weight:900;line-height:1.1;margin-top:4px;text-shadow:0 0 12px rgba(46,189,89,0.14);'>{ppl_display_h}</div>
                        </div>
                        <div style='background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);padding:14px 16px;border-radius:16px;box-shadow:4px 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(150,110,255,0.10);'>
                            <div style='font-size:11px;color:#888;font-weight:bold;letter-spacing:0.5px;'>Километри</div>
                            <div style='font-size:24px;color:white;font-weight:900;line-height:1.1;margin-top:4px;'>{km_display_h}</div>
                        </div>
                    </div>
                    <div style='font-size:12px;color:#e4e8ef;margin-top:12px;line-height:1.4;font-weight:700;'>{html.escape(desc_display_h)}</div>
                    <div style='margin-top:10px;padding:10px 11px;border-radius:11px;background:rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.06);font-size:11px;color:{compare_color};font-weight:800;line-height:1.4;'>{compare_html}</div>
                </div>
                """, unsafe_allow_html=True)

                if fuel_count > 1:
                    st.markdown("<div class='compact-fuel-nav-marker'></div>", unsafe_allow_html=True)
                    nav = st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center", gap="small")
                    with nav:
                        st.button("‹", key=f"fuel_prev_{trip_id}", on_click=_navigate_fuel, args=("prev", trip_id), width="content")
                        st.markdown(f"<div style='text-align:center;min-width:55px;padding-top:3px;color:#8b929e;font-size:11px;line-height:1.25;'><b style='color:#fff;font-size:12px;'>{fuel_count - fuel_idx} / {fuel_count}</b></div>", unsafe_allow_html=True)
                        st.button("›", key=f"fuel_next_{trip_id}", on_click=_navigate_fuel, args=("next", trip_id), width="content")
        except Exception:
            pass

        st.markdown("<br>", unsafe_allow_html=True)


    
    @st.dialog("⚙️ Настройки за автомобил и период")
    def edit_car_modal():
        v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=trip_locked)
        new_sk = st.number_input("Начални километри (км):", value=None if s_km == 0.0 else s_km, placeholder="Въведете началните км...", disabled=trip_locked)
        
        # Полето приема само положителни числа за сигурност
        new_mf = st.number_input("Добави пропуснато гориво (л):", value=None, placeholder="Въведете литри...", min_value=0.0, disabled=trip_locked)

        has_cash_expense = st.checkbox("💵 Помня и платената сума за това гориво?") if (new_mf and new_mf > 0 and not trip_locked) else False
        manual_cash_amt = st.number_input("Въведете платена сума (EUR):", value=None, format="%.2f", placeholder="Въведете сумата...") if has_cash_expense else 0.0
        if new_mf and new_mf > 0 and not trip_locked and not has_cash_expense:
            st.caption("📝 Ще се запише като зареждане, за което са известни само литрите.")
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
        
        if st.button("💾 Обнови настройките", use_container_width=True, type="primary", disabled=trip_locked):
            sk_val = float(new_sk) if new_sk is not None else 0.0
            added_liters = float(new_mf) if new_mf is not None else 0.0
            mf_val = max(0.0, m_fuel + (added_liters if (has_cash_expense and manual_cash_amt and manual_cash_amt > 0) else 0.0))

            # БЕЗОПАСЕН ФИКС: Извикваме .strftime() САМО върху отделните обекти в списъка
            if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0:
                s_d_str = edit_range[0].strftime("%d.%m.%Y") if hasattr(edit_range[0], "strftime") else st_date
                e_d_str = edit_range[-1].strftime("%d.%m.%Y") if (len(edit_range) > 1 and hasattr(edit_range[-1], "strftime")) else s_d_str
            elif hasattr(edit_range, "strftime"):
                s_d_str = edit_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = st_date, en_date

            if added_liters > 0:
                if has_cash_expense and manual_cash_amt and manual_cash_amt > 0:
                    add_expense(trip_id, manual_cash_amt, "Транспорт", f"[ПРОПУСНАТО ГОРИВО] Добавени {added_liters:.1f} литра", False, 0.0, 0.0)
                else:
                    add_expense(trip_id, 0.0, "Транспорт", f"[ГОРИВО БЕЗ СТОЙНОСТ] Добавени {added_liters:.1f} литра", False, added_liters, 0.0)
            
            save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, s_d_str, e_d_str)
            st.session_state["form_version"] += 1
            st.rerun()
            
        # Автоматизирано нулиране на литри И премахване на паричните записи от хронологията
        if m_fuel > 0 and not trip_locked:
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
            st.button(
                "🔒 Заключени настройки" if trip_locked else "⚙️ Настройки автомобил",
                use_container_width=True,
                disabled=trip_locked,
                on_click=edit_car_modal
            )
        with col_manage2:
            if is_trip_finished:
                if st.button(
                    "🔒 Заключи редакцията" if is_edit_unlocked else "🏁 Пътуването е приключено 🔒",
                    use_container_width=True,
                    disabled=not is_edit_unlocked,
                    key=f"relock_trip_{trip_id}"
                ):
                    lock_trip_editing(trip_id)
                    st.rerun()
            else:
                st.button(
                    "🏁 Край на пътуването",
                    use_container_width=True,
                    on_click=finish_trip_modal
                )
    else:
        if st.button("🚗 Добави автомобил към пътуването", use_container_width=True, disabled=trip_locked):
            edit_car_modal()



    st.markdown("<br>", unsafe_allow_html=True)

    # Номерирани секции на анализа – общ визуален маркер.
    st.markdown("""
    <style>
        .tm-section-title {
            display:flex;
            align-items:center;
            gap:10px;
            font-size:15px;
            font-weight:800;
            color:#ffffff;
            letter-spacing:.3px;
            font-family:inherit;
        }
        .tm-section-number {
            width:28px;
            height:28px;
            min-width:28px;
            border-radius:50%;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            color:#fff;
            font-size:13px;
            font-weight:900;
            background:rgba(255,255,255,.025);
            box-shadow:0 2px 7px rgba(0,0,0,.22), inset 0 1px 1px rgba(255,255,255,.05);
        }
        .tm-n1 { border:2px solid #00f2fe; }
        .tm-n2 { border:2px solid #ffd43b; }
        .tm-n3 { border:2px solid #9b7cff; }
        .tm-n4 { border:2px solid #63d391; }
        .tm-n5 { border:2px solid #ff8a65; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='tm-section-title' style='margin-bottom:12px;'><span class='tm-section-number tm-n2'>2</span><span>Анализ на разходите</span></div>", unsafe_allow_html=True)

    # Бюджет: може общ бюджет ИЛИ отделни бюджети по категории.
    category_budgets = get_category_budgets(trip_id)
    global_budget = get_global_budget(trip_id)
    category_budget_total = sum(v for v in category_budgets.values() if v > 0)
    has_category_budgets = category_budget_total > 0
    active_budget_mode = "global" if global_budget > 0 else ("category" if has_category_budgets else "none")

    if active_budget_mode == "category":
        active_budget_total = category_budget_total
        active_budget_spent = sum(float(categories_totals.get(cat, 0.0)) for cat in category_budgets if category_budgets.get(cat, 0) > 0)
    else:
        active_budget_total = global_budget
        # При общ бюджет следим всичко изхарчено до момента — включително депозити.
        active_budget_spent = depozit_hotel + total_on_site
    active_budget_remaining = active_budget_total - active_budget_spent

    budget_col1, budget_col2 = st.columns([2, 1])
    with budget_col1:
        if active_budget_mode == "category":
            budget_caption = "По Категории"
        elif active_budget_mode == "global":
            budget_caption = "По обща Сума"
        else:
            budget_caption = "По Категории или Обща Сума"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(255,212,59,.10),rgba(255,255,255,.025));border:1px solid rgba(255,212,59,.28);padding:14px 16px;border-radius:16px;margin-bottom:14px;font-family:inherit;">
            <div style="font-size:13px;font-weight:800;color:#ffd43b;letter-spacing:.3px;font-family:inherit;">🎯 БЮДЖЕТ</div>
            <div style="font-size:11px;color:#9aa1ad;margin-top:4px;font-family:inherit;">{budget_caption}</div>
        </div>
        """, unsafe_allow_html=True)
    with budget_col2:
        budget_locked = trip_locked
        if st.button(
            "🔒 Настрой бюджет" if budget_locked else "🎯 Настрой бюджет",
            use_container_width=True,
            key=f"open_budget_settings_{trip_id}",
            disabled=budget_locked,
        ):
            @st.dialog("🎯 Настройка на бюджет", width="large")
            def _budget_settings_dialog():
                mode_options = ["Общ бюджет", "Бюджет по категории"]
                current_mode = 0 if active_budget_mode in ("none", "global") else 1
                mode = st.radio("Как искаш да следиш бюджета?", mode_options, index=current_mode, horizontal=True, key=f"budget_mode_{trip_id}")
                if mode == "Общ бюджет":
                    total_budget_input = st.number_input(
                        "Общ бюджет на пътуването (EUR)",
                        min_value=0.0,
                        value=(float(global_budget) if float(global_budget) > 0 else None),
                        placeholder="Въведете сума...",
                        step=50.0,
                        format="%.2f",
                        key=f"global_budget_input_{trip_id}"
                    )
                    st.caption("В този режим не е нужно да задаваш лимит за всяка категория.")
                    if st.button("💾 Запази общия бюджет", type="primary", use_container_width=True, key=f"save_global_budget_{trip_id}"):
                        if total_budget_input is None or float(total_budget_input) <= 0:
                            st.warning("⚠️ Въведете сума за бюджета.")
                        elif save_budget_config(trip_id, "global", total_amount=total_budget_input):
                            st.success("✅ Общият бюджет е записан.")
                            st.rerun()
                        else:
                            st.error("❌ Бюджетът не можа да бъде записан.")
                else:
                    st.caption("Задай 0 EUR на категория, която не искаш да лимитираш.")
                    inputs = {}
                    budget_cats = [cat for cat in KATEGORII if cat != "Депозит/Резервация"]
                    c1, c2 = st.columns(2)
                    for i, cat in enumerate(budget_cats):
                        with (c1 if i % 2 == 0 else c2):
                            existing_category_budget = float(category_budgets.get(cat, 0.0) or 0.0)
                            inputs[cat] = st.number_input(
                                f"{get_emoji(cat)} {get_display_category(cat)}",
                                min_value=0.0,
                                value=(existing_category_budget if existing_category_budget > 0 else None),
                                placeholder="Въведете сума...",
                                step=50.0,
                                format="%.2f",
                                key=f"cat_budget_{trip_id}_{i}"
                            )
                    if st.button("💾 Запази бюджетите по категории", type="primary", use_container_width=True, key=f"save_category_budgets_{trip_id}"):
                        has_any_category_budget = any(
                            value is not None and float(value) > 0
                            for value in inputs.values()
                        )
                        if not has_any_category_budget:
                            st.warning("⚠️ Въведете поне една сума за бюджет.")
                        elif save_budget_config(trip_id, "category", budgets=inputs):
                            st.success("✅ Бюджетите по категории са записани.")
                            st.rerun()
                        else:
                            st.error("❌ Бюджетите не можаха да бъдат записани.")
            _budget_settings_dialog()

    # ОБЩ БЮДЖЕТ — същият 3D контейнер и същата прогрес лента
    # като при „Общо по Категории“.
    if global_budget > 0:
        global_spent = float(depozit_hotel + total_on_site)
        global_remaining = float(global_budget - global_spent)
        global_pct = max(0.0, min(100.0, (global_spent / global_budget) * 100.0))
        remaining_text = (
            f"Остават {global_remaining:.2f} EUR"
            if global_remaining >= 0
            else f"Над бюджета с {abs(global_remaining):.2f} EUR"
        )
        remaining_color = "#8bd5ff" if global_remaining >= 0 else "#ff4b4b"

        st.markdown(f"""
        <div style="background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.08);padding:12px 15px;border-radius:14px;margin-bottom:15px;font-family:inherit;">
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:7px;font-family:inherit;">
                <span style="color:#aeb5c0;font-weight:700;font-family:inherit;">Общ бюджет</span>
                <span style="font-weight:800;font-family:inherit;">{global_spent:.2f} / {global_budget:.2f} EUR</span>
            </div>
            <div style="height:16px;background:rgba(0,0,0,.45);border-radius:20px;padding:2px;box-shadow:inset 2px 2px 5px rgba(0,0,0,.5), inset -1px -1px 2px rgba(255,255,255,.05);position:relative;display:flex;align-items:center;overflow:hidden;">
                <div style="width:{global_pct:.2f}%;height:100%;background:{'#ff4b4b' if global_remaining < 0 else 'linear-gradient(90deg,#4facfe 0%,#00f2fe 100%)'};border-radius:20px;box-shadow:2px 2px 5px rgba(0,242,254,.35),inset 0 2px 2px rgba(255,255,255,.3);transition:width .5s ease-in-out;"></div>
                <span style="position:absolute;right:8px;font-size:10px;font-weight:900;color:rgba(255,255,255,.85);text-shadow:1px 1px 2px rgba(0,0,0,.8);font-family:inherit;">{global_pct:.1f}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-top:6px;font-family:inherit;">
                <span style="color:#ffd43b;font-family:inherit;">🟡 Бюджет</span>
                <span style="color:{remaining_color};font-weight:800;font-family:inherit;">{remaining_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if active_budget_mode != "none" and global_budget <= 0:
        total_pct_budget = max(0.0, min(100.0, active_budget_spent / active_budget_total * 100.0))
        remaining_text = f"Остават {active_budget_remaining:.2f} EUR" if active_budget_remaining >= 0 else f"Над бюджета с {abs(active_budget_remaining):.2f} EUR"
        remaining_color = "#8bd5ff" if active_budget_remaining >= 0 else "#ff4b4b"
        budget_label = "Общ бюджет" if active_budget_mode == "global" else "Общо по Категории"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.08);padding:12px 15px;border-radius:14px;margin-bottom:15px;font-family:inherit;">
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:7px;font-family:inherit;">
                <span style="color:#aeb5c0;font-weight:700;font-family:inherit;">{budget_label}</span>
                <span style="font-weight:800;font-family:inherit;">{active_budget_spent:.2f} / {active_budget_total:.2f} EUR</span>
            </div>
            <div style="height:16px;background:rgba(0,0,0,.45);border-radius:20px;padding:2px;box-shadow:inset 2px 2px 5px rgba(0,0,0,.5), inset -1px -1px 2px rgba(255,255,255,.05);position:relative;display:flex;align-items:center;overflow:hidden;">
                <div style="width:{total_pct_budget:.2f}%;height:100%;background:{'#ff4b4b' if active_budget_remaining < 0 else 'linear-gradient(90deg,#4facfe 0%,#00f2fe 100%)'};border-radius:20px;box-shadow:2px 2px 5px rgba(0,242,254,.35),inset 0 2px 2px rgba(255,255,255,.3);transition:width .5s ease-in-out;"></div>
                <span style="position:absolute;right:8px;font-size:10px;font-weight:900;color:rgba(255,255,255,.85);text-shadow:1px 1px 2px rgba(0,0,0,.8);font-family:inherit;">{total_pct_budget:.1f}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-top:6px;font-family:inherit;">
                <span style="color:#ffd43b;font-family:inherit;">🟡 Бюджет</span>
                <span style="color:{remaining_color};font-weight:800;font-family:inherit;">{remaining_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        with stat_grid[idx % 2]:
            # Процентният бар показва дела на категорията от всички изхарчени средства
            # за пътуването, включително платените депозити.
            grand_total_for_analysis = depozit_hotel + total_on_site
            pct = (s_value / grand_total_for_analysis * 100) if grand_total_for_analysis > 0 else 0.0
            display_kat = get_display_category(kat)
            budget = float(category_budgets.get(kat, 0.0) or 0.0) if active_budget_mode == "category" else 0.0

            if budget <= 0:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between; font-family: inherit;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 500; font-size: 15px; font-family: inherit;">{get_emoji(kat)} {display_kat}</span>
                        <span style="font-weight: bold; color: #ff4b4b; font-size: 15px; font-family: inherit;">{s_value:.2f} EUR</span>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5), inset -1px -1px 2px rgba(255,255,255,0.05); position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 4px;">
                        <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 20px; box-shadow: 2px 2px 5px rgba(0, 242, 254, 0.4), inset 0 2px 2px rgba(255,255,255,0.3); transition: width 0.5s ease-in-out;"></div>
                        <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: rgba(255,255,255,0.85); text-shadow: 1px 1px 2px rgba(0,0,0,0.8); font-family: inherit;">{pct:.1f}%</span>
                    </div>
                    {"<div style='font-size:10px;color:#7e8494;margin-top:5px;font-family:inherit;'>Бюджет: няма зададен</div>" if active_budget_mode == "category" else ""}
                </div>
                """, unsafe_allow_html=True)
            else:
                ratio = s_value / budget
                fill_pct = min(100.0, max(0.0, ratio * 100.0))
                over = s_value > budget
                remaining = budget - s_value
                fill_gradient = "#ff4b4b" if over else "linear-gradient(90deg, #4facfe 0%, #00f2fe 100%)"
                status_html = (
                    f"<span style='color:#ff4b4b;font-weight:800;font-family:inherit;'>Над бюджета с {abs(remaining):.2f} EUR</span>"
                    if over else
                    f"<span style='color:#8bd5ff;font-weight:800;font-family:inherit;'>Остават {remaining:.2f} EUR</span>"
                )
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between; font-family: inherit;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 500; font-size: 15px; font-family: inherit;">{get_emoji(kat)} {display_kat}</span>
                        <span style="font-weight: bold; color: #ff4b4b; font-size: 15px; font-family: inherit;">{s_value:.2f} EUR</span>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5), inset -1px -1px 2px rgba(255,255,255,0.05); position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 4px;">
                        <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 20px; box-shadow: 2px 2px 5px rgba(0, 242, 254, 0.4), inset 0 2px 2px rgba(255,255,255,0.3); transition: width 0.5s ease-in-out;"></div>
                        <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: rgba(255,255,255,0.85); text-shadow: 1px 1px 2px rgba(0,0,0,0.8); font-family: inherit;">{pct:.1f}%</span>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5), inset -1px -1px 2px rgba(255,255,255,0.05); position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 4px;">
                        <div style="width: {fill_pct}%; height: 100%; background: {fill_gradient}; border-radius: 20px; box-shadow: 2px 2px 5px rgba(0, 242, 254, 0.35), inset 0 2px 2px rgba(255,255,255,0.3); transition: width 0.5s ease-in-out;"></div>
                        <div style="position: absolute; right: 0; top: -3px; width: 3px; height: 19px; background: #ffd43b; border-radius: 3px; box-shadow: 0 0 8px rgba(255,212,59,0.75);"></div>
                        <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: rgba(255,255,255,0.85); text-shadow: 1px 1px 2px rgba(0,0,0,0.8); font-family: inherit;">{min(100.0, ratio*100.0):.1f}%</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-top:6px;font-family:inherit;">
                        <span style="color:#ffd43b;font-family:inherit;">🟡 Бюджет</span>
                        {status_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # =========================================================
    # ДНЕВЕН БЮДЖЕТ + ТЕМП НА ХАРЧЕНЕ
    # Хотелът и депозитът НЕ участват в тези два показателя.
    # Общият бюджет и общата прогрес лента продължават да включват всичко.
    # =========================================================
    if active_budget_mode != "none" and active_budget_total > 0:
        try:
            start_date_obj = datetime.datetime.strptime(st_date, "%d.%m.%Y").date() if st_date and st_date != "nan" else None
            end_date_obj = datetime.datetime.strptime(en_date, "%d.%m.%Y").date() if en_date and en_date != "nan" else None
            today_obj = datetime.date.today()

            if start_date_obj and end_date_obj:
                total_days = max(1, (end_date_obj - start_date_obj).days + 1)
                elapsed_days = max(1, min(total_days, (today_obj - start_date_obj).days + 1))
                days_remaining = max(0, total_days - elapsed_days)

                # Хотел + депозит се отделят от ежедневното харчене.
                hotel_spent_for_pace = float(df_expenses[df_expenses["category"] == "Нощувки/Хотел"]["amount"].sum())
                deposit_spent_for_pace = float(depozit_hotel)

                # Разходи на място без хотел. Депозитите не са в total_on_site,
                # но ги изваждаме отделно от бюджетния пул за яснота.
                daily_spent_total = max(0.0, float(total_on_site) - hotel_spent_for_pace)

                if active_budget_mode == "category":
                    # При категориален бюджет махаме бюджета на хотелската категория.
                    hotel_budget_for_pace = float(category_budgets.get("Нощувки/Хотел", 0.0) or 0.0)
                    daily_budget_total = max(0.0, float(active_budget_total) - hotel_budget_for_pace)
                else:
                    # При общ бюджет махаме вече платения хотел + депозит от дневния пул.
                    daily_budget_total = max(0.0, float(active_budget_total) - hotel_spent_for_pace - deposit_spent_for_pace)

                daily_budget_remaining = daily_budget_total - daily_spent_total
                daily_target = daily_budget_total / total_days
                avg_daily_spend = daily_spent_total / elapsed_days
                projected_total = avg_daily_spend * total_days
                forecast_delta = daily_budget_total - projected_total

                daily_remaining_budget = daily_budget_remaining / days_remaining if days_remaining > 0 else daily_budget_remaining
                daily_status = (
                    f"€{daily_remaining_budget:.2f} / ден" if days_remaining > 0 and daily_budget_remaining >= 0
                    else "Бюджетът е изчерпан" if daily_budget_remaining < 0
                    else "Пътуването приключва днес"
                )

                forecast_color = "#8bd5ff" if forecast_delta >= 0 else "#ff4b4b"
                forecast_text = (
                    f"Очакван остатък: €{forecast_delta:.2f}" if forecast_delta >= 0
                    else f"Очаквано надхвърляне: €{abs(forecast_delta):.2f}"
                )

                daily_card = f"""
                <div class='tm-budget-card-inner tm-budget-accent-daily' style='background:linear-gradient(135deg,rgba(255,255,255,.03),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.08);padding:20px;border-radius:16px;height:100%;font-family:inherit;box-shadow:4px 4px 12px rgba(0,0,0,.3);'>
                    <div style='font-size:12px;color:#8b929e;font-weight:700;letter-spacing:.3px;'>📅 ДНЕВЕН ЛИМИТ</div>
                    <div style='font-size:26px;color:#ffffff;font-weight:900;margin-top:6px;'>€{daily_target:.2f}</div>
                    <div style='font-size:11px;color:#7e8494;margin-top:2px;'>По план</div>
                    <div style='margin-top:12px;font-size:12px;color:#aeb5c0;'>Остават <b style='color:#ffffff;'>{days_remaining}</b> дни</div>
                    <div style='margin-top:4px;font-size:12px;color:#aeb5c0;'>Препоръчително оттук: <b style='color:#8bd5ff;'>{daily_status}</b></div>
                </div>
                """

                pace_card = f"""
                <div class='tm-budget-card-inner tm-budget-accent-pace' style='background:linear-gradient(135deg,rgba(255,255,255,.03),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.08);padding:20px;border-radius:16px;height:100%;font-family:inherit;box-shadow:4px 4px 12px rgba(0,0,0,.3);'>
                    <div style='font-size:12px;color:#8b929e;font-weight:700;letter-spacing:.3px;'>📈 ТЕМП НА ХАРЧЕНЕ</div>
                    <div style='font-size:26px;color:#ffffff;font-weight:900;margin-top:6px;'>€{avg_daily_spend:.2f}</div>
                    <div style='font-size:11px;color:#7e8494;margin-top:2px;'>Изхарчени средно</div>
                    <div style='margin-top:12px;font-size:12px;color:#aeb5c0;'>Прогноза до края: <b style='color:#ffffff;'>€{projected_total:.2f}</b></div>
                    <div style='margin-top:4px;font-size:12px;color:{forecast_color};font-weight:800;'>{forecast_text}</div>
                </div>
                """

                # =========================================================
                # СТАТУС НА ТРЕТАТА КАРТА
                # Сравняваме реалното средно харчене на ден
                # директно с дневния лимит.
                # =========================================================
                pace_difference = avg_daily_spend - daily_target
                pace_ratio = (avg_daily_spend / daily_target) if daily_target > 0 else 0.0

                # Статусът на третата карта:
                # до 80% от дневния лимит -> зелено
                # над 80% до 100% -> жълто
                # над 100% -> червено
                if pace_ratio <= 0.80:
                    health_icon = "🟢"
                    health_title = "БЮДЖЕТЪТ ВЪРВИ ДОБРЕ"
                    health_color = "#2ebd59"
                elif pace_ratio <= 1.00:
                    health_icon = "🟡"
                    health_title = "ХАРЧИШ ПО-БЪРЗО ОТ ПЛАНА"
                    health_color = "#ffaa00"
                else:
                    health_icon = "🔴"
                    health_title = "ХАРЧИШ ПРЕКАЛЕНО БЪРЗО"
                    health_color = "#ff3b30"

                if pace_difference < 0:
                    health_text = f"Под плана си с €{abs(pace_difference):.2f}/ден"
                elif pace_difference > 0:
                    health_text = f"Над плана си с €{pace_difference:.2f}/ден"
                else:
                    health_text = "Точно по плана си"

                # Запазваме стария вътрешен блок валиден, въпреки че не се визуализира.
                planned_to_date = daily_budget_total * elapsed_days / total_days

                health_card = f"""
                <div style='background:linear-gradient(135deg,rgba(255,255,255,.04),rgba(255,255,255,.015));border:1px solid rgba(255,255,255,.09);padding:15px 16px;border-radius:16px;margin-top:12px;font-family:inherit;box-shadow:0 6px 18px rgba(0,0,0,.16);'>
                    <div style='font-size:12px;color:{health_color};font-weight:800;letter-spacing:.3px;'>{health_icon} {health_title}</div>
                    <div style='font-size:12px;color:#aeb5c0;margin-top:9px;'>Реално до момента: <b style='color:#ffffff;'>€{daily_spent_total:.2f}</b> · План до момента: <b style='color:#ffffff;'>€{planned_to_date:.2f}</b></div>
                    <div style='margin-top:5px;font-size:12px;color:{health_color};font-weight:800;'>{health_text}</div>
                    <div style='margin-top:4px;font-size:11px;color:#7e8494;'>Прогноза: <b style='color:#ffffff;'>€{projected_total:.2f}</b> от бюджет €{daily_budget_total:.2f}</div>
                </div>
                """

                # Трите показателя са компактни 3D карти – удобни и на телефон.
                cards_css = """
                <style>
                .tm-budget-mini-card {
                    position:relative; overflow:hidden; min-height:146px;
                    margin-bottom:1px !important;
                    padding:20px; border-radius:16px;
                    font-family:inherit;
                    background:linear-gradient(135deg,rgba(255,255,255,.03),rgba(255,255,255,.01));
                    border:1px solid rgba(255,255,255,.08);
                    box-shadow:4px 4px 12px rgba(0,0,0,.3);
                }
                .tm-budget-mini-card:after {
                    content:""; position:absolute; left:-30px; top:-45px; width:110px; height:110px;
                    border-radius:50%; background:rgba(255,255,255,.035); filter:blur(2px); pointer-events:none;
                }
                .tm-budget-accent-daily { border-color:rgba(0,242,254,.36) !important; box-shadow:4px 4px 12px rgba(0,0,0,.3), inset 0 1px 0 rgba(0,242,254,.10) !important; }
                .tm-budget-accent-pace { border-color:rgba(155,124,255,.36) !important; box-shadow:4px 4px 12px rgba(0,0,0,.3), inset 0 1px 0 rgba(155,124,255,.10) !important; }
                .tm-budget-accent-health { border-color:rgba(255,212,59,.42) !important; box-shadow:4px 4px 12px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,212,59,.12) !important; }
                .tm-budget-mini-label { font-size:11px; font-weight:800; letter-spacing:.35px; color:#9aa1ad; }
                .tm-budget-mini-value { font-size:24px; font-weight:900; color:#fff; margin-top:5px; line-height:1.05; }
                .tm-budget-mini-sub { font-size:10px; color:#7e8494; margin-top:4px; }
                .tm-budget-mini-line { font-size:11px; color:#b7bec9; margin-top:10px; }
                </style>
                """
                st.markdown(cards_css, unsafe_allow_html=True)

                health_card_compact = f"""
                <div class='tm-budget-mini-card tm-budget-card-inner tm-budget-accent-health'>
                    <div class='tm-budget-mini-label'>
                        <span style='color:{health_color};font-size:10px;'>●</span>
                        <span style='color:#9aa1ad;'> БЮДЖЕТ - Дневен Лимит</span>
                    </div>
                    <div class='tm-budget-mini-value' style='font-size:15px;line-height:1.2;color:{health_color};margin-top:9px;'>{health_title}</div>
                    <div class='tm-budget-mini-line'>Реално: <b style='color:#fff;'>€{avg_daily_spend:.2f}/ден</b></div>
                    <div class='tm-budget-mini-line' style='margin-top:4px;'>План: <b style='color:#fff;'>€{daily_target:.2f}/ден</b></div>
                    <div style='margin-top:7px;font-size:9px;color:#7e8494;font-weight:700;letter-spacing:.1px;'>ℹ️ Нощувки и хотел не са включени</div>
                    <div class='tm-budget-mini-sub' style='margin-top:5px;color:{health_color};font-size:12px;line-height:1.25;font-weight:800;'>{health_text}</div>
                </div>
                """
                daily_compact = daily_card
                pace_compact = pace_card

                # Един собствен HTML контейнер за трите карти.
                # Така spacing-ът работи надеждно и при мобилното подреждане,
                # без да разчитаме на поведението на st.columns.
                three_budget_cards = f"""
                <style>
                    .tm-budget-three-cards {{
                        display:grid;
                        grid-template-columns:repeat(3,minmax(0,1fr));
                        gap:6px;
                        width:100%;
                        align-items:stretch;
                    }}
                    .tm-budget-three-cards > .tm-budget-slot {{
                        min-width:0;
                    }}
                    @media (max-width: 640px) {{
                        .tm-budget-three-cards {{
                            grid-template-columns:1fr;
                            gap:6px;
                        }}
                    }}
                </style>
                <div class='tm-budget-three-cards'>
                    <div class='tm-budget-slot'>{daily_compact}</div>
                    <div class='tm-budget-slot'>{pace_compact}</div>
                    <div class='tm-budget-slot'>{health_card_compact}</div>
                </div>
                <div style='height:14px'></div>
                """
                st.markdown(three_budget_cards, unsafe_allow_html=True)
        except Exception:
            pass

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
                        if st.button("🗑️", key=f"quick_del_{idx}", use_container_width=True, disabled=trip_locked):
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




    st.markdown("""
    <style>
    @media (max-width: 640px) {
        /* Компактна навигация за горивото: 18% / 64% / 18% на един ред. */
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            min-width: 0 !important;
            gap: 0.25rem !important;
            align-items: center !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
            max-width: none !important;
            flex-shrink: 0 !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1),
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(3) {
            flex: 0 0 18% !important;
            max-width: 18% !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
            flex: 1 1 64% !important;
            max-width: 64% !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-fuel-nav-marker) + div[data-testid="stHorizontalBlock"] button {
            width: 100% !important;
            min-width: 0 !important;
            min-height: 34px !important;
            padding: 0.1rem 0.2rem !important;
        }


        /* Само текстът на задачата: ляво подравняване, без промяна на mobile layout-а. */
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button {
            text-align: left !important;
            justify-content: flex-start !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button > div,
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button > div > div,
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button [data-testid="stMarkdownContainer"],
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button p,
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button span {
            text-align: left !important;
            justify-content: flex-start !important;
            align-items: flex-start !important;
            width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }

        /* Компактен ред за задачите: текстът + кошчето остават на един ред. */
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            min-width: 0 !important;
            gap: 0.25rem !important;
            align-items: center !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1) {
            flex: 1 1 auto !important;
            max-width: calc(100% - 48px) !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
            flex: 0 0 42px !important;
            max-width: 42px !important;
        }
        div[data-testid="stElementContainer"]:has(.compact-task-row-marker) + div[data-testid="stHorizontalBlock"] button {
            width: 100% !important;
            min-width: 0 !important;
            min-height: 38px !important;
            padding: 0.15rem 0.25rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # =========================================================
    # 🧳 ПЛАН НА ПЪТУВАНЕТО
    # =========================================================
    plan_df = get_trip_plan(trip_id)
    plan_done = int(plan_df["done"].sum()) if not plan_df.empty else 0
    plan_total = len(plan_df)
    plan_pct = (plan_done / plan_total * 100.0) if plan_total else 0.0

    st.markdown("""
    <style>
        .tm-plan-header {
            display:flex; justify-content:space-between; align-items:center; gap:10px;
            margin:14px 14px 10px 14px;
            padding-bottom:10px;
            border-bottom:1px solid rgba(255,255,255,.06);
        }
        .tm-plan-title-wrap { display:flex; align-items:center; gap:10px; min-width:0; }
        .tm-plan-title { color:#fff; font-size:15px; font-weight:800; letter-spacing:.25px; }
        .tm-plan-count {
            color:#aeb5c0; font-size:11px; white-space:nowrap;
            padding:4px 8px; border-radius:999px;
            background:rgba(255,255,255,.035);
            border:1px solid rgba(255,255,255,.06);
        }
        .tm-plan-progress-wrap { margin:0 14px 12px 14px; }
        .tm-plan-progress {
            height:6px; width:100%;
            background:rgba(255,255,255,.07);
            border-radius:99px; overflow:hidden;
            box-shadow:inset 0 1px 2px rgba(0,0,0,.35);
        }
        .tm-plan-progress-fill {
            height:100%;
            background:linear-gradient(90deg,#9b7cff,#b79cff);
            border-radius:99px;
        }
        .tm-plan-progress-meta {
            display:flex; justify-content:flex-end;
            margin-top:5px; color:#8f96a3; font-size:10px;
        }
        .tm-plan-list {
            margin:0 10px 10px 10px;
            padding-top:2px;
        }
        @media (max-width:640px) {
            .tm-plan-title { font-size:14px; }
            .tm-plan-header { margin:12px 12px 9px 12px; }
            .tm-plan-progress-wrap { margin:0 12px 10px 12px; }
            .tm-plan-list { margin:0 8px 8px 8px; }
        }
        @media (max-width:640px) {
            .tm-plan-title { font-size:14px; }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='tm-section-title' style='margin-bottom:12px;'><span class='tm-section-number tm-n3'>3</span><span>ПЛАН НА ПЪТУВАНЕТО</span></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="tm-plan-progress-wrap">
        <div class="tm-plan-progress"><div class="tm-plan-progress-fill" style="width:{plan_pct:.2f}%;"></div></div>
        <div class="tm-plan-progress-meta">{plan_pct:.1f}% завършено · {plan_done}/{plan_total} изпълнени</div>
    </div>
    """, unsafe_allow_html=True)

    plan_col1, plan_col2 = st.columns([1, 1])
    with plan_col1:
        plan_input_key = f"trip_plan_new_{trip_id}"
        new_plan_item = st.text_input(
            "Добави задача",
            placeholder="Пътуването е приключено." if float(e_km) > 0.0 else "напр. Резервация за ресторант...",
            key=plan_input_key,
            disabled=float(e_km) > 0.0,
        )
    with plan_col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        plan_input_key = f"trip_plan_new_{trip_id}"
        plan_locked = float(e_km) > 0.0
        if st.button(
            "🔒 Пътуването е приключено" if plan_locked else "➕ Добави в плана",
            use_container_width=True,
            key=f"trip_plan_add_{trip_id}",
            on_click=None if plan_locked else _add_plan_item_and_clear,
            args=(trip_id, plan_input_key),
            disabled=plan_locked,
        ):
            pass

    if not plan_df.empty:
        st.markdown("<div class='tm-plan-list'>", unsafe_allow_html=True)
        for row_num, (_, plan_row) in enumerate(plan_df.iterrows()):
            st.markdown("<div class='compact-task-row-marker'></div>", unsafe_allow_html=True)
            item_id = str(plan_row["item_id"])
            item_done = bool(plan_row.get("done", False))
            title = str(plan_row.get("title", "Задача"))
            icon = "✅" if item_done else "⬜"
            task_row = st.container(horizontal=True, vertical_alignment="center", gap="small")
            with task_row:
                left_shift = max(18, min(55, 72 - len(title)))
                task_label = f"{icon} {title}" + "\u00a0" * left_shift
                st.button(task_label, key=f"task_toggle_{trip_id}_{item_id}", on_click=_toggle_plan_item, args=(item_id,), width="stretch")
                st.button("🗑️", key=f"task_delete_{trip_id}_{item_id}", on_click=_delete_plan_item, args=(item_id,), width="content")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#7e8494;font-size:12px;margin-top:12px;margin-bottom:4px;'>Добави резервации, места или задачи, които не искаш да забравиш.</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='tm-section-title' style='margin-bottom:10px;'><span class='tm-section-number tm-n4'>4</span><span>КАРТА НА СПИРКИТЕ И ДЕСТИНАЦИИТЕ</span></div>", unsafe_allow_html=True)
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
            
    if "active_click" in st.session_state and st.session_state["active_click"] is not None and not trip_locked:
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
    def _delete_map_point(idx):
        try:
            df_map = pd.read_csv(MAP_FILE, encoding="utf-8")
            if idx in df_map.index:
                df_map = df_map.drop(index=idx)
                df_map.to_csv(MAP_FILE, index=False, encoding="utf-8")
        except Exception:
            pass

    if not df_points.empty:
        st.markdown("<div class='tm-section-title' style='margin-top:4px;margin-bottom:10px;'><span class='tm-section-number tm-n5'>5</span><span>Любими места от пътуването</span></div>", unsafe_allow_html=True)
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
                    st.button(
                        "❌",
                        key=f"del_pin_{idx}",
                        use_container_width=True,
                        disabled=trip_locked,
                        on_click=_delete_map_point,
                        args=(idx,)
                    )
        except Exception:
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
                min-height: 38.4px !important;
                box-sizing: border-box !important;
                background: linear-gradient(135deg, #252932, #16191f) !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 12px !important;
                padding: 0.25rem 0.75rem !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                letter-spacing: 0.5px !important;
                cursor: pointer !important;
                user-select: none !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
                transition: all 0.25s ease !important;
            }
            .twin-premium-3d-btn:hover {
                background: linear-gradient(135deg, #2e343f, #1c2028) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
                border-color: rgba(0, 242, 254, 0.2) !important;
            }
            .twin-premium-3d-btn:active {
                transform: translateY(0) !important;
                box-shadow: 0 3px 10px rgba(0,0,0,0.3) !important;
            }
            .twin-grid-wrapper a {
                text-decoration: none !important;
                width: 100% !important;
                display: block !important;
            }
        
/* ===== V11 SAFE CARD BUTTONS ===== */
div[class*="st-key-trip_card_"] div[data-testid="stButton"] {
    position: relative !important;
    z-index: 3 !important;
    margin-top: 6px !important;
}
div[class*="st-key-trip_card_"] div[data-testid="stButton"] button {
    width: 100% !important;
    min-height: 42px !important;
    text-align: left !important;
    justify-content: flex-start !important;
}
/* ===== END V11 SAFE CARD BUTTONS ===== */
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
                    for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, LABELS_FILE, CATEGORY_BUDGETS_FILE]:
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
                            for f_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, LABELS_FILE, CATEGORY_BUDGETS_FILE]:
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
        st.markdown("##### 🔓 Редакция на приключено пътуване")
        st.caption("Отключването е временно. Крайните километри и статусът „Приключено“ се запазват. След редакцията натисни „🔒 Заключи редакцията“.")

        finished_trips_admin = get_finished_trip_ids()
        if finished_trips_admin:
            finished_trip_labels = {tid: tid.replace("_", " ") for tid in finished_trips_admin}
            current_unlocked_admin = st.session_state.get("edit_unlocked_trip")

            if current_unlocked_admin in finished_trips_admin:
                st.success(f"✏️ В момента е отключено: **{finished_trip_labels[current_unlocked_admin]}**")
                if st.button("🔒 ЗАКЛЮЧИ РЕДАКЦИЯТА", use_container_width=True, type="primary", key="admin_relock_finished_trip_btn"):
                    lock_trip_editing(current_unlocked_admin)
                    st.rerun()
            else:
                admin_finished_choice = st.selectbox(
                    "Избери приключено пътуване:",
                    finished_trips_admin,
                    format_func=lambda tid: f"🔴 {finished_trip_labels.get(tid, tid.replace('_', ' '))}",
                    key="admin_finished_trip_select"
                )
                if st.button("🔓 ОТКЛЮЧИ ЗА РЕДАКЦИЯ", use_container_width=True, type="primary", key="admin_unlock_finished_trip_btn"):
                    st.session_state["edit_unlocked_trip"] = str(admin_finished_choice)
                    st.session_state["current_trip"] = str(admin_finished_choice)
                    st.session_state["show_admin_panel"] = False
                    st.rerun()
        else:
            st.info("Няма приключени пътувания за отключване.")

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

        current_fuel_threshold = float(UI_LABELS.get("fuel_red_threshold", 1.80) or 1.80)
        new_fuel_threshold = st.number_input(
            "⛽ Гориво — червено над (EUR/л):",
            min_value=0.01,
            value=current_fuel_threshold,
            step=0.05,
            format="%.2f",
            help="Цената за литър ще се визуализира в червено, когато е над тази стойност. До прага остава зелена."
        )

        if st.button("💾 Запази настройките", use_container_width=True, type="primary", key="save_category_labels_btn"):
            if new_accommodation_labels == "Хотелски такси + Депозит за резервация":
                hotel_label = "Хотелски такси"
                deposit_label = "Депозит за резервация"
            else:
                hotel_label = "Нощувки/Хотел"
                deposit_label = "Депозит/Резервация"

            if save_ui_labels(new_pet_label, hotel_label, deposit_label, new_fuel_threshold):
                st.success("✅ Настройките са запазени.")
                st.rerun()
            else:
                st.error("❌ Неуспешно запазване на имената на категориите.")
