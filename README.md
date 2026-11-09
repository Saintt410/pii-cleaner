# PII Cleaner

A tool designed by uncle saint that scans CSV files and hides personal data like names, emails,
phone numbers and card numbers, so the data can be shared or analysed safely.

## Why it matters
What PII is (personal data like names, emails, phone numbers).
Why GDPR means companies must protect it before sharing or analysing data.

## What it detects
- Emails, phone numbers, SSNs, IP addresses
- Card numbers (checked with the Luhn checksum, so order numbers are kept)
- Whole name columns

## How to run it
    python3 -m venv .venv
    source .venv/bin/activate
    pip install pandas pytest
    python3 pii_cleaner.py data/customers.csv
    python3 pii_cleaner.py data/customers.csv --mode hash

## Example
Paste a "before" row and an "after" row from your own output.

## Tests
    pytest

## What I'd add next
For example: Estonian ID codes (isikukood), or support for Excel files.

