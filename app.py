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
import textwrap
import streamlit.components.v1 as components
import re
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None
    _PYTESSERACT_AVAILABLE = False

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

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


def _tm_tesseract_diagnostics():
    """Check both pytesseract and the real Tesseract executable."""
    import os
    import shutil
    import subprocess

    result = {
        "pytesseract": bool(_PYTESSERACT_AVAILABLE),
        "module_version": None,
        "executable": None,
        "path": os.environ.get("PATH", ""),
        "version": None,
        "error": None,
    }

    if _PYTESSERACT_AVAILABLE:
        try:
            result["module_version"] = getattr(pytesseract, "__version__", "unknown")
        except Exception:
            result["module_version"] = "unknown"

    candidates = []
    try:
        found = shutil.which("tesseract")
        if found:
            candidates.append(found)
    except Exception:
        pass

    for candidate in (
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/bin/tesseract",
        "/opt/bin/tesseract",
    ):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            candidates.append(candidate)

    candidates = list(dict.fromkeys(candidates))

    if candidates:
        result["executable"] = candidates[0]
        try:
            proc = subprocess.run(
                [candidates[0], "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            first_line = (proc.stdout or proc.stderr).strip().splitlines()
            result["version"] = first_line[0] if first_line else "unknown"
            if proc.returncode != 0:
                result["error"] = (proc.stderr or proc.stdout).strip()
        except Exception as exc:
            result["error"] = str(exc)
    else:
        result["error"] = (
            "Tesseract executable не е намерен в PATH "
            "или стандартните Linux пътища."
        )

    return result


def _tm_receipt_preprocess(image):
    """Подготовка на снимката за OCR, без да променя оригинала."""
    img = image.convert("RGB")
    img = img.resize(
        (max(1, int(img.width * 2.2)), max(1, int(img.height * 2.2))),
        Image.Resampling.LANCZOS,
    )
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    gray = gray.filter(ImageFilter.SHARPEN)
    return gray


def _tm_receipt_normalize_text(text):
    """Нормализира OCR текста без да променя оригиналния резултат."""
    text = (text or "").replace("\xa0", " ")
    text = text.replace(",", ".")
    text = text.replace("„", '"').replace("“", '"').replace("”", '"')
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _tm_receipt_number_candidates(text):
    """Връща всички парични числа с позицията им в OCR текста."""
    return [
        (float(m.group(1)), m.start(1))
        for m in re.finditer(r"(?<!\d)(\d{1,7}\.\d{2})(?!\d)", text)
    ]


def _tm_find_amount_near_label(lines, label_patterns, min_value=0.01):
    """
    Търси сума около конкретен етикет.
    Предпочита същия ред, после следващите 1-3 реда.
    Това предотвратява вземането на 18.32/90.44 вместо крайната сума.
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in label_patterns]

    for i, line in enumerate(lines):
        if any(p.search(line) for p in compiled):
            window = " ".join(lines[i:i + 4])
            candidates = [
                value for value, _ in _tm_receipt_number_candidates(window)
                if value >= min_value
            ]
            if candidates:
                # При "ОБЩА СУМА" крайната стойност обичайно е най-голямата
                # парична стойност в малкия прозорец.
                return max(candidates)

    return None


def _tm_receipt_targeted_ocr(image):
    """
    Втори OCR пас само върху долната част на бележката.
    Там обичайно са TOTAL, TOTAL EUR, дата и час.
    """
    if not _PYTESSERACT_AVAILABLE:
        return ""

    try:
        img = image.convert("RGB")
        # За снимки с касовата бележка по средата запазваме долните ~45%.
        crop_top = int(img.height * 0.52)
        crop = img.crop((0, crop_top, img.width, img.height))
        prepared = _tm_receipt_preprocess(crop)

        results = []
        for config in ("--oem 3 --psm 6", "--oem 3 --psm 11"):
            try:
                out = pytesseract.image_to_string(
                    prepared,
                    lang="bul+eng",
                    config=config,
                )
                if out and out.strip():
                    results.append(out)
            except Exception:
                pass

        return "\n".join(results)
    except Exception:
        return ""


def _tm_receipt_ocr(image):
    """
    V12 — OCR за касови бележки.

    Извлича само:
        - EUR сума
        - дата
        - час

    BGN НЕ се използва като източник на сумата.

    Pipeline:
        EXIF orientation
        -> crop margins
        -> resize
        -> grayscale
        -> contrast
        -> light sharpening
        -> OCR
    """

    if not _PYTESSERACT_AVAILABLE:
        return {
            "ok": False,
            "error": "pytesseract не е инсталиран.",
            "text": "",
            "total_bgn": None,
            "total_eur": None,
            "date": None,
            "date_ocr": None,
            "date_corrected": False,
            "time": None,
        }

    try:
        from PIL import ImageOps, ImageEnhance, ImageFilter

        # =====================================================
        # 1. НОРМАЛИЗИРАНЕ НА ORIENTATION
        # =====================================================

        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        # Работим върху копие
        image = image.copy()

        # =====================================================
        # 2. RGB
        # =====================================================

        try:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        except Exception:
            pass

        # =====================================================
        # 3. ЛЕК CROP НА КРАИЩАТА
        #
        # Не режем агресивно.
        # Целта е да махнем само малко празно пространство
        # около снимката.
        # =====================================================

        try:
            width, height = image.size

            if width > 100 and height > 100:

                crop_x = int(width * 0.02)
                crop_y = int(height * 0.02)

                image = image.crop(
                    (
                        crop_x,
                        crop_y,
                        width - crop_x,
                        height - crop_y,
                    )
                )

        except Exception:
            pass

        # =====================================================
        # 4. RESIZE
        #
        # Малки снимки увеличаваме.
        # Огромни снимки ограничаваме.
        # =====================================================

        try:
            width, height = image.size
            longest = max(width, height)

            if longest < 1800:

                scale = 1800 / float(longest)

                new_size = (
                    max(1, int(width * scale)),
                    max(1, int(height * scale)),
                )

                image = image.resize(
                    new_size
                )

            elif longest > 2600:

                scale = 2600 / float(longest)

                new_size = (
                    max(1, int(width * scale)),
                    max(1, int(height * scale)),
                )

                image = image.resize(
                    new_size
                )

        except Exception:
            pass

        # =====================================================
        # 5. GRAYSCALE
        # =====================================================

        try:
            gray = ImageOps.grayscale(image)
        except Exception:
            gray = image

        # =====================================================
        # 6. CONTRAST
        # =====================================================

        try:
            gray = ImageEnhance.Contrast(
                gray
            ).enhance(1.8)
        except Exception:
            pass

        # =====================================================
        # 7. SHARPNESS
        #
        # Леко sharpen, без тежка обработка.
        # =====================================================

        try:
            gray = gray.filter(
                ImageFilter.SHARPEN
            )
        except Exception:
            pass

        # =====================================================
        # 8. OCR
        #
        # Само един pass.
        # Това е важно за скоростта.
        # =====================================================

        raw_text = pytesseract.image_to_string(
            gray,
            lang="bul+eng",
            config="--oem 3 --psm 4",
        )

    except Exception as exc:

        return {
            "ok": False,
            "error": f"OCR грешка: {exc}",
            "text": "",
            "total_bgn": None,
            "total_eur": None,
            "date": None,
            "date_ocr": None,
            "date_corrected": False,
            "time": None,
        }

    # =========================================================
    # 9. НЯМА OCR ТЕКСТ
    # =========================================================

    if not raw_text or not raw_text.strip():

        return {
            "ok": True,
            "error": "OCR не върна текст.",
            "text": "[OCR НЕ ВЪРНА ТЕКСТ]",
            "total_bgn": None,
            "total_eur": None,
            "date": None,
            "date_ocr": None,
            "date_corrected": False,
            "time": None,
        }

    # =========================================================
    # 10. НОРМАЛИЗИРАНЕ НА OCR ТЕКСТА
    # =========================================================

    text = raw_text.replace(
        "\r",
        "\n"
    )

    # ---------------------------------------------------------
    # 79. 00 -> 79.00
    # 909. 16 -> 909.16
    # 79, 00 -> 79,00
    # ---------------------------------------------------------

    text = re.sub(
        r"(\d{1,7})\s*([.,])\s*(\d{2})",
        r"\1\2\3",
        text,
    )

    # ---------------------------------------------------------
    # Понякога OCR прави:
    #
    # 79 .00
    #
    # ---------------------------------------------------------

    text = re.sub(
        r"(\d{1,7})\s+\.(\d{2})",
        r"\1.\2",
        text,
    )

    # =========================================================
    # 11. LINES
    # =========================================================

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # =========================================================
    # 12. EUR SUM
    #
    # Първо търсим най-силните маркери.
    # =========================================================

    # =========================================================
    # 12. EUR SUM — V13
    #
    # Приоритет:
    #
    # 1. ОБЩА СУМА ЕВРО 79.00
    # 2. СУМА ЕВРО 79.00
    # 3. 79,00 EUR / 79.00 EUR
    #
    # BGN / ЛВ / ЛЕВА стойности се игнорират.
    # =========================================================

    total_eur = None

    # ---------------------------------------------------------
    # OCR поправки за EUR стойности
    # ---------------------------------------------------------

    eur_text = text

    # 79-00 -> 79.00
    eur_text = re.sub(
        r"(\d{1,7})\s*-\s*(\d{2})",
        r"\1.\2",
        eur_text,
    )

    # 79,00 -> 79.00
    eur_text = re.sub(
        r"(\d{1,7})\s*,\s*(\d{2})",
        r"\1.\2",
        eur_text,
    )

    # 79. 00 -> 79.00
    eur_text = re.sub(
        r"(\d{1,7})\s*\.\s*(\d{2})",
        r"\1.\2",
        eur_text,
    )

    # ---------------------------------------------------------
    # 1. НАЙ-СИЛЕН МАРКЕР
    #
    # ОБЩА СУМА ЕВРО 79.00
    # ОБЩА СУМА ЕВРО 79-00
    # ОБЩА СУМА. ЕВРО 79.00
    # ---------------------------------------------------------

    strong_patterns = [

        r"ОБЩА\s*СУМА\.?\s*ЕВРО"
        r"\s*[:\-]?\s*"
        r"(\d{1,7}\.\d{2})",

        r"СУМА\.?\s*ЕВРО"
        r"\s*[:\-]?\s*"
        r"(\d{1,7}\.\d{2})",
    ]

    for pattern in strong_patterns:

        match = re.search(
            pattern,
            eur_text,
            flags=re.IGNORECASE,
        )

        if match:

            try:
                total_eur = float(
                    match.group(1)
                )
            except Exception:
                total_eur = None

            if total_eur is not None:
                break

    # ---------------------------------------------------------
    # 2. EUR НА СЪЩИЯ РЕД
    #
    # Например:
    #
    # СУМА: 79,00 EUR
    # 79,00 EUR
    # 79.00 €
    # ---------------------------------------------------------

    if total_eur is None:

        eur_patterns = [

            r"СУМА\s*[:\-]?\s*"
            r"(\d{1,7}\.\d{2})"
            r"\s*(?:EUR|ЕВРО|€)",

            r"(\d{1,7}\.\d{2})"
            r"\s*(?:EUR|ЕВРО|€)",
        ]

        for pattern in eur_patterns:

            match = re.search(
                pattern,
                eur_text,
                flags=re.IGNORECASE,
            )

            if match:

                try:
                    total_eur = float(
                        match.group(1)
                    )
                except Exception:
                    total_eur = None

                if total_eur is not None:
                    break

    # ---------------------------------------------------------
    # 3. ТЪРСЕНЕ ПО РЕДОВЕ
    #
    # Ако OCR е написал:
    #
    # СУМА ЕВРО
    # 79.00
    #
    # ---------------------------------------------------------

    if total_eur is None:

        for i, line in enumerate(lines):

            upper = line.upper()

            if (
                "ЕВРО" in upper
                or "EUR" in upper
                or "€" in upper
            ):

                # Търсим само числа с точно 2 знака
                # след десетичната точка.
                candidates = re.findall(
                    r"\b\d{1,7}\.\d{2}\b",
                    line,
                )

                for candidate_text in candidates:

                    try:
                        candidate = float(
                            candidate_text
                        )
                    except Exception:
                        continue

                    # Ако на реда има BGN маркер,
                    # тази стойност не е EUR.
                    if re.search(
                        r"\b(?:BGN|ЛВ|ЛЕВА|ЛЕВ)\b",
                        upper,
                        re.IGNORECASE,
                    ):
                        continue

                    total_eur = candidate
                    break

                # Следващите два реда
                if total_eur is None:

                    for next_line in lines[
                        i + 1:i + 3
                    ]:

                        upper_next = next_line.upper()

                        # BGN редове не участват.
                        if re.search(
                            r"\b(?:BGN|ЛВ|ЛЕВА|ЛЕВ)\b",
                            upper_next,
                            re.IGNORECASE,
                        ):
                            continue

                        candidates = re.findall(
                            r"\b\d{1,7}\.\d{2}\b",
                            next_line,
                        )

                        if candidates:

                            try:
                                total_eur = float(
                                    candidates[0]
                                )
                            except Exception:
                                total_eur = None

                            if total_eur is not None:
                                break

                if total_eur is not None:
                    break

    # ---------------------------------------------------------
    # 4. ВАЖНО:
    #
    # НЕ правим fallback:
    #
    # BGN / 1.95583
    #
    # и НЕ вземаме просто най-голямото число.
    #
    # Ако няма надежден EUR маркер → оставяме None.
    # ---------------------------------------------------------
    # =========================================================
    # 16. ДАТА + ЧАС
    # =========================================================

    date_value = None
    time_value = None

    date_patterns = [

        r"\b(\d{2}\.\d{2}\.\d{4})\b",

        r"\b(\d{2}/\d{2}/\d{4})\b",

        r"\b(\d{2}-\d{2}-\d{4})\b",
    ]

    # ---------------------------------------------------------
    # Първо търсим дата и час на ЕДИН ред.
    # ---------------------------------------------------------

    for line in lines:

        date_match = None

        for pattern in date_patterns:

            date_match = re.search(
                pattern,
                line,
            )

            if date_match:
                break

        time_match = re.search(
            r"\b(\d{2}:\d{2}:\d{2})\b",
            line,
        )

        if date_match:

            date_value = (
                date_match.group(1)
                .replace("/", ".")
                .replace("-", ".")
            )

            if time_match:

                time_value = (
                    time_match.group(1)
                )

            break

    # =========================================================
    # 17. DATE FALLBACK
    # =========================================================

    if date_value is None:

        for pattern in date_patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:

                date_value = (
                    match.group(1)
                    .replace("/", ".")
                    .replace("-", ".")
                )

                break

    # =========================================================
    # 18. TIME FALLBACK
    # =========================================================

    if time_value is None:

        time_matches = re.findall(
            r"\b(\d{2}:\d{2}:\d{2})\b",
            text,
        )

        if time_matches:

            time_value = (
                time_matches[-1]
            )

    # =========================================================
    # 19. ФИНАЛЕН РЕЗУЛТАТ
    # =========================================================

    return {
        "ok": True,
        "error": "",

        # Показваме суровия OCR текст
        # за да можем да диагностицираме следващата бележка.
        "text": raw_text,

        "targeted_text": "",

        # BGN вече НЕ се използва.
        "total_bgn": None,

        # Единствената парична стойност,
        # която ни интересува.
        "total_eur": total_eur,

        "date": date_value,
        "date_ocr": date_value,
        "date_corrected": False,

        "time": time_value,

        "lang": "bul+eng",
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
if "open_receipt_ocr_test" not in st.session_state: st.session_state["open_receipt_ocr_test"] = False
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

if st.session_state["current_trip"] is None:
    st.session_state["edit_unlocked_trip"] = None
    st.markdown("""
    <div class="tm-home-header">
        <div class="tm-home-brand">🐾 <span>PixelApp</span></div>
        <div class="tm-home-brand-sub">Travel Manager</div>
    </div>
    """, unsafe_allow_html=True)

    # Пътуване се счита за съществуващо и без разход:
    # пазим го в SETTINGS_FILE още при създаването, а бюджетът е отделно в CATEGORY_BUDGETS_FILE.
    _trip_ids_data = (
        list(pd.read_csv(DATA_FILE)["trip_id"].dropna().unique())
        if os.path.exists(DATA_FILE) else []
    )
    _trip_ids_settings = (
        list(pd.read_csv(SETTINGS_FILE)["trip_id"].dropna().unique())
        if os.path.exists(SETTINGS_FILE) else []
    )
    _trip_ids_budget = (
        list(pd.read_csv(CATEGORY_BUDGETS_FILE)["trip_id"].dropna().unique())
        if os.path.exists(CATEGORY_BUDGETS_FILE) else []
    )
    existing = list(dict.fromkeys(
        [str(t).strip() for t in (_trip_ids_settings + _trip_ids_budget + _trip_ids_data)
         if pd.notna(t) and str(t).strip() != ""]
    ))

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

        /* ===== V9 VISUAL REFRESH — NO LOGIC CHANGES ===== */
        div[class*="st-key-trip_card_"] {
            margin-bottom: 10px !important;
            filter: drop-shadow(0 10px 20px rgba(0,0,0,.18));
        }
        div[class*="st-key-trip_card_"] button {
            min-height: 122px !important;
            padding: 16px 18px 30px 18px !important;
            border-radius: 18px !important;
            border: 1px solid rgba(255,255,255,.10) !important;
            background:
                linear-gradient(180deg, rgba(19,29,37,.96), rgba(8,15,21,.96)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.04),
                0 8px 22px rgba(0,0,0,.24) !important;
            backdrop-filter: blur(8px) !important;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease !important;
        }
        div[class*="st-key-trip_card_"] button:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(75,210,255,.30) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.05),
                0 14px 28px rgba(0,0,0,.30),
                0 0 0 1px rgba(75,210,255,.04) !important;
        }
        div[class*="st-key-trip_card_"] button p {
            font-size: 15px !important;
            line-height: 1.55 !important;
            letter-spacing: .1px !important;
        }
        div[class*="st-key-trip_card_"] button::after {
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            bottom: 11px;
            height: 5px;
            border-radius: 999px;
            background: linear-gradient(90deg, #43b9ff, #6fe7ff);
            opacity: .85;
            pointer-events: none;
        }
        /* Modern map section */
        .tm-modern-map-shell {
            margin-top: 8px !important;
            padding: 12px !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,.08) !important;
            background: linear-gradient(180deg, rgba(12,20,27,.92), rgba(7,12,17,.92)) !important;
            box-shadow: 0 12px 28px rgba(0,0,0,.22) !important;
        }
        .tm-map-meta-row {
            display:flex; justify-content:space-between; align-items:center; gap:12px;
            margin: 0 2px 10px 2px;
            color:#aeb6c0; font-size:11px;
        }
        .tm-map-count {
            display:inline-flex; align-items:center; gap:6px;
            padding:6px 9px; border-radius:999px;
            background:rgba(69,203,255,.08);
            border:1px solid rgba(69,203,255,.14);
            color:#b9e8ff; font-weight:800;
        }
        .tm-fav-grid {
            display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:10px;
        }
        .tm-fav-card {
            display:flex; align-items:center; gap:9px; min-width:0;
            padding:10px 11px; border-radius:13px;
            background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.018));
            border:1px solid rgba(255,255,255,.07);
        }
        .tm-fav-pin {
            width:30px; height:30px; flex:0 0 30px; display:grid; place-items:center;
            border-radius:10px; background:rgba(75,210,255,.08); border:1px solid rgba(75,210,255,.12);
            font-size:15px;
        }
        .tm-fav-name {
            min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
            color:#eef3f7; font-size:11px; font-weight:800;
        }
        .tm-fav-coords {
            color:#7f8b96; font-size:9px; margin-top:2px;
        }
        @media(max-width:640px){
            div[class*="st-key-trip_card_"] button { min-height: 112px !important; padding: 14px 14px 28px 14px !important; }
            div[class*="st-key-trip_card_"] button::after { left:14px; right:14px; bottom:10px; }
            .tm-fav-grid { grid-template-columns:1fr; }
        }
        /* ===== END V9 VISUAL REFRESH ===== */


        /* =========================================================
           HOME V10 — unified dashboard design
           ========================================================= */
        .tm-home-header {
            text-align:center;
            margin: 2px 0 24px 0;
        }
        .tm-home-brand {
            color:#eef7fb;
            font-family:"Segoe UI",Roboto,sans-serif;
            font-size:38px;
            line-height:1.05;
            font-weight:900;
            letter-spacing:-1.2px;
            text-shadow:0 0 22px rgba(75,210,255,.10);
        }
        .tm-home-brand span {
            background:linear-gradient(135deg,#f3fbff 0%,#8edfff 55%,#4facfe 100%);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            background-clip:text;
        }
        .tm-home-brand-sub {
            margin-top:4px;
            color:#8d99a5;
            font-size:13px;
            font-weight:600;
            letter-spacing:.4px;
        }

        /* Two primary actions */
        div[class*="st-key-quick_expense_top_btn"] button,
        div[class*="st-key-new_trip_home_btn"] button {
            min-height:68px !important;
            padding:13px 16px !important;
            border-radius:17px !important;
            text-align:left !important;
            justify-content:flex-start !important;
            align-items:flex-start !important;
            white-space:pre-wrap !important;
            border:1px solid rgba(255,255,255,.09) !important;
            background:linear-gradient(145deg,rgba(20,34,44,.98),rgba(8,16,23,.98)) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 9px 22px rgba(0,0,0,.23) !important;
            transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button {
            border-color:rgba(75,210,255,.18) !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button:hover,
        div[class*="st-key-new_trip_home_btn"] button:hover {
            transform:translateY(-2px) !important;
            border-color:rgba(75,210,255,.28) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.05),0 14px 30px rgba(0,0,0,.30),0 0 18px rgba(75,210,255,.045) !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button p,
        div[class*="st-key-new_trip_home_btn"] button p {
            width:100% !important;
            text-align:left !important;
            white-space:pre-wrap !important;
            font-size:13px !important;
            line-height:1.38 !important;
            font-weight:800 !important;
            color:#f4f8fb !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button p::first-line,
        div[class*="st-key-new_trip_home_btn"] button p::first-line {
            font-size:15px !important;
            font-weight:800 !important;
        }
        /* Explanatory second line: smaller, lighter, not bold */
        div[class*="st-key-quick_expense_top_btn"] button p,
        div[class*="st-key-new_trip_home_btn"] button p {
            white-space:pre-line !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button p::after,
        div[class*="st-key-new_trip_home_btn"] button p::after {
            font-weight:400 !important;
        }


        div[class*="st-key-quick_expense_top_btn"] button p,
        div[class*="st-key-new_trip_home_btn"] button p {
            color:#9aa8b3 !important;
            font-weight:400 !important;
            line-height:1.32 !important;
        }
        div[class*="st-key-quick_expense_top_btn"] button p::first-line,
        div[class*="st-key-new_trip_home_btn"] button p::first-line {
            color:#f4f8fb !important;
            font-weight:800 !important;
        }


        /* V3 — subtle premium polish for trip cards */
        div[class*="st-key-trip_card_"] {
            border-radius:18px !important;
        }
        div[class*="st-key-trip_card_"] > div {
            border-radius:18px !important;
        }
        div[class*="st-key-trip_card_"] button {
            border-radius:18px !important;
            background:
                linear-gradient(145deg, rgba(20,35,45,.98) 0%, rgba(13,24,32,.98) 58%, rgba(9,17,24,.99) 100%) !important;
            border-color:rgba(75,210,255,.15) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.035),
                0 10px 26px rgba(0,0,0,.25) !important;
            transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease !important;
        }
        div[class*="st-key-trip_card_"] button:hover {
            transform:translateY(-2px) !important;
            border-color:rgba(75,210,255,.28) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.045),
                0 15px 32px rgba(0,0,0,.32),
                0 0 18px rgba(75,210,255,.04) !important;
        }

        /* Receipt OCR test button */
        div[class*="st-key-receipt_ocr_test_btn"] button {
            min-height:62px !important;
            padding:11px 15px !important;
            border-radius:16px !important;
            text-align:left !important;
            justify-content:flex-start !important;
            align-items:flex-start !important;
            white-space:pre-wrap !important;
            background:linear-gradient(145deg,rgba(20,32,42,.94),rgba(9,17,24,.98)) !important;
            border:1px solid rgba(93,126,148,.18) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.03),0 8px 20px rgba(0,0,0,.20) !important;
        }
        div[class*="st-key-receipt_ocr_test_btn"] button p {
            width:100% !important;
            white-space:pre-line !important;
            text-align:left !important;
            font-size:13px !important;
            line-height:1.32 !important;
            font-weight:400 !important;
            color:#9aa8b3 !important;
        }
        div[class*="st-key-receipt_ocr_test_btn"] button p::first-line {
            font-size:14px !important;
            font-weight:800 !important;
            color:#f4f8fb !important;
        }


        /* Receipt OCR test button */
        div[class*="st-key-receipt_ocr_test_btn"] button {
            min-height:62px !important;
            padding:11px 15px !important;
            border-radius:16px !important;
            text-align:left !important;
            justify-content:flex-start !important;
            align-items:flex-start !important;
            white-space:pre-wrap !important;
            background:linear-gradient(145deg,rgba(20,32,42,.94),rgba(9,17,24,.98)) !important;
            border:1px solid rgba(93,126,148,.18) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.03),0 8px 20px rgba(0,0,0,.20) !important;
        }
        div[class*="st-key-receipt_ocr_test_btn"] button p {
            width:100% !important;
            white-space:pre-line !important;
            text-align:left !important;
            font-size:13px !important;
            line-height:1.32 !important;
            font-weight:400 !important;
            color:#9aa8b3 !important;
        }
        div[class*="st-key-receipt_ocr_test_btn"] button p::first-line {
            font-size:14px !important;
            font-weight:800 !important;
            color:#f4f8fb !important;
        }

        /* Trips heading */
        .tm-home-trips-title {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:10px;
            color:#aab4be;
            font-size:11px;
            font-weight:900;
            letter-spacing:.8px;
            margin:22px 0 10px 2px;
            padding-bottom:9px;
            border-bottom:1px solid rgba(255,255,255,.07);
        }
        .tm-home-trips-count {
            color:#71808d;
            font-size:9px;
            font-weight:700;
            letter-spacing:.2px;
            text-transform:none;
        }

        /* Lower information cards: graphite-blue, same effects as trip cards */
        .tm-home-extra {
            margin-top:12px;
            padding:14px 15px;
            border-radius:17px;
            border:1px solid rgba(93,126,148,.22);
            background:linear-gradient(145deg,rgba(20,32,42,.97),rgba(9,17,24,.97));
            box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 9px 24px rgba(0,0,0,.24);
            backdrop-filter:blur(8px);
            transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
        }
        .tm-home-extra:hover {
            transform:translateY(-2px);
            border-color:rgba(75,210,255,.22);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 14px 30px rgba(0,0,0,.30),0 0 0 1px rgba(75,210,255,.035);
        }
        .tm-home-extra-title {
            color:#aeb8c2 !important;
            font-size:10px !important;
            font-weight:900 !important;
            letter-spacing:.75px !important;
            margin-bottom:8px !important;
        }
        .tm-home-extra-main {
            color:#f4f8fb !important;
            font-size:16px !important;
            font-weight:850 !important;
            line-height:1.25 !important;
        }
        .tm-home-extra-sub {
            color:#8996a2 !important;
            font-size:11px !important;
            font-weight:500 !important;
            margin-top:4px !important;
            line-height:1.35 !important;
        }
        .tm-home-stats {
            display:flex;
            gap:8px;
            margin-top:11px;
        }
        .tm-home-stat {
            flex:1;
            min-width:0;
            padding:11px 7px;
            border-radius:14px;
            border:1px solid rgba(93,126,148,.17);
            background:linear-gradient(180deg,rgba(25,39,51,.82),rgba(12,21,28,.82));
            box-shadow:inset 0 1px 0 rgba(255,255,255,.025);
            text-align:center;
        }
        .tm-home-stat-value {
            color:#f2f7fa !important;
            font-size:15px;
            font-weight:850;
            line-height:1.2;
        }
        .tm-home-stat-label {
            color:#7f8c98 !important;
            font-size:8px;
            font-weight:700;
            margin-top:4px;
            white-space:nowrap;
            letter-spacing:.25px;
        }


        /* V4 — Quick Overview: coordinated cool-color accents */
        .tm-home-stat:nth-child(1) .tm-home-stat-value {
            color:#4dd8ff !important;
            text-shadow:0 0 12px rgba(77,216,255,.12);
        }
        .tm-home-stat:nth-child(2) .tm-home-stat-value {
            color:#8edfff !important;
            text-shadow:0 0 12px rgba(142,223,255,.10);
        }
        .tm-home-stat:nth-child(3) .tm-home-stat-value {
            color:#70c9c0 !important;
            text-shadow:0 0 12px rgba(112,201,192,.10);
        }

        /* Map is now visually part of the same card family */
        .tm-modern-map-shell {
            margin-top:8px !important;
            padding:12px !important;
            border-radius:18px !important;
            border:1px solid rgba(93,126,148,.22) !important;
            background:linear-gradient(145deg,rgba(20,32,42,.97),rgba(9,17,24,.97)) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 10px 26px rgba(0,0,0,.25) !important;
        }
        .tm-map-section-head {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:10px;
            margin:0 2px 10px 2px;
        }
        .tm-map-section-title {
            color:#aeb8c2;
            font-size:10px;
            font-weight:900;
            letter-spacing:.75px;
        }
        .tm-map-count {
            padding:5px 9px !important;
            border-radius:999px !important;
            background:rgba(75,210,255,.07) !important;
            border:1px solid rgba(75,210,255,.13) !important;
            color:#b9e8ff !important;
            font-size:9px !important;
            font-weight:800 !important;
        }

        @media(max-width:640px){
            .tm-home-brand { font-size:32px; }
            .tm-home-header { margin-bottom:20px; }
            div[class*="st-key-quick_expense_top_btn"] button,
            div[class*="st-key-new_trip_home_btn"] button {
                min-height:64px !important;
                padding:12px 14px !important;
                border-radius:16px !important;
            }
            .tm-home-trips-title { margin-top:18px; }
            .tm-home-extra { padding:12px 13px; }
            .tm-home-stats { gap:6px; }
            .tm-home-stat { padding:10px 5px; }
            .tm-home-stat-value { font-size:13px; }
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
    if st.button("➕  Бърз Разход\nДобави разход за секунди", use_container_width=True, type="primary", key="quick_expense_top_btn"):
        st.session_state["open_quick_expense"] = True
        st.rerun()

    # ---------------------------------------------------------
    # ТЕСТОВ МОДУЛ — СНИМКА НА КАСОВА БЕЛЕЖКА
    # Inline panel вместо dialog: uploader-ът не се затваря при rerun.
    # Нищо не се записва в разходите.
    # ---------------------------------------------------------
    if "show_receipt_ocr_test" not in st.session_state:
        st.session_state["show_receipt_ocr_test"] = False

    if st.button(
        "📸  Тест: Касова бележка\nСнимай бележка и виж какво разпознава",
        use_container_width=True,
        key="receipt_ocr_test_btn",
    ):
        st.session_state["show_receipt_ocr_test"] = not st.session_state.get(
            "show_receipt_ocr_test", False
        )
        if not st.session_state["show_receipt_ocr_test"]:
            st.session_state.pop("receipt_ocr_result", None)
        st.rerun()

    if st.session_state.get("show_receipt_ocr_test"):

        # --- OCR system diagnostics ---
        diag = _tm_tesseract_diagnostics()
        st.markdown("### 🧪 Диагностика на OCR")

        d1, d2 = st.columns(2)
        with d1:
            if diag["pytesseract"]:
                st.success(
                    f"🟢 pytesseract: OK · {diag['module_version'] or 'unknown'}"
                )
            else:
                st.error("🔴 pytesseract: ЛИПСВА")

        with d2:
            if diag["executable"]:
                st.success("🟢 Tesseract: OK")
                st.code(diag["executable"], language="text")
            else:
                st.error("🔴 Tesseract: ЛИПСВА")

        if diag["version"]:
            st.caption(diag["version"])

        with st.expander("Техническа информация"):
            st.write("PATH:")
            st.code(diag["path"] or "(празен)", language="text")
            if diag["error"]:
                st.write("Грешка:")
                st.code(diag["error"], language="text")

        if diag["executable"] and diag["pytesseract"]:
            if st.button(
                "⚙️ Тест на самия Tesseract",
                key="tesseract_self_test_btn",
                use_container_width=True,
            ):
                try:
                    from PIL import ImageDraw
                    test_img = Image.new("RGB", (900, 220), "white")
                    draw = ImageDraw.Draw(test_img)
                    draw.text((40, 70), "OCR TEST 123.45", fill="black")
                    test_text = pytesseract.image_to_string(
                        test_img,
                        config="--oem 3 --psm 6",
                    ).strip()

                    if test_text:
                        st.success("🟢 Tesseract работи.")
                        st.code(test_text, language="text")
                    else:
                        st.warning(
                            "🟡 Tesseract се стартира, но не върна текст."
                        )
                except Exception as exc:
                    st.error(f"🔴 Tesseract self-test грешка: {exc}")

        st.markdown(
            """
            <div class="tm-home-extra" style="margin-top:10px;">
                <div class="tm-home-extra-title">🧾 OCR ТЕСТ</div>
                <div class="tm-home-extra-sub">
                    Качи снимка на касова бележка. Тук само проверяваме
                    какво успява да разчете системата — <b>няма запис на разход</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not _PYTESSERACT_AVAILABLE:
            st.warning(
                "⚠️ Python OCR библиотеката pytesseract не е налична. "
                "Провери дали `pytesseract` е добавен в requirements.txt."
            )
        else:
            try:
                import shutil
                _tesseract_path = shutil.which("tesseract")
            except Exception:
                _tesseract_path = None

            if not _tesseract_path:
                st.error(
                    "❌ Tesseract OCR engine не е инсталиран на сървъра. "
                    "Добави `tesseract-ocr` и `tesseract-ocr-bul` в packages.txt "
                    "и рестартирай приложението."
                )

        st.caption("📷 На телефон: натисни камерата → снимай → OK → разчитането започва автоматично.")

        # V5: директна камера + галерия.
        # camera_input връща снимката след натискане на OK на телефона.
        cam_col, gal_col = st.columns(2)

        with cam_col:
            camera_photo = st.camera_input(
                "📷 Сними касовата бележка",
                key="receipt_camera_v5",
            )

        with gal_col:
            gallery_photo = st.file_uploader(
                "🖼️ Избери от галерията",
                type=["jpg", "jpeg", "png", "webp"],
                key="receipt_gallery_v5",
            )

        # Камерата е с приоритет, ако има и двете.
        uploaded = camera_photo if camera_photo is not None else gallery_photo

        if uploaded is not None:
            try:
                receipt_img = Image.open(uploaded)
                receipt_img.load()
            except Exception as exc:
                st.error(f"❌ Не успях да отворя снимката: {exc}")
            else:
                # Уникален ключ за конкретната снимка. Така при rerun
                # след натискане OK OCR се стартира автоматично само веднъж.
                try:
                    image_bytes = uploaded.getvalue()
                except Exception:
                    image_bytes = bytes(uploaded.getbuffer())

                import hashlib
                image_key = hashlib.sha256(image_bytes).hexdigest()

                st.image(
                    receipt_img,
                    caption=f"Получена снимка · {receipt_img.width} × {receipt_img.height}px",
                    use_container_width=True,
                )

                if st.session_state.get("receipt_ocr_image_key") != image_key:
                    st.session_state["receipt_ocr_image_key"] = image_key
                    st.session_state.pop("receipt_ocr_result", None)

                    import time
                    _ocr_started = time.perf_counter()
                    with st.spinner("🔍 Разчитам касовата бележка…"):
                        st.session_state["receipt_ocr_result"] = _tm_receipt_ocr(
                            receipt_img
                        )
                    st.session_state["receipt_ocr_elapsed"] = time.perf_counter() - _ocr_started

                result = st.session_state.get("receipt_ocr_result")

                if result:
                    if not result.get("ok"):
                        st.error(
                            f"❌ {result.get('error', 'OCR не върна резултат.')}"
                        )
                    else:
                        st.markdown("### 🔎 Какво намерих")

                        c1, c2 = st.columns(2)
                        with c1:
                            bgn = result.get("total_bgn")
                            st.metric(
                                "Обща сума (лв.)",
                                f"{bgn:,.2f} лв." if bgn is not None else "—",
                            )
                        with c2:
                            eur = result.get("total_eur")
                            st.metric(
                                "Обща сума (евро)",
                                f"{eur:,.2f} €" if eur is not None else "—",
                            )

                        c3, c4 = st.columns(2)
                        with c3:
                            st.metric("Дата", result.get("date") or "—")
                        with c4:
                            st.metric("Час", result.get("time") or "—")

                        st.markdown("### 📝 Суров разпознат текст")
                        st.text_area(
                            "OCR резултат",
                            result.get("text", ""),
                            height=260,
                            key="receipt_ocr_raw_text_v2",
                        )

                        _elapsed = st.session_state.get("receipt_ocr_elapsed")
                        if _elapsed is not None:
                            st.caption(f"⏱️ Време за OCR: {_elapsed:.1f} сек. · V6 използва един OCR pass.")

                        st.caption(
                            f"OCR език: {result.get('lang') or 'неизвестен'} · "
                            "Тестов режим — нищо не е записано."
                        )

    # Диалогът за ново пътуване е дефиниран преди бутона, за да няма нова страница.
    @st.dialog("Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:",placeholder="Въведете име...").strip()

        # Дубликатите са позволени — показваме само информативно предупреждение.
        _existing_base_ids = set(
            str(x).strip()
            for x in existing
            if str(x).strip()
        )
        _typed_base_id = txt.replace(" ", "_") if txt else ""
        if _typed_base_id in _existing_base_ids:
            st.info("ℹ️ Вече имаш пътуване до тази дестинация. Новото ще бъде отделно пътуване със собствен бюджет и разходи.")

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

    # Ново пътуване — над списъка, но след основното действие.
    if st.button("✈️  Ново Пътуване\nСъздай ново приключение", use_container_width=True, key="new_trip_home_btn"):
        create_trip_modal()

    # Sort trips: active/upcoming first by start date, completed last by most recent start date.
    def _trip_sort_key(tid):
        stg = get_trip_settings(str(tid))
        start = str(stg.get("start_date", "") or "").strip()
        finished = (
            float(stg.get("end_km", 0.0) or 0.0) > 0.0
            if str(stg.get("car_trip", "Не")) == "Да"
            else str(stg.get("trip_finished", "Не")).strip().lower() in ["да", "yes", "true", "1"]
        )
        try:
            d = datetime.datetime.strptime(start, "%d.%m.%Y").date()
        except Exception:
            d = datetime.date.max
        today = datetime.date.today()
        if not finished:
            return (0, 0 if d >= today else 1, d)
        return (1, 0, -d.toordinal() if d != datetime.date.max else 0)

    existing = sorted(existing, key=_trip_sort_key)

    if existing:
        st.markdown(f"<div class='tm-home-trips-title'><span>МОИТЕ ПЪТУВАНИЯ</span><span class='tm-home-trips-count'>{len(existing)} пътувания</span></div>", unsafe_allow_html=True)

        for _trip in existing:
            _trip_id = str(_trip)
            _trip_name = get_trip_display_name(_trip_id)
            _settings = get_trip_settings(_trip_id)
            _trip_start_date = str(_settings.get("start_date", "") or "").strip()
            _trip_end_date = str(_settings.get("end_date", "") or "").strip()
            _trip_dates_line = ""
            if _trip_start_date and _trip_start_date.lower() != "nan":
                _trip_dates_line = (
                    f"{_trip_start_date} → {_trip_end_date}"
                    if _trip_end_date and _trip_end_date.lower() != "nan" and _trip_end_date != _trip_start_date
                    else _trip_start_date
                )
            _finished = (
                float(_settings.get("end_km", 0.0) or 0.0) > 0.0
                if str(_settings.get("car_trip", "Не")) == "Да"
                else str(_settings.get("trip_finished", "Не")).strip().lower() in ["да", "yes", "true", "1"]
            )

            # ПАРСВАНЕ НА ДАТИТЕ ЗА ПРОВЕРКА НА СТАТУСА
            today = datetime.date.today()
            start_d = None
            end_d = None
            
            try:
                if _trip_start_date and _trip_start_date.lower() != "nan":
                    start_d = datetime.datetime.strptime(_trip_start_date, "%d.%m.%Y").date()
                if _trip_end_date and _trip_end_date.lower() != "nan":
                    end_d = datetime.datetime.strptime(_trip_end_date, "%d.%m.%Y").date()
            except Exception:
                pass

            # ОПРЕДЕЛЯНЕ НА ЦВЕТА НА ТОЧКАТА И ТЕКСТА
            if _finished or (end_d and today > end_d):
                _status_dot = "🔴"
                _status_text = "Приключено"
            elif start_d and today < start_d:
                _status_dot = "🟡"
                _status_text = "Предстоящо"
            else:
                _status_dot = "🟢"
                _status_text = "Активно"

            # Продължение на твоя код...
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
                    /* MODERN TRIP CARD — само визуална промяна */
                    {_card_selector} button {{
                        min-height:148px !important;
                        height:auto !important;
                        width:100% !important;
                        box-sizing:border-box !important;
                        padding:16px 18px 28px 18px !important;
                        border-radius:20px !important;
                        border:1px solid rgba(255,255,255,.085) !important;
                        border-left:3px solid rgba(0,242,254,.42) !important;
                        background:
                            {_bar_gradient} bottom / 100% 7px no-repeat,
                            radial-gradient(circle at 92% 8%, rgba(0,242,254,.08), transparent 34%),
                            linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.014)) !important;
                        box-shadow:0 8px 24px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.025) !important;
                        color:#fff !important;
                        text-align:left !important;
                        justify-content:flex-start !important;
                        align-items:flex-start !important;
                        white-space:pre-wrap !important;
                        font-family:inherit !important;
                        font-size:15px !important;
                        font-weight:500 !important;
                        line-height:1.52 !important;
                        transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
                    }}
                    {_card_selector} button:hover {{
                        border-color:rgba(0,242,254,.24) !important;
                        border-left-color:rgba(0,242,254,.82) !important;
                        background:
                            {_bar_gradient} bottom / 100% 7px no-repeat,
                            radial-gradient(circle at 92% 8%, rgba(0,242,254,.11), transparent 34%),
                            linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.022)) !important;
                        box-shadow:0 12px 30px rgba(0,0,0,.30), 0 0 18px rgba(0,242,254,.055) !important;
                        transform:translateY(-2px) !important;
                    }}
                    {_card_selector} button:active {{
                        transform:translateY(0) !important;
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
                            min-height:140px !important;
                            padding:14px 14px 27px 14px !important;
                            border-radius:18px !important;
                            font-size:14px !important;
                        }}
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                _remaining_card = max(0.0, _budget - _spent) if _budget > 0 else 0.0
                if _budget > 0:
                    _label = (
                        f"🚙  **{_trip_name}**\n"
                        f"{_status_dot}  {_status_text}"
                        f"{f' · {_trip_dates_line}' if _trip_dates_line else ''}\n\n"
                        f"**€{_spent:,.2f}** / €{_budget:,.2f}    **{_pct:.0f}%**\n"
                        f"💳 Остават **€{_remaining_card:,.0f}**"
                    )
                else:
                    _label = (
                        f"🚙  **{_trip_name}**\n"
                        f"{_status_dot}  {_status_text}"
                        f"{f' · {_trip_dates_line}' if _trip_dates_line else ''}\n\n"
                        f"Без зададен бюджет"
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

        # ---------------------------------------------------------
        # НАЧАЛЕН ЕКРАН — БЪРЗ ПОГЛЕД / СЛЕДВАЩО ПЪТУВАНЕ / АКТИВНОСТ
        # Само информационни панели — не променят картите и бутоните.
        # ---------------------------------------------------------
        _home_stats = {
            "trips": len(existing),
            "spent": 0.0,
            "km": 0.0,
        }
        _next_trip = None
        _next_trip_date = None
        _last_activity = None
        _last_activity_date = None

        for _home_tid in existing:
            try:
                _hs = get_trip_settings(str(_home_tid))
                _hs_start = str(_hs.get("start_date", "") or "").strip()
                _hs_end = str(_hs.get("end_date", "") or "").strip()

                if _hs_start and _hs_start.lower() != "nan":
                    _hs_start_obj = datetime.datetime.strptime(_hs_start, "%d.%m.%Y").date()
                    if _hs_start_obj >= datetime.date.today() and (_next_trip_date is None or _hs_start_obj < _next_trip_date):
                        _next_trip_date = _hs_start_obj
                        _next_trip = str(_home_tid).replace("_", " ")

                _hs_skm = float(_hs.get("start_km", 0.0) or 0.0)
                _hs_ekm = float(_hs.get("end_km", 0.0) or 0.0)
                if _hs_ekm > _hs_skm:
                    _home_stats["km"] += _hs_ekm - _hs_skm

                _hs_df = get_trip_data(str(_home_tid))
                if not _hs_df.empty:
                    if "amount" in _hs_df.columns:
                        _home_stats["spent"] += float(
                            pd.to_numeric(_hs_df["amount"], errors="coerce").fillna(0).sum()
                        )

                    if "date" in _hs_df.columns:
                        for _idx, _row in _hs_df.iterrows():
                            try:
                                _d = pd.to_datetime(_row["date"], dayfirst=True, errors="coerce")
                                if pd.notna(_d) and (_last_activity_date is None or _d > _last_activity_date):
                                    _last_activity_date = _d
                                    _last_activity = (
                                        str(_home_tid).replace("_", " "),
                                        float(_row.get("amount", 0.0) or 0.0),
                                        str(_row.get("category", "Разход")),
                                        str(_row.get("description", "Без описание") or "Без описание")
                                    )
                            except Exception:
                                pass
            except Exception:
                pass

        st.markdown("""
            <style>
                .st-key-recent_expenses_home_btn {
            margin-top:12px !important;
        }
        .tm-home-extra {
                    margin-top:12px;
                    padding:13px 14px;
                    border-radius:16px;
                    border:1px solid rgba(93,126,148,.22);
                    background:linear-gradient(180deg, rgba(20,32,42,.96), rgba(9,17,24,.96));
                    box-shadow:inset 0 1px 0 rgba(255,255,255,.035), 0 8px 22px rgba(0,0,0,.24);
                    backdrop-filter:blur(8px);
                    transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease;
                }
        .tm-home-extra:hover {
                    transform:translateY(-2px);
                    border-color:rgba(75,210,255,.22);
                    box-shadow:inset 0 1px 0 rgba(255,255,255,.045), 0 14px 28px rgba(0,0,0,.30), 0 0 0 1px rgba(75,210,255,.035);
                }
                .tm-home-extra-title {
                    color:#9aa1ad;
                    font-size:13px;
                    font-weight:800;
                    letter-spacing:0;
                    margin-bottom:8px;
                    font-family:inherit;
                }
                .tm-home-extra-main {
                    color:#ffffff;
                    font-size:15px;
                    font-weight:800;
                    line-height:1.3;
                    font-family:inherit;
                }
                .tm-home-extra-sub {
                    color:#8f97a3;
                    font-size:11px;
                    font-weight:400;
                    margin-top:3px;
                    line-height:1.35;
                    font-family:inherit;
                }
                .tm-home-stats {
                    display:flex;
                    gap:7px;
                    margin-top:12px;
                }
                .tm-home-stat {
                    flex:1;
                    min-width:0;
                    padding:10px 8px;
                    border-radius:13px;
                    border:1px solid rgba(93,126,148,.16);
                    background:linear-gradient(180deg, rgba(25,39,51,.82), rgba(12,21,28,.82));
                    box-shadow:inset 0 1px 0 rgba(255,255,255,.025);
                    text-align:center;
                }
                .tm-home-stat-value {
                    color:#fff;
                    font-size:15px;
                    font-weight:800;
                    line-height:1.2;
                    font-family:inherit;
                }
                .tm-home-stat-trips {
                    color:#00f2fe;
                }
                .tm-home-stat-spent {
                    color:#ffd43b;
                }
                .tm-home-stat-km {
                    color:#63d391;
                }
                .tm-home-stat-label {
                    color:#858d99;
                    font-size:9px;
                    margin-top:4px;
                    white-space:nowrap;
                }
                @media(max-width:640px){
                    .tm-home-extra { padding:11px 12px; }
                    .tm-home-stats { gap:5px; }
                    .tm-home-stat { padding:9px 5px; }
                    .tm-home-stat-value { font-size:13px; }
                    .tm-home-stat-label { font-size:8px; }
                }
            </style>
        """, unsafe_allow_html=True)

        if _next_trip:
            _days_to_next = max(0, (_next_trip_date - datetime.date.today()).days)
            _when = "днес" if _days_to_next == 0 else f"след {_days_to_next} дни"
            st.markdown(
                f"""
                <div class="tm-home-extra">
                    <div class="tm-home-extra-title">✈️ СЛЕДВАЩО ПЪТУВАНЕ</div>
                    <div class="tm-home-extra-main">{_next_trip}</div>
                    <div class="tm-home-extra-sub">{_next_trip_date.strftime("%d.%m.%Y")} · {_when}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if _last_activity:
            _la_trip, _la_amount, _la_cat, _la_desc = _last_activity
            st.markdown(
                f"""
                <div class="tm-home-extra">
                    <div class="tm-home-extra-title">🕐 ПОСЛЕДНА АКТИВНОСТ</div>
                    <div class="tm-home-extra-main">€{_la_amount:,.2f}</div>
                    <div class="tm-home-extra-sub">{_la_trip} · {_la_cat} · {_la_desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            f"""
            <div class="tm-home-extra" style="margin-bottom:4px;">
                <div class="tm-home-extra-title">📊 БЪРЗ ПОГЛЕД</div>
                <div class="tm-home-stats">
                    <div class="tm-home-stat">
                        <div class="tm-home-stat-value tm-home-stat-trips">{_home_stats["trips"]}</div>
                        <div class="tm-home-stat-label">ПЪТУВАНИЯ</div>
                    </div>
                    <div class="tm-home-stat">
                        <div class="tm-home-stat-value tm-home-stat-spent">€{_home_stats["spent"]:,.0f}</div>
                        <div class="tm-home-stat-label">РАЗХОДИ</div>
                    </div>
                    <div class="tm-home-stat">
                        <div class="tm-home-stat-value tm-home-stat-km">{_home_stats["km"]:,.0f}</div>
                        <div class="tm-home-stat-label">КМ</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-top:10px;'>Все още нямате записани почивки. Създайте първото си приключение по-горе!</div>", unsafe_allow_html=True)

    @st.dialog("➕ Бърз разход", width="large")
    def quick_expense_modal():

        # Бърз Разход показва само АКТИВНИТЕ пътувания.
        existing_quick = []

        if os.path.exists(SETTINGS_FILE):
            try:
                _quick_settings_df = pd.read_csv(
                    SETTINGS_FILE,
                    encoding="utf-8"
                )

                if "trip_id" in _quick_settings_df.columns:

                    for _, _quick_row in _quick_settings_df.iterrows():

                        _quick_tid = str(
                            _quick_row.get("trip_id", "")
                        ).strip()

                        if not _quick_tid:
                            continue

                        _quick_car = str(
                            _quick_row.get("car_trip", "Не")
                        ).strip()

                        _quick_end_km = float(
                            _quick_row.get("end_km", 0.0) or 0.0
                        )

                        # За пътуване без автомобил гледаме
                        # новия флаг за приключване.
                        _quick_finished_manual = (
                            str(
                                _quick_row.get(
                                    "trip_finished",
                                    "Не"
                                )
                            ).strip().lower()
                            in ["да", "yes", "true", "1"]
                        )

                        # С автомобил:
                        # приключено = има финални километри.
                        #
                        # Без автомобил:
                        # приключено = trip_finished = Да.
                        _quick_finished = (
                            _quick_end_km > 0.0
                            if _quick_car == "Да"
                            else _quick_finished_manual
                        )

                        # Само активните попадат в списъка.
                        if not _quick_finished:
                            existing_quick.append(_quick_tid)

                    existing_quick = list(
                        dict.fromkeys(existing_quick)
                    )

            except Exception:
                existing_quick = []

        if not existing_quick:
            st.info(
                "Първо създайте поне едно активно пътуване."
            )
            return

        trip_display = [
            get_trip_display_name(t)
            if "get_trip_display_name" in globals()
            else t.replace("_", " ")
            for t in existing_quick
        ]

        selected_trip_display = st.selectbox(
            "Пътуване",
            trip_display,
            key="quick_expense_trip"
        )

        selected_trip = existing_quick[
            trip_display.index(selected_trip_display)
        ]

        quick_settings = get_trip_settings(
            selected_trip
        )

        quick_car_trip = (
            str(
                quick_settings.get(
                    "car_trip",
                    "Не"
                )
            ).strip() == "Да"
        )

        quick_start_km = float(
            quick_settings.get(
                "start_km",
                0.0
            ) or 0.0
        )

        quick_end_km = float(
            quick_settings.get(
                "end_km",
                0.0
            ) or 0.0
        )

        quick_manual_fuel = float(
            quick_settings.get(
                "manual_fuel",
                0.0
            ) or 0.0
        )

        quick_trip_finished = (
            quick_end_km > 0.0
            if quick_car_trip
            else str(
                quick_settings.get(
                    "trip_finished",
                    "Не"
                )
            ).strip().lower()
            in ["да", "yes", "true", "1"]
        )

        c1, c2 = st.columns(2)

        with c1:
            amount = st.number_input(
                "Сума (EUR)",
                min_value=0.01,
                value=None,
                step=1.00,
                placeholder="Въведете сума...",
                format="%.2f",
                key="quick_expense_amount"
            )

        with c2:
            description = st.text_input(
                "Описание",
                placeholder="Например: обяд, паркинг...",
                key="quick_expense_description"
            )

        category_options = [
            cat
            for cat in KATEGORII
            if cat != "Депозит/Резервация"
        ]

        selected_category = st.selectbox(
            "Категория",
            category_options,
            format_func=lambda cat:
                f"{get_emoji(cat)} {get_display_category(cat)}",
            key="quick_expense_category"
        )

        # Същото разпознаване на гориво.
        fuel_keywords = [
            "газ",
            "гориво",
            "зареждане",
            "бензин",
            "дизел"
        ]

        is_quick_fuel = (
            selected_category == "Транспорт"
            and any(
                k in description.strip().lower()
                for k in fuel_keywords
            )
        )

        liters = 0.0
        km_input = 0.0
        fuel_type = "ЧАСТИЧНО"
        last_km = quick_start_km

        if is_quick_fuel:

            st.markdown("---")

            st.markdown(
                "<div style='color:#00f2fe;"
                "font-weight:700;font-size:14px;"
                "margin-bottom:10px;"
                "font-family:inherit;'>"
                "⛽ Данни за зареждането"
                "</div>",
                unsafe_allow_html=True
            )

            if not quick_car_trip:

                st.warning(
                    "🚗 За проследяване на горивото "
                    "това пътуване трябва да е със "
                    "собствен автомобил."
                )

            elif (
                quick_trip_finished
                and not trip_edit_unlocked(selected_trip)
            ):

                st.error(
                    "🔒 Пътуването е приключено. "
                    "Зареждането на гориво е заключено."
                )

            else:

                fuel_c1, fuel_c2 = st.columns(2)

                with fuel_c1:
                    liters_input = st.number_input(
                        "Литри",
                        value=None,
                        min_value=0.0,
                        step=0.1,
                        placeholder="Напишете литри...",
                        key="quick_fuel_liters"
                    )

                with fuel_c2:
                    fuel_type_choice = st.radio(
                        "Тип на зареждането",
                        [
                            "Да, до горе (Пълен резервоар)",
                            "Не, частично (за конкретна сума)"
                        ],
                        index=0,
                        key="quick_fuel_type"
                    )

                km_input_value = st.number_input(
                    "Текущи километри на таблото (км)",
                    value=None,
                    min_value=0.0,
                    step=1.0,
                    placeholder="Въведете км...",
                    key="quick_fuel_km"
                )

                df_qf = get_trip_data(
                    selected_trip
                )

                if (
                    not df_qf.empty
                    and "current_km" in df_qf.columns
                ):

                    df_qf = df_qf[
                        (df_qf["category"] == "Транспорт")
                        & (df_qf["current_km"] > 0)
                    ].sort_index()

                    last_km = (
                        float(df_qf["current_km"].max())
                        if not df_qf.empty
                        else quick_start_km
                    )

                else:

                    df_qf = pd.DataFrame(
                        columns=[
                            "current_km",
                            "liters",
                            "description"
                        ]
                    )

                liters = (
                    float(liters_input)
                    if liters_input is not None
                    else 0.0
                )

                km_input = (
                    float(km_input_value)
                    if km_input_value is not None
                    else 0.0
                )

                fuel_type = (
                    "ПЪЛНО"
                    if "до горе"
                    in fuel_type_choice.lower()
                    else "ЧАСТИЧНО"
                )

                if (
                    liters > 0
                    and km_input > last_km
                    and fuel_type == "ПЪЛНО"
                ):

                    df_since_full = df_qf[
                        df_qf["description"]
                        .astype(str)
                        .str.contains(
                            "ПЪЛЕН|ПЪЛНО",
                            na=False
                        )
                    ]

                    if not df_since_full.empty:

                        last_full_km = float(
                            df_since_full.iloc[-1]["current_km"]
                        )

                        partial_liters = float(
                            df_qf[
                                df_qf["current_km"]
                                > last_full_km
                            ]["liters"].sum()
                        )

                        total_segment_liters = (
                            partial_liters
                            + liters
                        )

                        segment_dist = (
                            km_input
                            - last_full_km
                        )

                    else:

                        total_segment_liters = (
                            float(
                                df_qf["liters"].sum()
                            )
                            + liters
                            + quick_manual_fuel
                        )

                        segment_dist = (
                            km_input
                            - quick_start_km
                        )

                    if (
                        segment_dist > 0
                        and total_segment_liters > 0
                    ):

                        st.success(
                            f"📊 Реален разход за етапа: "
                            f"**{(total_segment_liters / segment_dist * 100):.1f} "
                            f"л / 100 км**"
                        )

        if st.button(
            "✔️ Запиши",
            use_container_width=True,
            type="primary",
            key="quick_expense_save"
        ):

            # Заключено приключено пътуване никога
            # не приема нов разход.
            if (
                quick_trip_finished
                and not trip_edit_unlocked(selected_trip)
            ):

                st.error(
                    "🔒 Това пътуване е приключено и заключено."
                )
                return

            if amount is None or float(amount) <= 0:

                st.warning(
                    "⚠️ Добавете разход или затворете полето."
                )
                return

            desc = (
                description.strip()
                or "Бърз разход"
            )

            # Гориво.
            if is_quick_fuel:

                if not quick_car_trip:

                    st.error(
                        "❌ Това пътуване не е настроено "
                        "за собствен автомобил."
                    )
                    return

                if (
                    quick_trip_finished
                    and not trip_edit_unlocked(selected_trip)
                ):

                    st.error(
                        "❌ Пътуването е приключено."
                    )
                    return

                if liters <= 0:

                    st.error(
                        "❌ Въведете литри за зареждането."
                    )
                    return

                if km_input <= 0:

                    st.error(
                        "❌ Въведете текущите километри "
                        "на таблото."
                    )
                    return

                df_qf = get_trip_data(
                    selected_trip
                )

                if (
                    not df_qf.empty
                    and "current_km" in df_qf.columns
                ):

                    df_qf = df_qf[
                        (df_qf["category"] == "Транспорт")
                        & (df_qf["current_km"] > 0)
                    ].sort_index()

                else:

                    df_qf = pd.DataFrame(
                        columns=[
                            "current_km",
                            "liters",
                            "description"
                        ]
                    )

                last_km_save = (
                    float(df_qf["current_km"].max())
                    if not df_qf.empty
                    else quick_start_km
                )

                full_desc = (
                    f"[{fuel_type} ЗАРЕЖДАНЕ] {desc}"
                )

                if (
                    km_input > last_km_save
                    and fuel_type == "ПЪЛНО"
                ):

                    df_since_full = df_qf[
                        df_qf["description"]
                        .astype(str)
                        .str.contains(
                            "ПЪЛЕН|ПЪЛНО",
                            na=False
                        )
                    ]

                    if not df_since_full.empty:

                        last_full_km = float(
                            df_since_full.iloc[-1]["current_km"]
                        )

                        partial_liters = float(
                            df_qf[
                                df_qf["current_km"]
                                > last_full_km
                            ]["liters"].sum()
                        )

                        t_liters = (
                            partial_liters
                            + liters
                        )

                        t_dist = (
                            km_input
                            - last_full_km
                        )

                    else:

                        t_liters = (
                            float(
                                df_qf["liters"].sum()
                            )
                            + liters
                            + quick_manual_fuel
                        )

                        t_dist = (
                            km_input
                            - quick_start_km
                        )

                    if (
                        t_dist > 0
                        and t_liters > 0
                    ):

                        full_desc += (
                            f" (Етап: {t_dist:.0f}км, "
                            f"Реален разход: "
                            f"{(t_liters / t_dist * 100):.1f}"
                            f"л/100км)"
                        )

                if add_expense(
                    selected_trip,
                    float(amount),
                    "Транспорт",
                    full_desc,
                    False,
                    liters,
                    km_input
                ):

                    st.success(
                        "✅ Зареждането е записано успешно."
                    )
                    st.rerun()

                else:

                    st.error(
                        "❌ Зареждането не можа да бъде записано."
                    )

                return

            # Нормален разход.
            if add_expense(
                selected_trip,
                float(amount),
                selected_category,
                desc,
                False
            ):

                st.success(
                    "✅ Разходът е записан успешно."
                )
                st.rerun()

            else:

                st.error(
                    "❌ Разходът не можа да бъде записан."
                )


    if st.session_state.get("open_quick_expense", False):
        st.session_state["open_quick_expense"] = False
        quick_expense_modal()


    if st.session_state.get("open_quick_expense", False):
        st.session_state["open_quick_expense"] = False
        quick_expense_modal()

    # ---------------------------------------------------------
    # МОИТЕ МЕСТА — обща карта на всички вече записани точки.
    # Използва само съществуващия MAP_FILE; не добавя нова геокодираща логика.
    # ---------------------------------------------------------

    _home_map_points = []
    try:
        if os.path.exists(MAP_FILE):
            _mp_home = pd.read_csv(MAP_FILE, encoding="utf-8")
            _valid_home_trip_ids = set()
            if os.path.exists(SETTINGS_FILE):
                try:
                    _settings_home = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                    if "trip_id" in _settings_home.columns:
                        _valid_home_trip_ids = {
                            str(x).strip() for x in _settings_home["trip_id"].dropna().tolist()
                            if str(x).strip() and str(x).strip().lower() not in {"none", "nan", "null"}
                        }
                except Exception:
                    _valid_home_trip_ids = set()
            for _, _mpr in _mp_home.iterrows():
                try:
                    _mtid = str(_mpr.get("trip_id", "")).strip()
                    _lat = float(_mpr.get("lat"))
                    _lon = float(_mpr.get("lon"))
                    if not _mtid or _mtid.lower() in {"none", "nan", "null"}:
                        continue
                    if _valid_home_trip_ids and _mtid not in _valid_home_trip_ids:
                        continue
                    _home_map_points.append((_lat, _lon, str(_mpr.get("title", "Място")), _mtid))
                except Exception:
                    continue
    except Exception:
        _home_map_points = []

    st.markdown(
        f"""
        <div class="tm-modern-map-shell">
            <div class="tm-map-section-head">
                <div class="tm-map-section-title">🌍 МОИТЕ МЕСТА</div>
                <div class="tm-map-count">{len(_home_map_points)} места</div>
            </div>
        """,
        unsafe_allow_html=True
    )

    if _home_map_points:
        _map_center = (
            sum(p[0] for p in _home_map_points) / len(_home_map_points),
            sum(p[1] for p in _home_map_points) / len(_home_map_points),
        )
        _home_map = folium.Map(
            location=_map_center,
            zoom_start=6,
            tiles="OpenStreetMap",
            control_scale=True,
        )
        for _lat, _lon, _title, _mtid in _home_map_points:
            folium.Marker(
                [_lat, _lon],
                tooltip=get_trip_display_name(_mtid),
                popup=f"<b>{html.escape(_title)}</b><br>{html.escape(get_trip_display_name(_mtid))}",
                icon=folium.Icon(color="green", icon="map-marker", prefix="fa"),
            ).add_to(_home_map)
        st_folium(_home_map, use_container_width=True, height=300, key="home_my_places_map_1237")
    else:
        st.markdown(
            "<div class='tm-home-extra'><div class='tm-home-extra-sub'>Няма записани места за показване.</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

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
    trip_finished_manual = str(c_s.get("trip_finished", "Не")).strip().lower() in ["да", "yes", "true", "1"]

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
                    if os.path.exists(MAP_FILE):
                        df_map_delete = pd.read_csv(MAP_FILE, encoding="utf-8")
                        if "trip_id" in df_map_delete.columns:
                            df_map_delete[df_map_delete["trip_id"].astype(str) != str(trip_id)].to_csv(
                                MAP_FILE, index=False, encoding="utf-8"
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

    is_trip_finished = (
        e_km > 0.0 if car_trip == "Да" else trip_finished_manual
    )
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
        # Без автомобил: директно приключване, без да искаме километри.
        if car_trip != "Да":
            st.success("✅ Това пътуване е приключено.")
            save_trip_settings(
                trip_id, car_trip, t_fuel, s_km, e_km,
                m_fuel, st_date, en_date, "Да"
            )
            st.session_state["form_version"] += 1
            st.rerun()
            return

        # С автомобил: старата логика с финални километри.
        end_km_input = st.number_input(
            "Финални километри от таблото:",
            value=None if e_km == 0.0 else e_km,
            step=1.0
        )
        if st.button("🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"):
            if end_km_input and end_km_input > s_km:
                save_trip_settings(
                    trip_id, car_trip, t_fuel, s_km, float(end_km_input),
                    m_fuel, st_date, en_date, "Не"
                )
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
        col_manage1, col_manage2 = st.columns(2)
        with col_manage1:
            if st.button("🚗 Добави автомобил към пътуването", use_container_width=True, disabled=trip_locked):
                edit_car_modal()
        with col_manage2:
            if not is_trip_finished:
                st.button(
                    "🏁 Край на пътуването",
                    use_container_width=True,
                    on_click=finish_trip_modal,
                    key=f"finish_no_car_{trip_id}"
                )
            else:
                if st.button(
                    "🔒 Заключи редакцията" if is_edit_unlocked else "🏁 Пътуването е приключено 🔒",
                    use_container_width=True,
                    disabled=not is_edit_unlocked,
                    key=f"relock_trip_no_car_{trip_id}"
                ):
                    lock_trip_editing(trip_id)
                    st.rerun()



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

    if active_budget_mode != "none":
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
    # =========================================================
    # ДНЕВЕН БЮДЖЕТ + ТЕМП НА ХАРЧЕНЕ
    # =========================================================
    # Вместо трите стари карти показваме едно общо информативно поле.
    # Данните използват същата логика за общ бюджет / бюджети по категории.
    if active_budget_mode != "none" and active_budget_total > 0:
        # --- Дати ---
        try:
            start_date_obj = (
                datetime.datetime.strptime(st_date, "%d.%m.%Y").date()
                if st_date and st_date != "nan" else None
            )
            end_date_obj = (
                datetime.datetime.strptime(en_date, "%d.%m.%Y").date()
                if en_date and en_date != "nan" else None
            )
        except Exception:
            start_date_obj, end_date_obj = None, None

        today_obj = datetime.date.today()
        if start_date_obj and end_date_obj:
            total_days = max(1, (end_date_obj - start_date_obj).days + 1)
            elapsed_days = max(
                1,
                min(total_days, (today_obj - start_date_obj).days + 1)
            )
            days_remaining = max(0, total_days - elapsed_days)
        else:
            total_days = 1
            elapsed_days = 1
            days_remaining = 0

        # --- Дневен пул ---
        # Хотелът и депозитът остават извън дневния лимит/темпо,
        # както е в оригиналната логика.
        try:
            hotel_spent_for_pace = float(
                df_expenses[df_expenses["category"] == "Нощувки/Хотел"]["amount"].sum()
            )
        except Exception:
            hotel_spent_for_pace = 0.0

        deposit_spent_for_pace = float(depozit_hotel or 0.0)
        daily_spent_total = max(
            0.0,
            float(total_on_site or 0.0) - hotel_spent_for_pace
        )

        if active_budget_mode == "category":
            try:
                hotel_budget_for_pace = float(
                    category_budgets.get("Нощувки/Хотел", 0.0) or 0.0
                )
            except Exception:
                hotel_budget_for_pace = 0.0

            daily_budget_total = max(
                0.0,
                float(active_budget_total) - hotel_budget_for_pace
            )
            rich_label = "Бюджет по категории"
        else:
            daily_budget_total = max(
                0.0,
                float(active_budget_total)
                - hotel_spent_for_pace
                - deposit_spent_for_pace
            )
            rich_label = "Общ бюджет"

        daily_budget_remaining = daily_budget_total - daily_spent_total
        daily_target = daily_budget_total / total_days if total_days > 0 else 0.0
        avg_daily_spend = daily_spent_total / elapsed_days if elapsed_days > 0 else 0.0
        projected_total = avg_daily_spend * total_days
        forecast_delta = daily_budget_total - projected_total

        pace_ratio = (
            avg_daily_spend / daily_target
            if daily_target > 0 else 0.0
        )

        if pace_ratio <= 0.80:
            health_icon = "🟢"
            health_title = "БЮДЖЕТЪТ ВЪРВИ ДОБРЕ"
            health_color = "#35d06a"
        elif pace_ratio <= 1.00:
            health_icon = "🟡"
            health_title = "ХАРЧИШ БЛИЗО ДО ПЛАНА"
            health_color = "#ffd03c"
        else:
            health_icon = "🔴"
            health_title = "ХАРЧИШ ПРЕКАЛЕНО БЪРЗО"
            health_color = "#ff4b4b"

        pace_difference = avg_daily_spend - daily_target
        if pace_difference < 0:
            health_text = f"Под плана си с €{abs(pace_difference):.2f}/ден"
        elif pace_difference > 0:
            health_text = f"Над плана си с €{pace_difference:.2f}/ден"
        else:
            health_text = "Точно по плана си"

        # --- Последните 7 дни ---
        chart_days = []
        chart_values = []
        try:
            chart_df = df_expenses.copy()
            if not chart_df.empty and "date" in chart_df.columns:
                chart_df["_tm_date"] = pd.to_datetime(
                    chart_df["date"].astype(str),
                    dayfirst=True,
                    errors="coerce"
                )
                chart_df = chart_df[chart_df["_tm_date"].notna()].copy()
                if not chart_df.empty:
                    chart_df["_tm_day"] = chart_df["_tm_date"].dt.date
                    grouped = chart_df.groupby("_tm_day")["amount"].sum().tail(7)
                    chart_days = [d.strftime("%d.%m") for d in grouped.index]
                    chart_values = [float(v or 0.0) for v in grouped.values]
        except Exception:
            chart_days, chart_values = [], []

        chart_max = max(chart_values) if chart_values else 1.0
        if chart_values:
            chart_bars = []
            for day_label, value in zip(chart_days, chart_values):
                bar_height = max(8.0, (value / chart_max) * 100.0)
                chart_bars.append(
                    f"""
                    <div style="flex:1;min-width:30px;display:flex;flex-direction:column;
                                align-items:center;justify-content:flex-end;gap:5px;height:118px;">
                        <div style="font-size:9px;color:#aeb5c0;font-weight:800;">€{value:.0f}</div>
                        <div style="width:100%;max-width:34px;height:{bar_height:.1f}%;
                                    min-height:8px;border-radius:7px 7px 3px 3px;
                                    background:linear-gradient(180deg,#00f2fe,#4facfe);
                                    box-shadow:0 3px 9px rgba(0,242,254,.16);"></div>
                        <div style="font-size:9px;color:#6f7a86;">{html.escape(day_label)}</div>
                    </div>
                    """
                )
            daily_chart_html = (
                "<div style='display:flex;align-items:flex-end;gap:8px;"
                "height:140px;margin-top:4px;'>"
                + "".join(chart_bars)
                + "</div>"
            )
        else:
            daily_chart_html = (
                "<div style='height:140px;display:flex;align-items:center;"
                "justify-content:center;color:#77828c;font-size:11px;'>"
                "Няма достатъчно данни за дневна графика."
                "</div>"
            )

        # --- Категории ---
        category_items = []
        try:
            for cat_name, cat_value in categories_totals.items():
                value = float(cat_value or 0.0)
                if value > 0:
                    category_items.append((cat_name, value))
            category_items.sort(key=lambda x: x[1], reverse=True)
        except Exception:
            category_items = []

        category_total_spent = sum(v for _, v in category_items)
        category_colors = ["#35d06a", "#35a8ff", "#965cff", "#ff7d22", "#ffd03c", "#63d391"]

        category_html = ""
        for idx, (cat_name, cat_value) in enumerate(category_items[:6]):
            cat_pct = (
                cat_value / category_total_spent * 100.0
                if category_total_spent > 0 else 0.0
            )
            cat_color = category_colors[idx % len(category_colors)]
            category_html += f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;gap:8px;
                            font-size:10px;line-height:1.2;">
                    <span style="color:#dce1e8;font-weight:700;white-space:nowrap;
                                 overflow:hidden;text-overflow:ellipsis;">
                        {html.escape(get_display_category(cat_name))}
                    </span>
                    <span style="color:#fff;font-weight:800;white-space:nowrap;">
                        €{cat_value:.2f}
                    </span>
                </div>
                <div style="height:6px;border-radius:99px;background:rgba(255,255,255,.07);
                            overflow:hidden;margin-top:5px;">
                    <div style="height:100%;width:{min(100.0, cat_pct):.1f}%;
                                background:{cat_color};border-radius:99px;"></div>
                </div>
            </div>
            """

        if not category_html:
            category_html = (
                "<div style='color:#77828c;font-size:11px;padding-top:18px;'>"
                "Няма записани разходи по категории."
                "</div>"
            )

        # --- KPI стойности ---
        remaining_value = float(active_budget_remaining or 0.0)
        remaining_display = (
            f"€{remaining_value:.2f}"
            if remaining_value >= 0
            else f"-€{abs(remaining_value):.2f}"
        )
        remaining_color = "#8bd5ff" if remaining_value >= 0 else "#ff4b4b"

        overall_pct = (
            max(0.0, min(100.0, active_budget_spent / active_budget_total * 100.0))
            if active_budget_total > 0 else 0.0
        )
        forecast_color = "#35d06a" if forecast_delta >= 0 else "#ff4b4b"
        forecast_text = (
            f"Остават €{forecast_delta:.2f}"
            if forecast_delta >= 0
            else f"Надхвърляне €{abs(forecast_delta):.2f}"
        )

        st.markdown(
            """
            <style>
            .tm-rich-budget-v4{
                margin:14px 0 16px 0;
                padding:16px;
                border-radius:16px;
                border:1px solid rgba(255,255,255,.09);
                background:linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
                box-shadow:4px 4px 14px rgba(0,0,0,.26);
                font-family:inherit;
            }
            .tm-rich-budget-v4-grid{
                display:grid;
                grid-template-columns:repeat(4,minmax(0,1fr));
                gap:10px;
            }
            .tm-rich-budget-v4-kpi{
                padding:12px 13px;
                border-radius:12px;
                background:rgba(0,0,0,.16);
                border:1px solid rgba(255,255,255,.06);
            }
            .tm-rich-budget-v4-label{
                font-size:9px;color:#8f98a3;font-weight:900;
                letter-spacing:.45px;
            }
            .tm-rich-budget-v4-value{
                font-size:21px;color:#fff;font-weight:900;
                margin-top:5px;line-height:1.05;
            }
            .tm-rich-budget-v4-sub{
                font-size:10px;color:#7e8792;margin-top:4px;
            }
            .tm-rich-budget-v4-body{
                display:grid;
                grid-template-columns:1.2fr 1fr .85fr;
                gap:10px;
                margin-top:10px;
            }
            .tm-rich-budget-v4-panel{
                padding:13px 14px;
                border-radius:12px;
                background:rgba(0,0,0,.13);
                border:1px solid rgba(255,255,255,.05);
                min-width:0;
            }
            .tm-rich-budget-v4-title{
                font-size:10px;color:#a8b0ba;font-weight:900;
                letter-spacing:.35px;margin-bottom:7px;
            }
            .tm-rich-budget-v4-track{
                height:10px;border-radius:99px;background:rgba(0,0,0,.42);
                padding:2px;overflow:hidden;
            }
            .tm-rich-budget-v4-track > div{
                height:100%;border-radius:99px;
            }
            .tm-rich-budget-v4-status{
                margin-top:10px;padding:9px;border-radius:10px;
                background:rgba(255,255,255,.025);
                font-size:10px;font-weight:900;
            }
            .tm-rich-budget-v4::before{
                content:""; display:block; height:3px; border-radius:99px;
                background:linear-gradient(90deg,#00f2fe,#4facfe,#965cff);
                margin:-4px 0 14px 0; opacity:.8;
            }
            .tm-rich-budget-v4-kpi{
                transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
                box-shadow:inset 0 1px 0 rgba(255,255,255,.03);
            }
            .tm-rich-budget-v4-kpi:hover{
                transform:translateY(-1px); border-color:rgba(0,242,254,.16);
                box-shadow:0 8px 20px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.04);
            }
            .tm-rich-budget-v4-body{align-items:stretch;}
            .tm-rich-budget-v4-panel{
                min-height:205px; box-shadow:inset 0 1px 0 rgba(255,255,255,.025);
            }
            .tm-rich-budget-v4-title{display:flex;align-items:center;gap:7px;}
            .tm-rich-budget-v4-status{border:1px solid rgba(255,255,255,.06);}
            .tm-rich-budget-v4-panel + .tm-rich-budget-v4-panel{position:relative;}
            .tm-rich-budget-v4-panel + .tm-rich-budget-v4-panel:before{
                content:""; position:absolute; left:-6px; top:12px; bottom:12px; width:1px;
                background:rgba(255,255,255,.045);
            }
            @media(max-width:640px){.tm-rich-budget-v4-panel + .tm-rich-budget-v4-panel:before{display:none;}}
            @media(max-width:900px){
                .tm-rich-budget-v4-grid{grid-template-columns:repeat(2,1fr);}
                .tm-rich-budget-v4-body{grid-template-columns:1fr 1fr;}
                .tm-rich-budget-v4-body > .tm-rich-budget-v4-panel:last-child{
                    grid-column:1/-1;
                }
            }
            @media(max-width:640px){
                .tm-rich-budget-v4-grid{grid-template-columns:1fr 1fr;}
                .tm-rich-budget-v4-body{grid-template-columns:1fr;}
                .tm-rich-budget-v4-body > .tm-rich-budget-v4-panel:last-child{
                    grid-column:auto;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        rich_budget_html = f"""
        <div class="tm-rich-budget-v4">
            <div class="tm-rich-budget-v4-grid">
                <div class="tm-rich-budget-v4-kpi">
                    <div class="tm-rich-budget-v4-label">ОБЩ БЮДЖЕТ</div>
                    <div class="tm-rich-budget-v4-value" style="color:#49dc72;">
                        €{active_budget_total:.2f}
                    </div>
                    <div class="tm-rich-budget-v4-sub">{html.escape(rich_label)}</div>
                </div>

                <div class="tm-rich-budget-v4-kpi">
                    <div class="tm-rich-budget-v4-label">ПОХАРЧЕНО</div>
                    <div class="tm-rich-budget-v4-value" style="color:#39b6ff;">
                        €{active_budget_spent:.2f}
                    </div>
                    <div class="tm-rich-budget-v4-sub">{overall_pct:.1f}% от бюджета</div>
                </div>

                <div class="tm-rich-budget-v4-kpi">
                    <div class="tm-rich-budget-v4-label">ОСТАВАЩО</div>
                    <div class="tm-rich-budget-v4-value" style="color:{remaining_color};">
                        {remaining_display}
                    </div>
                    <div class="tm-rich-budget-v4-sub">
                        {"В бюджета" if remaining_value >= 0 else "Над бюджета"}
                    </div>
                </div>

                <div class="tm-rich-budget-v4-kpi">
                    <div class="tm-rich-budget-v4-label">ОСТАВАЩИ ДНИ</div>
                    <div class="tm-rich-budget-v4-value" style="color:#ff9a34;">
                        {days_remaining}
                    </div>
                    <div class="tm-rich-budget-v4-sub">от {total_days} дни</div>
                </div>
            </div>

            <div style="margin-top:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            font-size:10px;color:#8e98a3;margin-bottom:5px;">
                    <span>БЮДЖЕТЕН ПРОГРЕС</span>
                    <b style="color:#e9edf1;">{overall_pct:.1f}%</b>
                </div>
                <div class="tm-rich-budget-v4-track">
                    <div style="width:{overall_pct:.1f}%;
                                background:{'#ff4b4b' if remaining_value < 0 else 'linear-gradient(90deg,#4facfe 0%,#00f2fe 100%)'};">
                    </div>
                </div>
            </div>

            <div class="tm-rich-budget-v4-body">
                <div class="tm-rich-budget-v4-panel">
                    <div class="tm-rich-budget-v4-title">📈 РАЗХОДИ ПО ДНИ</div>
                    {daily_chart_html}
                </div>

                <div class="tm-rich-budget-v4-panel">
                    <div class="tm-rich-budget-v4-title">📊 ПО КАТЕГОРИЯ</div>
                    {category_html}
                </div>

                <div class="tm-rich-budget-v4-panel">
                    <div class="tm-rich-budget-v4-title">📅 ДНЕВЕН ТЕМП</div>
                    <div class="tm-rich-budget-v4-value" style="font-size:21px;">
                        €{daily_target:.2f}
                    </div>
                    <div class="tm-rich-budget-v4-sub">планирано на ден</div>

                    <div style="margin-top:10px;font-size:11px;color:#b7bec9;">
                        Реално:
                        <b style="color:#fff;">€{avg_daily_spend:.2f}/ден</b>
                    </div>

                    <div style="margin-top:4px;font-size:11px;color:#b7bec9;">
                        Прогноза:
                        <b style="color:#fff;">€{projected_total:.2f}</b>
                    </div>

                    <div class="tm-rich-budget-v4-status" style="color:{health_color};">
                        {health_icon} {health_title}
                        <div style="font-size:10px;margin-top:3px;font-weight:700;">
                            {health_text}
                        </div>
                        <div style="font-size:10px;margin-top:4px;color:{forecast_color};">
                            {forecast_text}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

        st.html(textwrap.dedent(rich_budget_html).strip())
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
    st.markdown(f"<div class='tm-modern-map-shell'><div class='tm-map-meta-row'><div style='color:#7e8494;font-size:12px;margin-top:12px;margin-bottom:4px;'><span>📍 Запазени места от това пътуване - </span><span class='tm-map-count'>{len(df_points)} {'място' if len(df_points)==1 else 'места'}</span></div>", unsafe_allow_html=True)
    
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
    st.markdown("</div>", unsafe_allow_html=True)

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

    # =========================================================
    # ❤️ ЛЮБИМИ МЕСТА — реална таблична визуализация
    # =========================================================
    st.markdown("""
    <style>
        .tm-fav-headline {
            margin-top:18px;
            margin-bottom:9px;
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:10px;
        }
        .tm-fav-title {
            color:#ffffff;
            font-size:13px;
            font-weight:900;
            letter-spacing:.25px;
        }
        .tm-fav-count {
            color:#aeb7c1;
            font-size:10px;
            padding:5px 8px;
            border-radius:999px;
            background:rgba(255,255,255,.035);
            border:1px solid rgba(255,255,255,.07);
        }
        .tm-fav-head-row,
        .tm-fav-data-row {
            display:grid;
            grid-template-columns:minmax(170px,1.35fr) minmax(180px,1.15fr) minmax(170px,1fr) 52px;
            gap:0;
            align-items:center;
        }
        .tm-fav-table {
            overflow:hidden;
            border:1px solid rgba(255,255,255,.07);
            border-radius:16px;
            background:linear-gradient(180deg,rgba(12,19,25,.96),rgba(7,12,17,.96));
            box-shadow:0 10px 26px rgba(0,0,0,.20);
        }
        .tm-fav-head-row {
            min-height:34px;
            background:rgba(255,255,255,.025);
            border-bottom:1px solid rgba(255,255,255,.07);
        }
        .tm-fav-th {
            color:#737e89;
            font-size:9px;
            font-weight:900;
            letter-spacing:.65px;
            padding:0 10px;
            text-transform:uppercase;
        }
        .tm-fav-data-row {
            min-height:54px;
            border-bottom:1px solid rgba(255,255,255,.055);
        }
        .tm-fav-data-row:last-child { border-bottom:0; }
        .tm-fav-cell {
            color:#dfe4ea;
            font-size:11px;
            line-height:1.35;
            padding:9px 10px;
            min-width:0;
        }
        .tm-fav-place {
            color:#fff;
            font-weight:800;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }
        .tm-fav-description {
            color:#aab3bd;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }
        .tm-fav-coord {
            color:#8d98a4;
            font-variant-numeric:tabular-nums;
            font-size:10px;
        }
        .tm-fav-dot {
            display:inline-block;
            width:7px;
            height:7px;
            border-radius:50%;
            margin-right:7px;
            vertical-align:1px;
        }
        @media(max-width:760px){
            .tm-fav-head-row,
            .tm-fav-data-row { grid-template-columns:minmax(120px,1.1fr) minmax(130px,1fr) 94px 44px; }
            .tm-fav-th,.tm-fav-cell { padding-left:8px; padding-right:8px; }
            .tm-fav-cell { font-size:10px; }
        }
        @media(max-width:560px){
            .tm-fav-head-row { display:none; }
            .tm-fav-data-row {
                grid-template-columns:minmax(0,1fr) 44px;
                grid-template-areas:"place action" "description action" "coord action";
                padding:8px 0;
            }
            .tm-fav-data-row .fav-place-cell { grid-area:place; }
            .tm-fav-data-row .fav-desc-cell { grid-area:description; }
            .tm-fav-data-row .fav-coord-cell { grid-area:coord; }
            .tm-fav-data-row .fav-action-cell { grid-area:action; }
        }
    </style>
    """, unsafe_allow_html=True)

    df_points = get_map_points(trip_id)
    st.markdown(
        f"<div class='tm-fav-headline'><div class='tm-fav-title'>❤️ ЛЮБИМИ МЕСТА</div><div class='tm-fav-count'>{len(df_points)} {'място' if len(df_points)==1 else 'места'}</div></div>",
        unsafe_allow_html=True,
    )

    if df_points.empty:
        st.markdown(
            "<div class='tm-fav-table' style='padding:18px;color:#7f8994;font-size:11px;'>Все още няма запазени места за това пътуване.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='tm-fav-table'><div class='tm-fav-head-row'>"
            "<div class='tm-fav-th'>МЯСТО</div><div class='tm-fav-th'>ОПИСАНИЕ</div>"
            "<div class='tm-fav-th'>КООРДИНАТИ</div><div class='tm-fav-th'></div></div>",
            unsafe_allow_html=True,
        )
        for _fav_i, (_fav_idx, _fav_row) in enumerate(df_points.iterrows()):
            _fav_title = str(_fav_row.get('title','Място') or 'Място').strip()
            _fav_lat = float(_fav_row.get('lat',0) or 0)
            _fav_lon = float(_fav_row.get('lon',0) or 0)
            _fav_color = str(_fav_row.get('color','blue') or 'blue').strip().lower()
            _fav_color_map = {
                'red':'#ff5b63','green':'#42d96f','blue':'#4facfe','purple':'#9a6cff','orange':'#ff9b3d'
            }
            _fav_dot_color = _fav_color_map.get(_fav_color, '#4facfe')
            _fav_desc = 'Запазено място'
            if ':' in _fav_title:
                _fav_left, _fav_right = _fav_title.split(':',1)
                if _fav_right.strip():
                    _fav_desc = _fav_left.strip().replace('🏁','').strip()
                    _fav_title = _fav_right.strip()
            st.markdown(
                f"<div class='tm-fav-data-row'>"
                f"<div class='tm-fav-cell fav-place-cell'><div class='tm-fav-place'><span class='tm-fav-dot' style='background:{_fav_dot_color}'></span>{html.escape(_fav_title)}</div></div>"
                f"<div class='tm-fav-cell fav-desc-cell'><div class='tm-fav-description'>{html.escape(_fav_desc)}</div></div>"
                f"<div class='tm-fav-cell fav-coord-cell'><div class='tm-fav-coord'>{_fav_lat:.5f}, {_fav_lon:.5f}</div></div>"
                f"<div class='tm-fav-cell fav-action-cell'></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            _fav_action_cols = st.columns([1, 12])
            with _fav_action_cols[1]:
                if st.button('🗑️', key=f'fav_delete_{trip_id}_{_fav_idx}', help=f'Изтрий {_fav_title}'):
                    try:
                        df_map = pd.read_csv(MAP_FILE, encoding='utf-8')
                        if _fav_idx in df_map.index:
                            df_map = df_map.drop(index=_fav_idx)
                            df_map.to_csv(MAP_FILE, index=False, encoding='utf-8')
                            st.rerun()
                    except Exception:
                        pass
        st.markdown("</div>", unsafe_allow_html=True)

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
                import smtplib
                from email.message import EmailMessage

                # =====================================================
                # СЪЗДАВАНЕ НА ZIP АРХИВ
                # =====================================================
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(
                    zip_buffer,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as zip_file:

                    for file_name in [
                        DATA_FILE,
                        SETTINGS_FILE,
                        MAP_FILE,
                        LABELS_FILE,
                        CATEGORY_BUDGETS_FILE
                    ]:
                        if os.path.exists(file_name):
                            zip_file.write(
                                file_name,
                                arcname=file_name
                            )

                zip_data = zip_buffer.getvalue()

                # =====================================================
                # ЛОКАЛНО СВАЛЯНЕ
                # =====================================================
                st.download_button(
                    label="📥 Свали всички CSV логове (.ZIP)",
                    data=zip_data,
                    file_name="PixelApp_Data_Backup.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="download_all_csv_backup_btn"
                )

                # =====================================================
                # ИЗПРАЩАНЕ ПО ИМЕЙЛ
                # =====================================================
                st.markdown("##### 📧 Изпращане на архив по e-mail")

                email_to = st.text_input(
                    "Получател",
                    placeholder="name@example.com",
                    key="backup_email_to"
                )

                if st.button(
                    "📧 Изпрати архива",
                    use_container_width=True,
                    key="send_backup_email_btn"
                ):

                    if not email_to.strip():

                        st.warning(
                            "⚠️ Моля, въведи имейл адрес."
                        )

                    else:

                        # =================================================
                        # GMAIL НАСТРОЙКИ
                        # =================================================
                        SMTP_SERVER = "smtp.gmail.com"
                        SMTP_PORT = 465

                        # Тези две стойности се вземат от Streamlit Secrets
                        SMTP_USERNAME = st.secrets["gmail"]["username"]
                        SMTP_PASSWORD = st.secrets["gmail"]["app_password"]

                        # =================================================
                        # СЪЗДАВЯНЕ НА ИМЕЙЛА
                        # =================================================
                        msg = EmailMessage()

                        msg["Subject"] = "PixelApp – архив на данните"
                        msg["From"] = SMTP_USERNAME
                        msg["To"] = email_to.strip()

                        msg.set_content(
                            "Здравей,\n\n"
                            "Прикачен е архив с данните от PixelApp.\n\n"
                            "Файл: PixelApp_Data_Backup.zip\n\n"
                            "Поздрави,\n"
                            "PixelApp"
                        )

                        # =================================================
                        # ПРИКАЧВАНЕ НА ZIP АРХИВА
                        # =================================================
                        msg.add_attachment(
                            zip_data,
                            maintype="application",
                            subtype="zip",
                            filename="PixelApp_Data_Backup.zip"
                        )

                        # =================================================
                        # GMAIL SMTP - SSL / PORT 465
                                                # =================================================
                        with smtplib.SMTP_SSL(
                            SMTP_SERVER,
                            SMTP_PORT,
                            timeout=30
                        ) as server:
                            server.login(SMTP_USERNAME, SMTP_PASSWORD)
                            server.send_message(msg)



                        st.success(
                            f"✅ Архивът беше изпратен успешно до "
                            f"{email_to.strip()}."
                        )

            except Exception as e:

                st.error(
                    f"❌ Грешка при създаване или изпращане на архива: {e}"
                )

                
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
        st.markdown("##### ✏️ Преименуване на съществуващо пътуване")
        st.caption("Преименуването променя само името на пътуването. Разходи, бюджети, километри, маршрут и дати се запазват.")

        # Само реално създадените пътувания от SETTINGS_FILE.
        _admin_trip_ids = []
        if os.path.exists(SETTINGS_FILE):
            try:
                _admin_settings_df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                if "trip_id" in _admin_settings_df.columns:
                    _admin_trip_ids = list(dict.fromkeys(
                        str(x).strip()
                        for x in _admin_settings_df["trip_id"].dropna().unique()
                        if str(x).strip()
                    ))
            except Exception:
                _admin_trip_ids = []

        if _admin_trip_ids:
            def _rename_trip_label(tid):
                display_name = get_trip_display_name(tid)
                settings = get_trip_settings(tid)
                sd = str(settings.get("start_date", "") or "").strip()
                ed = str(settings.get("end_date", "") or "").strip()

                if sd and sd.lower() != "nan":
                    date_part = f"{sd} → {ed}" if ed and ed.lower() != "nan" and ed != sd else sd
                    return f"🚙 {display_name} · {date_part}"
                return f"🚙 {display_name}"

            admin_rename_choice = st.selectbox(
                "Избери пътуване:",
                _admin_trip_ids,
                format_func=_rename_trip_label,
                key="admin_rename_trip_select"
            )

            admin_new_trip_name = st.text_input(
                "Ново име на дестинацията:",
                value="",
                key="admin_rename_trip_name",
                placeholder="Например: Бургас"
            ).strip()

            if st.button(
                "✏️ ПРЕИМЕНУВАЙ ПЪТУВАНЕТО",
                use_container_width=True,
                type="primary",
                key="admin_rename_trip_btn"
            ):
                if not admin_new_trip_name:
                    st.warning("⚠️ Въведи ново име.")
                elif admin_new_trip_name == get_trip_display_name(admin_rename_choice):
                    st.info("ℹ️ Новото име е същото като текущото.")
                else:
                    ok_rename, rename_result = rename_trip(admin_rename_choice, admin_new_trip_name)
                    if ok_rename:
                        st.success(f"✅ Пътуването е преименувано на „{get_trip_display_name(rename_result)}“.")
                        st.session_state["show_admin_panel"] = False
                        st.rerun()
                    else:
                        st.error(f"❌ Преименуването не успя: {rename_result}")
        else:
            st.info("Няма налични пътувания за преименуване.")

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
            "⛽ Гориво — индикатор за висока цена (EUR/л):",
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
