import requests
from config import BB_API_URL, BB_API_KEY

HEADERS = {
    "X-API-Key": BB_API_KEY,
    "Content-Type": "application/json"
}


def add_coins(user_id: int, amount: int, reason: str = "mafia_win") -> bool:
    """
    BB botga pul qo'shish so'rovi yuboradi.
    BB server tomonida /api/add_coins endpoint bo'lishi kerak.
    """
    try:
        resp = requests.post(
            f"{BB_API_URL}/api/add_coins",
            json={
                "user_id": user_id,
                "amount": amount,
                "reason": reason
            },
            headers=HEADERS,
            timeout=5
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"BB API xato: {e}")
        return False


def get_profile(user_id: int) -> dict | None:
    """
    BB dan foydalanuvchi profilini oladi.
    """
    try:
        resp = requests.get(
            f"{BB_API_URL}/api/profile/{user_id}",
            headers=HEADERS,
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"BB API xato: {e}")
        return None


def update_game_stats(user_id: int, won: bool) -> bool:
    """
    O'yin statistikasini yangilaydi (g'alaba/mag'lubiyat).
    """
    try:
        resp = requests.post(
            f"{BB_API_URL}/api/game_stats",
            json={
                "user_id": user_id,
                "game": "mafia",
                "won": won
            },
            headers=HEADERS,
            timeout=5
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"BB API xato: {e}")
        return False


def reward_winners(winners: list, losers: list, reward: int = 50):
    """
    G'oliblarга pul beradi, statistikani yangilaydi.
    Async emas — thread da chaqirish mumkin.
    """
    import threading

    def _send():
        for uid in winners:
            add_coins(uid, reward, "mafia_win")
            update_game_stats(uid, True)
        for uid in losers:
            update_game_stats(uid, False)

    t = threading.Thread(target=_send, daemon=True)
    t.start()
