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
                name TEXT UNIQUE NOT NULL,
                logo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                price REAL NOT NULL CHECK(price >= 0),
                discount REAL DEFAULT 0 CHECK(discount >= 0),
                stock INTEGER DEFAULT 0 CHECK(stock >= 0),

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
        """)

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


def get_user_by_telegram_id(telegram_id: int) -> dict[str, Any] | None:
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
        return cursor.lastrowid
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


# =========================================================
# BRANDS
# =========================================================

def add_brand(name: str, logo: str | None = None) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO brands (name, logo) VALUES (?, ?)",
            (name.strip(), logo),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_brands() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands ORDER BY name")
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_brand(brand_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands WHERE id = ?", (brand_id,))
        return row_to_dict(cursor.fetchone())
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
            SELECT DISTINCT
                b.id,
                b.name,
                b.logo,
                b.created_at
            FROM brands AS b
            INNER JOIN products AS p
                ON p.brand_id = b.id
            WHERE p.category_id = ?
              AND p.is_active = 1
            ORDER BY b.name
            """,
            (category_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_brand(
    brand_id: int,
    name: str,
    logo: str | None = None,
) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE brands
            SET name = ?, logo = ?
            WHERE id = ?
            """,
            (name.strip(), logo, brand_id),
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
        return cursor.lastrowid
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
    discount: float = 0,
    stock: int = 0,
    city: str | None = None,
    warranty: str | None = None,
    battery_health: str | None = None,
    sim_type: str | None = None,
    image: str | None = None,
    name: str | None = None,
) -> int:
    """
    image ва name барои мутобиқат бо коди кӯҳна қабул мешаванд.
    Агар image дода шавад, ҳамчун сурати якум нигоҳ дошта мешавад.
    """
    if not title and name:
        title = name

    if not title:
        raise ValueError("Номи маҳсулот холӣ аст")

    if price < 0:
        raise ValueError("Нарх манфӣ шуда наметавонад")

    if discount < 0 or discount > price:
        raise ValueError("Тахфиф нодуруст аст")

    if stock < 0:
        raise ValueError("Миқдор манфӣ шуда наметавонад")

    if condition not in {"new", "used"}:
        raise ValueError("Ҳолат бояд new ё used бошад")

    conn = get_connection()

    try:
        cursor = conn.cursor()

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
                price,
                discount,
                stock,
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
                price,
                discount,
                stock,
                city,
                warranty,
                battery_health,
                sim_type,
            ),
        )

        product_id = cursor.lastrowid

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
            + """
            WHERE p.id = ?
            """,
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
        search_value = f"%{query.strip()}%"

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
            (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
            ),
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
    discount: float = 0,
    stock: int = 0,
    city: str | None = None,
    warranty: str | None = None,
    battery_health: str | None = None,
    sim_type: str | None = None,
) -> bool:
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
                price = ?,
                discount = ?,
                stock = ?,
                city = ?,
                warranty = ?,
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
                price,
                discount,
                stock,
                city,
                warranty,
                battery_health,
                sim_type,
                product_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_product_stock(product_id: int, stock: int) -> bool:
    if stock < 0:
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE products
            SET stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (stock, product_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


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
    position: int,
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
        return cursor.lastrowid
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
            SELECT stock
            FROM products
            WHERE id = ?
              AND is_active = 1
            """,
            (product_id,),
        )
        product = cursor.fetchone()

        if not product:
            return False

        stock = product["stock"]

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
            new_quantity = cart_item["quantity"] + quantity

            if new_quantity > stock:
                return False

            cursor.execute(
                "UPDATE cart SET quantity = ? WHERE id = ?",
                (new_quantity, cart_item["id"]),
            )
        else:
            if quantity > stock:
                return False

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
                p.stock,

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
            "SELECT stock FROM products WHERE id = ?",
            (product_id,),
        )
        product = cursor.fetchone()

        if not product or quantity > product["stock"]:
            return False

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
    address: str,
    phone: str,
) -> int | None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                c.product_id,
                c.quantity,
                p.title,
                p.price,
                p.discount,
                p.stock,
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

        total_price = 0.0

        for item in cart_items:
            if item["quantity"] > item["stock"]:
                return None

            total_price += float(item["final_price"]) * item["quantity"]

        cursor.execute(
            """
            INSERT INTO orders (
                user_id,
                total_price,
                address,
                phone,
                status
            )
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (user_id, total_price, address.strip(), phone.strip()),
        )

        order_id = cursor.lastrowid

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
                """
                UPDATE products
                SET stock = stock - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND stock >= ?
                """,
                (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"],
                ),
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return None

        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
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
                u.username
            FROM orders AS o
            LEFT JOIN users AS u
                ON u.id = o.user_id
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
                u.username
            FROM orders AS o
            LEFT JOIN users AS u
                ON u.id = o.user_id
            ORDER BY o.created_at DESC
            """
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


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

        brands = [
            "Apple",
            "Samsung",
            "Xiaomi",
            "Huawei",
            "JBL",
            "Baseus",
            "Anker",
        ]

        for name in brands:
            cursor.execute(
                "INSERT OR IGNORE INTO brands (name) VALUES (?)",
                (name,),
            )

        conn.commit()
        print("✅ Categories and brands added")

    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    seed_test_data()