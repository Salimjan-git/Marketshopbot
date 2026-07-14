from config import ADMIN_IDS


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS