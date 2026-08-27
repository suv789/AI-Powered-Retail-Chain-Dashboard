"""
ai_assistant.py
Gemini powered AI assistant for the Retail Dashboard.
Supports two modes:
  1. Conversational — answers questions grounded in dashboard KPI context
  2. SQL generation — generates + runs a safe SELECT query, returns DataFrame
"""

import os
import re
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── Model name ───────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

# ── Configure Gemini ─────────────────────────────────────────
def _get_model(temperature=0.3, max_tokens=1024):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )


# ── Schema Summary ────────────────────────────────────────────
DB_SCHEMA_SUMMARY = """
DATABASE SCHEMA (Retail Chain — PostgreSQL):

Table: regions
  - region_id (int, PK)
  - region_name (varchar): North, South, East, West, Central
  - country (varchar)

Table: stores
  - store_id (int, PK)
  - store_name (varchar)
  - city (varchar)
  - region_id (int, FK → regions)
  - opened_date (date)
  - store_size (varchar): Small, Medium, Large

Table: categories
  - category_id (int, PK)
  - category_name (varchar): Electronics, Clothing, Groceries, Home & Kitchen,
    Sports & Fitness, Beauty & Personal Care, Books & Stationery, Toys & Games
  - department (varchar)

Table: products
  - product_id (int, PK)
  - sku (varchar)
  - product_name (varchar)
  - category_id (int, FK → categories)
  - unit_price (numeric)
  - cost_price (numeric)

Table: customers
  - customer_id (int, PK)
  - full_name (varchar)
  - email (varchar)
  - city (varchar)
  - region_id (int, FK → regions)
  - signup_date (date)
  - customer_segment (varchar): Bronze, Silver, Gold, Platinum

Table: orders
  - order_id (int, PK)
  - customer_id (int, FK → customers)
  - store_id (int, FK → stores)
  - order_date (date)
  - order_status (varchar): Completed, Returned, Cancelled
  - payment_method (varchar): UPI, Credit Card, Debit Card, Net Banking, Cash on Delivery

Table: order_items
  - item_id (int, PK)
  - order_id (int, FK → orders)
  - product_id (int, FK → products)
  - quantity (int)
  - unit_price (numeric)
  - discount_pct (numeric)
  - line_total (numeric, auto-computed = quantity * unit_price * (1 - discount_pct/100))
"""

BUSINESS_CONTEXT = """
BUSINESS CONTEXT:
- Retail chain across India: 14 stores in 5 regions
- 2,000 customers in 4 loyalty tiers: Bronze (40%), Silver (30%), Gold (20%), Platinum (10%)
- 40 SKUs across 8 categories
- 24 months of data with seasonal spikes Oct/Nov/Dec (festive season)
"""


# ── System prompt for conversational mode ────────────────────
def build_chat_system_prompt(dashboard_context: dict) -> str:
    ctx_str = json.dumps(dashboard_context, indent=2, default=str)
    return f"""You are an expert retail business analyst assistant embedded in a sales analytics dashboard.

{DB_SCHEMA_SUMMARY}
{BUSINESS_CONTEXT}

CURRENT DASHBOARD DATA (live snapshot):
{ctx_str}

YOUR ROLE:
1. Answer questions about the business data clearly and concisely.
2. Provide actionable business recommendations backed by the data.
3. Identify trends, anomalies, and opportunities from the numbers.
4. Always ground your answers in the provided data — do not invent figures.

RESPONSE STYLE:
- Conversational but precise. No unnecessary filler.
- Use bullet points for recommendations (3 max).
- Bold key numbers using **markdown**.
- Keep responses under 250 words unless asked for detail.
"""


# ── System prompt for SQL generation mode ────────────────────
# SQL_SYSTEM_PROMPT = f"""You are a PostgreSQL expert. Generate ONLY a complete, valid SELECT query.

# {DB_SCHEMA_SUMMARY}
# {BUSINESS_CONTEXT}

# REQUIREMENTS:
# 1. Output ONLY the SQL query — nothing else, no markdown, no backticks, no explanation.
# 2. Query MUST be complete and syntactically valid.
# 3. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER.
# 4. Always use ROUND(...::numeric, 2) for currency.
# 5. Always include WHERE o.order_status = 'Completed' for revenue queries.
# 6. Always end with semicolon and LIMIT 50.
# 7. Always JOIN properly — never use table aliases in WHERE without proper JOINs.
# 8. Complete all FROM/JOIN clauses before WHERE clause.

# Example (copy this structure):
# SELECT r.region_name, ROUND(SUM(oi.line_total)::numeric, 2) AS revenue, COUNT(DISTINCT o.order_id) AS orders
# FROM orders o
# JOIN stores s ON s.store_id = o.store_id
# JOIN regions r ON r.region_id = s.region_id
# JOIN order_items oi ON oi.order_id = o.order_id
# WHERE o.order_status = 'Completed'
#   AND o.order_date >= CURRENT_DATE - INTERVAL '6 months'
# GROUP BY r.region_name
# ORDER BY revenue DESC
# LIMIT 50;
# """
SQL_SYSTEM_PROMPT = """You are a PostgreSQL expert. Your job is to generate ONE complete, valid SELECT query.

IMPORTANT: 
- Output ONLY the SQL query, nothing else
- Do NOT truncate - output the COMPLETE query
- Do NOT use markdown or backticks
- Always end with semicolon
- Query must have all FROM and JOIN clauses

Example query structure:
SELECT columns FROM table JOIN table2 ON ... WHERE ... GROUP BY ... ORDER BY ... LIMIT 50;

Schema tables: regions, stores, categories, products, customers, orders, order_items

For revenue analysis:
- Always JOIN: orders → stores → regions, orders → order_items → products
- Filter: WHERE o.order_status = 'Completed'
- Use: ROUND(SUM(oi.line_total)::numeric, 2) for revenue

Generate the complete SQL query now:
"""

# ── Safety check ─────────────────────────────────────────────
def _is_safe_sql(sql: str) -> bool:
    """Block any non-SELECT or dangerous SQL."""
    cleaned = sql.strip().upper()
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
                 "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXEC"]
    if not cleaned.startswith("SELECT"):
        return False
    for word in dangerous:
        if re.search(rf'\b{word}\b', cleaned):
            return False
    return True


# ── Generate SQL from natural language ───────────────────────
# def generate_sql(user_question: str) -> str:
#     """Ask Gemini to convert a natural language question into a SQL query."""
#     try:
#         model = _get_model(temperature=0.1, max_tokens=800)
#         prompt = f"{SQL_SYSTEM_PROMPT}\n\nQuestion: {user_question}\n\nGenerate the complete SQL query:"
#         response = model.generate_content(prompt)
#         sql = response.text.strip()
#         # Strip any accidental markdown fences
#         sql = re.sub(r"```sql|```", "", sql).strip()
        
#         # Validate SQL is complete
#         if not sql.upper().startswith("SELECT"):
#             raise ValueError("Generated output is not a SELECT query")
#         if not sql.rstrip().endswith(";"):
#             sql = sql.rstrip() + ";"
#         if sql.count("(") != sql.count(")"):
#             raise ValueError("SQL has unmatched parentheses - query is incomplete")
        
#         return sql
#     except Exception as e:
#         raise RuntimeError(f"SQL generation failed: {e}")
def generate_sql(user_question: str) -> str:
    """Ask Gemini to convert a natural language question into a SQL query."""
    try:
        model = _get_model(temperature=0.1, max_tokens=1200)  # Increase to 1200
        prompt = f"{SQL_SYSTEM_PROMPT}\n\nQuestion: {user_question}\n\nComplete SQL query:"
        response = model.generate_content(prompt)
        sql = response.text.strip()
        
        # Strip markdown
        sql = re.sub(r"```sql|```", "", sql).strip()
        
        # Ensure it ends with semicolon
        if not sql.rstrip().endswith(";"):
            sql = sql.rstrip() + ";"
        
        # Basic validation
        if not sql.upper().startswith("SELECT"):
            raise ValueError("Not a SELECT query")
        
        return sql
    except Exception as e:
        raise RuntimeError(f"SQL generation failed: {e}")

# ── Run generated SQL safely ──────────────────────────────────
def run_generated_sql(sql: str) -> pd.DataFrame:
    """Validate and execute the generated SQL, return a DataFrame."""
    from app.database import run_query

    if not _is_safe_sql(sql):
        raise ValueError("Generated SQL failed safety check — only SELECT queries are allowed.")

    return run_query(sql)


# ── Conversational answer ─────────────────────────────────────
def ask_gemini(
    user_message: str,
    chat_history: list,
    dashboard_context: dict,
) -> str:
    try:
        model = _get_model(temperature=0.4, max_tokens=1024)

        system_turn = [
            {"role": "user",  "parts": [build_chat_system_prompt(dashboard_context)]},
            {"role": "model", "parts": [
                "Understood. I'm your retail analytics assistant with the current "
                "dashboard data loaded. What would you like to know?"
            ]},
        ]

        chat = model.start_chat(history=system_turn + chat_history)
        response = chat.send_message(user_message)
        return response.text

    except Exception as e:
        return f"⚠️ Gemini error (raw): {str(e)}"


# ── Auto-pick best chart type ─────────────────────────────────
def suggest_chart_type(df: pd.DataFrame) -> str:
    """Heuristic to pick the best Plotly chart for a given DataFrame."""
    cols = list(df.columns)
    num_cols  = df.select_dtypes(include="number").columns.tolist()
    cat_cols  = df.select_dtypes(exclude="number").columns.tolist()
    date_cols = [c for c in cols if "date" in c.lower() or "month" in c.lower()]

    if date_cols and num_cols:
        return "line"
    if len(cat_cols) == 1 and len(num_cols) == 1:
        return "bar"
    if len(cat_cols) == 1 and len(num_cols) >= 2:
        return "bar"
    if len(num_cols) >= 2 and len(cat_cols) == 0:
        return "scatter"
    return "bar"


# ── Starter questions ─────────────────────────────────────────
STARTER_QUESTIONS = [
    "Show me revenue by region",
    "Show me revenue by category",
    "Which customer segment should we focus on?",
    "Show top 10 products by revenue",
    "What are the top 3 actions to increase average order value?",
    "Show monthly revenue trend",
    "Which store has the highest revenue?",
    "Show revenue by payment method",
]

# Questions that should trigger SQL + chart (data questions)
def is_data_question(question: str) -> bool:
    """Detect if a question should trigger SQL generation + chart."""
    q = question.lower()
    
    # Data questions need specific data-related context
    data_keywords = ["show", "list", "compare", "breakdown", "trend", "monthly", "weekly", "ranking"]
    has_data_kw = any(kw in q for kw in data_keywords)
    
    # "Top/bottom/best/worst" only count if followed by data nouns
    if not has_data_kw:
        data_nouns = ["products", "product", "stores", "store", "regions", "region", "categories", "category", 
                      "revenue", "profit", "orders", "customers", "sales"]
        has_data_noun = any(noun in q for noun in data_nouns)
        if "top" in q or "bottom" in q or "best" in q or "worst" in q:
            return has_data_noun
        if "how many" in q or "how much" in q or "total" in q:
            return has_data_noun
        return False
    
    return True