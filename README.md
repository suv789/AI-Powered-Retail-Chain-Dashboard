# 🛒 Retail Chain Sales Analytics Dashboard

A full-stack data analytics dashboard for a retail chain business, built with **Python**, **PostgreSQL**, and **Streamlit**.

---

## 📁 Project Structure

```
retail_dashboard/
├── README.md
├── requirements.txt
├── .env.example              ← Copy to .env and fill in your DB credentials
├── db/
│   ├── schema.sql            ← Run first: creates all tables
│   └── seed_data.py          ← Run second: generates 24 months of synthetic data
└── app/
    ├── __init__.py
    ├── database.py           ← SQLAlchemy engine & query helper
    ├── queries.py            ← All SQL queries returning DataFrames
    └── dashboard.py          ← Streamlit app (main entry point)
```

---

## 🗄️ Database Schema

| Table         | Description                              |
|---------------|------------------------------------------|
| `regions`     | 5 geographic regions (North/South/East/West/Central) |
| `stores`      | 14 stores across regions with city & size |
| `categories`  | 8 product categories across departments  |
| `products`    | 40 SKUs with unit price & cost price     |
| `customers`   | 2,000 customers with segment (Bronze → Platinum) |
| `orders`      | ~14,000+ orders over 24 months with seasonal boosts |
| `order_items` | Line items with quantity, discount, auto-computed total |

---

## ⚡ Quick Start

### 1. Clone / download the project

```bash
cd retail_dashboard
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your database

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_dashboard
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 5. Create the database

In `psql` or pgAdmin:

```sql
CREATE DATABASE retail_dashboard;
```

### 6. Run the schema

```bash
psql -U postgres -d retail_dashboard -f db/schema.sql
```

Or paste `db/schema.sql` into pgAdmin's Query Tool.

### 7. Seed the data (24 months of synthetic data)

```bash
python -m db.seed_data
```

This inserts ~14,000+ orders with seasonal patterns. Takes about **1–2 minutes**.

### 8. Launch the dashboard

```bash
streamlit run app/dashboard.py
```

Open your browser at: **http://localhost:8501**

---

## 📊 Dashboard Features

| Section | Charts / Analysis |
|---|---|
| **KPI Cards** | Total Revenue, Orders, Unique Customers, Avg Order Value + growth % |
| **Revenue Trend** | Monthly revenue line + orders bar (dual-axis) |
| **Top Products** | Horizontal bar by revenue, color-coded by category |
| **Category Share** | Donut chart showing % revenue per category |
| **Regional Performance** | Revenue by region bar + Store scatter (orders vs revenue) |
| **Customer Segmentation** | Revenue by segment bar + Customers vs Avg Spend bubble chart |
| **RFM Table** | Top 20 customers by monetary value with frequency & recency |

### Sidebar Filters
- **Date range** — pick any start & end date within the 24-month window
- **Region** — filter all charts to a specific region

---

## 🧠 Synthetic Data Details

- **Seasonal multipliers** applied: Oct (1.4×), Nov (1.6×), Dec (1.8×), Jan (1.3×) to simulate festive seasons
- **Customer segments**: Bronze (40%), Silver (30%), Gold (20%), Platinum (10%)
- **Order status**: Completed (88%), Returned (7%), Cancelled (5%)
- **Payment methods**: UPI, Credit Card, Debit Card, Net Banking, Cash on Delivery
- **Products**: 40 SKUs across 8 categories with realistic Indian pricing

---

## 🔧 Customisation Tips

| Goal | Where to change |
|---|---|
| Add a new chart | `app/dashboard.py` |
| Add a new SQL query | `app/queries.py` |
| Change DB credentials | `.env` |
| Add more products/stores | `db/seed_data.py` → reference data dicts |
| Change date range | `db/seed_data.py` → `END_DATE` / `START_DATE` |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Database | PostgreSQL 14+ |
| ORM / DB driver | SQLAlchemy 2.0 + psycopg2 |
| Data manipulation | pandas |
| Web app | Streamlit |
| Charts | Plotly Express + Graph Objects |
| Fake data | Faker |

---

## 📌 Common Issues

**`psycopg2` install fails on Mac M1/M2:**
```bash
pip install psycopg2-binary
```

**`ModuleNotFoundError: No module named 'app'`:**
Make sure you run Streamlit from the project root:
```bash
# From retail_dashboard/ directory:
streamlit run app/dashboard.py
```

**`dateutil` not found:**
```bash
pip install python-dateutil
```
