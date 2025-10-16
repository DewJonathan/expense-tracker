from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select, insert
from datetime import datetime, timedelta
from db import engine, users_table
from utils import  load_user_expenses, add_expense, edit_expense, delete_expense, get_summary, get_monthly_summary, validate_expense_input, validate_signup
from flask_wtf import CSRFProtect
import os
from flask_wtf.csrf import generate_csrf
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# --- CSRF Protection ---
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

MAX_ATTEMPTS = 5       
LOCK_TIME = timedelta(minutes=5)

@app.route("/test_csrf")
def test_csrf():
    return jsonify({"csrf": generate_csrf()})

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def get_user_by_username(username):
    stmt = select(users_table).where(users_table.c.username == username)
    with engine.connect() as conn:
        return conn.execute(stmt).mappings().first()

def create_user(username, password_hash):
    stmt = insert(users_table).values(username=username, password=password_hash)
    with engine.begin() as conn:
        return conn.execute(stmt).inserted_primary_key[0]

@login_manager.user_loader
def load_user(user_id):
    stmt = select(users_table).where(users_table.c.id == int(user_id))
    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()
    if row:
        return User(row["id"], row["username"], row["password"])
    return None

# --- Routes ---
@app.route("/")
@login_required
def home():
    df = load_user_expenses(current_user.id)
    category_summary = get_summary(df)
    monthly_summary = get_monthly_summary(df)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d") if not df.empty else []
    return render_template("home.html", user=current_user.username, expenses=df.to_dict(orient="records"), category_plot=category_summary, monthly_plot=monthly_summary)

@app.route("/chart_data")
@login_required
def chart_data():
    df = load_user_expenses(current_user.id)
    if df.empty:
        return jsonify({"category": [], "monthly": []})  
        
    category_summary = get_summary(df)
    monthly_summary = get_monthly_summary(df)
    return jsonify({"category": category_summary, "monthly": monthly_summary})

@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense_route():
    data = request.get_json()

    # Extract fields safely
    date_str = data.get("date", "").strip()
    category = data.get("category", "").strip()
    amount = data.get("amount")
    description = data.get("description", "").strip()

    try:
        # Validate input
        validate_expense_input(date_str, category, amount)

        # Add to database
        add_expense(date_str, category, amount, description, current_user.id)

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        print("Server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

    # Return updated data
    df = load_user_expenses(current_user.id)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d") if not df.empty else []
    return jsonify({
        "success": True,
        "expenses": df.to_dict(orient="records"),
        "category": get_summary(df),
        "monthly": get_monthly_summary(df)
    })

@app.route("/get_expenses", methods=["GET"])
@login_required
def get_expenses():
    df = load_user_expenses(current_user.id)
    if df.empty:
        return jsonify({"expenses": [], "category": [], "monthly": []})
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return jsonify({
        "expenses": df.to_dict(orient="records"),
        "category": get_summary(df),
        "monthly": get_monthly_summary(df)
    })

@app.route("/edit_expense/<int:exp_id>", methods=["POST"])
@login_required
def edit_expense_route(exp_id):
    data = request.get_json()

    # Extract fields safely
    date_str = data.get("date", "").strip()
    category = data.get("category", "").strip()
    amount = data.get("amount")
    description = data.get("description", "").strip()

    try:
        # Validate input
        validate_expense_input(date_str, category, amount)

        # Update database
        edit_expense(exp_id, current_user.id, date_str, category, amount, description)

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        print("Server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

    # Return updated data
    df = load_user_expenses(current_user.id)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d") if not df.empty else []
    return jsonify({
        "success": True,
        "expenses": df.to_dict(orient="records"),
        "category": get_summary(df),
        "monthly": get_monthly_summary(df)
    })

@app.route("/delete_expense/<int:exp_id>", methods=["POST"])
@login_required
def delete_expense_route(exp_id):
    delete_expense(exp_id, current_user.id)
    df = load_user_expenses(current_user.id)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d") if not df.empty else []
    return jsonify({"success": True, "expenses": df.to_dict(orient="records"), "category": get_summary(df), "monthly": get_monthly_summary(df)})

# --- Auth Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if "login_attempts" not in session:
            session["login_attempts"] = {}

        user_attempts = session["login_attempts"].get(username, {"count": 0, "time": None})
        last_attempt_time = datetime.min
        if isinstance(user_attempts.get("time"), str):
            last_attempt_time = datetime.fromisoformat(user_attempts["time"])

        if user_attempts["count"] >= MAX_ATTEMPTS and datetime.now() - last_attempt_time < LOCK_TIME:
            flash("Too many failed attempts. Try again later.", "error")
            return render_template("login.html")

        row = get_user_by_username(username)
        if row and check_password_hash(row["password"], password):
            login_user(User(row["id"], row["username"], row["password"]))
            session["login_attempts"].pop(username, None)
            return redirect(url_for("home"))
        else:
            user_attempts["count"] += 1
            user_attempts["time"] = datetime.now().isoformat()
            session["login_attempts"][username] = user_attempts
            flash("Invalid username or password.", "error")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            validate_signup(username, password)
            if get_user_by_username(username):
                flash("Username already exists.", "error")
            else:
                hashed_pw = generate_password_hash(password)
                create_user(username, hashed_pw)
                flash("Signup successful. Please login.", "success")
                return redirect(url_for("login"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)