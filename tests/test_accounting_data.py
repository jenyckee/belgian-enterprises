"""
Integration tests for the NBB CBSO accounting-data endpoints.

These hit the live NBB API, so they need AUTHENTIC_DATA_PRIMARY_KEY (or the
secondary key) in .env / .env.local. When no key is present the tests skip.

Run with:  pytest test_accounting_data.py -v
       or:  python test_accounting_data.py
"""
import os
import json
import urllib.request
import urllib.error
import uuid

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(".env.local", override=True)
load_dotenv(".env", override=False)

from api.main import app
from api.routes import NBB_USER_AGENT

client = TestClient(app)

# irex Consulting (enterprise number without dots)
ENTERPRISE_NUMBER = "0689587747"
FISCAL_YEAR = 2024
# Known-good deposit reference for irex Consulting's 2024 exercise.
WORKING_REFERENCE = "2025-00570954"

API_KEY = os.getenv("AUTHENTIC_DATA_PRIMARY_KEY") or os.getenv("AUTHENTIC_DATA_SECONDARY_KEY")
requires_key = pytest.mark.skipif(not API_KEY, reason="NBB API key not configured")


@requires_key
def test_direct_accounting_data_call():
    """Direct NBB call for a known reference succeeds (regression: UA must be set)."""
    url = f"https://ws.cbso.nbb.be/authentic/deposit/{WORKING_REFERENCE}/accountingData"

    request = urllib.request.Request(url)
    request.add_header("Accept", "application/x.jsonxbrl")
    request.add_header("X-Request-Id", str(uuid.uuid4()))
    request.add_header("Cache-Control", "no-cache")
    request.add_header("NBB-CBSO-Subscription-Key", API_KEY)
    # NBB's Azure gateway 403s the default "Python-urllib/x.y" User-Agent.
    request.add_header("User-Agent", NBB_USER_AGENT)

    with urllib.request.urlopen(request) as response:
        assert response.getcode() == 200
        data = json.loads(response.read().decode())

    assert data.get("ReferenceNumber") == WORKING_REFERENCE
    assert data.get("Rubrics")


@requires_key
def test_get_enterprise_references():
    """The /references endpoint returns the enterprise's deposits."""
    response = client.get(f"/enterprise/{ENTERPRISE_NUMBER}/references")
    assert response.status_code == 200, response.text

    data = response.json()
    assert isinstance(data, list) and data, "expected at least one reference"

    references = {ref["reference_number"] for ref in data}
    assert WORKING_REFERENCE in references


@requires_key
def test_get_accounting_data():
    """The /accountingdata/{year} endpoint returns rubrics for the fiscal year."""
    response = client.get(f"/enterprise/{ENTERPRISE_NUMBER}/accountingdata/{FISCAL_YEAR}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["reference_number"] == WORKING_REFERENCE
    assert data["enterprise_name"]
    assert data["rubrics"], "expected accounting rubrics"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
