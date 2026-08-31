import os
import re
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False


def _tm_receipt_normalize_text(text: str) -> str:
    """Нормализира текста от OCR за по-лесно извличане на числа и дати."""
    if not text:
        return ""
    # Замяна на често допускани грешки от OCR при кирилица/латиница
    replacements = {
        'О': '0', 'O': '0',
        'о': '0', 'o': '0',
        'З': '3', 'з': '3',
        'S': '5', 's': '5',
        ',': '.',
    }
    # Нормализация на основните символи
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(line.strip())
    return "\n".join(cleaned_lines)


def _tm_receipt_number_candidates(text: str):
    """Извлича числови кандидати (суми) от даден текстов прозорец."""
    candidates = []
    # Търси числа във формат 12.34 или 123.45
    matches = re.findall(r"\b\d+[\.\,]\d{2}\b", text)
    for m in matches:
        try:
            val = float(m.replace(',', '.'))
            candidates.append((val, m))
        except ValueError:
            continue
    return candidates


def _tm_receipt_preprocess(image: Image.Image) -> Image.Image:
    """Оптимизирана подготовка на изображението за Tesseract OCR."""
    img = image.convert("RGB")
    # Мащабиране за по-добро разчитане на дребни шрифтове
    img = img.resize(
        (max(1, int(img.width * 2.0)), max(1, int(img.height * 2.0))),
        Image.Resampling.LANCZOS,
    )
    gray = ImageOps.grayscale(img)
    # По-плавно регулиране на контраста без унищожаване на детайлите
    gray = ImageOps.autocontrast(gray, cutoff=0.5)
    return gray


def _tm_receipt_targeted_ocr(image: Image.Image) -> str:
    """Целеви OCR за долната част на бележката без отрязване на тотала."""
    if not _PYTESSERACT_AVAILABLE or image is None:
        return ""
    try:
        # Взимаме долните 70% от изображението вместо само 48%, за да не се режат суми
        crop_top = int(image.height * 0.30)
        crop = image.crop((0, crop_top, image.width, image.height))
        prep = _tm_receipt_preprocess(crop)

        try:
            return pytesseract.image_to_string(prep, lang="bul+eng", config="--oem 3 --psm 6")
        except Exception:
            return pytesseract.image_to_string(prep, lang="eng", config="--oem 3 --psm 6")
    except Exception:
        return ""


def _tm_receipt_ocr(image: Image.Image) -> dict:
    """Подобрен OCR за касови бележки."""
    if not _PYTESSERACT_AVAILABLE:
        return {"ok": False, "error": "pytesseract не е инсталиран.", "text": ""}

    try:
        prepared = _tm_receipt_preprocess(image)
        # Опит за разчитане с bul+eng, при грешка — fallback към eng
        try:
            raw_text = pytesseract.image_to_string(prepared, lang="bul+eng", config="--oem 3 --psm 6")
        except Exception:
            raw_text = pytesseract.image_to_string(prepared, lang="eng", config="--oem 3 --psm 6")

    except Exception as exc:
        return {"ok": False, "error": f"OCR грешка: {exc}", "text": ""}

    if not raw_text.strip():
        # Опит с targeted OCR ако основният върне празен резултат
        raw_text = _tm_receipt_targeted_ocr(image)

    if not raw_text.strip():
        return {"ok": False, "error": "OCR не върна текст.", "text": ""}

    normalized = _tm_receipt_normalize_text(raw_text)
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]

    total_bgn = None
    total_eur = None

    # Расширен списък от ключови думи за търсене на крайна сума
    total_keywords = ["ОБЩА", "ОБЩО", "СУМА", "TOTAL", "TOT", "В СКУПНО", "БРОЙКА", "PAY", "ТОТАЛ"]

    for i, line in enumerate(lines):
        upper = line.upper()
        if any(kw in upper for kw in total_keywords):
            # Вземаме същия ред и следващите 2 реда
            window = " ".join(lines[i:min(i + 3, len(lines))])
            nums = [v for v, _ in _tm_receipt_number_candidates(window)]

            # Приемаме всяка валидна положителна сума (премахнато v >= 100)
            valid_nums = [v for v in nums if v > 0]
            if valid_nums:
                total_bgn = max(valid_nums)

            smaller = [v for v in valid_nums if total_bgn and 0 < v < total_bgn]
            if ("ЕВРО" in upper or "EUR" in upper) and smaller:
                total_eur = min(smaller)

    # Дати и час
    dates = re.findall(r"\b(\d{2}[\.\/-]\d{2}[\.\/-]\d{2,4})\b", normalized)
    times = re.findall(r"\b(\d{2}:\d{2}(?::\d{2})?)\b", normalized)

    return {
        "ok": True,
        "error": "",
        "text": raw_text,
        "targeted_text": "",
        "total_bgn": total_bgn,
        "total_eur": total_eur,
        "date": dates[-1] if dates else None,
        "date_ocr": dates[-1] if dates else None,
        "date_corrected": False,
        "time": times[-1] if times else None,
        "lang": "bul+eng",
    }
