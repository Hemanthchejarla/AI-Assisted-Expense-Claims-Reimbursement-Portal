import re
from datetime import datetime


def extract_amount(text):
    """
    Find an amount such as:
    ₹245
    ₹1,250.50
    Rs 245
    Total: 245.00
    """

    patterns = [
        r'₹\s*([\d,]+(?:\.\d{1,2})?)',
        r'Rs\.?\s*([\d,]+(?:\.\d{1,2})?)',
        r'Total\s*[:\-]?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)',
        r'Amount\s*[:\-]?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1)

            return float(
                value.replace(",", "")
            )

    return None


def extract_date(text):

    patterns = [

        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',

        r'(\d{1,2}\s+'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r'[a-z]*\s+\d{4})'

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            raw_date = match.group(1)

            for fmt in [
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%d %b %Y",
                "%d %B %Y"
            ]:

                try:

                    parsed = datetime.strptime(
                        raw_date,
                        fmt
                    )

                    return parsed.strftime(
                        "%Y-%m-%d"
                    )

                except ValueError:
                    pass

    return None


def extract_merchant(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    ignored_words = [
        "receipt",
        "invoice",
        "bill",
        "total",
        "amount",
        "date",
        "tax",
        "gst"
    ]

    for line in lines[:5]:

        lower = line.lower()

        if not any(
            word in lower
            for word in ignored_words
        ):

            return line

    return lines[0]


def detect_category(text):

    text = text.lower()

    if any(
        word in text
        for word in [
            "uber",
            "ola",
            "taxi",
            "cab",
            "transport"
        ]
    ):

        return "Transportation"

    if any(
        word in text
        for word in [
            "hotel",
            "room",
            "stay",
            "booking"
        ]
    ):

        return "Hotel"

    if any(
        word in text
        for word in [
            "restaurant",
            "dinner",
            "lunch",
            "food",
            "cafe"
        ]
    ):

        return "Food"

    if any(
        word in text
        for word in [
            "flight",
            "airlines",
            "travel"
        ]
    ):

        return "Travel"

    if any(
        word in text
        for word in [
            "stationery",
            "office",
            "supplies"
        ]
    ):

        return "Office Supplies"

    return "Other"


def parse_receipt(text):

    return {
        "merchant": extract_merchant(text),
        "amount": extract_amount(text),
        "expense_date": extract_date(text),
        "category": detect_category(text)
    }
