"""
queries.py
All SQL queries for the dashboard, each returning a DataFrame.
Filters: start_date, end_date, region_id (optional), category_id (optional).
"""

from app.database import run_query


# ── KPI Cards ────────────────────────────────────────────────

def get_kpi_summary(start_date, end_date, region_id=None, category_id=None):
    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            COUNT(DISTINCT o.order_id)                          AS total_orders,
            COUNT(DISTINCT o.customer_id)                       AS unique_customers,
            ROUND(SUM(oi.line_total)::numeric, 2)               AS total_revenue,
            ROUND(AVG(order_totals.order_revenue)::numeric, 2)  AS avg_order_value
        FROM orders o
        JOIN stores s ON o.store_id = s.store_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN (
            SELECT order_id, SUM(line_total) AS order_revenue
            FROM order_items GROUP BY order_id
        ) order_totals ON order_totals.order_id = o.order_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {region_filter}
          {category_filter}
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


def get_revenue_growth(start_date, end_date, region_id=None, category_id=None):
    """Compare current period vs same-length prior period."""
    from datetime import timedelta
    delta = (end_date - start_date).days
    prior_start = start_date - timedelta(days=delta + 1)
    prior_end   = start_date - timedelta(days=1)

    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""

    sql = f"""
        SELECT
            SUM(CASE WHEN o.order_date BETWEEN :start_date AND :end_date
                     THEN oi.line_total ELSE 0 END)       AS current_revenue,
            SUM(CASE WHEN o.order_date BETWEEN :prior_start AND :prior_end
                     THEN oi.line_total ELSE 0 END)       AS prior_revenue
        FROM orders o
        JOIN stores s ON o.store_id = s.store_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :prior_start AND :end_date
          {region_filter}
          {category_filter}
    """
    params = {
        "start_date": start_date, "end_date": end_date,
        "prior_start": prior_start, "prior_end": prior_end,
    }
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


# ── Revenue Trend ────────────────────────────────────────────

def get_monthly_revenue(start_date, end_date, region_id=None, category_id=None):
    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            DATE_TRUNC('month', o.order_date)::date  AS month,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue,
            COUNT(DISTINCT o.order_id)               AS orders
        FROM orders o
        JOIN stores s ON o.store_id = s.store_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {region_filter}
          {category_filter}
        GROUP BY 1
        ORDER BY 1
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


# ── Top Products / Categories ────────────────────────────────

def get_top_products(start_date, end_date, region_id=None, category_id=None, limit=10):
    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            p.product_name,
            cat.category_name,
            SUM(oi.quantity)                         AS units_sold,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue
        FROM order_items oi
        JOIN orders o    ON o.order_id   = oi.order_id
        JOIN stores s    ON s.store_id   = o.store_id
        JOIN products p  ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {region_filter}
          {category_filter}
        GROUP BY 1, 2
        ORDER BY revenue DESC
        LIMIT :limit
    """
    params = {"start_date": start_date, "end_date": end_date, "limit": limit}
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


def get_category_revenue(start_date, end_date, region_id=None, category_id=None):
    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            cat.category_name,
            cat.department,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue,
            SUM(oi.quantity)                         AS units_sold
        FROM order_items oi
        JOIN orders o       ON o.order_id    = oi.order_id
        JOIN stores s       ON s.store_id    = o.store_id
        JOIN products p     ON p.product_id  = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {region_filter}
          {category_filter}
        GROUP BY 1, 2
        ORDER BY revenue DESC
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


# ── Regional Performance ─────────────────────────────────────

def get_regional_performance(start_date, end_date, category_id=None):
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            r.region_name,
            COUNT(DISTINCT o.order_id)               AS total_orders,
            COUNT(DISTINCT o.customer_id)            AS unique_customers,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue
        FROM orders o
        JOIN stores s       ON s.store_id   = o.store_id
        JOIN regions r      ON r.region_id  = s.region_id
        JOIN order_items oi ON oi.order_id  = o.order_id
        JOIN products p     ON p.product_id = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {category_filter}
        GROUP BY 1
        ORDER BY revenue DESC
    """
    params = {"start_date": start_date, "end_date": end_date}
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


def get_store_performance(start_date, end_date, region_id=None, category_id=None):
    region_filter = "AND s.region_id = :region_id" if region_id else ""
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            s.store_name,
            r.region_name,
            s.city,
            s.store_size,
            COUNT(DISTINCT o.order_id)               AS total_orders,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue
        FROM orders o
        JOIN stores s       ON s.store_id  = o.store_id
        JOIN regions r      ON r.region_id = s.region_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p     ON p.product_id = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {region_filter}
          {category_filter}
        GROUP BY 1, 2, 3, 4
        ORDER BY revenue DESC
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_id:
        params["region_id"] = region_id
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


# ── Customer Segmentation (RFM) ──────────────────────────────

def get_customer_segment_summary(start_date, end_date, category_id=None):
    subquery_category_filter = "AND p2.category_id = :category_id" if category_id else ""
    outer_category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            c.customer_segment,
            COUNT(DISTINCT c.customer_id)            AS num_customers,
            COUNT(DISTINCT o.order_id)               AS total_orders,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS total_revenue,
            ROUND(AVG(cust_totals.cust_spend)::numeric, 2) AS avg_spend_per_customer
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN (
            SELECT o2.customer_id, SUM(oi2.line_total) AS cust_spend
            FROM orders o2
            JOIN order_items oi2 ON oi2.order_id = o2.order_id
            JOIN products p2 ON p2.product_id = oi2.product_id
            WHERE o2.order_status = 'Completed'
              AND o2.order_date BETWEEN :start_date AND :end_date
              {subquery_category_filter}
            GROUP BY o2.customer_id
        ) cust_totals ON cust_totals.customer_id = c.customer_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {outer_category_filter}
        GROUP BY 1
        ORDER BY total_revenue DESC
    """
    params = {"start_date": start_date, "end_date": end_date}
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


def get_rfm_data(start_date, end_date, category_id=None):
    category_filter = "AND p.category_id = :category_id" if category_id else ""
    sql = f"""
        SELECT
            c.customer_id,
            c.full_name,
            c.customer_segment,
            MAX(o.order_date)                          AS last_order_date,
            COUNT(DISTINCT o.order_id)                 AS frequency,
            ROUND(SUM(oi.line_total)::numeric, 2)      AS monetary
        FROM customers c
        JOIN orders o       ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id   = o.order_id
        JOIN products p     ON p.product_id  = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          {category_filter}
        GROUP BY 1, 2, 3
        ORDER BY monetary DESC
        LIMIT 500
    """
    params = {"start_date": start_date, "end_date": end_date}
    if category_id:
        params["category_id"] = category_id
    return run_query(sql, params)


# ── Filters ──────────────────────────────────────────────────

def get_regions():
    return run_query("SELECT region_id, region_name FROM regions ORDER BY region_name")


def get_categories():
    return run_query("SELECT category_id, category_name FROM categories ORDER BY category_name")