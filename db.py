from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date

DB_FILE = "expenses.db"
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)
metadata = MetaData()

# Users table
users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, unique=True, nullable=False),
    Column("password", String, nullable=False)
)

# Expenses table
expenses_table = Table(
    "expenses", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("category", String, nullable=False),
    Column("amount", Float, nullable=False),
    Column("description", String),
    Column("user_id", Integer, nullable=False)
)

metadata.create_all(engine)