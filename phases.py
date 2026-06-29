import threading
import time
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from game_state import GameState, get_game, delete_game
from keyboards import night_action_keyboard, vote_keyboard, role_keyboard
from bb_api import reward_winners
from config import (
    NIGHT_TIMEOUT, VOTE_TIMEOUT, LAST_WORDS_TIMEOUT, JOIN_TIMEOUT,
    GIF_NIGHT, GIF_DAY, GIF_START, WIN_REWARD
)
from roles import ROLES


# ─────────────────────────────────────────────────────────────
#  YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────────────────────

def player_list_text(game: GameState) -> str:
    lines = []
    for i, p in enumerate(game.alive_players(), 1):
        lines.append(f"{i}. {p.name}")
    return "\n".join(lines)


def send_role_to_player(bot: TeleBot, game: GameState, player):
    """Har bir o'yinchiga shaxsiy xabarda rolini yuboradi"""
    role = player.role
    if not role:
        return

    # Mafiya tomonidagilarga boshqa mafiyalarni ko'rsatamiz
    extra = ""
    if role["side"] == "mafia":
        teammates = [
            p.name for p in game.players.values()
            if p.side == "mafia" and p.user_id != player.user_id
        ]
        if teammates:
            extra = f"\n\n🤝 Jamoangiz: {', '.join(teammates)}"

    text = (
        f"🎭 <b>Sizning rolingiz:</b>\n\n"
        f"{role['name']}\n\n"
        f"<i>{role['description']}</i>"
        f"{extra}"
    )
    try:
        bot.send_message(player.user_id, text, parse_mode="HTML")
    except Exception:
        pass  # Foydalanuvchi bilan shaxsiy chat yo'q


def notify_night_actors(bot: TeleBot, game: GameState):
    """Tunda harakatlanishi kerak bo'lgan o'yinchilarga xabar yuboradi"""
    for p in game.alive_players():
        role = p.role
        if not role or not role.get("night_action"):
            continue

        action_type = role.get("action_type")

        # Don & Mafia - birgalikda o'ldiradi (Don tanlaydi)
        if p.role_key == "don":
            kb = night_action_keyboard(game, p.user_id, "kill")
            bot.send_message(
                p.user_id,
                "🌙 <b>Tun keldi.</b>\nKimni o'ldirmoqchisiz?",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "uboyca":
            kb = night_action_keyboard(game, p.user_id, "kill_solo")
            bot.send_message(
                p.user_id,
                "🕴️ <b>Siz bu kecha kimni yo'q qilasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "komissar":
            kb = night_action_keyboard(game, p.user_id, "check")
            bot.send_message(
                p.user_id,
                "🕵🏼 <b>Kimni tekshirmoqchisiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "serjant" and not any(
            pl.role_key == "komissar" and pl.alive for pl in game.players.values()
        ):
            kb = night_action_keyboard(game, p.user_id, "check")
            bot.send_message(
                p.user_id,
                "👮🏼 <b>Siz endi Komissar! Kimni tekshirasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "doktor":
            kb = night_action_keyboard(game, p.user_id, "heal")
            bot.send_message(
                p.user_id,
                "👨🏼‍⚕️ <b>Kimni davolaysiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "mashuqa":
            kb = night_action_keyboard(game, p.user_id, "distract")
            bot.send_message(
                p.user_id,
                "💃 <b>Bu kecha kimnikiga borasiz?</b>\n<i>(U bir kun uxlaydi)</i>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "daydi":
            kb = night_action_keyboard(game, p.user_id, "visit")
            bot.send_message(
                p.user_id,
                "🧙🏼 <b>Bu kecha kimnikiga kirasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "advokat":
            kb = night_action_keyboard(game, p.user_id, "protect")
            bot.send_message(
                p.user_id,
                "👨🏼‍💼 <b>Kimni himoya qilasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "jurnalist":
            kb = night_action_keyboard(game, p.user_id, "spy")
            bot.send_message(
                p.user_id,
                "👩🏼‍💻 <b>Bu kecha kimga intervyu olasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "aferist":
            kb = night_action_keyboard(game, p.user_id, "steal")
            bot.send_message(
                p.user_id,
                "🤹🏻 <b>Kimning ovozini o'g'irlaysiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "g_azabkor":
            kb = night_action_keyboard(game, p.user_id, "haunt")
            bot.send_message(
                p.user_id,
                f"🧟 <b>Kimni tanlaysiz?</b>\n<i>Tanlagan: {game.g_azabkor_count}/3</i>",
                reply_markup=kb, parse_mode="HTML"
            )

        elif p.role_key == "qotil":
            kb = night_action_keyboard(game, p.user_id, "kill_solo")
            bot.send_message(
                p.user_id,
                "🔪 <b>Bu kecha kimni yo'q qilasiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )


# ─────────────────────────────────────────────────────────────
#  TUN BOSQICHI
# ─────────────────────────────────────────────────────────────

def start_night(bot: TeleBot, game: GameState):
    game.phase = "night"
    game.night_number += 1
    game.reset_night_actions()

    # Guruhga GIF + tun xabari
    night_texts = [
        "🔪 Qotil Butalar orasiga yashirinib oldi...",
        "👨🏼‍⚕️ Shifokor tungi navbatchilikka ketdi...",
        "🕵🏼 Komissar Katani shaharni kuzatyapti...",
        "🤵🏻 Don o'z jamoasiga ko'rsatma bermoqda...",
    ]

    alive_roles = set(p.role_key for p in game.alive_players() if p.role)
    lines = []
    if "qotil" in alive_roles:
        lines.append("🔪 Qotil Butalar orasiga yashirinib oldi...")
    if "doktor" in alive_roles:
        lines.append("👨🏼‍⚕️ Shifokor tungi navbatchilikka ketdi...")
    if "komissar" in alive_roles:
        lines.append("🕵🏼 Komissar Katani shaharni kuzatyapti...")
    if "don" in alive_roles:
        lines.append("🤵🏻 Don o'z jamoasiga ko'rsatma bermoqda...")
    if "mashuqa" in alive_roles:
        lines.append("💃 Ma'shuqa mehmonini kutmoqda...")

    text = (
        f"🌙 <b>{game.night_number}-tun</b>\n\n"
        + "\n".join(lines) if lines else f"🌙 <b>{game.night_number}-tun boshlandi</b>"
    )

    try:
        bot.send_animation(game.chat_id, GIF_NIGHT, caption=text, parse_mode="HTML")
    except Exception:
        bot.send_message(game.chat_id, text, parse_mode="HTML")

    # Harakatlanuvchi o'yinchilarga xabar
    notify_night_actors(bot, game)

    # Vaqt tugashi
    game.timer_start = time.time()
    game.timer_duration = NIGHT_TIMEOUT
    game.timer = threading.Timer(NIGHT_TIMEOUT, resolve_night, args=[bot, game])
    game.timer.start()


# ─────────────────────────────────────────────────────────────
#  TUN YAKUNLASH - natijalarni hisoblash
# ─────────────────────────────────────────────────────────────

def resolve_night(bot: TeleBot, game: GameState):
    if game.phase != "night":
        return

    dead_this_night = []     # (player, cause, killer_role)
    messages = []

    # 1. Mashuqa bloklash
    blocked = set(game.night_distract.values())

    # 2. Don/Uboyca o'ldirish
    kill_targets = {}
    for killer_id, target_id in game.night_kills.items():
        if killer_id not in blocked:
            kill_targets[target_id] = killer_id
    for killer_id, target_id in game.night_kills.items():
        if target_id not in kill_targets and killer_id not in blocked:
            kill_targets[target_id] = killer_id

    # Qotil o'ldirishi
    # (night_kills ga qotil ham yozgan bo'ladi action_type orqali)

    # 3. Doktor davolash
    healed = set(game.night_heals.values())

    # 4. O'ldirish + davolash
    for target_id, killer_id in kill_targets.items():
        if target_id in healed:
            messages.append(f"🏥 Doktor bir odamni o'limdan qutqardi!")
            continue

        target = game.get_player(target_id)
        killer = game.get_player(killer_id)
        if not target or not target.alive:
            continue

        killer_role_name = killer.role_name if killer else "???"

        result = game.kill_player(target_id, cause="mafia_kill")
        if result["killed"]:
            dead_this_night.append((target, killer_role_name))
            # Kamikaze
            if "kamikaze_revenge" in result["side_effects"]:
                killer_result = game.kill_player(killer_id)
                if killer_result["killed"]:
                    messages.append(
                        f"💣 {target.name} - Kamikaze edi! "
                        f"Uni o'ldirishga uringan {killer.name} ham halok bo'ldi!"
                    )
        elif "bori_to_mafia" in result["side_effects"]:
            messages.append(
                f"🐺 {target.name} - Bo'ri edi! Mafiya hujumidan so'ng mafiyaga aylandi!"
            )
        elif "bori_to_serjant" in result["side_effects"]:
            messages.append(
                f"🐺 {target.name} - Bo'ri edi! Komissar uni Serjantga aylantirdi!"
            )
        elif "omadli_saved" in result["side_effects"]:
            messages.append(f"🤞 {target.name} - Omad kulib boqdi va omon qoldi!")

    # 5. Komissar tekshiruvi natijasi
    for checker_id, target_id in game.night_checks.items():
        if checker_id in blocked:
            continue
        checker = game.get_player(checker_id)
        target = game.get_player(target_id)
        if not checker or not target:
            continue

        # Advokat himoyasi
        protected = set(game.night_visits.get("advokat", []))
        if target_id in protected:
            role_shown = "👨🏼 Tinch aholi"
        else:
            role_shown = target.role_name

        # Sotqin passivi - barchaga e'lon qiladi
        sotqin_alive = any(
            p.role_key == "sotqin" and p.alive for p in game.players.values()
        )
        if sotqin_alive:
            bot.send_message(
                game.chat_id,
                f"🤓 <b>Sotqin:</b> Komissar {target.name}ni tekshirdi → {role_shown}",
                parse_mode="HTML"
            )

        try:
            bot.send_message(
                checker_id,
                f"🔍 Tekshiruv natijasi:\n{target.name} → {role_shown}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # 6. G'azabkor
    for target_id in game.night_haunt:
        game.g_azabkor_count += 1
        g_player = next(
            (p for p in game.players.values() if p.role_key == "g_azabkor"), None
        )
        if game.g_azabkor_count >= 3 and g_player:
            # O'zi ham o'ladi, tanlanganlarni ham o'ldiradi
            for tid in game.night_haunt:
                t = game.get_player(tid)
                if t:
                    game.kill_player(tid)
                    dead_this_night.append((t, "🧟 G'azabkor"))
            game.kill_player(g_player.user_id)
            messages.append(f"🧟 G'azabkor 3 qurbonini yig'ib, o'zi ham jo'nadi!")

    # ── Tun natijasi xabari ──
    if not dead_this_night:
        messages.insert(0, "😮 Hayratlanarli! Bu kecha hech kim halok bo'lmadi!")
    else:
        result_lines = []
        for victim, killer_role in dead_this_night:
            killer = game.get_player(
                next((k for k, v in kill_targets.items() if v == victim.user_id), None)
            )
            killer_name = killer.name if killer else "???"
            result_lines.append(
                f"Tunda 🤦🏼‍♂️ {victim.role_name} <b>{victim.name}</b> vahshiylarcha o'ldirildi...\n"
                f"Aytishlaricha unikiga {killer_role} kelgan"
            )
        messages = result_lines + messages

    # Oxirgi so'z navbatini tayyor qilish
    game.last_words_queue = [
        p for p in game.players.values()
        if not p.alive and not p.last_words_sent
    ]

    # Kunni boshlash (oxirgi so'zlar orqali)
    start_day(bot, game, messages)


# ─────────────────────────────────────────────────────────────
#  KUN BOSQICHI
# ─────────────────────────────────────────────────────────────

def start_day(bot: TeleBot, game: GameState, night_messages: list = None):
    game.phase = "day"
    game.day_number += 1

    # G'olibni tekshir
    winner = game.check_winner()
    if winner:
        end_game(bot, game, winner)
        return

    # GIF + kun xabari
    day_text = (
        f"🏙 <b>{game.day_number}-kun</b>\n"
        "Quyosh chiqib, tunda to'kilgan qonlarni quritdi..."
    )
    if night_messages:
        day_text += "\n\n" + "\n\n".join(night_messages)

    try:
        bot.send_animation(game.chat_id, GIF_DAY, caption=day_text, parse_mode="HTML")
    except Exception:
        bot.send_message(game.chat_id, day_text, parse_mode="HTML")

    # Tirik o'yinchilar ro'yxati
    alive_text = "🎯 <b>Tirik o'yinchilar:</b>\n\n" + player_list_text(game)
    bot.send_message(game.chat_id, alive_text, parse_mode="HTML")

    # Oxirgi so'zlarni boshlash (agar bor bo'lsa)
    if game.last_words_queue:
        process_last_words(bot, game)
    else:
        start_vote(bot, game)


def process_last_words(bot: TeleBot, game: GameState):
    """O'lgan o'yinchilarga navbatma-navbat oxirgi so'z beradi"""
    game.phase = "last_words"

    if not game.last_words_queue:
        start_vote(bot, game)
        return

    player = game.last_words_queue.pop(0)
    game.current_last_words = player.user_id
    player.last_words_sent = True

    # Guruhga e'lon
    bot.send_message(
        game.chat_id,
        f"💬 <b>{player.name}</b>ga oxirgi so'z berildi.\n"
        f"<i>20 sekund ichida yozsin...</i>",
        parse_mode="HTML"
    )

    # O'yinchiga shaxsiy
    try:
        bot.send_message(
            player.user_id,
            "✍️ <b>Oxirgi so'zingizni yozing!</b>\n"
            f"Guruhga yuboriladi. 20 sekund vaqtingiz bor.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    game.cancel_timer()
    game.timer_start = time.time()
    game.timer_duration = 20
    game.timer = threading.Timer(20, _next_last_words, args=[bot, game])
    game.timer.start()


def _next_last_words(bot: TeleBot, game: GameState):
    if game.phase != "last_words":
        return
    if game.last_words_queue:
        process_last_words(bot, game)
    else:
        game.current_last_words = None
        start_vote(bot, game)


# ─────────────────────────────────────────────────────────────
#  OVOZ BERISH
# ─────────────────────────────────────────────────────────────

def start_vote(bot: TeleBot, game: GameState):
    game.phase = "vote"
    game.reset_votes()

    # G'olibni tekshir
    winner = game.check_winner()
    if winner:
        end_game(bot, game, winner)
        return

    text = (
        "⚖️ <b>Aybdorlarni aniqlash va jazolash vaqti keldi.</b>\n"
        f"Ovoz berish uchun <b>{VOTE_TIMEOUT} sekund</b>"
    )
    bot.send_message(game.chat_id, text, parse_mode="HTML")

    # Har bir tirik o'yinchiga shaxsiy ovoz berish tugmasi
    for p in game.alive_players():
        try:
            kb = vote_keyboard(game, p.user_id)
            bot.send_message(
                p.user_id,
                "🗳 <b>Kimni osmoqchisiz?</b>",
                reply_markup=kb, parse_mode="HTML"
            )
        except Exception:
            pass

    game.cancel_timer()
    game.timer_start = time.time()
    game.timer_duration = VOTE_TIMEOUT
    game.timer = threading.Timer(VOTE_TIMEOUT, resolve_vote, args=[bot, game])
    game.timer.start()


def resolve_vote(bot: TeleBot, game: GameState):
    if game.phase != "vote":
        return

    vote_counts = {}  # { target_id: count }

    for voter_id, target_id in game.votes.items():
        voter = game.get_player(voter_id)
        if not voter or not voter.alive:
            continue

        # Janob - 2 ta ovoz
        weight = 2 if voter.role_key == "janob" else 1

        # Aferist o'g'irlagan ovoz
        actual_target = game.night_steal.get(voter_id, target_id)

        vote_counts[actual_target] = vote_counts.get(actual_target, 0) + weight

    skip_count = len(game.skip_votes)

    if not vote_counts:
        bot.send_message(game.chat_id, "😶 Hech kim ovoz bermadi. O'yin davom etadi.", parse_mode="HTML")
        start_night(bot, game)
        return

    max_votes = max(vote_counts.values())
    top_targets = [uid for uid, cnt in vote_counts.items() if cnt == max_votes]

    # Ko'p ovoz olganlar birdan ko'p bo'lsa - hech kim osilmaydi
    if len(top_targets) > 1 or max_votes <= skip_count:
        results = "\n".join(
            f"{game.get_player(uid).name if game.get_player(uid) else '???'} — {cnt} ovoz"
            for uid, cnt in sorted(vote_counts.items(), key=lambda x: -x[1])
        )
        bot.send_message(
            game.chat_id,
            f"📊 <b>Ovoz berish natijalari:</b>\n{results}\n\n⏭ Kelishuv yo'q — hech kim osilmadi.",
            parse_mode="HTML"
        )
        start_night(bot, game)
        return

    hanged_id = top_targets[0]
    hanged = game.get_player(hanged_id)

    results_text = "\n".join(
        f"{game.get_player(uid).name if game.get_player(uid) else '???'} — {cnt} ovoz"
        for uid, cnt in sorted(vote_counts.items(), key=lambda x: -x[1])
    )

    # Suisid yutadi
    if hanged and hanged.role_key == "suisid":
        bot.send_message(
            game.chat_id,
            f"📊 <b>Ovoz berish natijalari:</b>\n{results_text}\n\n"
            f"🤦🏼 <b>{hanged.name}</b> — ni osyapmiz!\n\n"
            f"🤦🏼 Suisid edi... va U G'OLIB!",
            parse_mode="HTML"
        )
        end_game(bot, game, "suisid", suisid_id=hanged_id)
        return

    result = game.kill_player(hanged_id, cause="hanged")

    if result["killed"]:
        role_reveal = hanged.role_name if hanged else "???"
        msg = (
            f"📊 <b>Ovoz berish natijalari:</b>\n{results_text}\n\n"
            f"⚖️ <b>{hanged.name}</b> — ni osyapmiz!\n\n"
            f"<b>{hanged.name}</b> — {role_reveal} edi"
        )

        # Kamikaze
        if "kamikaze_revenge" in result["side_effects"]:
            # Eng ko'p ovoz bergan kishi ham o'ladi
            top_voter = max(
                ((uid for uid, tid in game.votes.items() if tid == hanged_id)),
                default=None
            )
            if top_voter:
                t = game.get_player(top_voter)
                game.kill_player(top_voter, cause="kamikaze")
                msg += f"\n\n💣 Kamikaze o'ch oldi! {t.name} ham halok bo'ldi!"

        bot.send_message(game.chat_id, msg, parse_mode="HTML")
    else:
        bot.send_message(
            game.chat_id,
            f"📊 {results_text}\n\n🤞 {hanged.name} omon qoldi! (Omad)",
            parse_mode="HTML"
        )

    winner = game.check_winner()
    if winner:
        end_game(bot, game, winner)
    else:
        start_night(bot, game)


# ─────────────────────────────────────────────────────────────
#  O'YIN TUGADI
# ─────────────────────────────────────────────────────────────

def end_game(bot: TeleBot, game: GameState, winner: str, **kwargs):
    game.phase = "ended"
    game.cancel_timer()

    # G'olib tomonini aniqlash
    winner_side_map = {
        "town": ("🏙 Tinch aholi", "town"),
        "mafia": ("🤵🏻 Mafiya", "mafia"),
        "qotil": ("🔪 Qotil", None),
        "suisid": ("🤦🏼 Suisid", None),
        "g_azabkor": ("🧟 G'azabkor", None),
        "draw": ("🤝 Durrang", None),
    }

    winner_name, winner_side = winner_side_map.get(winner, ("???", None))

    # G'oliblar va yutqizganlar
    winners_list = []
    losers_list = []

    if winner_side:
        for p in game.players.values():
            if p.side == winner_side:
                winners_list.append(p)
            else:
                losers_list.append(p)
    elif winner == "suisid":
        sid = kwargs.get("suisid_id")
        for p in game.players.values():
            if p.user_id == sid:
                winners_list.append(p)
            else:
                losers_list.append(p)
    elif winner == "qotil":
        for p in game.players.values():
            if p.role_key == "qotil":
                winners_list.append(p)
            else:
                losers_list.append(p)
    else:
        losers_list = list(game.players.values())

    # G'oliblar matni
    winners_text = "\n".join(f"{p.name} — {p.role_name}" for p in winners_list) or "—"
    # Qolgan o'yinchilar (yutqizganlar + tiriklar)
    all_players_text = "\n".join(
        f"{p.name} — {p.role_name}" for p in game.players.values()
    )

    result_msg = (
        f"🏆 <b>O'yin tugadi!</b>\n"
        f"G'olib: <b>{winner_name}</b>\n\n"
        f"<b>G'oliblar:</b>\n{winners_text}\n\n"
        f"<b>Barcha o'yinchilar:</b>\n{all_players_text}\n\n"
        f"⏱ O'yin: <b>{game.game_duration()}</b> davom etdi"
    )

    bot.send_message(game.chat_id, result_msg, parse_mode="HTML")

    # BB ga mukofot
    winner_ids = [p.user_id for p in winners_list]
    loser_ids = [p.user_id for p in losers_list]
    reward_winners(winner_ids, loser_ids, WIN_REWARD)

    # O'yinni o'chirish
    delete_game(game.chat_id)
