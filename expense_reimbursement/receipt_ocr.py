import re
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def ocr_image(image):
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "OCR packages are not installed. Run: "
            "python -m pip install pytesseract pillow"
        )
    # On Windows, use the normal installation path if it exists.
    try:
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
    except Exception:
        pass
    return pytesseract.image_to_string(image)


def extract_amount(text):
    patterns = [
        r"(?:total|grand total|amount payable|amount due)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return float(m.group(1).replace(",", ""))
    return None


def extract_date(text):
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if not m:
            continue
        raw = m.group(1)
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d",
                    "%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def extract_time(text):
    for p in (
        r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\b",
        r"\b(\d{1,2}\.\d{2}\s*(?:AM|PM)?)\b",
    ):
        m = re.search(p, text, re.I)
        if m:
            return m.group(1)
    return None


def extract_merchant(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    ignored = ("receipt", "invoice", "bill", "total", "amount", "date",
               "time", "tax", "gst", "phone", "mobile", "thank you")
    for line in lines[:10]:
        low = line.lower()
        if any(x in low for x in ignored):
            continue
        if not re.fullmatch(r"[\d\s:/.,\-]+", line):
            return line
    return lines[0] if lines else None


def extract_receipt_number(text):
    patterns = [
        r"(?:receipt|invoice|bill)\s*(?:no|number|#)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
        r"(?:txn|transaction\s*id|trip\s*id|order\s*id)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1)
    return None


def extract_tax(text):
    p = r"(?:GST|CGST|SGST|tax)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)"
    m = re.search(p, text, re.I)
    return float(m.group(1).replace(",", "")) if m else None


def detect_category(text):
    t = text.lower()
    if any(x in t for x in ("uber", "ola", "taxi", "cab", "transport")):
        return "Transportation"
    if any(x in t for x in ("hotel", "room", "stay", "booking")):
        return "Hotel"
    if any(x in t for x in ("restaurant", "dinner", "lunch", "food", "cafe")):
        return "Food"
    if any(x in t for x in ("flight", "airlines", "travel")):
        return "Travel"
    if any(x in t for x in ("stationery", "office", "supplies")):
        return "Office Supplies"
    return "Other"


def parse_receipt_image(image):
    raw = ocr_image(image)
    return {
        "merchant": extract_merchant(raw),
        "amount": extract_amount(raw),
        "expense_date": extract_date(raw),
        "expense_time": extract_time(raw),
        "receipt_number": extract_receipt_number(raw),
        "tax_amount": extract_tax(raw),
        "category": detect_category(raw),
        "raw_text": raw,
    }
