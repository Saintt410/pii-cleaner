"""PII Cleaner — web demo.

Upload a CSV, get it back with personal data hidden.
Same cleaning logic as pii_cleaner.py, wrapped in a webpage.
"""

import hashlib
import io
import re

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Cleaning logic (identical to the command-line tool)
# ---------------------------------------------------------------------------

PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "CARD": re.compile(r"\b\d(?:[ -]?\d){12,15}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"),
}

NAME_COLUMNS = {"name", "first_name", "last_name", "full_name", "address"}


def luhn_valid(number):
    """Real card numbers pass the Luhn checksum. Random long numbers usually don't."""
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return len(digits) >= 13 and total % 10 == 0


def replacement(kind, value, mode):
    if mode == "hash":
        return f"{kind}_" + hashlib.sha256(value.encode()).hexdigest()[:10]
    return f"[{kind}]"


def clean_text(text, mode="mask", found=None):
    if not isinstance(text, str):
        return text
    for kind, pattern in PATTERNS.items():
        def _sub(m):
            if kind == "CARD" and not luhn_valid(m.group()):
                return m.group()
            if found is not None:
                found[kind] = found.get(kind, 0) + 1
            return replacement(kind, m.group(), mode)
        text = pattern.sub(_sub, text)
    return text


def clean_dataframe(df, mode="mask"):
    df = df.copy()
    found = {}
    for col in df.columns:
        if col.lower() in NAME_COLUMNS:
            found["NAME"] = found.get("NAME", 0) + int(df[col].notna().sum())
            df[col] = df[col].apply(
                lambda v: replacement("NAME", str(v), mode) if pd.notna(v) else v
            )
        else:
            df[col] = df[col].apply(lambda v: clean_text(v, mode, found))
    return df, found


# ---------------------------------------------------------------------------
# Sample data so the demo works even with no upload
# ---------------------------------------------------------------------------

SAMPLE = """customer_id,name,email,phone,notes,card
1,Asem Saint,asem.s@example.com,+1 415 555 0142,Called from 192.168.10.12,4111 1111 1111 1111
2,Maria Lopez,maria.l@example.org,415-555-9988,Prefers email maria.l@example.org,5500 0000 0000 0004
3,Peter Kask,,,Order #1234567890123 shipped,
4,Jane Doe,jane.doe@example.net,212-555-0199,SSN given: 123-45-6789,
"""

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PII Cleaner", page_icon="🕶️", layout="wide")

st.title("PII Cleaner")
st.write(
    "Upload a CSV and get it back with names, emails, phone numbers, SSNs, "
    "card numbers and IP addresses hidden. Nothing is stored — the file is "
    "cleaned in your browser session and nothing is written to a database."
)

with st.sidebar:
    st.header("Options")
    mode = st.radio(
        "Replacement mode",
        ["mask", "hash"],
        help=(
            "mask: swap values for [EMAIL], [PHONE] and so on.\n"
            "hash: swap values for a stable code, so the same customer keeps "
            "the same code and you can still count unique customers."
        ),
    )
    st.divider()
    st.caption("Built with Python, pandas and regular expressions.")

upload = st.file_uploader("Upload a CSV file", type="csv")

if upload is None:
    st.info("No file uploaded — showing the sample customer file.", icon="ℹ️")
    raw = pd.read_csv(io.StringIO(SAMPLE), dtype=str)
    source_name = "sample_customers"
else:
    raw = pd.read_csv(upload, dtype=str)
    source_name = upload.name.rsplit(".", 1)[0]

st.subheader("Before")
st.dataframe(raw, width="stretch")

clean, found = clean_dataframe(raw, mode)

st.subheader("After")
st.dataframe(clean, width="stretch")

st.subheader("What was replaced")
if found:
    counts = pd.DataFrame(
        sorted(found.items(), key=lambda kv: -kv[1]),
        columns=["Type of data", "Times replaced"],
    )
    st.dataframe(counts, width="stretch", hide_index=True)
else:
    st.success("Nothing was replaced — no personal data found in this file.")

st.download_button(
    f"Download cleaned CSV ({mode} mode)",
    clean.to_csv(index=False).encode("utf-8"),
    file_name=f"{source_name}_clean.csv",
    mime="text/csv",
)

st.divider()
st.caption(
    "Card numbers are only replaced when they pass the Luhn checksum, so an "
    "order number that happens to be 13 digits long is left alone. "
    "All sample values are fake."
)
