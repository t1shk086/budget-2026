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
import re

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# =========================================================
# GLASSMORPHISM DESIGN - MODERN UI
# =========================================================
st.markdown("""
<style>
    :root {
        --primary-green: #00f2fe;
        --secondary-green: #63d391;
        --accent-yellow: #ffd43b;
        --accent-orange: #ff8a65;
        --dark-bg: #0a0e11;
        --card-bg: rgba(255, 255, 255, 0.04);
        --card-border: rgba(255, 255, 255, 0.08);
        --text-primary: #ffffff;
        --text-secondary: #aeb5c0;
        --text-muted: #7e8494;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }

    /* GLASSMORPHISM CARDS */
    .glass-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 18px !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        transition: all 0.3s ease !important;
    }

    .glass-card:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04)) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.1) !important;
    }

    /* INPUT FIELDS */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 12px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }

    /* BUTTONS */
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #00f2fe 0%, #63d391 100%) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3) !important;
        transition: all 0.25s ease !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
        padding: 12px 20px !important;
    }

    button[data-testid="stBaseButton-secondary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(0, 242, 254, 0.4) !important;
    }

    /* SECONDARY BUTTON STYLE */
    button[data-testid="stBaseButton-secondary"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)) !important;
        color: #fff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    button[data-testid="stBaseButton-secondary"]:hover {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(0, 242, 254, 0.05)) !important;
        border-color: rgba(0, 242, 254, 0.3) !important;
    }

    /* TEXT STYLING */
    h1, h2, h3 {
        font-family: 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 900 !important;
        letter-spacing: 0.3px !important;
    }

    h1 {
        background: linear-gradient(135deg, #00f2fe, #63d391) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 32px !important;
    }

    h2 {
        color: #00f2fe !important;
        font-size: 24px !important;
    }

    h3 {
        color: #ffffff !important;
        font-size: 18px !important;
    }

    small {
        color: #7e8494 !important;
    }

    /* PROGRESS BARS */
    .progress-bar {
        background: rgba(0, 0, 0, 0.3) !important;
        border-radius: 20px !important;
        height: 14px !important;
        overflow: hidden !important;
        box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.45) !important;
    }

    .progress-fill {
        height: 100% !important;
        background: linear-gradient(90deg, #00f2fe 0%, #63d391 100%) !important;
        border-radius: 20px !important;
        box-shadow: inset 0 2px 2px rgba(255, 255, 255, 0.25) !important;
        transition: width 0.5s ease !important;
    }

    /* STAT CARDS */
    .stat-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01)) !important;
        border: 1px solid rgba(0, 242, 254, 0.15) !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
    }

    .stat-card:hover {
        border-color: rgba(0, 242, 254, 0.3) !important;
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.08), rgba(0, 242, 254, 0.02)) !important;
    }

    /* TRIP CARDS */
    .trip-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.01)) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    .trip-card:hover {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.08), rgba(0, 242, 254, 0.02)) !important;
        border-color: rgba(0, 242, 254, 0.3) !important;
        transform: translateX(4px) !important;
    }

    /* ANIMATIONS */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fadeIn 0.4s ease-in-out !important;
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.03);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0, 242, 254, 0.3);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 242, 254, 0.5);
    }

    /* RESPONSIVE DESIGN */
    @media (max-width: 768px) {
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 16px !important; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FULLSCREEN BUTTON
# =========================================================
components.html(
    """
    <style>
        #fullscreenBtn {
            position: fixed;
            top: 12px;
            right: 16px;
            z-index: 999999;
            width: 34px;
            height: 34px;
            border: none;
            border-radius: 9px;
            background: transparent;
            color: #8b8f98;
            font-size: 20px;
            font-weight: 400;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0.65;
            transition: all 0.2s ease;
        }

        #fullscreenBtn:hover {
            opacity: 1;
            color: #b0b4bc;
            background: rgba(255,255,255,0.06);
            transform: scale(1.04);
        }

        #fullscreenBtn:active {
            transform: scale(0.94);
        }

        #fullscreenBtn.exit {
            transform: rotate(180deg);
        }

        #fullscreenBtn.exit:hover {
            transform: rotate(180deg) scale(1.04);
        }

        #fullscreenBtn.exit:active {
            transform: rotate(180deg) scale(0.94);
        }
    </style>

    <button id="fullscreenBtn" title="Fullscreen">⛶</button>

    <script>
        const btn = document.getElementById("fullscreenBtn");

        function updateFullscreenIcon() {
            if (window.parent.document.fullscreenElement) {
                btn.classList.add("exit");
                btn.title = "Изход от Fullscreen";
            } else {
                btn.classList.remove("exit");
                btn.title = "Fullscreen";
            }
        }

        btn.addEventListener("click", async () => {
            try {
                if (!window.parent.document.fullscreenElement) {
                    await window.parent.document.documentElement.requestFullscreen();
                } else {
                    await window.parent.document.exitFullscreen();
                }
                updateFullscreenIcon();
            } catch (error) {
                console.log("Fullscreen error:", error);
            }
        });

        window.parent.document.addEventListener("fullscreenchange", updateFullscreenIcon);
        updateFullscreenIcon();
    </script>
    """,
    height=48,
)

# =========================================================
# DATA FILES & CONFIGURATION
# =========================================================
KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"
TRIP_PLAN_FILE = "trip_plan_2026.csv"
CATEGORY_BUDGETS_FILE = "trip_category_budgets_2026.csv"

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

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "💳"}
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
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": "", "trip_finished": "Не"}
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
                "end_date": str(res.get("end_date", "")),
                "trip_finished": str(res.get("trip_finished", "Не"))
            }
    except:
        pass
    return d

def get_trip_display_name(t_id):
    name = str(t_id).replace("_", " ")
    marker = " __ "
    if marker in name:
        base_name, suffix = name.rsplit(marker, 1)
        if suffix.strip().isdigit():
            return base_name.strip()
    return name

def get_unique_trip_id(base_id):
    base_id = str(base_id).strip()
    try:
        existing_ids = set()
        if os.path.exists(DATA_FILE):
            existing_ids.update(str(x).strip() for x in pd.read_csv(DATA_FILE, encoding="utf-8")["trip_id"].dropna().unique())
        if os.path.exists(SETTINGS_FILE):
            existing_ids.update(str(x).strip() for x in pd.read_csv(SETTINGS_FILE, encoding="utf-8")["trip_id"].dropna().unique())
        if os.path.exists(CATEGORY_BUDGETS_FILE):
            existing_ids.update(str(x).strip() for x in pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")["trip_id"].dropna().unique())
    except Exception:
        existing_ids = set()

    if base_id not in existing_ids:
        return base_id

    n = 2
    while f"{base_id}__{n}" in existing_ids:
        n += 1
    return f"{base_id}__{n}"

def rename_trip(old_id, new_name):
    try:
        old_id = str(old_id).strip()
        new_name = str(new_name).strip()
        if not old_id or not new_name:
            return False, "Името не може да бъде празно."
        base_id = new_name.replace(" ", "_")
        all_ids = set()
        for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, TRIP_PLAN_FILE, CATEGORY_BUDGETS_FILE]:
            if os.path.exists(file_name):
                try:
                    df_tmp = pd.read_csv(file_name, encoding="utf-8")
                    if "trip_id" in df_tmp.columns:
                        all_ids.update(str(x).strip() for x in df_tmp["trip_id"].dropna().unique() if str(x).strip())
                except Exception:
                    pass
        all_ids.discard(old_id)
        if base_id in all_ids:
            n = 2
            new_id = f"{base_id}__{n}"
            while new_id in all_ids:
                n += 1
                new_id = f"{base_id}__{n}"
        else:
            new_id = base_id

        for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, TRIP_PLAN_FILE, CATEGORY_BUDGETS_FILE]:
            if not os.path.exists(file_name):
                continue
            try:
                df_tmp = pd.read_csv(file_name, encoding="utf-8")
                if "trip_id" in df_tmp.columns:
                    df_tmp.loc[df_tmp["trip_id"].astype(str) == old_id, "trip_id"] = new_id
                    if file_name == MAP_FILE and "title" in df_tmp.columns:
                        old_name_display = get_trip_display_name(old_id)
                        new_name_display = get_trip_display_name(new_id)
                        mask_title = df_tmp["trip_id"].astype(str) == new_id
                        df_tmp.loc[mask_title & df_tmp["title"].astype(str).str.contains(f"Център: {old_name_display}", regex=False, na=False), "title"] = df_tmp.loc[mask_title & df_tmp["title"].astype(str).str.contains(f"Център: {old_name_display}", regex=False, na=False), "title"].astype(str).str.replace(f"Център: {old_name_display}", f"Център: {new_name_display}", regex=False)
                    df_tmp.to_csv(file_name, index=False, encoding="utf-8")
            except Exception:
                return False, f"Проблем при обновяване на {file_name}."

        if st.session_state.get("current_trip") == old_id:
            st.session_state["current_trip"] = new_id
        if st.session_state.get("edit_unlocked_trip") == old_id:
            st.session_state["edit_unlocked_trip"] = new_id
        return True, new_id
    except Exception as exc:
        return False, str(exc)

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d="", trip_finished=None):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        old_rows = df[df["trip_id"] == t_id]
        old_finished = str(old_rows.iloc[0].get("trip_finished", "Не")) if not old_rows.empty else "Не"
        df = df[df["trip_id"] != t_id]
        if trip_finished is None:
            trip_finished = old_finished
        new_row = pd.DataFrame([{
            "trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f),
            "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f),
            "start_date": str(s_d), "end_date": str(e_d), "trip_finished": str(trip_finished)
        }])
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
# BUDGET FUNCTIONS
# =========================================================
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
            df = pd.concat([df, pd.DataFrame([{"trip_id": str(t_id), "category": "__GLOBAL__", "budget": amount}])], ignore_index=True)
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
            new_rows.append({"trip_id": str(t_id), "category": "__GLOBAL__", "budget": amount})
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
                    new_rows.append({"trip_id": str(t_id), "category": cat, "budget": amount})
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

# =========================================================
# TRIP PLAN & MAP FUNCTIONS
# =========================================================
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

# =========================================================
# SESSION STATE
# =========================================================
if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "edit_unlocked_trip" not in st.session_state: st.session_state["edit_unlocked_trip"] = None
if "open_quick_expense" not in st.session_state: st.session_state["open_quick_expense"] = False

def trip_edit_unlocked(t_id):
    return st.session_state.get("edit_unlocked_trip") == str(t_id)

def lock_trip_editing(t_id=None):
    if t_id is None or st.session_state.get("edit_unlocked_trip") == str(t_id):
        st.session_state["edit_unlocked_trip"] = None

def get_finished_trip_ids():
    result = []
    try:
        if os.path.exists(SETTINGS_FILE):
            df_settings = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
            if not df_settings.empty and "trip_id" in df_settings.columns:
                for _, row in df_settings.iterrows():
                    tid = str(row.get("trip_id", "")).strip()
                    if not tid:
                        continue
                    car_trip = str(row.get("car_trip", "Не")).strip()
                    end_km = float(row.get("end_km", 0.0) or 0.0)
                    trip_finished = str(row.get("trip_finished", "Не")).strip().lower() in ["да", "yes", "true", "1"]
                    if (car_trip == "Да" and end_km > 0) or (car_trip != "Да" and trip_finished):
                        result.append(tid)
    except Exception:
        pass
    return list(dict.fromkeys(result))

# =========================================================
# MAIN APP
# =========================================================
if st.session_state["current_trip"] is None:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1>🐾 PixelApp Travel Manager</h1>
        <p style='color: #aeb5c0; font-size: 14px;'>Управление на разходите при пътувания</p>
    </div>
    """, unsafe_allow_html=True)

    _trip_ids_data = (list(pd.read_csv(DATA_FILE)["trip_id"].dropna().unique()) if os.path.exists(DATA_FILE) else [])
    _trip_ids_settings = (list(pd.read_csv(SETTINGS_FILE)["trip_id"].dropna().unique()) if os.path.exists(SETTINGS_FILE) else [])
    _trip_ids_budget = (list(pd.read_csv(CATEGORY_BUDGETS_FILE)["trip_id"].dropna().unique()) if os.path.exists(CATEGORY_BUDGETS_FILE) else [])
    existing = list(dict.fromkeys([str(t).strip() for t in (_trip_ids_settings + _trip_ids_budget + _trip_ids_data) if pd.notna(t) and str(t).strip() != ""]))

    # Quick Expense Button
    if st.button("➕ Бърз Разход", use_container_width=True):
        st.session_state["open_quick_expense"] = True
        st.rerun()

    # New Trip Dialog
    @st.dialog("Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:", placeholder="Въведете име...").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---")
        st.write("🚗 Пътувате ли със собствен автомобил?")
        viber_car = st.radio("Изберете вариант:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        if st.button("✔️ Създай и Отвори", use_container_width=True) and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"):
                s_d_str = d_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            base_id = txt.replace(" ", "_")
            target_id = get_unique_trip_id(base_id)
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

    if st.button("  Ново Пътуване", use_container_width=True):
        create_trip_modal()

    if existing:
        st.markdown("<div style='margin-top: 20px; color: #aeb5c0; font-size: 11px; font-weight: 800; letter-spacing: 1px;'>ИЗБЕРИ ДЕСТИНАЦИЯ</div>", unsafe_allow_html=True)
        for _trip in existing:
            _trip_id = str(_trip)
            _trip_name = get_trip_display_name(_trip_id)
            _settings = get_trip_settings(_trip_id)
            _trip_start_date = str(_settings.get("start_date", "") or "").strip()
            _trip_end_date = str(_settings.get("end_date", "") or "").strip()
            _trip_dates_line = ""
            if _trip_start_date and _trip_start_date.lower() != "nan":
                _trip_dates_line = (f"{_trip_start_date} → {_trip_end_date}" if _trip_end_date and _trip_end_date.lower() != "nan" and _trip_end_date != _trip_start_date else _trip_start_date)

            _df_home_trip = get_trip_data(_trip_id)
            _global = float(get_global_budget(_trip_id) or 0.0)
            _cat_budgets = get_category_budgets(_trip_id)
            _category_total = sum(float(v or 0.0) for v in _cat_budgets.values() if float(v or 0.0) > 0)

            if _global > 0:
                _budget = _global
            elif _category_total > 0:
                _budget = _category_total
            else:
                _budget = 0.0

            try:
                _spent = 0.0
                if not _df_home_trip.empty and "amount" in _df_home_trip.columns:
                    _spent = float(_df_home_trip["amount"].sum())
            except Exception:
                _spent = 0.0

            if _budget > 0:
                _pct = max(0.0, min(100.0, (_spent / _budget) * 100.0))
                _budget_line = f"€{_spent:,.2f} / €{_budget:,.2f} · {_pct:.0f}%"
            else:
                _budget_line = "Без Бюджет"

            _status_dot = "🟢" if not (_settings.get("end_km", 0) > 0 or _settings.get("trip_finished") == "Да") else "🔴"
            _status_text = "Активно" if not (_settings.get("end_km", 0) > 0 or _settings.get("trip_finished") == "Да") else "Приключено"

            _label = f"🚙 **{_trip_name}**\n{_status_dot} {_status_text} {f'· {_trip_dates_line}' if _trip_dates_line else ''}\n{_budget_line}"

            if st.button(_label, use_container_width=True, key=f"trip_{_trip_id}"):
                st.session_state["current_trip"] = _trip_id
                st.rerun()

else:
    trip_id = st.session_state["current_trip"]
    c_s = get_trip_settings(trip_id)
    car_trip = str(c_s["car_trip"])
    st.markdown(f"<h2>🚙 {get_trip_display_name(trip_id)}</h2>", unsafe_allow_html=True)

    if st.button("🔙 НАЗАД КЪМ НАЧАЛЕН ЕКРАН", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()

    st.markdown("---")
    st.success("✅ Приложението е готово за използване!")
