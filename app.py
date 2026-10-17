from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)

DATABASE = "pharmastock.db"


# Connect to the database
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create the database table
def create_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reorder_level INTEGER NOT NULL DEFAULT 20,
                purchase_price REAL NOT NULL DEFAULT 0,
                selling_price REAL NOT NULL DEFAULT 0,
                expiry_date TEXT NOT NULL
            )
        """)


# Calculate expiry status
def get_expiry_status(expiry_date):
    expiry = date.fromisoformat(expiry_date)
    today = date.today()

    if expiry < today:
        return "EXPIRED"

    if expiry <= today + timedelta(days=90):
        return "EXPIRING SOON"

    return "OK"


# Dashboard
@app.route("/")
def dashboard():
    with get_db() as db:
        products = db.execute(
            "SELECT * FROM products ORDER BY expiry_date"
        ).fetchall()

    today = date.today()
    total_products = len(products)
    total_units = sum(p["quantity"] for p in products)

    low_stock = sum(
        1 for p in products
        if p["quantity"] <= p["reorder_level"]
    )

    expired = sum(
        1 for p in products
        if date.fromisoformat(p["expiry_date"]) < today
    )

    expiring_soon = sum(
        1 for p in products
        if today <= date.fromisoformat(p["expiry_date"])
        <= today + timedelta(days=90)
    )

    return render_template(
        "index.html",
        products=products,
        total_products=total_products,
        total_units=total_units,
        low_stock=low_stock,
        expired=expired,
        expiring_soon=expiring_soon,
        get_expiry_status=get_expiry_status
    )


# Add a product
@app.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch_number", "").strip()
    expiry = request.form.get("expiry_date", "")

    try:
        quantity = int(request.form.get("quantity", ""))
        reorder_level = int(
            request.form.get("reorder_level", "20")
        )
        purchase_price = float(
            request.form.get("purchase_price", "0")
        )
        selling_price = float(
            request.form.get("selling_price", "0")
        )

        date.fromisoformat(expiry)

        if not name or not batch:
            return "Product name and batch number are required.", 400

        if (
            quantity < 0
            or reorder_level < 0
            or purchase_price < 0
            or selling_price < 0
        ):
            return "Values cannot be negative.", 400

    except (ValueError, TypeError):
        return "Enter valid quantities, prices, and expiry date.", 400

    with get_db() as db:
        db.execute("""
            INSERT INTO products (
                name, batch_number, quantity,
                reorder_level, purchase_price,
                selling_price, expiry_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, batch, quantity, reorder_level,
            purchase_price, selling_price, expiry
        ))

    return redirect("/")


# Run the application
create_database()

if __name__ == "__main__":
    app.run(debug=True)