import re
import pandas as pd

# A regex pattern describes what a piece of text "looks like".
PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"),
}



def clean_text(text):
    if not isinstance(text, str):      # empty cells are NaN, not text — skip them
        return text
    for kind, pattern in PATTERNS.items():
        text = pattern.sub(f"[{kind}]", text)
    return text


df = pd.read_csv("data/customers.csv", dtype=str)
for col in df.columns:
    df[col] = df[col].apply(clean_text)
print(df)
