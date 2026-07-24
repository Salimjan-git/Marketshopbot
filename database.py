import sqlite3
from pathlib import Path
from typing import Any

from config import DB_NAME


# =========================================================
# SQLITE CONNECTION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / DB_NAME


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _column_exists(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row["name"] == column_name for row in cursor.fetchall())


def _add_column_if_missing(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    if not _column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {definition}"
        )



def _drop_column_if_exists(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
) -> None:
    """Сутуни нолозимро аз базаи мавҷуда нест мекунад."""
    if _column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
        )


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables() -> None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                username TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                logo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(category_id, name),

                FOREIGN KEY(category_id)
                    REFERENCES categories(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(brand_id, name),

                FOREIGN KEY(brand_id)
                    REFERENCES brands(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                brand_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,

                condition TEXT NOT NULL DEFAULT 'new'
                    CHECK(condition IN ('new', 'used')),

                ram TEXT,
                storage TEXT,
                color TEXT,

                has_imei INTEGER NOT NULL DEFAULT 0
                    CHECK(has_imei IN (0, 1)),

                price REAL NOT NULL CHECK(price >= 0),
                discount REAL DEFAULT 0 CHECK(discount >= 0),

                city TEXT,
                warranty TEXT,
                battery_health TEXT,
                sim_type TEXT,

                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(category_id)
                    REFERENCES categories(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(brand_id)
                    REFERENCES brands(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(model_id)
                    REFERENCES models(id)
                    ON DELETE CASCADE
            )
        """)

        # Мигратсияи сабук барои базаи мавҷуда.
        _add_column_if_missing(
            cursor,
            "products",
            "has_imei",
            "INTEGER NOT NULL DEFAULT 0",
        )

        # stock дигар истифода намешавад.
        _drop_column_if_exists(
            cursor,
            "products",
            "stock",
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                telegram_file_id TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1 CHECK(quantity > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, product_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_price REAL NOT NULL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                address TEXT NOT NULL,
                phone TEXT NOT NULL,

                payment_method TEXT NOT NULL DEFAULT 'cash'
                    CHECK(payment_method IN ('cash', 'online')),
                payment_status TEXT NOT NULL DEFAULT 'unpaid',
                payment_bank_id INTEGER,
                payment_method_id INTEGER,
                receipt_file_id TEXT,
                paid_at TIMESTAMP,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(payment_bank_id)
                    REFERENCES payment_banks(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(payment_method_id)
                    REFERENCES payment_methods(id)
                    ON DELETE SET NULL
            )
        """)

        # Сутунҳои пардохтро ба базаи кӯҳна илова мекунад.
        _add_column_if_missing(
            cursor,
            "orders",
            "payment_method",
            "TEXT DEFAULT 'cash'",
        )
        _add_column_if_missing(
            cursor,
            "orders",
            "payment_status",
            "TEXT DEFAULT 'unpaid'",
        )
        _add_column_if_missing(
            cursor,
            "orders",
            "receipt_file_id",
            "TEXT",
        )
        _add_column_if_missing(
            cursor,
            "orders",
            "paid_at",
            "TIMESTAMP",
        )
        _add_column_if_missing(
            cursor,
            "orders",
            "payment_bank_id",
            "INTEGER",
        )
        _add_column_if_missing(
            cursor,
            "orders",
            "payment_method_id",
            "INTEGER",
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price REAL NOT NULL CHECK(price >= 0),

                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                card_holder TEXT,
                logo_file_id TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id INTEGER NOT NULL,
                method_type TEXT NOT NULL
                    CHECK(method_type IN ('card', 'phone', 'qr')),
                title TEXT NOT NULL,
                value TEXT,
                qr_file_id TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(bank_id)
                    REFERENCES payment_banks(id)
                    ON DELETE CASCADE,

                CHECK(
                    (method_type = 'qr' AND qr_file_id IS NOT NULL)
                    OR
                    (method_type IN ('card', 'phone') AND value IS NOT NULL)
                )
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_brands_category
            ON brands(category_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_models_brand
            ON models(brand_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_category
            ON products(category_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_brand
            ON products(brand_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_model
            ON products(model_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_images_product
            ON product_images(product_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cart_user
            ON cart(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_user
            ON orders(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_payment_status
            ON orders(payment_status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_methods_bank
            ON payment_methods(bank_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_banks_active
            ON payment_banks(is_active)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_methods_active
            ON payment_methods(is_active)
        """)

        conn.commit()
        print(f"✅ SQLite database initialized: {DATABASE_PATH}")

    finally:
        conn.close()


# =========================================================
# USERS
# =========================================================

def get_or_create_user(
    telegram_id: int,
    full_name: str,
    username: str | None = None,
    phone: str | None = None,
) -> dict[str, Any]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        user = cursor.fetchone()

        if user:
            cursor.execute(
                """
                UPDATE users
                SET full_name = ?, username = ?
                WHERE telegram_id = ?
                """,
                (full_name, username, telegram_id),
            )
            conn.commit()

            cursor.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            return dict(cursor.fetchone())

        cursor.execute(
            """
            INSERT INTO users (
                telegram_id,
                full_name,
                username,
                phone
            )
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, full_name, username, phone),
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        created_user = cursor.fetchone()

        if not created_user:
            raise RuntimeError("Корбар сохта нашуд")

        return dict(created_user)

    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_user_by_telegram_id(
    telegram_id: int,
) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_all_users() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_user_phone(user_id: int, phone: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET phone = ? WHERE id = ?",
            (phone, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# CATEGORIES
# =========================================================

def add_category(name: str, image: str | None = None) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, image) VALUES (?, ?)",
            (name.strip(), image),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_categories() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_category(category_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM categories WHERE id = ?",
            (category_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_category(
    category_id: int,
    name: str,
    image: str | None = None,
) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE categories
            SET name = ?, image = ?
            WHERE id = ?
            """,
            (name.strip(), image, category_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_category(category_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM categories WHERE id = ?",
            (category_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def is_phone_category(category_id: int) -> bool:
    category = get_category(category_id)

    if not category:
        return False

    name = str(category["name"]).lower()

    return any(
        word in name
        for word in (
            "телефон",
            "смартфон",
            "phone",
            "iphone",
            "мобил",
        )
    )


# =========================================================
# BRANDS
# =========================================================

def add_brand(
    category_id: int,
    name: str,
    logo: str | None = None,
) -> int:
    name = name.strip()

    if len(name) < 2:
        raise ValueError("Номи бренд хеле кӯтоҳ аст")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO brands (category_id, name, logo)
            VALUES (?, ?, ?)
            """,
            (category_id, name, logo),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_brands() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.*,
                c.name AS category_name
            FROM brands AS b
            INNER JOIN categories AS c
                ON c.id = b.category_id
            ORDER BY c.name, b.name
            """
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_brands_by_category(
    category_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.*,
                c.name AS category_name
            FROM brands AS b
            INNER JOIN categories AS c
                ON c.id = b.category_id
            WHERE b.category_id = ?
            ORDER BY b.name
            """,
            (category_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_brand(brand_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.*,
                c.name AS category_name
            FROM brands AS b
            INNER JOIN categories AS c
                ON c.id = b.category_id
            WHERE b.id = ?
            """,
            (brand_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_brand(
    brand_id: int,
    category_id: int,
    name: str,
    logo: str | None = None,
) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE brands
            SET category_id = ?, name = ?, logo = ?
            WHERE id = ?
            """,
            (category_id, name.strip(), logo, brand_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_brand(brand_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# MODELS
# =========================================================

def add_model(brand_id: int, name: str) -> int:
    name = name.strip()

    if len(name) < 2:
        raise ValueError("Номи модел хеле кӯтоҳ аст")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO models (brand_id, name) VALUES (?, ?)",
            (brand_id, name),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_models_by_brand(
    brand_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                m.*,
                b.name AS brand_name
            FROM models AS m
            INNER JOIN brands AS b
                ON b.id = m.brand_id
            WHERE m.brand_id = ?
            ORDER BY m.name
            """,
            (brand_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_models_by_category_and_brand(
    category_id: int,
    brand_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                m.*,
                b.name AS brand_name
            FROM models AS m
            INNER JOIN brands AS b
                ON b.id = m.brand_id
            INNER JOIN products AS p
                ON p.model_id = m.id
            WHERE p.category_id = ?
              AND p.brand_id = ?
              AND p.is_active = 1
            ORDER BY m.name
            """,
            (category_id, brand_id),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_model(model_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                m.*,
                b.name AS brand_name
            FROM models AS m
            INNER JOIN brands AS b
                ON b.id = m.brand_id
            WHERE m.id = ?
            """,
            (model_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_model(model_id: int, brand_id: int, name: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE models
            SET brand_id = ?, name = ?
            WHERE id = ?
            """,
            (brand_id, name.strip(), model_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_model(model_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# PRODUCTS
# =========================================================

def add_product(
    category_id: int,
    brand_id: int,
    model_id: int,
    title: str,
    price: float,
    description: str | None = None,
    condition: str = "new",
    ram: str | None = None,
    storage: str | None = None,
    color: str | None = None,
    has_imei: bool = False,
    warranty: str | None = None,
    stock: int | None = None,  # Барои мутобиқат; истифода намешавад.
    image: str | None = None,
    name: str | None = None,
    discount: float = 0,
    city: str | None = None,
    battery_health: str | None = None,
    sim_type: str | None = None,
) -> int:
    if not title and name:
        title = name

    if not title or not title.strip():
        raise ValueError("Номи маҳсулот холӣ аст")

    if price <= 0:
        raise ValueError("Нарх бояд аз 0 зиёд бошад")

    if condition not in {"new", "used"}:
        raise ValueError("Ҳолат бояд new ё used бошад")

    phone_category = is_phone_category(category_id)

    if not phone_category:
        condition = "new"
        ram = None
        storage = None
        color = None
        has_imei = False
        warranty = None

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                b.category_id AS brand_category_id,
                m.brand_id AS model_brand_id
            FROM brands AS b
            INNER JOIN models AS m
                ON m.id = ?
            WHERE b.id = ?
            """,
            (model_id, brand_id),
        )
        relation = cursor.fetchone()

        if not relation:
            raise ValueError("Бренд ё модел ёфт нашуд")

        if int(relation["brand_category_id"]) != int(category_id):
            raise ValueError(
                "Бренд ба категорияи интихобшуда тааллуқ надорад"
            )

        if int(relation["model_brand_id"]) != int(brand_id):
            raise ValueError(
                "Модел ба бренди интихобшуда тааллуқ надорад"
            )

        cursor.execute(
            """
            INSERT INTO products (
                category_id,
                brand_id,
                model_id,
                title,
                description,
                condition,
                ram,
                storage,
                color,
                has_imei,
                price,
                discount,
                city,
                warranty,
                battery_health,
                sim_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category_id,
                brand_id,
                model_id,
                title.strip(),
                description,
                condition,
                ram,
                storage,
                color,
                1 if has_imei else 0,
                float(price),
                float(discount),
                city,
                warranty,
                battery_health,
                sim_type,
            ),
        )

        product_id = int(cursor.lastrowid)

        if image:
            cursor.execute(
                """
                INSERT INTO product_images (
                    product_id,
                    telegram_file_id,
                    position
                )
                VALUES (?, ?, 1)
                """,
                (product_id, image),
            )

        conn.commit()
        return product_id

    finally:
        conn.close()


def _product_select_sql() -> str:
    return """
        SELECT
            p.*,
            p.title AS name,
            c.name AS category_name,
            b.name AS brand_name,
            m.name AS model_name,

            (
                SELECT pi.telegram_file_id
                FROM product_images AS pi
                WHERE pi.product_id = p.id
                ORDER BY pi.position
                LIMIT 1
            ) AS image,

            (
                SELECT pi.telegram_file_id
                FROM product_images AS pi
                WHERE pi.product_id = p.id
                ORDER BY pi.position
                LIMIT 1
            ) AS main_image

        FROM products AS p
        INNER JOIN categories AS c
            ON c.id = p.category_id
        INNER JOIN brands AS b
            ON b.id = p.brand_id
        INNER JOIN models AS m
            ON m.id = p.model_id
    """


def get_products() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.is_active = 1
            ORDER BY p.created_at DESC
            """
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_product(product_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + " WHERE p.id = ?",
            (product_id,),
        )

        product = cursor.fetchone()

        if not product:
            return None

        product_data = dict(product)

        cursor.execute(
            """
            SELECT *
            FROM product_images
            WHERE product_id = ?
            ORDER BY position
            """,
            (product_id,),
        )
        product_data["images"] = rows_to_dicts(cursor.fetchall())
        return product_data
    finally:
        conn.close()


def get_products_by_category(
    category_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.category_id = ?
              AND p.is_active = 1
            ORDER BY p.title
            """,
            (category_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_products_by_brand(
    brand_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.brand_id = ?
              AND p.is_active = 1
            ORDER BY p.title
            """,
            (brand_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_products_by_category_and_brand(
    category_id: int,
    brand_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.category_id = ?
              AND p.brand_id = ?
              AND p.is_active = 1
            ORDER BY p.title
            """,
            (category_id, brand_id),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_products_by_model(
    model_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.model_id = ?
              AND p.is_active = 1
            ORDER BY p.price
            """,
            (model_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def search_products(query: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        value = f"%{query.strip()}%"

        cursor.execute(
            _product_select_sql()
            + """
            WHERE p.is_active = 1
              AND (
                  p.title LIKE ?
                  OR p.description LIKE ?
                  OR b.name LIKE ?
                  OR m.name LIKE ?
                  OR c.name LIKE ?
                  OR p.storage LIKE ?
                  OR p.color LIKE ?
              )
            ORDER BY p.title
            """,
            (value, value, value, value, value, value, value),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_product(
    product_id: int,
    category_id: int,
    brand_id: int,
    model_id: int,
    title: str,
    price: float,
    description: str | None = None,
    condition: str = "new",
    ram: str | None = None,
    storage: str | None = None,
    color: str | None = None,
    has_imei: bool = False,
    warranty: str | None = None,
    stock: int | None = None,  # Барои мутобиқат; истифода намешавад.
    discount: float = 0,
    city: str | None = None,
    battery_health: str | None = None,
    sim_type: str | None = None,
    image: str | None = None,
) -> bool:
    if not title or not title.strip():
        return False

    if price <= 0:
        return False

    if condition not in {"new", "used"}:
        return False

    phone_category = is_phone_category(category_id)

    if not phone_category:
        condition = "new"
        ram = None
        storage = None
        color = None
        has_imei = False
        warranty = None

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE products
            SET category_id = ?,
                brand_id = ?,
                model_id = ?,
                title = ?,
                description = ?,
                condition = ?,
                ram = ?,
                storage = ?,
                color = ?,
                has_imei = ?,
                warranty = ?,
                price = ?,
                discount = ?,
                city = ?,
                battery_health = ?,
                sim_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                category_id,
                brand_id,
                model_id,
                title.strip(),
                description,
                condition,
                ram,
                storage,
                color,
                1 if has_imei else 0,
                warranty,
                float(price),
                float(discount),
                city,
                battery_health,
                sim_type,
                product_id,
            ),
        )

        updated = cursor.rowcount > 0

        if image:
            cursor.execute(
                """
                INSERT INTO product_images (
                    product_id,
                    telegram_file_id,
                    position
                )
                VALUES (
                    ?,
                    ?,
                    COALESCE(
                        (
                            SELECT MAX(position) + 1
                            FROM product_images
                            WHERE product_id = ?
                        ),
                        1
                    )
                )
                """,
                (product_id, image, product_id),
            )

        conn.commit()
        return updated
    finally:
        conn.close()


def update_product_stock(product_id: int, stock: int) -> bool:
    """Функсияи кӯҳна барои мутобиқат; stock дигар нигоҳ дошта намешавад."""
    return get_product(product_id) is not None

def delete_product(product_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# PRODUCT IMAGES
# =========================================================

def add_product_image(
    product_id: int,
    telegram_file_id: str,
    position: int = 1,
) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO product_images (
                product_id,
                telegram_file_id,
                position
            )
            VALUES (?, ?, ?)
            """,
            (product_id, telegram_file_id, position),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_product_images(
    product_id: int,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM product_images
            WHERE product_id = ?
            ORDER BY position
            """,
            (product_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def delete_product_images(product_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM product_images WHERE product_id = ?",
            (product_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# =========================================================
# CART
# =========================================================

def add_to_cart(
    user_id: int,
    product_id: int,
    quantity: int = 1,
) -> bool:
    if quantity <= 0:
        return False

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
              AND is_active = 1
            """,
            (product_id,),
        )

        if not cursor.fetchone():
            return False

        cursor.execute(
            """
            SELECT id, quantity
            FROM cart
            WHERE user_id = ?
              AND product_id = ?
            """,
            (user_id, product_id),
        )
        cart_item = cursor.fetchone()

        if cart_item:
            new_quantity = int(cart_item["quantity"]) + quantity
            cursor.execute(
                "UPDATE cart SET quantity = ? WHERE id = ?",
                (new_quantity, cart_item["id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                """,
                (user_id, product_id, quantity),
            )

        conn.commit()
        return True
    finally:
        conn.close()

def get_cart(user_id: int) -> list[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                c.id AS cart_id,
                c.user_id,
                c.product_id,
                c.quantity,
                p.title,
                p.title AS name,
                p.price,
                p.discount,

                (
                    SELECT pi.telegram_file_id
                    FROM product_images AS pi
                    WHERE pi.product_id = p.id
                    ORDER BY pi.position
                    LIMIT 1
                ) AS image,

                CASE
                    WHEN p.price - p.discount < 0 THEN 0
                    ELSE p.price - p.discount
                END AS final_price,

                CASE
                    WHEN p.price - p.discount < 0 THEN 0
                    ELSE (p.price - p.discount) * c.quantity
                END AS total

            FROM cart AS c
            INNER JOIN products AS p
                ON p.id = c.product_id

            WHERE c.user_id = ?
              AND p.is_active = 1

            ORDER BY c.created_at DESC
            """,
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_cart_quantity(
    user_id: int,
    product_id: int,
    quantity: int,
) -> bool:
    if quantity <= 0:
        return remove_from_cart(user_id, product_id)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE cart
            SET quantity = ?
            WHERE user_id = ?
              AND product_id = ?
            """,
            (quantity, user_id, product_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def remove_from_cart(user_id: int, product_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM cart
            WHERE user_id = ?
              AND product_id = ?
            """,
            (user_id, product_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def clear_cart(user_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_cart_total(user_id: int) -> float:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    CASE
                        WHEN p.price - p.discount < 0 THEN 0
                        ELSE (p.price - p.discount) * c.quantity
                    END
                ),
                0
            ) AS total
            FROM cart AS c
            INNER JOIN products AS p
                ON p.id = c.product_id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return float(result["total"] or 0)
    finally:
        conn.close()


# =========================================================
# ORDERS
# =========================================================

def create_order(
    user_id: int,
    address: str = "",
    phone: str = "",
    payment_method: str = "cash",
    payment_bank_id: int | None = None,
    payment_method_id: int | None = None,
) -> int | None:
    allowed_methods = {"cash", "online"}

    if payment_method not in allowed_methods:
        return None

    if payment_method == "cash":
        payment_bank_id = None
        payment_method_id = None

    if payment_method == "online":
        if payment_bank_id is None or payment_method_id is None:
            return None

    conn = get_connection()

    try:
        cursor = conn.cursor()

        if payment_method == "online":
            cursor.execute(
                """
                SELECT pm.id
                FROM payment_methods AS pm
                INNER JOIN payment_banks AS pb
                    ON pb.id = pm.bank_id
                WHERE pm.id = ?
                  AND pm.bank_id = ?
                  AND pm.is_active = 1
                  AND pb.is_active = 1
                """,
                (payment_method_id, payment_bank_id),
            )

            if not cursor.fetchone():
                return None

        cursor.execute(
            """
            SELECT
                c.product_id,
                c.quantity,
                p.title,
                p.price,
                p.discount,
                CASE
                    WHEN p.price - p.discount < 0 THEN 0
                    ELSE p.price - p.discount
                END AS final_price
            FROM cart AS c
            INNER JOIN products AS p
                ON p.id = c.product_id
            WHERE c.user_id = ?
              AND p.is_active = 1
            """,
            (user_id,),
        )

        cart_items = cursor.fetchall()

        if not cart_items:
            return None

        total_price = sum(
            float(item["final_price"]) * int(item["quantity"])
            for item in cart_items
        )

        payment_status = (
            "pending_receipt"
            if payment_method == "online"
            else "unpaid"
        )

        cursor.execute(
            """
            INSERT INTO orders (
                user_id,
                total_price,
                address,
                phone,
                status,
                payment_method,
                payment_status,
                payment_bank_id,
                payment_method_id
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (
                user_id,
                total_price,
                address.strip(),
                phone.strip(),
                payment_method,
                payment_status,
                payment_bank_id,
                payment_method_id,
            ),
        )

        order_id = int(cursor.lastrowid)

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    quantity,
                    price
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["title"],
                    item["quantity"],
                    float(item["final_price"]),
                ),
            )

        cursor.execute(
            "DELETE FROM cart WHERE user_id = ?",
            (user_id,),
        )

        conn.commit()
        return order_id

    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_orders(user_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_order_details(order_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                o.*,
                u.full_name,
                u.telegram_id,
                u.username,
                pb.name AS payment_bank_name,
                pb.card_holder AS payment_card_holder,
                pm.method_type AS payment_method_type,
                pm.title AS payment_method_title,
                pm.value AS payment_method_value,
                pm.qr_file_id AS payment_qr_file_id
            FROM orders AS o
            LEFT JOIN users AS u
                ON u.id = o.user_id
            LEFT JOIN payment_banks AS pb
                ON pb.id = o.payment_bank_id
            LEFT JOIN payment_methods AS pm
                ON pm.id = o.payment_method_id
            WHERE o.id = ?
            """,
            (order_id,),
        )

        order = cursor.fetchone()

        if not order:
            return None

        order_data = dict(order)

        cursor.execute(
            """
            SELECT
                oi.*,
                (
                    SELECT pi.telegram_file_id
                    FROM product_images AS pi
                    WHERE pi.product_id = oi.product_id
                    ORDER BY pi.position
                    LIMIT 1
                ) AS image
            FROM order_items AS oi
            WHERE oi.order_id = ?
            ORDER BY oi.id
            """,
            (order_id,),
        )

        order_data["items"] = rows_to_dicts(cursor.fetchall())
        return order_data
    finally:
        conn.close()


def get_all_orders() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                o.*,
                u.full_name,
                u.telegram_id,
                u.username,
                pb.name AS payment_bank_name,
                pm.method_type AS payment_method_type,
                pm.title AS payment_method_title
            FROM orders AS o
            LEFT JOIN users AS u
                ON u.id = o.user_id
            LEFT JOIN payment_banks AS pb
                ON pb.id = o.payment_bank_id
            LEFT JOIN payment_methods AS pm
                ON pm.id = o.payment_method_id
            ORDER BY o.created_at DESC
            """
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_order_status(order_id: int, status: str) -> bool:
    allowed_statuses = {
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
    }

    if status not in allowed_statuses:
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def save_order_receipt(
    order_id: int,
    receipt_file_id: str,
) -> bool:
    if not receipt_file_id:
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE orders
            SET receipt_file_id = ?,
                payment_status = 'receipt_sent'
            WHERE id = ?
              AND payment_method = 'online'
            """,
            (receipt_file_id, order_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_payment_status(
    order_id: int,
    payment_status: str,
) -> bool:
    allowed_statuses = {
        "unpaid",
        "pending_receipt",
        "receipt_sent",
        "confirmed",
        "rejected",
    }

    if payment_status not in allowed_statuses:
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()

        if payment_status == "confirmed":
            cursor.execute(
                """
                UPDATE orders
                SET payment_status = ?,
                    paid_at = CURRENT_TIMESTAMP,
                    status = CASE
                        WHEN status = 'pending' THEN 'processing'
                        ELSE status
                    END
                WHERE id = ?
                """,
                (payment_status, order_id),
            )
        else:
            cursor.execute(
                """
                UPDATE orders
                SET payment_status = ?,
                    paid_at = NULL
                WHERE id = ?
                """,
                (payment_status, order_id),
            )

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_orders_waiting_payment_review() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                o.*,
                u.full_name,
                u.telegram_id,
                u.username,
                pb.name AS payment_bank_name,
                pm.method_type AS payment_method_type,
                pm.title AS payment_method_title
            FROM orders AS o
            LEFT JOIN users AS u
                ON u.id = o.user_id
            LEFT JOIN payment_banks AS pb
                ON pb.id = o.payment_bank_id
            LEFT JOIN payment_methods AS pm
                ON pm.id = o.payment_method_id
            WHERE o.payment_method = 'online'
              AND o.payment_status = 'receipt_sent'
            ORDER BY o.created_at ASC
            """
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def cancel_order(order_id: int, user_id: int | None = None) -> bool:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        if user_id is None:
            cursor.execute(
                """
                SELECT status
                FROM orders
                WHERE id = ?
                """,
                (order_id,),
            )
        else:
            cursor.execute(
                """
                SELECT status
                FROM orders
                WHERE id = ?
                  AND user_id = ?
                """,
                (order_id, user_id),
            )

        order = cursor.fetchone()

        if not order or order["status"] not in {"pending", "confirmed"}:
            return False

        if user_id is None:
            cursor.execute(
                """
                UPDATE orders
                SET status = 'cancelled'
                WHERE id = ?
                """,
                (order_id,),
            )
        else:
            cursor.execute(
                """
                UPDATE orders
                SET status = 'cancelled'
                WHERE id = ?
                  AND user_id = ?
                """,
                (order_id, user_id),
            )

        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# =========================================================
# PAYMENT BANKS
# =========================================================

def add_payment_bank(
    name: str,
    card_holder: str | None = None,
    logo_file_id: str | None = None,
    is_active: bool = True,
) -> int:
    name = name.strip()
    card_holder = card_holder.strip() if card_holder else None

    if len(name) < 2:
        raise ValueError("Номи бонк хеле кӯтоҳ аст")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payment_banks (
                name,
                card_holder,
                logo_file_id,
                is_active
            )
            VALUES (?, ?, ?, ?)
            """,
            (name, card_holder, logo_file_id, 1 if is_active else 0),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_payment_banks(active_only: bool = False) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            SELECT
                pb.*,
                (
                    SELECT COUNT(*)
                    FROM payment_methods AS pm
                    WHERE pm.bank_id = pb.id
                ) AS methods_count
            FROM payment_banks AS pb
        """
        if active_only:
            sql += " WHERE pb.is_active = 1"
        sql += " ORDER BY pb.name"
        cursor.execute(sql)
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_payment_bank(bank_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                pb.*,
                (
                    SELECT COUNT(*)
                    FROM payment_methods AS pm
                    WHERE pm.bank_id = pb.id
                ) AS methods_count
            FROM payment_banks AS pb
            WHERE pb.id = ?
            """,
            (bank_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_payment_bank(
    bank_id: int,
    name: str | None = None,
    card_holder: str | None = None,
    logo_file_id: str | None = None,
    is_active: bool | None = None,
) -> bool:
    bank = get_payment_bank(bank_id)
    if not bank:
        return False

    new_name = bank["name"] if name is None else name.strip()
    if len(new_name) < 2:
        return False

    new_holder = (
        bank.get("card_holder")
        if card_holder is None
        else card_holder.strip() or None
    )
    new_logo = (
        bank.get("logo_file_id")
        if logo_file_id is None
        else logo_file_id or None
    )
    new_active = (
        int(bank["is_active"])
        if is_active is None
        else (1 if is_active else 0)
    )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payment_banks
            SET name = ?,
                card_holder = ?,
                logo_file_id = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_name, new_holder, new_logo, new_active, bank_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_payment_bank(bank_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM payment_banks WHERE id = ?",
            (bank_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_payment_bank_active(bank_id: int, is_active: bool) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payment_banks
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if is_active else 0, bank_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =========================================================
# PAYMENT METHODS
# =========================================================

def add_payment_method(
    bank_id: int,
    method_type: str,
    title: str,
    value: str | None = None,
    qr_file_id: str | None = None,
    is_active: bool = True,
) -> int:
    method_type = method_type.strip().lower()
    title = title.strip()
    value = value.strip() if value else None

    if method_type not in {"card", "phone", "qr"}:
        raise ValueError("Навъи пардохт бояд card, phone ё qr бошад")

    if len(title) < 2:
        raise ValueError("Номи усули пардохт хеле кӯтоҳ аст")

    if not get_payment_bank(bank_id):
        raise ValueError("Бонк ёфт нашуд")

    if method_type == "qr":
        if not qr_file_id:
            raise ValueError("Барои QR сурат лозим аст")
        value = None
    else:
        if not value:
            raise ValueError("Рақам ё маълумоти пардохт лозим аст")
        qr_file_id = None

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payment_methods (
                bank_id,
                method_type,
                title,
                value,
                qr_file_id,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                bank_id,
                method_type,
                title,
                value,
                qr_file_id,
                1 if is_active else 0,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_payment_methods(
    bank_id: int,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            SELECT
                pm.*,
                pb.name AS bank_name,
                pb.card_holder
            FROM payment_methods AS pm
            INNER JOIN payment_banks AS pb
                ON pb.id = pm.bank_id
            WHERE pm.bank_id = ?
        """
        if active_only:
            sql += """
              AND pm.is_active = 1
              AND pb.is_active = 1
            """
        sql += " ORDER BY pm.created_at, pm.id"
        cursor.execute(sql, (bank_id,))
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_payment_method(method_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                pm.*,
                pb.name AS bank_name,
                pb.card_holder,
                pb.logo_file_id AS bank_logo_file_id,
                pb.is_active AS bank_is_active
            FROM payment_methods AS pm
            INNER JOIN payment_banks AS pb
                ON pb.id = pm.bank_id
            WHERE pm.id = ?
            """,
            (method_id,),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_payment_method(
    method_id: int,
    title: str | None = None,
    value: str | None = None,
    qr_file_id: str | None = None,
    is_active: bool | None = None,
) -> bool:
    method = get_payment_method(method_id)
    if not method:
        return False

    new_title = method["title"] if title is None else title.strip()
    if len(new_title) < 2:
        return False

    new_active = (
        int(method["is_active"])
        if is_active is None
        else (1 if is_active else 0)
    )

    if method["method_type"] == "qr":
        new_qr = (
            method.get("qr_file_id")
            if qr_file_id is None
            else qr_file_id or None
        )
        if not new_qr:
            return False
        new_value = None
    else:
        new_value = (
            method.get("value")
            if value is None
            else value.strip() or None
        )
        if not new_value:
            return False
        new_qr = None

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payment_methods
            SET title = ?,
                value = ?,
                qr_file_id = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_title, new_value, new_qr, new_active, method_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_payment_method(method_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM payment_methods WHERE id = ?",
            (method_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_payment_method_active(method_id: int, is_active: bool) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payment_methods
            SET is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if is_active else 0, method_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def mask_card_number(card_number: str | None) -> str:
    if not card_number:
        return "Ворид нашудааст"

    clean = str(card_number).replace(" ", "").replace("-", "")

    if len(clean) < 8:
        return clean

    return f"{clean[:4]} **** **** {clean[-4:]}"


# =========================================================
# OPTIONAL TEST DATA
# =========================================================

def seed_test_data() -> None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        categories = [
            "📱 Смартфоны",
            "🎧 Наушники",
            "⌚ Смарт-часы",
            "📱 Чехлы",
            "🔋 Power Bank",
            "🔌 Зарядные устройства",
        ]

        for name in categories:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (name,),
            )

        conn.commit()
        print("✅ Categories added")

    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()