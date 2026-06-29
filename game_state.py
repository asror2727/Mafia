import random
import time
from roles import ROLES, get_role_pool

# ── GLOBAL O'YIN HOLATLARI ───────────────────────────────────
# { chat_id: GameState }
games = {}


class Player:
    def __init__(self, user_id: int, name: str, username: str = None):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.role_key = None          # "don", "komissar" va h.k.
        self.alive = True
        self.last_words_sent = False
        self.survived_once = False    # Omadli passiv
        self.votes_received = 0
        self.stolen_vote = None       # Aferist o'g'irlagan ovoz
        self.night_action_done = False

    @property
    def role(self):
        if self.role_key:
            return ROLES[self.role_key]
        return None

    @property
    def role_name(self):
        if self.role:
            return self.role["name"]
        return "❓"

    @property
    def side(self):
        if self.role:
            return self.role["side"]
        return None

    def mention(self):
        """HTML mention"""
        return f'<a href="tg://user?id={self.user_id}">{self.name}</a>'


class GameState:
    def __init__(self, chat_id: int, creator_id: int):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.phase = "waiting"   # waiting | night | day | vote | last_words | ended
        self.players = {}        # { user_id: Player }
        self.day_number = 0
        self.night_number = 0

        # Tun harakatlari
        self.night_kills = {}    # { killer_id: target_id }
        self.night_heals = {}    # { healer_id: target_id }
        self.night_checks = {}   # { checker_id: target_id }
        self.night_distract = {} # { mashuqa_id: target_id }
        self.night_visits = {}   # { daydi_id: target_id }
        self.night_spy = {}      # { jurnalist_id: target_id }
        self.night_haunt = []    # g'azabkor tanlagan o'yinchilar
        self.night_steal = {}    # { aferist_id: target_id }

        # Ovoz berish
        self.votes = {}          # { voter_id: target_id }
        self.skip_votes = set()  # "o'tkazib yuborish" ovozlari

        # Oxirgi so'z navbati
        self.last_words_queue = []  # o'lgan o'yinchilar navbati
        self.current_last_words = None

        # Timer (threading.Timer ob'ekti)
        self.timer = None
        self.timer_start = None
        self.timer_duration = 0

        # O'yin boshlangan vaqt
        self.start_time = None

        # G'azabkor hisoblash
        self.g_azabkor_count = 0

        # Bir martalik omon qolish (Omadli)
        self.omadli_used = set()

    # ── OYINCHILAR ───────────────────────────────────────────
    def add_player(self, user_id: int, name: str, username: str = None) -> bool:
        from config import MAX_PLAYERS
        if user_id in self.players:
            return False
        if len(self.players) >= MAX_PLAYERS:
            return False
        self.players[user_id] = Player(user_id, name, username)
        return True

    def alive_players(self) -> list:
        return [p for p in self.players.values() if p.alive]

    def alive_count(self) -> int:
        return len(self.alive_players())

    def get_player(self, user_id: int) -> Player:
        return self.players.get(user_id)

    def players_by_side(self, side: str) -> list:
        return [p for p in self.alive_players() if p.side == side]

    # ── ROL TAQSIMLASH ───────────────────────────────────────
    def assign_roles(self):
        player_list = list(self.players.values())
        role_pool = get_role_pool(len(player_list))
        random.shuffle(player_list)
        for i, player in enumerate(player_list):
            player.role_key = role_pool[i] if i < len(role_pool) else "tinch_aholi"

    # ── O'LISH LOGIKASI ──────────────────────────────────────
    def kill_player(self, user_id: int, cause: str = "night") -> dict:
        """
        O'yinchini o'ldiradi. Passiv effektlarni qaytaradi.
        Returns: {"killed": bool, "side_effects": [...]}
        """
        player = self.get_player(user_id)
        if not player or not player.alive:
            return {"killed": False, "side_effects": []}

        side_effects = []

        # Omadli - bir marta omon qoladi
        if player.role_key == "omadli" and user_id not in self.omadli_used and cause == "night":
            self.omadli_used.add(user_id)
            return {"killed": False, "side_effects": ["omadli_saved"]}

        # Kamikaze - o'ldirganni ham o'ldiradi
        if player.role_key == "kamikaze":
            side_effects.append("kamikaze_revenge")

        # Bo'ri - transformatsiya
        if player.role_key == "bori":
            if cause == "mafia_kill":
                player.role_key = "mafia"
                player.alive = True  # o'lmaydi, mafiyaga aylanadi
                return {"killed": False, "side_effects": ["bori_to_mafia"]}
            elif cause == "komissar_kill":
                player.role_key = "serjant"
                player.alive = True
                return {"killed": False, "side_effects": ["bori_to_serjant"]}

        player.alive = False
        return {"killed": True, "side_effects": side_effects}

    # ── G'OLIB ANIQLASH ─────────────────────────────────────
    def check_winner(self) -> str | None:
        """
        G'olibni tekshiradi.
        Returns: "town" | "mafia" | "qotil" | "suisid" | "g_azabkor" | None
        """
        alive = self.alive_players()
        town = self.players_by_side("town")
        mafia = self.players_by_side("mafia")
        neutral = self.players_by_side("neutral")

        alive_count = len(alive)
        town_count = len(town)
        mafia_count = len(mafia)

        # Hamma o'ldi
        if alive_count == 0:
            return "draw"

        # Mafiya yo'q — shahar g'alaba
        if mafia_count == 0:
            # Qotil yashasa
            qotil_alive = any(p.role_key == "qotil" for p in neutral)
            if qotil_alive and alive_count > 1:
                return None  # O'yin davom etadi
            return "town"

        # Mafiya ≥ shahar — mafiya g'alaba
        if mafia_count >= town_count:
            # Neytrallar hisob
            if len(neutral) == 0:
                return "mafia"

        # Faqat qotil qoldi
        if alive_count == 1:
            last = alive[0]
            if last.role_key == "qotil":
                return "qotil"

        # G'azabkor maqsadi bajarildi
        for p in self.players.values():
            if p.role_key == "g_azabkor" and not p.alive and self.g_azabkor_count >= 3:
                return "g_azabkor"

        return None

    # ── TIMER ────────────────────────────────────────────────
    def cancel_timer(self):
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        self.timer = None

    def time_left(self) -> int:
        if self.timer_start is None:
            return 0
        elapsed = int(time.time() - self.timer_start)
        return max(0, self.timer_duration - elapsed)

    # ── STATISTIKA ───────────────────────────────────────────
    def game_duration(self) -> str:
        if not self.start_time:
            return "0 sek."
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        if minutes:
            return f"{minutes} min. {seconds} sek."
        return f"{seconds} sek."

    def reset_night_actions(self):
        self.night_kills.clear()
        self.night_heals.clear()
        self.night_checks.clear()
        self.night_distract.clear()
        self.night_visits.clear()
        self.night_spy.clear()
        self.night_steal.clear()
        for p in self.players.values():
            p.night_action_done = False

    def reset_votes(self):
        self.votes.clear()
        self.skip_votes.clear()
        for p in self.players.values():
            p.votes_received = 0


def get_game(chat_id: int) -> GameState | None:
    return games.get(chat_id)

def create_game(chat_id: int, creator_id: int) -> GameState:
    game = GameState(chat_id, creator_id)
    games[chat_id] = game
    return game

def delete_game(chat_id: int):
    games.pop(chat_id, None)
