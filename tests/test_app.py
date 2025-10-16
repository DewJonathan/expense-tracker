import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from utils import (
    validate_expense_input,
    validate_signup,
    add_expense,
    edit_expense,
    delete_expense,
    load_user_expenses,
    get_summary,
    get_monthly_summary,
)
from db import engine, expenses_table
from app import app  # Flask app
import random
import string

# ---------------------------
# Helper for unique usernames
# ---------------------------
def random_username(base="user"):
    return base + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    app.config["WTF_CSRF_ENABLED"] = False  # <--- disable CSRF for tests
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user():
    username = random_username("testuser")
    password = "Test1234"
    # Normally signup would insert user; here we just simulate an ID
    return {"id": random.randint(1, 1000), "username": username, "password": password}

# ---------------------------
# Unit Tests
# ---------------------------

def test_validate_expense_input_valid():
    assert validate_expense_input("2025-10-14", "Food", 10.5) is True

def test_validate_expense_input_invalid_date():
    import pytest
    with pytest.raises(ValueError):
        validate_expense_input("14-10-2025", "Food", 10.5)

def test_validate_expense_input_invalid_amount():
    import pytest
    with pytest.raises(ValueError):
        validate_expense_input("2025-10-14", "Food", -5)

def test_validate_signup_valid():
    validate_signup("ValidUser123", "Password1")  # should not raise

def test_validate_signup_invalid():
    import pytest
    with pytest.raises(ValueError):
        validate_signup("", "short")
    with pytest.raises(ValueError):
        validate_signup("ab", "Password1")
    with pytest.raises(ValueError):
        validate_signup("ValidUser", "pass")
    with pytest.raises(ValueError):
        validate_signup("ValidUser", "password")  # no number
    with pytest.raises(ValueError):
        validate_signup("ValidUser", "PASSWORD1")  # no lowercase

def test_add_edit_delete_expense(test_user):
    user_id = test_user["id"]

    # Add
    exp_id = add_expense("2025-10-14", "Food", 10.5, "Lunch", user_id)
    df = load_user_expenses(user_id)
    assert len(df) >= 1  # >=1 because DB may have previous entries

    # Edit
    edit_expense(exp_id, user_id, "2025-10-15", "Food", 15.0, "Dinner")
    df = load_user_expenses(user_id)
    edited = df[df["id"] == exp_id].iloc[0]
    assert edited["amount"] == 15.0
    assert edited["description"] == "Dinner"

    # Delete
    delete_expense(exp_id, user_id)
    df = load_user_expenses(user_id)
    assert exp_id not in df["id"].values

def test_summary_functions(test_user):
    user_id = test_user["id"]

    add_expense("2025-10-14", "Food", 10.0, "Lunch", user_id)
    add_expense("2025-10-15", "Transport", 5.0, "Bus", user_id)
    df = load_user_expenses(user_id)

    category_summary = get_summary(df)
    monthly_summary = get_monthly_summary(df)

    assert any(item["category"] == "Food" for item in category_summary)
    assert any(item["category"] == "Transport" for item in category_summary)
    assert len(monthly_summary) >= 1

# ---------------------------
# Flask Route Tests
# ---------------------------
def test_signup_login_logout(client):
    username = random_username("routeuser")
    password = "Test1234"

    # Signup
    response = client.post(
        "/signup",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    # Check signup redirect to login page
    assert b"Login" in response.data

    # Login
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    # Check that the dashboard loaded
    assert b"Expense Tracker" in response.data
    assert bytes(username, "utf-8") in response.data  # username appears on dashboard

    # Logout
    response = client.get("/logout", follow_redirects=True)
    # Check redirect back to login page
    assert b"Login" in response.data