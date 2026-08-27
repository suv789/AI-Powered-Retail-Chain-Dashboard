"""
seed_data.py
Generates 24 months of realistic synthetic retail data and inserts it into PostgreSQL.
Run once after setting up schema.sql.
"""

import os
import random
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

# ── DB Connection ────────────────────────────────────────────
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)

# ── Date Range ───────────────────────────────────────────────
END_DATE   = date.today().replace(day=1) - timedelta(days=1)
START_DATE = END_DATE - relativedelta(months=24) + timedelta(days=1)

# ── Reference Data ───────────────────────────────────────────
REGIONS = [
    ("North", "India"), ("South", "India"),
    ("East",  "India"), ("West",  "India"),
    ("Central", "India"),
]

STORES_PER_REGION = {
    "North":   ["Delhi Central", "Noida Hub", "Gurugram Outlet"],
    "South":   ["Bengaluru Main", "Chennai Square", "Hyderabad Plaza"],
    "East":    ["Kolkata Park", "Bhubaneswar Store", "Patna Centre"],
    "West":    ["Mumbai Flagship", "Pune City", "Ahmedabad Mall"],
    "Central": ["Bhopal Store", "Nagpur Hub"],
}

REGION_CITIES = {
    "North":   ["Delhi", "Noida", "Gurugram", "Lucknow"],
    "South":   ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
    "East":    ["Kolkata", "Bhubaneswar", "Patna", "Guwahati"],
    "West":    ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "Central": ["Bhopal", "Nagpur", "Indore", "Raipur"],
}

CATEGORIES = [
    ("Electronics",    "Tech"),
    ("Clothing",       "Fashion"),
    ("Groceries",      "Food & Daily"),
    ("Home & Kitchen", "Home"),
    ("Sports & Fitness","Lifestyle"),
    ("Beauty & Personal Care", "Lifestyle"),
    ("Books & Stationery", "Education"),
    ("Toys & Games",   "Kids"),
]

PRODUCTS_PER_CATEGORY = {
    "Electronics":             [("Wireless Earbuds", 2499, 1400), ("Smart Watch", 4999, 3000),
                                ("Bluetooth Speaker", 1999, 1100), ("Phone Stand", 399, 180),
                                ("USB-C Hub", 1299, 700)],
    "Clothing":                [("Men's Formal Shirt", 999, 450), ("Women's Kurti", 799, 350),
                                ("Jeans - Regular Fit", 1299, 600), ("Sports T-Shirt", 599, 250),
                                ("Winter Jacket", 2499, 1200)],
    "Groceries":               [("Basmati Rice 5kg", 449, 300), ("Refined Oil 1L", 179, 110),
                                ("Whole Wheat Atta 10kg", 399, 260), ("Masala Combo Pack", 299, 170),
                                ("Organic Honey 500g", 349, 200)],
    "Home & Kitchen":          [("Non-Stick Tawa", 799, 420), ("Stainless Steel Casserole", 1199, 650),
                                ("Dinner Set 12pc", 1499, 800), ("Electric Kettle", 999, 550),
                                ("Water Purifier Filter", 599, 300)],
    "Sports & Fitness":        [("Yoga Mat", 699, 350), ("Resistance Bands Set", 499, 220),
                                ("Dumbbells 5kg Pair", 1299, 700), ("Running Shoes", 2499, 1300),
                                ("Cycling Gloves", 399, 180)],
    "Beauty & Personal Care":  [("Face Wash 150ml", 299, 140), ("Sunscreen SPF50", 449, 210),
                                ("Hair Oil 200ml", 199, 90), ("Lipstick Set", 599, 280),
                                ("Men's Grooming Kit", 899, 430)],
    "Books & Stationery":      [("Notebook Set of 3", 199, 90), ("Gel Pen Box 20pc", 149, 65),
                                ("Self-Help Bestseller", 399, 180), ("Art Sketchbook A4", 299, 130),
                                ("Sticky Notes Bundle", 99, 40)],
    "Toys & Games":            [("Building Blocks 200pc", 899, 450), ("Board Game Classic", 699, 340),
                                ("Remote Control Car", 1499, 780), ("Soft Toy Set", 599, 280),
                                ("Puzzle 1000pc", 499, 240)],
}

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]
ORDER_STATUS_WEIGHTS = [0.88, 0.07, 0.05]   # Completed, Returned, Cancelled
SEGMENT_WEIGHTS = [0.40, 0.30, 0.20, 0.10]  # Bronze, Silver, Gold, Platinum


def seasonal_multiplier(d: date) -> float:
    """Boost orders in festive/holiday months (Oct, Nov, Dec, Jan)."""
    boosts = {10: 1.4, 11: 1.6, 12: 1.8, 1: 1.3, 8: 1.1, 3: 1.15}
    return boosts.get(d.month, 1.0)


def insert_regions(conn):
    result = {}
    for name, country in REGIONS:
        row = conn.execute(
            text("INSERT INTO regions (region_name, country) VALUES (:n, :c) RETURNING region_id"),
            {"n": name, "c": country}
        ).fetchone()
        result[name] = row[0]
    print(f"  ✓ Inserted {len(result)} regions")
    return result


def insert_stores(conn, region_map):
    result = {}
    for region_name, stores in STORES_PER_REGION.items():
        rid = region_map[region_name]
        for store_name in stores:
            city = random.choice(REGION_CITIES[region_name])
            opened = fake.date_between(start_date="-6y", end_date="-2y")
            size   = random.choice(["Small", "Medium", "Large"])
            row = conn.execute(
                text("""INSERT INTO stores (store_name, city, region_id, opened_date, store_size)
                         VALUES (:sn, :city, :rid, :od, :sz) RETURNING store_id"""),
                {"sn": store_name, "city": city, "rid": rid, "od": opened, "sz": size}
            ).fetchone()
            result[store_name] = row[0]
    print(f"  ✓ Inserted {len(result)} stores")
    return result


def insert_categories(conn):
    result = {}
    for cat_name, dept in CATEGORIES:
        row = conn.execute(
            text("INSERT INTO categories (category_name, department) VALUES (:cn, :d) RETURNING category_id"),
            {"cn": cat_name, "d": dept}
        ).fetchone()
        result[cat_name] = row[0]
    print(f"  ✓ Inserted {len(result)} categories")
    return result


def insert_products(conn, category_map):
    result = {}
    for cat_name, products in PRODUCTS_PER_CATEGORY.items():
        cid = category_map[cat_name]
        for pname, price, cost in products:
            sku = "SKU-" + fake.bothify("??###").upper()
            row = conn.execute(
                text("""INSERT INTO products (sku, product_name, category_id, unit_price, cost_price)
                         VALUES (:sku, :pn, :cid, :up, :cp) RETURNING product_id"""),
                {"sku": sku, "pn": pname, "cid": cid, "up": price, "cp": cost}
            ).fetchone()
            result[pname] = row[0]
    print(f"  ✓ Inserted {len(result)} products (SKUs)")
    return result


def insert_customers(conn, region_map, n=2000):
    customer_ids = []
    segments = ["Bronze", "Silver", "Gold", "Platinum"]
    for _ in range(n):
        region_name = random.choices(list(region_map.keys()), weights=[25,25,20,20,10])[0]
        city        = random.choice(REGION_CITIES[region_name])
        signup      = fake.date_between(start_date=START_DATE - relativedelta(months=6), end_date=END_DATE)
        segment     = random.choices(segments, weights=SEGMENT_WEIGHTS)[0]
        row = conn.execute(
            text("""INSERT INTO customers (full_name, email, phone, city, region_id, signup_date, customer_segment)
                     VALUES (:fn, :em, :ph, :city, :rid, :sd, :seg) RETURNING customer_id"""),
            {
                "fn": fake.name(), "em": fake.unique.email(),
                "ph": fake.phone_number()[:20], "city": city,
                "rid": region_map[region_name], "sd": signup, "seg": segment
            }
        ).fetchone()
        customer_ids.append(row[0])
    print(f"  ✓ Inserted {len(customer_ids)} customers")
    return customer_ids


def insert_orders(conn, customer_ids, store_ids, product_ids):
    """Generate orders day by day across 24 months."""
    total_orders = 0
    total_items  = 0
    current = START_DATE

    while current <= END_DATE:
        multiplier = seasonal_multiplier(current)
        # ~15-30 orders per day per store across all stores, scaled by multiplier
        base_orders = int(random.gauss(20, 5) * multiplier)
        base_orders = max(5, base_orders)

        orders_batch = []
        for _ in range(base_orders):
            orders_batch.append({
                "cid":  random.choice(customer_ids),
                "sid":  random.choice(store_ids),
                "od":   current,
                "os":   random.choices(["Completed","Returned","Cancelled"], weights=ORDER_STATUS_WEIGHTS)[0],
                "pm":   random.choice(PAYMENT_METHODS),
            })

        order_rows = []
        for ob in orders_batch:
            row = conn.execute(
                text("""INSERT INTO orders (customer_id, store_id, order_date, order_status, payment_method)
                         VALUES (:cid, :sid, :od, :os, :pm) RETURNING order_id"""),
                ob
            ).fetchone()
            order_rows.append(row)

        items_batch = []
        for row in order_rows:
            oid = row[0]
            num_items = random.choices([1, 2, 3, 4, 5], weights=[35, 30, 20, 10, 5])[0]
            chosen_products = random.sample(product_ids, min(num_items, len(product_ids)))
            for pid, price in chosen_products:
                qty      = random.choices([1, 2, 3, 4], weights=[55, 25, 15, 5])[0]
                discount = random.choices([0, 5, 10, 15, 20], weights=[50, 20, 15, 10, 5])[0]
                items_batch.append({"oid": oid, "pid": pid, "qty": qty, "up": price, "disc": discount})

        if items_batch:
            conn.execute(
                text("""INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_pct)
                         VALUES (:oid, :pid, :qty, :up, :disc)"""),
                items_batch
            )

        total_orders += len(order_rows)
        total_items  += len(items_batch)
        current += timedelta(days=1)

    print(f"  ✓ Inserted {total_orders:,} orders with {total_items:,} line items")


def main():
    print("\n🚀 Starting data seeding...")
    print(f"   Date range: {START_DATE} → {END_DATE}\n")

    with engine.begin() as conn:
        print("📍 Inserting reference data...")
        region_map   = insert_regions(conn)
        store_map    = insert_stores(conn, region_map)
        category_map = insert_categories(conn)
        product_map  = insert_products(conn, category_map)

        print("\n👤 Inserting customers...")
        customer_ids = insert_customers(conn, region_map, n=2000)

        print("\n🛒 Inserting orders & line items (this may take ~1-2 min)...")
        store_ids   = list(store_map.values())
        # product_ids as (id, price) tuples for realistic pricing
        product_rows = conn.execute(text("SELECT product_id, unit_price FROM products")).fetchall()
        insert_orders(conn, customer_ids, store_ids, product_rows)

    print("\n✅ Seeding complete! Your database is ready.")


if __name__ == "__main__":
    main()
