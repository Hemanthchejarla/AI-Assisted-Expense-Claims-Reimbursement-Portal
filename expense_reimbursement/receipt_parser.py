import re
from datetime import datetime


def extract_amount(text):
    patterns = [
        r"(?:total|grand total|amount payable|amount due)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def extract_date(text):
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        raw = match.group(1)
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d",
                    "%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def extract_time(text):
    patterns = [
        r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\b",
        r"\b(\d{1,2}\.\d{2}\s*(?:AM|PM)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_merchant(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    ignored = ("receipt", "invoice", "bill", "total", "amount", "date",
               "time", "tax", "gst", "phone", "mobile", "thank you")
    for line in lines[:10]:
        lower = line.lower()
        if any(word in lower for word in ignored):
            continue
        if re.fullmatch(r"[\d\s:/.,\-]+", line):
            continue
        return line
    return lines[0] if lines else None


def extract_receipt_number(text):
    patterns = [
        r"(?:receipt|invoice|bill)\s*(?:no|number|#)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
        r"(?:txn|transaction\s*id|trip\s*id|order\s*id)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_tax(text):
    pattern = r"(?:GST|CGST|SGST|tax)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)"
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1).replace(",", "")) if match else None


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


def parse_receipt(text):
    return {
        "merchant": extract_merchant(text),
        "amount": extract_amount(text),
        "expense_date": extract_date(text),
        "expense_time": extract_time(text),
        "receipt_number": extract_receipt_number(text),
        "tax_amount": extract_tax(text),
        "category": detect_category(text),
        "raw_text": text,
    }
