# Expense Tracker Web App

A full-featured Expense Tracker built with Flask that helps users manage daily expenses, organize spending into categories, and visualize summaries — all within a clean and responsive dashboard.

---

## Features

- **User Authentication**: Secure signup and login system with password hashing.
- **Add, Edit, Delete Expenses**: Manage transactions
- **Expense Categories**: Organize spending by type
- **Dashboard & Summary**:
  - View total expenses by category.
  - Track monthly spending trends
- **Flash Messages**: Instant feedback on user actions.
- **Responsive UI**: Built with HTML, CSS, and JavaScript.

---

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite (`expenses.db`)
- **Frontend**: HTML, CSS, JavaScript, Jinja2
- **Testing**: Pytest
- **Environment Management**: `.env` for secrets, `venv` for virtual environment

**Dashboard**
![Dashboard](screenshots/dashboard.png)

## Setup & Installation

1. **Clone the repository:**

   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker

2. **Create and activate a virtual environment**

   ```bash
   source venv/bin/activate # On Windows: venv\Scripts\activate

   ```
3. **install dependencies**

   ```bash
   pip install -r requirements.txt

   ```

4. **Set up environment variables**
   Create a .env file in the project root:

   SECRET_KEY=your_secret_key
   FLASK_ENV=development

5. **Initialize the database**

   ```bash
   python db.py

   ```
6. **Run the app**

   ```bash
   flask run

   ```

   Open your browser and go to → http://127.0.0.1:5000

## Future Improvements

- Connect to Plaid API for real-time bank transactions
- Export expenses to CSV or PDF
- Pie & Line graphs
- Dark mode toggle

## Author

- Jonathan Dew
- Charlotte, NC

GitHub: https://github.com/DewJonathan
LinkedIn: https://www.linkedin.com/in/jonathandew
