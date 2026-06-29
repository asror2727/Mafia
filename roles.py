# ============================================================
#  ROLLAR - har bir rolning nomi, emoji, tomoni, vazifasi
# ============================================================

ROLES = {
    # ── TINCH AHOLI TOMONI ──────────────────────────────────
    "tinch_aholi": {
        "name": "👨🏼 Tinch aholi",
        "side": "town",
        "night_action": False,
        "description": "Vazifasi: mafiани topish va ovoz berish jarayonida ularni osish"
    },
    "omadli": {
        "name": "🤞 Omadli",
        "side": "town",
        "night_action": False,
        "description": "Suiqasd bo'lsa omon qolishi mumkin. Vazifasi: mafiyaga qarshi kurashish",
        "passive": "survive_once"   # bir marta o'limdan qutiladi
    },
    "daydi": {
        "name": "🧙🏼 Daydi",
        "side": "town",
        "night_action": True,
        "action_type": "visit",
        "description": "Xohlagan odamning uyiga kiradi — qotillikning guvohiga aylanishi mumkin"
    },
    "mashuqa": {
        "name": "💃 Ma'shuqa",
        "side": "town",
        "night_action": True,
        "action_type": "distract",
        "description": "Har tun mehmonga dorі beradi va u bir kun uxlaydi (bloklaydi). Donni o'ldirtishi mumkin"
    },
    "kamikaze": {
        "name": "💣 Kamikaze",
        "side": "town",
        "night_action": False,
        "description": "O'ldirilsa, o'ldirgan ham o'ladi. Kunduzgi osishda o'ldirilsa birovni o'zi bilan olib ketadi",
        "passive": "avenge"
    },
    "bori": {
        "name": "🐺 Bo'ri",
        "side": "town",
        "night_action": False,
        "description": "Mafiya o'ldirsa — mafiyaga aylanadi. Komissar o'ldirsa — Serjanтga aylanadi",
        "passive": "transform"
    },
    "komissar": {
        "name": "🕵🏼 Komissar Katani",
        "side": "town",
        "night_action": True,
        "action_type": "check",
        "description": "Shaharning asosiy himoyachisi. Har tun bir odamni tekshiradi"
    },
    "serjant": {
        "name": "👮🏼 Serjant",
        "side": "town",
        "night_action": True,
        "action_type": "check",
        "description": "Komissarning yordamchisi. Komissar o'lsa o'rnini egallaydi"
    },
    "doktor": {
        "name": "👨🏼‍⚕️ Doktor",
        "side": "town",
        "night_action": True,
        "action_type": "heal",
        "description": "Tunda kimnidir qutqarib qolishi mumkin"
    },
    "janob": {
        "name": "🎖 Janob",
        "side": "town",
        "night_action": False,
        "description": "Kunduzgi ovozida ikki ovozga teng!",
        "passive": "double_vote"
    },
    "advokat": {
        "name": "👨🏼‍💼 Advokat",
        "side": "town",
        "night_action": True,
        "action_type": "protect_identity",
        "description": "Tunda kimni himoya qilishni tanlaydi. Agar mafiyani tanlasa — komissar uni tanimaydi"
    },

    # ── MAFIYA TOMONI ────────────────────────────────────────
    "mafia": {
        "name": "🤵🏼 Mafia",
        "side": "mafia",
        "night_action": False,
        "description": "Don o'lsa yangi Don bo'lishi mumkin. Vazifasi: tinch aholini o'ldirish"
    },
    "don": {
        "name": "🤵🏻 Don",
        "side": "mafia",
        "night_action": True,
        "action_type": "kill",
        "description": "Har tun kim o'lishini u xal qiladi. Mafiyalar sardori"
    },
    "jurnalist": {
        "name": "👩🏼‍💻 Jurnalist",
        "side": "mafia",
        "night_action": True,
        "action_type": "spy",
        "description": "Har tun kimgadir intervyu oladi — o'sha kechada kimlar kelganini ko'radi"
    },
    "uboyca": {
        "name": "🕴️ Uboyca",
        "side": "mafia",
        "night_action": True,
        "action_type": "kill_solo",
        "description": "Mafiyaning asosiy quroli. Istalgan tinch aholini o'ldira oladi"
    },

    # ── NEYTRAL ROLLAR ───────────────────────────────────────
    "qotil": {
        "name": "🔪 Qotil",
        "side": "neutral",
        "night_action": True,
        "action_type": "kill_solo",
        "description": "Shahardagi hamma o'lishi kerak, undan tashqari :) Faqat o'zi uchun o'ynaydi!"
    },
    "g_azabkor": {
        "name": "🧟 G'azabkor",
        "side": "neutral",
        "night_action": True,
        "action_type": "haunt",
        "description": "Har tun 1 oyinchini tanlaydi. Kamida 3 ta o'yinchi tanlagandan so'ng o'zini ham olib ketadi"
    },
    "sehrgar": {
        "name": "🧙‍ Sehrgar",
        "side": "neutral",
        "night_action": False,
        "description": "O'z qonunlari bilan yashaydi. Kimdir o'ldirmoqchi bo'lsa — rahm yoki o'ldirish tanlovini beradi",
        "passive": "magic_shield"
    },
    "suisid": {
        "name": "🤦🏼 Suisid",
        "side": "neutral",
        "night_action": False,
        "description": "Uni osib o'ldirishsa — yutadi!",
        "win_condition": "get_hanged"
    },
    "aferist": {
        "name": "🤹🏻 Aferist",
        "side": "neutral",
        "night_action": True,
        "action_type": "steal_vote",
        "description": "Kechasi bir o'yinchinikiga borib, uning kunduzgi ovozini o'g'irlaydi"
    },
    "sotqin": {
        "name": "🤓 Sotqin",
        "side": "neutral",
        "night_action": False,
        "description": "Ikkiyuzlamachi. Komissar tekshirgan rolni kimligini ko'rib qoladi va barchaga aytadi",
        "passive": "reveal_check"
    },
}

# ── OYINCHI SONIGA QARAB ROL TAQSIMOTI ─────────────────────
def get_role_pool(player_count: int) -> list:
    """
    Nechta odam bo'lsa shuncha rol tayinlanadi.
    Don har doim bor. Mafiya soni ≈ 1/4.
    """
    roles = []

    if player_count < 3:
        return []

    # Mafiya soni
    mafia_count = max(1, player_count // 4)

    # Don har doim 1 ta
    roles.append("don")
    mafia_count -= 1

    # Qolgan mafiyalar
    for _ in range(mafia_count):
        roles.append("mafia")

    # Asosiy town rollari
    roles.append("komissar")
    roles.append("doktor")

    # Qolgan o'rinlar uchun town pool
    town_pool = [
        "tinch_aholi", "tinch_aholi", "tinch_aholi",
        "omadli", "daydi", "mashuqa", "kamikaze",
        "bori", "serjant", "janob", "advokat",
    ]

    # Neytral rollar (katta o'yinlarda)
    neutral_pool = []
    if player_count >= 6:
        neutral_pool += ["suisid"]
    if player_count >= 8:
        neutral_pool += ["qotil"]
    if player_count >= 10:
        neutral_pool += ["aferist", "g_azabkor"]
    if player_count >= 14:
        neutral_pool += ["sehrgar", "sotqin"]
    if player_count >= 16:
        neutral_pool += ["jurnalist", "uboyca"]

    # To'ldirish
    remaining = player_count - len(roles)
    import random
    combined = town_pool + neutral_pool
    random.shuffle(combined)
    roles += combined[:remaining]

    random.shuffle(roles)
    return roles
