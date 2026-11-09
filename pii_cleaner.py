import argparse
import hashlib
import re

import pandas as pd


PATTERNS = {
    "EMAIL": re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ),
    "CARD": re.compile(
        r"\b(?:\d[ -]?){13,16}\b"
    ),
    "SSN": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "IP": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
    "PHONE": re.compile(
        r"(?<!\d)(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"
    ),
}

# Combine the patterns so each part of the original text is checked once.
COMBINED_PATTERN = re.compile(
    "|".join(
        f"(?P<{kind}>{pattern.pattern})"
        for kind, pattern in PATTERNS.items()
    )
)

NAME_COLUMNS = {
    "name",
    "first_name",
    "last_name",
    "full_name",
    "address",
}


def luhn_valid(number):
    """Check whether a card number passes the Luhn checksum."""
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    total = 0

    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return len(digits) >= 13 and total % 10 == 0


def replacement(kind, value, mode):
    """Return either a mask or a stable hash for a sensitive value."""
    if mode == "hash":
        digest = hashlib.sha256(value.encode()).hexdigest()
        return f"{kind}_{digest[:10]}"

    return f"[{kind}]"


def clean_text(text, mode="mask", found=None):
    """Clean sensitive values inside one piece of text."""
    if not isinstance(text, str):
        return text

    def replace_match(match):
        kind = match.lastgroup
        value = match.group()

        # Keep long numbers that fail the card checksum.
        if kind == "CARD" and not luhn_valid(value):
            return value

        if found is not None:
            found[kind] = found.get(kind, 0) + 1

        return replacement(kind, value, mode)

    return COMBINED_PATTERN.sub(replace_match, text)


def clean_dataframe(df, mode="mask"):
    """Clean every column and return the table plus replacement counts."""
    df = df.copy()
    found = {}

    for col in df.columns:
        if col.lower() in NAME_COLUMNS:
            found["NAME"] = (
                found.get("NAME", 0)
                + int(df[col].notna().sum())
            )

            df[col] = df[col].apply(
                lambda value: (
                    replacement("NAME", str(value), mode)
                    if pd.notna(value)
                    else value
                )
            )
        else:
            df[col] = df[col].apply(
                lambda value: clean_text(value, mode, found)
            )

    return df, found


def main():
    parser = argparse.ArgumentParser(
        description="Remove PII from a CSV file"
    )
    parser.add_argument("input")
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--mode",
        choices=["mask", "hash"],
        default="mask",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype=str)
    clean, found = clean_dataframe(df, args.mode)

    out = args.out or args.input.replace(".csv", "_clean.csv")
    clean.to_csv(out, index=False)

    print(f"Cleaned {len(df)} rows -> {out}")

    for kind, count in sorted(found.items()):
        print(f"  {kind:<6} {count} replaced")


if __name__ == "__main__":
    main()
