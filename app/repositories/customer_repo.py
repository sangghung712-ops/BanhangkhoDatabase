from app.db import get_connection
from app.models import Customer


def get_by_user_id(user_id):
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM customers WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    finally:
        con.close()
    return Customer.from_row(row) if row else None
