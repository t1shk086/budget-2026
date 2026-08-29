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

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="wide", initial_sidebar_state="collapsed")

# =========================================================
# FULLSCREEN BUTTON - PIXELAPP STYLE
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

            transition:
                opacity 0.2s ease,
                background 0.2s ease,
                color 0.2s ease,
                transform 0.2s ease;
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

        /* Иконка за изход от fullscreen */
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
                // Fullscreen → иконката се обръща навътре
                btn.classList.add("exit");
                btn.title = "Изход от Fullscreen";
            } else {
                // Нормален режим → иконката сочи навън
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

        window.parent.document.addEventListener(
            "fullscreenchange",
            updateFullscreenIcon
        );

        updateFullscreenIcon();
    </script>
    """,
    height=48,
)

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
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date","trip_finished"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

# Миграция за вече съществуващи настройки: добавяме флаг за приключване
# само за пътувания без автомобил. Старите записи не се променят.
try:
    if os.path.exists(SETTINGS_FILE):
        _settings_migration = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        if "trip_finished" not in _settings_migration.columns:
            _settings_migration["trip_finished"] = "Не"
            _settings_migration.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
except Exception:
    pass

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
    """Връща чистото име на дестинацията за показване.
    Вътрешният ID може да има суфикс __2, __3 и т.н. при дублирани пътувания.
    """
    name = str(t_id).replace("_", " ")
    marker = " __ "
    if marker in name:
        base_name, suffix = name.rsplit(marker, 1)
        if suffix.strip().isdigit():
            return base_name.strip()
    return name


def get_unique_trip_id(base_id):
    """Гарантира уникален вътрешен ID, без да забранява една и съща дестинация."""
    base_id = str(base_id).strip()
    try:
        existing_ids = set()

        if os.path.exists(DATA_FILE):
            existing_ids.update(
                str(x).strip()
                for x in pd.read_csv(DATA_FILE, encoding="utf-8")["trip_id"].dropna().unique()
            )

        if os.path.exists(SETTINGS_FILE):
            existing_ids.update(
                str(x).strip()
                for x in pd.read_csv(SETTINGS_FILE, encoding="utf-8")["trip_id"].dropna().unique()
            )

        if os.path.exists(CATEGORY_BUDGETS_FILE):
            existing_ids.update(
                str(x).strip()
                for x in pd.read_csv(CATEGORY_BUDGETS_FILE, encoding="utf-8")["trip_id"].dropna().unique()
            )
    except Exception:
        existing_ids = set()

    if base_id not in existing_ids:
        return base_id

    n = 2
    while f"{base_id}__{n}" in existing_ids:
        n += 1
    return f"{base_id}__{n}"


def rename_trip(old_id, new_name):
    """Преименува пътуване във всички свързани CSV файлове.
    Самото пътуване остава същото: разходи, бюджет, километри и дати се запазват.
    """
    try:
        old_id = str(old_id).strip()
        new_name = str(new_name).strip()

        if not old_id or not new_name:
            return False, "Името не може да бъде празно."

        base_id = new_name.replace(" ", "_")
        # Не броим старото ID като заето, за да може да се преименува обратно
        # или да се използва същото основно име.
        all_ids = set()

        for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, TRIP_PLAN_FILE, CATEGORY_BUDGETS_FILE]:
            if os.path.exists(file_name):
                try:
                    df_tmp = pd.read_csv(file_name, encoding="utf-8")
                    if "trip_id" in df_tmp.columns:
                        all_ids.update(
                            str(x).strip()
                            for x in df_tmp["trip_id"].dropna().unique()
                            if str(x).strip()
                        )
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

        # Променяме trip_id във всички файлове, без да закачаме другите данни.
        for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE, TRIP_PLAN_FILE, CATEGORY_BUDGETS_FILE]:
            if not os.path.exists(file_name):
                continue

            try:
                df_tmp = pd.read_csv(file_name, encoding="utf-8")
                if "trip_id" in df_tmp.columns:
                    df_tmp.loc[df_tmp["trip_id"].astype(str) == old_id, "trip_id"] = new_id

                    # При картата обновяваме и генерирания надпис на центъра.
                    if file_name == MAP_FILE and "title" in df_tmp.columns:
                        old_name_display = get_trip_display_name(old_id)
                        new_name_display = get_trip_display_name(new_id)
                        mask_title = df_tmp["trip_id"].astype(str) == new_id
                        df_tmp.loc[
                            mask_title & df_tmp["title"].astype(str).str.contains(
                                f"Център: {old_name_display}", regex=False, na=False
                            ),
                            "title"
                        ] = df_tmp.loc[
                            mask_title & df_tmp["title"].astype(str).str.contains(
                                f"Център: {old_name_display}", regex=False, na=False
                            ),
                            "title"
                        ].astype(str).str.replace(
                            f"Център: {old_name_display}",
                            f"Център: {new_name_display}",
                            regex=False
                        )

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
    """Връща всички приключени пътувания:
    - с автомобил -> по end_km
    - без автомобил -> по trip_finished
    """
    result = []

    try:
        if os.path.exists(SETTINGS_FILE):
            df_settings = pd.read_csv(
                SETTINGS_FILE,
                encoding="utf-8"
            )

            if (
                not df_settings.empty
                and "trip_id" in df_settings.columns
            ):
                for _, row in df_settings.iterrows():

                    tid = str(
                        row.get("trip_id", "")
                    ).strip()

                    if not tid:
                        continue

                    car_trip = str(
                        row.get("car_trip", "Не")
                    ).strip()

                    end_km = float(
                        row.get("end_km", 0.0) or 0.0
                    )

                    trip_finished = (
                        str(
                            row.get(
                                "trip_finished",
                                "Не"
                            )
                        ).strip().lower()
                        in ["да", "yes", "true", "1"]
                    )

                    # С автомобил:
                    # приключено при въведени крайни километри.
                    #
                    # Без автомобил:
                    # приключено при trip_finished = Да.
                    if (
                        car_trip == "Да"
                        and end_km > 0
                    ) or (
                        car_trip != "Да"
                        and trip_finished
                    ):
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

# Dialog flags are mutually exclusive: Streamlit permits only one open dialog per run.
_DIALOG_FLAGS = ["open_create_trip", "open_quick_expense", "trip_add_expense_new", "trip_fuel_new", "trip_car_new", "open_delete_trip_new", "open_cat_analysis_new", "open_trip_settings_new"]
for _flag in _DIALOG_FLAGS:
    if _flag not in st.session_state:
        st.session_state[_flag] = False

def _close_other_dialogs(active_flag):
    for _flag in _DIALOG_FLAGS:
        if _flag != active_flag:
            st.session_state[_flag] = False



# =========================================================
# PIXEL APP — NEW PRESENTATION LAYER
# Functional helpers/data above stay intact; this section is the UI only.
# =========================================================

# Small helpers for the new visual layer.
def _money(v):
    return f"€{float(v or 0):,.2f}"

def _trip_finished_from_settings(settings):
    car = str(settings.get("car_trip", "Не")).strip() == "Да"
    end_km = float(settings.get("end_km", 0) or 0)
    manual = str(settings.get("trip_finished", "Не")).strip().lower() in ["да", "yes", "true", "1"]
    return end_km > 0 if car else manual

def _trip_budget_snapshot(tid):
    df = get_trip_data(tid)
    settings = get_trip_settings(tid)
    deposits = float(df.loc[df["type"].astype(str).str.lower().eq("deposit"), "amount"].sum()) if not df.empty else 0.0
    expenses = float(df.loc[df["type"].astype(str).str.lower().eq("expense"), "amount"].sum()) if not df.empty else 0.0
    global_budget = float(get_global_budget(tid) or 0)
    cat_budgets = get_category_budgets(tid)
    cat_total = sum(float(v or 0) for v in cat_budgets.values() if float(v or 0) > 0)
    if global_budget > 0:
        budget = global_budget
        spent = deposits + expenses
        mode = "global"
    elif cat_total > 0:
        budget = cat_total
        mode = "category"
        wanted = {c for c,v in cat_budgets.items() if float(v or 0) > 0}
        spent = float(df.loc[(df["type"].astype(str).str.lower() == "expense") & df["category"].astype(str).isin(wanted), "amount"].sum()) if not df.empty else 0.0
        if "Нощувки/Хотел" in wanted:
            spent += deposits
    else:
        budget = 0.0
        spent = deposits + expenses
        mode = "none"
    remaining = budget - spent if budget > 0 else 0.0
    pct = max(0.0, min(100.0, spent / budget * 100.0)) if budget > 0 else 0.0
    return {"df":df,"settings":settings,"budget":budget,"spent":spent,"remaining":remaining,"pct":pct,"mode":mode,"deposits":deposits,"expenses":expenses,"cat_budgets":cat_budgets}

def _all_trip_ids():
    # Само реално създадени пътувания. Празни/None стойности никога не се
    # показват като дестинация на началния екран.
    ids=[]
    invalid={"", "none", "nan", "null", "nat"}
    for fn in [SETTINGS_FILE, CATEGORY_BUDGETS_FILE, DATA_FILE]:
        if os.path.exists(fn):
            try:
                d=pd.read_csv(fn, encoding="utf-8")
                if "trip_id" in d.columns:
                    for x in d["trip_id"].dropna().unique():
                        value=str(x).strip()
                        if value and value.lower() not in invalid:
                            ids.append(value)
            except Exception:
                pass
    return list(dict.fromkeys(ids))

def _delete_trip_all(tid):
    for fn in [DATA_FILE, SETTINGS_FILE, MAP_FILE, TRIP_PLAN_FILE, CATEGORY_BUDGETS_FILE]:
        if not os.path.exists(fn):
            continue
        try:
            d=pd.read_csv(fn, encoding="utf-8")
            if "trip_id" in d.columns:
                d=d[d["trip_id"].astype(str)!=str(tid)]
                d.to_csv(fn,index=False,encoding="utf-8")
        except Exception:
            pass

def _home_recent_rows(limit=4):
    rows=[]
    if not os.path.exists(DATA_FILE): return rows
    try:
        d=pd.read_csv(DATA_FILE, encoding="utf-8")
        if d.empty: return rows
        for _,r in d.iloc[::-1].head(limit).iterrows():
            rows.append((get_trip_display_name(r.get("trip_id","")), str(r.get("date","")), str(r.get("description","Без описание")), float(r.get("amount",0) or 0), get_display_category(r.get("category","Разход")), str(r.get("category","Разход"))))
    except Exception: pass
    return rows

# Core CSS — intentionally compact so the existing data logic is not duplicated.
st.markdown("""
<style>
:root{--px-bg:#050b10;--px-panel:#081118;--px-panel2:#0b141c;--px-border:#1b2933;--px-text:#f4f7fa;--px-muted:#8d98a4;--px-green:#36d06a;--px-yellow:#ffcc45;--px-blue:#35a8ff;--px-purple:#8d5cff;--px-orange:#ff8a2a;}
html,body,[data-testid="stAppViewContainer"]{background:radial-gradient(1200px 700px at 70% 10%,rgba(33,78,92,.18),transparent 55%),linear-gradient(180deg,#050a0f,#071018 55%,#04080c)!important;color:var(--px-text)!important;font-family:Inter,Segoe UI,Roboto,sans-serif!important}
[data-testid="stHeader"]{background:transparent!important}
.block-container{max-width:1450px!important;padding:1.2rem 1.25rem 2.5rem!important}
button{font-family:inherit!important}
/* Generic real Streamlit buttons */
button[data-testid="stBaseButton-secondary"],button[data-testid="stBaseButton-primary"]{border-radius:13px!important;border:1px solid #1c2a34!important;background:linear-gradient(180deg,#0d1820,#091118)!important;color:#f5f7f9!important;box-shadow:0 8px 24px rgba(0,0,0,.22)!important;min-height:42px!important}
button[data-testid="stBaseButton-primary"]{background:linear-gradient(180deg,#38d96b,#28b957)!important;border-color:#42e173!important;color:#06110a!important}
button:hover{transform:translateY(-1px)!important;border-color:#2d4959!important}
/* Header */
.px-shell-head{display:grid;grid-template-columns:220px 1fr auto;gap:22px;align-items:center;margin-bottom:16px}
.px-brand{font-weight:900;font-size:28px;line-height:.95;letter-spacing:.8px}.px-brand-sub{color:#ffcf3e;font-size:13px;font-weight:800;margin-top:9px}
.px-title{font-size:31px;font-weight:900;line-height:1.05}.px-sub{color:#a4adb7;font-size:14px;margin-top:7px}.px-status{display:inline-flex;padding:5px 11px;border-radius:999px;background:rgba(54,208,106,.14);color:#4be67b;font-size:12px;font-weight:900;margin-left:8px}
.px-sidebar-nav{background:rgba(6,13,18,.75);border:1px solid #16232d;border-radius:16px;padding:10px}
.px-nav-title{font-size:10px;color:#73808b;font-weight:900;letter-spacing:.8px;padding:7px 10px 10px}
/* Hero */
.px-hero{position:relative;min-height:285px;border:1px solid #1a2933;border-radius:18px;overflow:hidden;background:#081118 url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=85') center/cover no-repeat;box-shadow:0 16px 36px rgba(0,0,0,.27)}
.px-hero:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,9,14,.80) 0%,rgba(4,9,14,.35) 42%,rgba(4,9,14,.10) 72%,rgba(4,9,14,.30) 100%)}
.px-report{position:absolute;left:22px;bottom:20px;width:250px;padding:18px;border-radius:14px;background:rgba(3,9,14,.82);border:1px solid rgba(255,255,255,.09);backdrop-filter:blur(8px);z-index:2}.px-report-label{font-size:12px;font-weight:900;letter-spacing:.6px}.px-report-amount{font-size:27px;font-weight:900;margin-top:10px}.px-report-amount b{color:#ffc632}.px-track{height:11px;background:#25313a;border-radius:99px;margin-top:12px;overflow:hidden}.px-fill{height:100%;border-radius:99px;background:#42d96f}
.px-weather{position:absolute;right:18px;top:18px;z-index:2;background:rgba(3,9,14,.78);border:1px solid rgba(255,255,255,.08);padding:14px 16px;border-radius:14px;backdrop-filter:blur(8px)}
/* KPI */
.px-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:14px 0}.px-kpi{background:linear-gradient(180deg,#0b141b,#071015);border:1px solid #18262f;border-radius:15px;padding:13px 14px}.px-kpi-label{font-size:10px;color:#a1aab4;font-weight:900;letter-spacing:.4px}.px-kpi-value{font-size:20px;font-weight:900;margin-top:5px}.px-kpi-green{color:#49dc72}.px-kpi-yellow{color:#ffd15b}.px-kpi-blue{color:#39b6ff}.px-kpi-purple{color:#9d6eff}.px-kpi-orange{color:#ff9a34}
/* Dashboard grid */
.px-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr) minmax(350px,.95fr);gap:12px}.px-panel{background:linear-gradient(180deg,#081118,#071018);border:1px solid #1a2831;border-radius:15px;padding:14px;min-width:0}.px-panel-title{font-size:12px;font-weight:900;letter-spacing:.4px;margin-bottom:12px}.px-panel-sub{color:#7f8b96;font-size:11px}.px-bottom-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.px-cat-list{display:flex;flex-direction:column;gap:9px}.px-cat{display:grid;grid-template-columns:22px 1fr auto auto;gap:8px;align-items:center;font-size:11px}.px-dot{width:14px;height:14px;border-radius:50%}.px-bar{height:7px;background:#18232b;border-radius:99px;overflow:hidden;margin-top:4px}.px-bar>span{display:block;height:100%;border-radius:99px;background:#35cc68}.px-muted{color:#77828c}.px-big{font-size:28px;font-weight:900}.px-row{display:flex;justify-content:space-between;gap:10px;align-items:center}.px-list{display:flex;flex-direction:column}.px-list-item{display:grid;grid-template-columns:32px 1fr auto;gap:9px;padding:11px 0;border-bottom:1px solid rgba(255,255,255,.06)}.px-list-item:last-child{border-bottom:0}.px-icon{width:32px;height:32px;border-radius:10px;background:#0f1c24;display:grid;place-items:center}.px-note{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)}.px-note:last-child{border-bottom:0}
/* Map */
.px-map-wrap iframe{border-radius:12px!important}
.px-side-stack{display:flex;flex-direction:column;gap:12px}.px-action{display:flex;align-items:center;gap:10px;padding:9px 11px;border:1px solid #1a2832;border-radius:11px;background:#081218;margin-bottom:8px}.px-action:last-child{margin-bottom:0}
/* Home */
.px-home-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}.px-trip-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.px-trip-card{position:relative;border:1px solid #1b2a34;background:linear-gradient(180deg,#09141b,#071016);border-radius:15px;padding:14px;min-height:116px;cursor:pointer}.px-trip-card:hover{border-color:#2e5160}.px-trip-title{font-size:15px;font-weight:900}.px-trip-meta{font-size:11px;color:#87929d;margin-top:4px}.px-trip-line{height:9px;border-radius:99px;background:#16222a;margin-top:12px;overflow:hidden}.px-trip-line>span{display:block;height:100%;background:#39cf68;border-radius:99px}.px-trip-foot{display:flex;justify-content:space-between;font-size:10px;color:#9ca5ae;margin-top:6px}
@media(max-width:1050px){.px-grid{grid-template-columns:1fr 1fr}.px-grid .px-map-panel{grid-column:1/-1}.px-kpis{grid-template-columns:repeat(3,1fr)}.px-shell-head{grid-template-columns:1fr auto}}
@media(max-width:700px){.block-container{padding:.6rem .55rem 5rem!important}.px-shell-head{grid-template-columns:1fr;gap:8px}.px-brand{font-size:22px}.px-title{font-size:24px}.px-hero{min-height:255px}.px-report{left:10px;right:10px;bottom:10px;width:auto}.px-weather{right:10px;top:10px}.px-kpis{grid-template-columns:1fr 1fr}.px-kpi:last-child{grid-column:1/-1}.px-grid,.px-bottom-grid{grid-template-columns:1fr}.px-home-actions{grid-template-columns:1fr}.px-trip-grid{grid-template-columns:1fr}.px-map-panel{order:-1}}
</style>
""", unsafe_allow_html=True)

# ---------------- HOME ----------------
if st.session_state["current_trip"] is None:
    ids = _all_trip_ids()

    st.markdown("""
    <div class="px-shell-head">
      <div><div class="px-brand">▣ PIXEL<br>APP</div><div class="px-brand-sub">Travel Manager</div></div>
      <div><div class="px-title">Твоите пътувания</div><div class="px-sub">Управлявай бюджетите, разходите и плановете си на едно място.</div></div>
      <div></div>
    </div>
    """, unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        if st.button("＋  Бърз разход", key="new_ui_quick_expense", type="primary", use_container_width=True):
            _close_other_dialogs("open_quick_expense")
            st.session_state["open_quick_expense"] = True
            st.rerun()
    with c2:
        if st.button("＋  Ново пътуване", key="new_ui_create_trip", use_container_width=True):
            _close_other_dialogs("open_create_trip")
            st.session_state["open_create_trip"] = True
            st.rerun()

    if st.session_state.get("open_create_trip"):
        @st.dialog("Ново пътуване", width="small")
        def _new_trip_dialog():
            name=st.text_input("Дестинация",placeholder="Напр. Бургас").strip()
            dates=st.date_input("Дати",value=[datetime.date.today(),datetime.date.today()])
            car=st.radio("Автомобил",["Не","Да"],horizontal=True)
            sk=st.number_input("Начални километри",min_value=0.0,value=0.0,step=1.0) if car=="Да" else 0.0
            if st.button("Създай и отвори",type="primary",use_container_width=True) and name:
                s=dates[0].strftime("%d.%m.%Y") if isinstance(dates,(list,tuple)) and len(dates)>0 else dates.strftime("%d.%m.%Y")
                e=dates[-1].strftime("%d.%m.%Y") if isinstance(dates,(list,tuple)) and len(dates)>1 else s
                tid=get_unique_trip_id(name.replace(" ","_"))
                save_trip_settings(tid,car,"Да" if car=="Да" else "Добави впоследствие",float(sk),0.0,0.0,s,e)
                try:
                    loc=Nominatim(user_agent="pixelapp_travel_manager_2026").geocode(f"{name}, Europe",language="bg,en")
                    if loc: add_map_point(tid,loc.latitude,loc.longitude,f"🏁 Център: {name}","red")
                except Exception: pass
                st.session_state["open_create_trip"]=False; st.session_state["current_trip"]=tid; st.rerun()
        _new_trip_dialog()

    if ids:
        st.markdown('<div class="px-panel-title" style="margin-top:16px">ПЪТУВАНИЯ</div>',unsafe_allow_html=True)
        cols=st.columns(2)
        for i,tid in enumerate(ids):
            snap=_trip_budget_snapshot(tid); settings=snap["settings"]; done=_trip_finished_from_settings(settings)
            date1=str(settings.get("start_date","") or "").strip(); date2=str(settings.get("end_date","") or "").strip()
            dates=(f"{date1} → {date2}" if date1 and date2 and date1!=date2 else date1) if date1 and date1.lower()!="nan" else ""
            with cols[i%2]:
                # The button IS the trip card.
                card_html=f"""
                <div class='px-trip-card'>
                  <div class='px-trip-title'>✈️ {html.escape(get_trip_display_name(tid))}</div>
                  <div class='px-trip-meta'>{'🔴 Приключено' if done else '🟢 В процес'} {('· '+html.escape(dates)) if dates else ''}</div>
                  <div style='display:flex;justify-content:space-between;margin-top:12px;font-size:12px'><span>{_money(snap['spent'])}</span><span class='px-muted'>{_money(snap['budget']) if snap['budget']>0 else 'Без бюджет'}</span></div>
                  <div class='px-trip-line'><span style='width:{snap['pct']:.1f}%'></span></div>
                  <div class='px-trip-foot'><span>{snap['pct']:.0f}% използвано</span><span>Отвори →</span></div>
                </div>"""
                # visual card + transparent real button immediately over it
                st.markdown(card_html,unsafe_allow_html=True)
                if st.button("",key=f"open_trip_visual_{hashlib.sha256(str(tid).encode()).hexdigest()[:12]}",use_container_width=True):
                    st.session_state["current_trip"]=tid; st.rerun()
    else:
        st.markdown("<div class='px-panel' style='text-align:center;padding:32px'>Все още нямаш създадени пътувания.</div>",unsafe_allow_html=True)

    # HOME INSERTS — after trips, before recent expenses.
    st.markdown('<div class="px-panel-title" style="margin-top:18px">МОИТЕ МЕСТА</div>',unsafe_allow_html=True)
    map_points=[]
    if os.path.exists(MAP_FILE):
        try:
            mp=pd.read_csv(MAP_FILE,encoding="utf-8")
            for _,r in mp.iterrows():
                try:
                    map_points.append((float(r["lat"]),float(r["lon"]),str(r.get("title","Място")),str(r.get("trip_id",""))))
                except Exception: pass
        except Exception: pass
    if map_points:
        center=(sum(p[0] for p in map_points)/len(map_points),sum(p[1] for p in map_points)/len(map_points))
        fmap=folium.Map(location=center,zoom_start=6,tiles="CartoDB dark_matter",control_scale=True)
        for lat,lon,title,tid in map_points:
            folium.Marker([lat,lon],tooltip=get_trip_display_name(tid),popup=f"<b>{html.escape(title)}</b><br>{html.escape(get_trip_display_name(tid))}",icon=folium.Icon(color="green",icon="map-marker",prefix="fa")).add_to(fmap)
        st_folium(fmap,use_container_width=True,height=340,key="home_world_map_new")
    else:
        st.markdown("<div class='px-panel' style='padding:28px;color:#8c98a4'>Картата ще се запълни автоматично с местата от твоите пътувания.</div>",unsafe_allow_html=True)

    # Compact global overview only — no duplicated next trip/activity cards.
    total_spent=sum(_trip_budget_snapshot(t)["spent"] for t in ids)
    total_km=0.0
    for tid in ids:
        s=get_trip_settings(tid); total_km+=max(0.0,float(s.get("end_km",0) or 0)-float(s.get("start_km",0) or 0))
    st.markdown(f"""
    <div class='px-panel' style='margin-top:12px'><div class='px-panel-title'>БЪРЗ ПОГЛЕД</div>
      <div class='px-kpis' style='margin:0'>
        <div class='px-kpi'><div class='px-kpi-label'>ПЪТУВАНИЯ</div><div class='px-kpi-value px-kpi-blue'>{len(ids)}</div></div>
        <div class='px-kpi'><div class='px-kpi-label'>ОБЩИ РАЗХОДИ</div><div class='px-kpi-value px-kpi-yellow'>{_money(total_spent)}</div></div>
        <div class='px-kpi'><div class='px-kpi-label'>КИЛОМЕТРИ</div><div class='px-kpi-value px-kpi-green'>{total_km:,.0f} км</div></div>
      </div>
    </div>""",unsafe_allow_html=True)

    recent=_home_recent_rows(5)
    st.markdown('<div class="px-panel-title" style="margin-top:18px">ПОСЛЕДНИ РАЗХОДИ</div>',unsafe_allow_html=True)
    if recent:
        st.markdown('<div class="px-panel px-list">'+''.join([f"<div class='px-list-item'><div class='px-icon'>{get_emoji(cat)}</div><div><div style='font-weight:800;font-size:12px'>{html.escape(desc)}</div><div class='px-muted' style='font-size:10px'>{html.escape(trip)} · {html.escape(date)}</div></div><div style='font-weight:900;color:#f5f7f9'>{_money(amount)}</div></div>" for trip,date,desc,amount,disp,cat in recent])+'</div>',unsafe_allow_html=True)

    st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)

# Quick expense modal on home — real button actions, tied to the same CSV logic.
if st.session_state.get("open_quick_expense"):
    @st.dialog("➕ Бърз разход", width="small")
    def _quick_expense_dialog():
        active=[]
        for tid in _all_trip_ids():
            try:
                if not _trip_finished_from_settings(get_trip_settings(tid)): active.append(tid)
            except Exception: pass
        if not active:
            st.info("Нямаш активно пътуване."); return
        labels=[get_trip_display_name(t) for t in active]
        sel=st.selectbox("Пътуване",labels,key="new_ui_q_trip")
        tid=active[labels.index(sel)]
        amount=st.number_input("Сума (EUR)",min_value=0.01,value=None,placeholder="0.00",key="new_ui_q_amount")
        desc=st.text_input("Описание",placeholder="Напр. Обяд",key="new_ui_q_desc")
        cats=[get_display_category(c) for c in KATEGORII]
        cat_label=st.selectbox("Категория",cats,key="new_ui_q_cat")
        cat=KATEGORII[cats.index(cat_label)]
        if st.button("Запиши разхода",type="primary",use_container_width=True):
            if amount is None or float(amount)<=0 or not desc.strip(): st.warning("Въведи сума и описание.")
            else:
                if add_expense(tid,float(amount),cat,desc.strip(),cat=="Депозит/Резервация"):
                    st.session_state["open_quick_expense"]=False; st.session_state["current_trip"]=tid; st.rerun()
    _quick_expense_dialog()

# ---------------- TRIP ----------------
else:
    tid=st.session_state["current_trip"]
    snap=_trip_budget_snapshot(tid); df=snap["df"]; settings=snap["settings"]
    car_trip=str(settings.get("car_trip","Не")); start_km=float(settings.get("start_km",0) or 0); end_km=float(settings.get("end_km",0) or 0)
    manual_fuel=float(settings.get("manual_fuel",0) or 0); trip_finished=_trip_finished_from_settings(settings)
    date1=str(settings.get("start_date","") or "").strip(); date2=str(settings.get("end_date","") or "").strip()
    dates=(f"{date1} – {date2}" if date1 and date2 and date1!=date2 else date1)
    name=get_trip_display_name(tid)

    # Header
    st.markdown(f"""
    <div class='px-shell-head'>
      <div><div class='px-brand'>▣ PIXEL<br>APP</div><div class='px-brand-sub'>Travel Manager</div></div>
      <div><div class='px-title'>🌴 Дестинация: {html.escape(name)} <span class='px-status'>{'ПРИКЛЮЧЕНО' if trip_finished else 'В ПРОЦЕС'}</span></div><div class='px-sub'>▦ {html.escape(dates)} {'· '+str(max(1,(datetime.datetime.strptime(date2,"%d.%m.%Y")-datetime.datetime.strptime(date1,"%d.%m.%Y")).days+1))+' дни' if date1 and date2 else ''}</div></div>
      <div style='display:flex;gap:8px;justify-content:flex-end' class='desktop-actions'></div>
    </div>
    """,unsafe_allow_html=True)
    b1,b2,b3=st.columns([1,1,1])
    with b1:
        if st.button("← Назад към пътуванията",key="new_ui_back",use_container_width=True):
            st.session_state["current_trip"]=None; st.session_state["edit_unlocked_trip"]=None; st.rerun()
    with b2:
        if st.button("✎ Редакция",key="new_ui_edit",use_container_width=True): _close_other_dialogs("open_trip_settings_new"); st.session_state["open_trip_settings_new"]=True; st.rerun()
    with b3:
        if st.button("🗑 Изтрий пътуване",key="new_ui_delete_trip",use_container_width=True): _close_other_dialogs("open_delete_trip_new"); st.session_state["open_delete_trip_new"]=True; st.rerun()

    # Hero
    st.markdown(f"""
    <div class='px-hero'>
      <div class='px-report'><div class='px-report-label'>ОТЧЕТ ЗА ПЪТУВАНЕ</div><div class='px-report-amount'><b>{_money(snap['spent'])}</b> / {_money(snap['budget']) if snap['budget']>0 else '—'}</div><div class='px-track'><div class='px-fill' style='width:{snap['pct']:.1f}%'></div></div><div style='font-size:11px;text-align:right;margin-top:5px'>{snap['pct']:.0f}%</div></div>
      <div class='px-weather'>☀️ <b>28°C</b><div style='font-size:11px;color:#a8b0b8;margin-top:4px'>Слънчево</div><div style='font-size:11px;margin-top:8px'>📍 {html.escape(name)}</div></div>
    </div>
    """,unsafe_allow_html=True)

    # KPI
    days_left=0
    try:
        if date2: days_left=max(0,(datetime.datetime.strptime(date2,"%d.%m.%Y").date()-datetime.date.today()).days)
    except Exception: pass
    avg_day=(snap["expenses"]/max(1,((datetime.datetime.strptime(date2,"%d.%m.%Y").date()-datetime.datetime.strptime(date1,"%d.%m.%Y").date()).days+1)) if date1 and date2 else 0) if snap["expenses"]>0 else 0
    st.markdown(f"""
    <div class='px-kpis'>
      <div class='px-kpi'><div class='px-kpi-label'>ОБЩ БЮДЖЕТ</div><div class='px-kpi-value px-kpi-green'>{_money(snap['budget']) if snap['budget'] else '—'}</div></div>
      <div class='px-kpi'><div class='px-kpi-label'>ПОХАРЧЕНО ДО СЕГА</div><div class='px-kpi-value px-kpi-blue'>{_money(snap['spent'])}</div></div>
      <div class='px-kpi'><div class='px-kpi-label'>ОСТАВАЩ БЮДЖЕТ</div><div class='px-kpi-value px-kpi-purple'>{_money(snap['remaining']) if snap['budget'] else '—'}</div></div>
      <div class='px-kpi'><div class='px-kpi-label'>ОСТАВАЩИ ДНИ</div><div class='px-kpi-value px-kpi-orange'>{days_left}</div></div>
      <div class='px-kpi'><div class='px-kpi-label'>СРЕДНО НА ДЕН</div><div class='px-kpi-value px-kpi-blue'>{_money(avg_day)}</div></div>
    </div>""",unsafe_allow_html=True)

    # Dashboard content. Real action buttons live below each visual card.
    cats={k:0.0 for k in KATEGORII if k!="Депозит/Резервация"}; cats["Нощувки/Хотел"]=snap["deposits"]
    for _,r in df[df["type"].astype(str).str.lower().eq("expense")].iterrows():
        if r["category"] in cats: cats[r["category"]]+=float(r["amount"] or 0)
    total=sum(cats.values()) or 1.0
    palette=["#35d06a","#35a8ff","#965cff","#ff7d22","#ffd03c","#768696"]
    conic=[]; cur=0
    for idx,(k,v) in enumerate(cats.items()):
        p=v/total*100; conic.append(f"{palette[idx%len(palette)]} {cur:.1f}% {cur+p:.1f}%"); cur+=p
    donut="conic-gradient("+",".join(conic)+")"

    map_points=get_map_points(tid)
    fmap=None
    if not map_points.empty:
        center=(float(map_points["lat"].mean()),float(map_points["lon"].mean()))
        fmap=folium.Map(location=center,zoom_start=11,tiles="CartoDB dark_matter",control_scale=True)
        for _,r in map_points.iterrows():
            try: folium.Marker([float(r["lat"]),float(r["lon"])],tooltip=str(r.get("title","Място")),icon=folium.Icon(color="green",icon="map-marker",prefix="fa")).add_to(fmap)
            except Exception: pass

    left,mid,right=st.columns([1.1,1.0,.95],gap="small")
    with left:
        st.markdown("<div class='px-panel'><div class='px-panel-title'>▸ РАЗПРЕДЕЛЕНИЕ ПО КАТЕГОРИИ</div><div style='display:grid;grid-template-columns:145px 1fr;gap:12px;align-items:center'><div style='width:138px;height:138px;border-radius:50%;background:"+donut+";position:relative'><div style='position:absolute;inset:29px;background:#081118;border-radius:50%;display:grid;place-items:center;text-align:center'><b style='font-size:20px'>"+_money(total)+"</b><span class='px-muted' style='font-size:9px'>общо</span></div></div><div class='px-cat-list'>"+"".join([f"<div class='px-cat'><div class='px-dot' style='background:{palette[i%len(palette)]}'></div><div><div>{html.escape(get_display_category(k))}</div><div class='px-bar'><span style='width:{v/total*100:.1f}%;background:{palette[i%len(palette)]}'></span></div></div><b>{_money(v)}</b><span class='px-muted'>{v/total*100:.1f}%</span></div>" for i,(k,v) in enumerate(cats.items())])+"</div></div></div>",unsafe_allow_html=True)
        if st.button("▥ Детайлен анализ",key="new_ui_cat_detail",use_container_width=True): _close_other_dialogs("open_cat_analysis_new"); st.session_state["open_cat_analysis_new"]=True; st.rerun()

    with mid:
        # Daily spending bars, using existing dates/data.
        st.markdown("<div class='px-panel'><div class='px-row'><div class='px-panel-title'>ДНЕВЕН ПРОГРЕС</div><div class='px-muted'>По дни</div></div>",unsafe_allow_html=True)
        if not df.empty:
            exp=df[df["type"].astype(str).str.lower().eq("expense")].copy()
            if not exp.empty:
                dates_sorted=exp.groupby(exp["date"].astype(str).str[:5])["amount"].sum().tail(5)
                maxv=float(dates_sorted.max()) if not dates_sorted.empty else 1
                for d,v in dates_sorted.items():
                    st.markdown(f"<div style='display:grid;grid-template-columns:50px 1fr 60px;gap:7px;align-items:center;margin:9px 0;font-size:10px'><span class='px-muted'>{html.escape(str(d))}</span><div class='px-bar' style='height:10px'><span style='width:{float(v)/maxv*100:.1f}%'></span></div><b>{_money(v)}</b></div>",unsafe_allow_html=True)
            else: st.markdown("<div class='px-muted'>Няма разходи.</div>",unsafe_allow_html=True)
        else: st.markdown("<div class='px-muted'>Няма разходи.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with right:
        st.markdown("<div class='px-panel px-map-panel'><div class='px-panel-title'>📍 КАРТА НА ПЪТУВАНЕТО</div></div>",unsafe_allow_html=True)
        if fmap is not None: st_folium(fmap,use_container_width=True,height=330,key="trip_map_new")
        else: st.markdown("<div class='px-panel px-muted' style='margin-top:-1px'>Няма добавени точки.</div>",unsafe_allow_html=True)

    # Bottom panels
    cA,cB=st.columns(2,gap="small")
    with cA:
        recent=df[df["type"].astype(str).str.lower().eq("expense")].tail(5).iloc[::-1] if not df.empty else pd.DataFrame()
        html_rows=[]
        for _,r in recent.iterrows():
            html_rows.append(f"<div class='px-list-item'><div class='px-icon'>{get_emoji(r.get('category',''))}</div><div><div style='font-weight:800;font-size:12px'>{html.escape(str(r.get('description','Без описание')))}</div><div class='px-muted' style='font-size:10px'>{html.escape(str(r.get('date','')))} · {html.escape(get_display_category(r.get('category','')))}</div></div><div style='font-weight:900'>{_money(r.get('amount',0))}</div></div>")
        st.markdown("<div class='px-panel'><div class='px-panel-title'>ПОСЛЕДНИ РАЗХОДИ</div><div class='px-list'>"+("".join(html_rows) if html_rows else "<div class='px-muted'>Няма разходи.</div>")+"</div></div>",unsafe_allow_html=True)

    # Quick actions — само реалните действия от новия дизайн.
    # "План" не е отделен quick-action бутон: задачите/бележките вече
    # се виждат в собствения панел и така не се повтаря информация.
    st.markdown("<div class='px-panel-title' style='margin-top:14px'>БЪРЗИ ДЕЙСТВИЯ</div>",unsafe_allow_html=True)
    q1,q2,q3=st.columns(3)
    with q1:
        if st.button("＋ Нов разход",key="new_ui_expense",use_container_width=True): _close_other_dialogs("trip_add_expense_new"); st.session_state["trip_add_expense_new"]=True; st.rerun()
    with q2:
        if st.button("⛽ Гориво",key="new_ui_fuel",use_container_width=True): _close_other_dialogs("trip_fuel_new"); st.session_state["trip_fuel_new"]=True; st.rerun()
    with q3:
        if st.button("🚗 Автомобил",key="new_ui_car",use_container_width=True): _close_other_dialogs("trip_car_new"); st.session_state["trip_car_new"]=True; st.rerun()

    # Стар флаг от предишна сесия не трябва да отваря План автоматично.
        # Expense dialog
    if st.session_state.get("trip_add_expense_new"):
        @st.dialog("Нов разход",width="small")
        def _trip_expense_dialog():
            amount=st.number_input("Сума (EUR)",min_value=0.01,value=None,placeholder="0.00",key="trip_new_amt")
            desc=st.text_input("Описание",key="trip_new_desc")
            labs=[get_display_category(c) for c in KATEGORII]
            lab=st.selectbox("Категория",labs,key="trip_new_cat")
            cat=KATEGORII[labs.index(lab)]
            if cat=="Транспорт":
                liters=st.number_input("Литри (по желание)",min_value=0.0,value=0.0,step=.1)
                km=st.number_input("Километри (по желание)",min_value=0.0,value=0.0,step=1.0)
            else: liters=0.0; km=0.0
            if st.button("Запиши",type="primary",use_container_width=True):
                if amount and desc.strip() and add_expense(tid,float(amount),cat,desc.strip(),cat=="Депозит/Резервация",float(liters),float(km)):
                    st.session_state["trip_add_expense_new"]=False; st.rerun()
        _trip_expense_dialog()

    # Fuel dialog — uses same expense storage fields.
    elif st.session_state.get("trip_fuel_new"):
        @st.dialog("⛽ Гориво",width="small")
        def _fuel_dialog():
            amount=st.number_input("Сума (EUR)",min_value=0.01,value=None,placeholder="0.00")
            liters=st.number_input("Литри",min_value=0.1,value=None,step=.1,placeholder="0.0")
            km=st.number_input("Текущи километри",min_value=0.0,value=None,step=1.0,placeholder="0")
            full=st.checkbox("До горе",value=True)
            if st.button("Запиши зареждането",type="primary",use_container_width=True):
                desc=f"[{'ПЪЛНО' if full else 'ЧАСТИЧНО'} ЗАРЕЖДАНЕ] Гориво"
                if amount and liters and add_expense(tid,float(amount),"Транспорт",desc,False,float(liters),float(km or 0)):
                    st.session_state["trip_fuel_new"]=False; st.rerun()
        _fuel_dialog()

    # Car dialog
    elif st.session_state.get("trip_car_new"):
        @st.dialog("🚗 Автомобил",width="small")
        def _car_dialog():
            car=st.radio("Автомобил",["Не","Да"],index=1 if car_trip=="Да" else 0,horizontal=True)
            sk=st.number_input("Начални км",min_value=0.0,value=start_km,step=1.0)
            ef=st.number_input("Крайни км",min_value=0.0,value=end_km,step=1.0)
            mf=st.number_input("Ръчно добавено гориво (л)",min_value=0.0,value=manual_fuel,step=.1)
            if st.button("Запази",type="primary",use_container_width=True):
                save_trip_settings(tid,car,"Да" if car=="Да" else "Добави впоследствие",float(sk),float(ef),float(mf),date1,date2, "Да" if ef>0 else str(settings.get("trip_finished","Не")))
                st.session_state["trip_car_new"]=False; st.rerun()
        _car_dialog()

    elif st.session_state.get("open_delete_trip_new"):
        @st.dialog("Изтриване на пътуването",width="small")
        def _del_trip_dialog():
            st.error(f"Сигурен ли си, че искаш да изтриеш „{name}“?")
            a,b=st.columns(2)
            with a:
                if st.button("Да, изтрий",type="primary",use_container_width=True):
                    _delete_trip_all(tid); st.session_state["current_trip"]=None; st.session_state["open_delete_trip_new"]=False; st.rerun()
            with b:
                if st.button("Отказ",use_container_width=True): st.session_state["open_delete_trip_new"]=False; st.rerun()
        _del_trip_dialog()

    elif st.session_state.get("open_cat_analysis_new"):
        @st.dialog("Разходи по категории",width="large")
        def _cat_dialog():
            for cat,v in cats.items():
                if v<=0: continue
                st.markdown(f"**{get_emoji(cat)} {get_display_category(cat)} — {_money(v)}**")
                subset=df[(df["type"].astype(str).str.lower()=="expense") & (df["category"]==cat)]
                for _,r in subset.iterrows(): st.markdown(f"<div style='padding:7px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:12px'>{html.escape(str(r.get('description','')))} <span style='float:right'>{_money(r.get('amount',0))}</span></div>",unsafe_allow_html=True)
        _cat_dialog()

    elif st.session_state.get("open_trip_settings_new"):
        @st.dialog("Редакция",width="small")
        def _edit_trip_dialog():
            new_name=st.text_input("Име на дестинацията",value=name)
            if st.button("Запази името",type="primary",use_container_width=True):
                ok,res=rename_trip(tid,new_name.strip())
                if ok: st.session_state["current_trip"]=res; st.session_state["open_trip_settings_new"]=False; st.rerun()
                else: st.error(res)
        _edit_trip_dialog()
