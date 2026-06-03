"""
database.py — PostgreSQL connection for Paraguay Import Calculator v5.
Single container, direct DB access. No seguro fields.
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "paraguay_calc"),
    "user": os.environ.get("DB_USER", "paraguay"),
    "password": os.environ.get("DB_PASSWORD", "paraguay"),
}


def get_conn():
    """Return a new database connection."""
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def connection():
    """Context manager for database connections."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema. Safe to call multiple times."""
    schema = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema):
        return
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(open(schema).read())


def save_calculation(data: dict) -> int:
    """Save a complete calculation. Returns calculation ID."""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO calculations (session_name, language, status, user_id)
                   VALUES (%(name)s, %(lang)s, 'draft', %(uid)s) RETURNING id""",
                {"name": data.get("session_name", ""), "lang": data.get("language", "de"), "uid": data.get("user_id", "anonymous")},
            )
            calc_id = cur.fetchone()[0]

            # Save inputs (v5 — no seguro fields, no cif_usd)
            cur.execute(
                """INSERT INTO calc_inputs (calculation_id, currency_fob, exchange_rate_fob,
                   purchase_unit, currency_flete, exchange_rate_flete,
                   fob_currency, fob_gs, cif_currency, cif_gs,
                   total_importacion, total_nacional, gran_total, gran_total_per_unit)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    calc_id,
                    data.get("currency_fob", "USD"),
                    data.get("exchange_rate_fob", 7500.0),
                    data.get("purchase_unit", "kg"),
                    data.get("currency_flete", "USD"),
                    data.get("exchange_rate_flete", 7500.0),
                    data.get("fob_currency", 0.0),
                    data.get("fob_gs", 0.0),
                    data.get("cif_currency", 0.0),
                    data.get("cif_gs", 0.0),
                    data.get("total_importacion", 0.0),
                    data.get("total_nacional", 0.0),
                    data.get("gran_total", 0.0),
                    data.get("gran_total_per_unit", 0.0),
                ),
            )

            # Save line items
            for table, key in [
                ("proveedor_items", "proveedor"),
                ("flete_items", "flete"),
                ("importacion_items", "importacion"),
                ("costo_nacional_items", "costo_nacional"),
            ]:
                for i, item in enumerate(data.get(key, [])):
                    cur.execute(
                        f"""INSERT INTO {table} (calculation_id, sort_order, descripcion,
                           betrag, aufteilung, impuesto, cantidad, peso_volumen,
                           betrag_sin_iva, costo_gs, iva_gs)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            calc_id, i,
                            item.get("descripcion", ""), item.get("betrag", 0.0),
                            item.get("aufteilung", "wert"), item.get("impuesto", "Exento"),
                            item.get("cantidad", 1.0), item.get("peso_volumen", 0.0),
                            item.get("betrag_sin_iva", 0.0), item.get("costo_gs", 0.0),
                            item.get("iva_gs", 0.0),
                        ),
                    )
            return calc_id


def load_calculation(calc_id: int) -> dict | None:
    """Load a full calculation by ID."""
    with connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM calculations WHERE id = %s", (calc_id,))
            calc = cur.fetchone()
            if not calc:
                return None

            cur.execute("SELECT * FROM calc_inputs WHERE calculation_id = %s", (calc_id,))
            inp = cur.fetchone()

            result = dict(calc)
            result["inputs"] = dict(inp) if inp else {}

            for table, key in [
                ("proveedor_items", "proveedor"),
                ("flete_items", "flete"),
                ("importacion_items", "importacion"),
                ("costo_nacional_items", "costo_nacional"),
            ]:
                cur.execute(
                    f"SELECT * FROM {table} WHERE calculation_id = %s ORDER BY sort_order",
                    (calc_id,),
                )
                result[key] = [dict(r) for r in cur.fetchall()]

            return result


def list_calculations(status: str | None = None, limit: int = 50) -> list[dict]:
    """List recent calculations."""
    with connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if status:
                cur.execute(
                    "SELECT * FROM calculations WHERE status = %s ORDER BY updated_at DESC LIMIT %s",
                    (status, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM calculations ORDER BY updated_at DESC LIMIT %s",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]


def delete_calculation(calc_id: int) -> None:
    """Delete a calculation (cascades to all items)."""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM calculations WHERE id = %s", (calc_id,))


def update_status(calc_id: int, status: str) -> None:
    """Update calculation status."""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE calculations SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, calc_id),
            )
