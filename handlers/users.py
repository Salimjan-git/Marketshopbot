from database import get_connection


def get_or_create_user(
    telegram_id,
    full_name,
    username=None,
    phone=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    if user:
        conn.close()
        return dict(user)

    cursor.execute(
        """
        INSERT INTO users(
            telegram_id,
            full_name,
            username,
            phone
        )
        VALUES(?,?,?,?)
        """,
        (
            telegram_id,
            full_name,
            username,
            phone,
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return dict(user)