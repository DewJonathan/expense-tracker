# utils.py
import re
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import select, insert, update, delete

from db import engine, expenses_table


# ---------------------------
# Expense Helpers
# ---------------------------
def load_user_expenses(user_id: int) -> pd.DataFrame:
    """
    Load all expenses for a given user and return as a DataFrame.
    """
    stmt = select(expenses_table).where(expenses_table.c.user_id == user_id)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

    if not rows:
        return pd.DataFrame(columns=["id", "date", "category", "amount", "description"])

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df[["id", "date", "category", "amount", "description"]]


def validate_expense_input(date_str, category, amount):
    # Strict date validation
    try:
        datetime.strptime(date_str, "%Y-%m-%d")  # Raise error if format invalid
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    # Category validation
    if not category or not category.strip():
        raise ValueError("Category cannot be empty.")

    # Amount validation
    if amount is None or str(amount).strip() == "":
        raise ValueError("Amount is required.")
    try:
        amount_value = float(str(amount).replace(",", "").strip())
    except ValueError:
        raise ValueError("Amount must be a number.")
    if amount_value <= 0:
        raise ValueError("Amount must be greater than 0.")

    return True


def validate_signup(username: str, password: str) -> None:
    """
    Validate username and password rules for signup.
    Raises ValueError on invalid input.
    """
    if not username.strip():
        raise ValueError("Username cannot be empty.")
    if not re.match(r'^[A-Za-z0-9_]{3,20}$', username):
        raise ValueError("Username must be 3-20 characters and contain only letters, numbers, or underscores.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")


# ---------------------------
# CRUD Operations
# ---------------------------
def add_expense(date_str: str, category: str, amount: float, description: str, user_id: int) -> None:
    validate_expense_input(date_str, category, amount)

    stmt = insert(expenses_table).values(
        date=pd.to_datetime(date_str),
        category=category.strip().title(),
        amount=float(amount),
        description=description.strip(),
        user_id=user_id
    )

    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.inserted_primary_key[0] 

def edit_expense(exp_id: int, user_id: int, date_str: str, category: str, amount: float, description: str) -> None:
    from sqlalchemy.exc import NoResultFound

    # Validate input
    validate_expense_input(date_str, category, amount)

    # Prepare update statement
    stmt = (
        update(expenses_table)
        .where(expenses_table.c.id == exp_id)
        .where(expenses_table.c.user_id == user_id)
        .values(
            date=pd.to_datetime(date_str),
            category=category.strip().title(),
            amount=float(amount),
            description=description.strip()
        )
    )

    # Execute update and ensure a row was modified
    with engine.begin() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            raise NoResultFound(f"No expense found with id={exp_id} for user_id={user_id}")


def delete_expense(exp_id: int, user_id: int) -> None:
    stmt = delete(expenses_table).where(
        expenses_table.c.id == exp_id,
        expenses_table.c.user_id == user_id
    )
    with engine.begin() as conn:
        conn.execute(stmt)


# ---------------------------
# Summary Functions
# ---------------------------
def get_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Return a summary of total amounts by category.
    """
    if df.empty:
        return []
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    summary = df.groupby("category", as_index=False)["amount"].sum()
    return summary.to_dict(orient="records")


def get_monthly_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Return total amounts grouped by month in YYYY-MM format.
    """
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    grouped = df.groupby("month", as_index=False)["amount"].sum()
    grouped["amount"] = grouped["amount"].astype(float)
    return grouped.to_dict(orient="records")