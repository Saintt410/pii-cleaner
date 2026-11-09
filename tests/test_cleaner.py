import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pandas as pd
from pii_cleaner import clean_text, clean_dataframe, luhn_valid


def test_email_is_masked():
    assert clean_text("mail me at a.b@x.com") == "mail me at [EMAIL]"

def test_ssn_is_masked():
    assert "[SSN]" in clean_text("ssn 123-45-6789")

def test_luhn():
    assert luhn_valid("4111 1111 1111 1111")
    assert not luhn_valid("1234567890123")

def test_order_number_not_treated_as_card():
    assert "1234567890123" in clean_text("Order #1234567890123")

def test_hash_is_stable():
    assert clean_text("a@b.com", "hash") == clean_text("a@b.com", "hash")

def test_name_column_masked():
    df, found = clean_dataframe(pd.DataFrame({"name": ["Anna"], "x": ["hi"]}))
    assert df.loc[0, "name"] == "[NAME]" and found["NAME"] == 1
