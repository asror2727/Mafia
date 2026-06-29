from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from game_state import GameState


def join_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Qo'shilish", callback_data=f"join_{chat_id}"))
    kb.add(InlineKeyboardButton("▶️ Boshlash", callback_data=f"start_game_{chat_id}"))
    return kb


def role_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎭 Rolimni ko'rish", callback_data=f"myrole_{user_id}"))
    return kb


def night_action_keyboard(game: GameState, actor_id: int, action_type: str) -> InlineKeyboardMarkup:
    """Tun harakati uchun o'yinchilar ro'yxati (o'ldirish/davolash/tekshirish)"""
    kb = InlineKeyboardMarkup(row_width=1)
    actor = game.get_player(actor_id)

    for p in game.alive_players():
        if p.user_id == actor_id:
            continue  # o'zini tanlolmaydi (asosan)
        # Mashuqa o'zini tanlolmaydi, don ham
        btn = InlineKeyboardButton(
            p.name,
            callback_data=f"night_{action_type}_{actor_id}_{p.user_id}"
        )
        kb.add(btn)
    return kb


def vote_keyboard(game: GameState, voter_id: int) -> InlineKeyboardMarkup:
    """Kunduzgi ovoz berish tugmalari"""
    kb = InlineKeyboardMarkup(row_width=1)
    for p in game.alive_players():
        if p.user_id == voter_id:
            continue
        btn = InlineKeyboardButton(
            p.name,
            callback_data=f"vote_{voter_id}_{p.user_id}"
        )
        kb.add(btn)
    kb.add(InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"skip_{voter_id}"))
    return kb


def confirm_keyboard(action: str, target_id: int, actor_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"confirm_{action}_{actor_id}_{target_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_{action}_{actor_id}")
    )
    return kb
