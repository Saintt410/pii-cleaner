import re
import pandas as pd


PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "CARD": re.compile(r"(?<!\d)\d(?:[ -]?\d){12,15}(?![ -]?\d)"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"),
}


def luhn_valid(number):
    # Remove spaces and hyphens, then turn each digit into a number.
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    total = 0

    # Start at the right-hand end of the number.
    for i, d in enumerate(reversed(digits)):
        # Double every second digit.
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    # Accept 13–16 digits only when the total is divisible by 10.
    return 13 <= len(digits) <= 16 and total % 10 == 0


def clean_text(text):
    # Leave empty cells alone.
    if not isinstance(text, str):
        return text

    for kind, pattern in PATTERNS.items():
        def replace_match(match):
            # Keep long numbers that fail the card checksum.
            if kind == "CARD" and not luhn_valid(match.group()):
                return match.group()
            return f"[{kind}]"

        text = pattern.sub(replace_match, text)

    return text


# Read the original CSV, keeping values as text.
df = pd.read_csv("data/customers.csv", dtype=str)

# Clean every cell in every column.
for col in df.columns:
    df[col] = df[col].apply(clean_text)

# Show every column, including notes and cards.
print(df.to_string(index=False))

