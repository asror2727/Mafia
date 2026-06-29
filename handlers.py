import threading
import time
from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from game_state import get_game, create_game, delete_game
from phases import start_night, start_day, process_last_words, resolve_vote, end_game, send_role_to_player
from keyboards import join_keyboard, role_keyboard
from config import MIN_PLAYERS, MAX_PLAYERS, JOIN_TIMEOUT, GIF_START


def register_handlers(bot: TeleBot):

    # ── /game — guruhda o'yin ochish ──────────────────────────
    @bot.message_handler(commands=["game"])
    def cmd_game(msg: Message):
        if msg.chat.type == "private":
            bot.reply_to(msg, "❌ Bu buyruq faqat guruhda ishlaydi!")
            return

        chat_id = msg.chat.id
        game = get_game(chat_id)

        if game:
            bot.reply_to(msg, "⚠️ Bu guruhda allaqachon o'yin bor!")
            return

        game = create_game(chat_id, msg.from_user.id)
        user = msg.from_user
        name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        game.add_player(user.id, name, user.username)

        text = (
            f"🎭 <b>Mafia o'yini ochildi!</b>\n\n"
            f"Qo'shilish uchun pastdagi tugmani bosing.\n"
            f"Minimum: <b>{MIN_PLAYERS}</b> | Maximum: <b>{MAX_PLAYERS}</b> o'yinchi\n\n"
            f"<b>Qo'shilganlar:</b>\n1. {name}\n\n"
            f"⏳ <b>{JOIN_TIMEOUT}</b> sekund"
        )

        try:
            bot.send_animation(
                chat_id, GIF_START,
                caption=text,
                reply_markup=join_keyboard(chat_id),
                parse_mode="HTML"
            )
        except Exception:
            bot.send_message(chat_id, text, reply_markup=join_keyboard(chat_id), parse_mode="HTML")

        # Avto boshlash timeri
        game.timer_start = time.time()
        game.timer_duration = JOIN_TIMEOUT
        game.timer = threading.Timer(JOIN_TIMEOUT, _auto_start, args=[bot, game])
        game.timer.start()

    def _auto_start(bot: TeleBot, game):
        """Vaqt tugaganda avtomatik boshlash"""
        g = get_game(game.chat_id)
        if not g or g.phase != "waiting":
            return

        if g.alive_count() < MIN_PLAYERS:
            bot.send_message(
                g.chat_id,
                f"❌ O'yin bekor qilindi. Minimum {MIN_PLAYERS} ta o'yinchi kerak.\n"
                f"Qo'shilgan: {g.alive_count()} ta"
            )
            delete_game(g.chat_id)
            return

        _begin_game(bot, g)

    # ── Qo'shilish tugmasi ────────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
    def cb_join(call: CallbackQuery):
        chat_id = int(call.data.split("_")[1])
        game = get_game(chat_id)

        if not game or game.phase != "waiting":
            bot.answer_callback_query(call.id, "❌ O'yin mavjud emas yoki boshlangan!")
            return

        user = call.from_user
        name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        joined = game.add_player(user.id, name, user.username)

        if not joined:
            bot.answer_callback_query(call.id, "✅ Siz allaqachon qo'shilgansiz!")
            return

        count = game.alive_count()
        player_lines = "\n".join(
            f"{i}. {p.name}" for i, p in enumerate(game.players.values(), 1)
        )
        text = (
            f"🎭 <b>Mafia o'yini</b>\n\n"
            f"<b>Qo'shilganlar ({count}/{MAX_PLAYERS}):</b>\n{player_lines}\n\n"
            f"⏳ {game.time_left()} sek. qoldi"
        )

        try:
            bot.edit_message_caption(
                caption=text,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=join_keyboard(chat_id),
                parse_mode="HTML"
            )
        except Exception:
            try:
                bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=join_keyboard(chat_id),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        bot.answer_callback_query(call.id, f"✅ {name} o'yinga qo'shildi!")

    # ── Boshlash tugmasi (qo'l bilan) ────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("start_game_"))
    def cb_start_game(call: CallbackQuery):
        chat_id = int(call.data.split("_")[2])
        game = get_game(chat_id)

        if not game or game.phase != "waiting":
            bot.answer_callback_query(call.id, "❌ O'yin mavjud emas!")
            return

        if call.from_user.id != game.creator_id:
            bot.answer_callback_query(call.id, "❌ Faqat o'yin ochgan kishi boshlaydi!")
            return

        if game.alive_count() < MIN_PLAYERS:
            bot.answer_callback_query(
                call.id,
                f"❌ Kamida {MIN_PLAYERS} ta o'yinchi kerak! Hozir: {game.alive_count()}"
            )
            return

        game.cancel_timer()
        bot.answer_callback_query(call.id, "▶️ O'yin boshlanmoqda!")
        _begin_game(bot, game)

    def _begin_game(bot: TeleBot, game):
        """O'yinni haqiqatda boshlash"""
        if game.phase != "waiting":
            return
        game.phase = "starting"
        game.start_time = time.time()

        # Rollarni taqsimlash
        game.assign_roles()

        # Guruhga xabar
        player_lines = "\n".join(
            f"{i}. {p.name}" for i, p in enumerate(game.players.values(), 1)
        )
        start_msg = bot.send_message(
            game.chat_id,
            f"🎮 <b>O'yin boshlandi!</b>\n\n"
            f"<b>Tirik o'yinchilar:</b>\n{player_lines}\n\n"
            f"Rolingizni ko'rish uchun botga kiring 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    "🎭 Rolimni ko'rish",
                    url=f"https://t.me/{bot.get_me().username}?start=role"
                )
            )
        )

        # Har bir o'yinchiga shaxsiy xabarda rol
        for p in game.players.values():
            send_role_to_player(bot, game, p)

        # 5 sekund kutish, keyin tun
        def _after_roles():
            g = get_game(game.chat_id)
            if g:
                start_night(bot, g)

        threading.Timer(5, _after_roles).start()

    # ── /start — shaxsiy botda (rol ko'rish) ──────────────────
    @bot.message_handler(commands=["start"])
    def cmd_start(msg: Message):
        if msg.chat.type != "private":
            bot.reply_to(msg, "👋 Mafia botiga xush kelibsiz!\nO'yin guruhda /game bilan ochiladi.")
            return

        # Rol so'rash
        user_id = msg.from_user.id
        # Barcha o'yinlarda shu userni qidirish
        from game_state import games
        for chat_id, game in games.items():
            p = game.get_player(user_id)
            if p and game.phase not in ("waiting", "ended"):
                send_role_to_player(bot, game, p)
                return

        bot.send_message(
            msg.chat.id,
            "🎭 <b>Mafia Bot</b>\n\n"
            "Guruhda /game yozing va o'yin oching!\n"
            "O'yinga qo'shilganingizdan so'ng rol bu yerga keladi.",
            parse_mode="HTML"
        )

    # ── /stop — o'yinni bekor qilish ─────────────────────────
    @bot.message_handler(commands=["stop"])
    def cmd_stop(msg: Message):
        if msg.chat.type == "private":
            return
        game = get_game(msg.chat.id)
        if not game:
            bot.reply_to(msg, "❌ Aktiv o'yin yo'q.")
            return

        # Faqat admin yoki yaratuvchi
        if msg.from_user.id != game.creator_id:
            try:
                admins = bot.get_chat_administrators(msg.chat.id)
                admin_ids = [a.user.id for a in admins]
                if msg.from_user.id not in admin_ids:
                    bot.reply_to(msg, "❌ Faqat admin yoki o'yin ochgan kishi to'xtatishi mumkin!")
                    return
            except Exception:
                pass

        game.cancel_timer()
        delete_game(msg.chat.id)
        bot.send_message(msg.chat.id, "⛔ O'yin to'xtatildi.")

    # ── /players — tirik o'yinchilar ro'yxati ─────────────────
    @bot.message_handler(commands=["players"])
    def cmd_players(msg: Message):
        game = get_game(msg.chat.id)
        if not game or game.phase == "waiting":
            bot.reply_to(msg, "❌ Aktiv o'yin yo'q.")
            return

        from phases import player_list_text
        text = f"🎯 <b>Tirik o'yinchilar ({game.alive_count()}):</b>\n\n" + player_list_text(game)
        bot.send_message(msg.chat.id, text, parse_mode="HTML")

    # ── Tun harakatlari callback ───────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("night_"))
    def cb_night_action(call: CallbackQuery):
        parts = call.data.split("_")
        # night_{action}_{actor_id}_{target_id}
        action = parts[1]
        actor_id = int(parts[2])
        target_id = int(parts[3])

        if call.from_user.id != actor_id:
            bot.answer_callback_query(call.id, "❌ Bu sizning tugmangiz emas!")
            return

        # Qaysi o'yinda ekanini topish
        from game_state import games
        game = None
        for g in games.values():
            p = g.get_player(actor_id)
            if p:
                game = g
                break

        if not game or game.phase != "night":
            bot.answer_callback_query(call.id, "❌ Tun bosqichi emas!")
            return

        actor = game.get_player(actor_id)
        target = game.get_player(target_id)

        if not actor or not target:
            bot.answer_callback_query(call.id, "❌ O'yinchi topilmadi!")
            return

        if actor.night_action_done:
            bot.answer_callback_query(call.id, "✅ Siz allaqachon harakat qildingiz!")
            return

        # Harakat saqlash
        if action == "kill" or action == "kill_solo":
            game.night_kills[actor_id] = target_id
        elif action == "heal":
            game.night_heals[actor_id] = target_id
        elif action == "check":
            game.night_checks[actor_id] = target_id
        elif action == "distract":
            game.night_distract[actor_id] = target_id
        elif action == "visit":
            game.night_visits[actor_id] = target_id
        elif action == "spy":
            game.night_spy[actor_id] = target_id
        elif action == "steal":
            game.night_steal[actor_id] = target_id
        elif action == "haunt":
            if target_id not in game.night_haunt:
                game.night_haunt.append(target_id)
        elif action == "protect":
            game.night_checks[actor_id] = target_id  # advokat himoyasi

        actor.night_action_done = True
        bot.answer_callback_query(call.id, f"✅ {target.name} tanlandi!")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.send_message(actor_id, f"✅ <b>{target.name}</b> tanlandi.", parse_mode="HTML")

        # Barcha harakatlar tugadimi? Erta tun yakunlash
        _check_all_night_done(bot, game)

    def _check_all_night_done(bot: TeleBot, game):
        """Barcha tun harakatlar bajarilsa - erta yakunlash"""
        from phases import resolve_night
        active_actors = [
            p for p in game.alive_players()
            if p.role and p.role.get("night_action") and not p.night_action_done
        ]
        # Mashuqa bloklanganlari hisobga olmasak...
        if not active_actors:
            game.cancel_timer()
            threading.Timer(1, resolve_night, args=[bot, game]).start()

    # ── Ovoz berish callback ───────────────────────────────────
    @bot.callback_query_handler(func=lambda c: c.data.startswith("vote_"))
    def cb_vote(call: CallbackQuery):
        parts = call.data.split("_")
        voter_id = int(parts[1])
        target_id = int(parts[2])

        if call.from_user.id != voter_id:
            bot.answer_callback_query(call.id, "❌ Bu sizning tugmangiz emas!")
            return

        from game_state import games
        game = None
        for g in games.values():
            if g.get_player(voter_id):
                game = g
                break

        if not game or game.phase != "vote":
            bot.answer_callback_query(call.id, "❌ Ovoz berish vaqti emas!")
            return

        target = game.get_player(target_id)
        if not target or not target.alive:
            bot.answer_callback_query(call.id, "❌ Bu o'yinchi allaqachon o'lik!")
            return

        game.votes[voter_id] = target_id
        bot.answer_callback_query(call.id, f"✅ {target.name}ga ovoz berildi!")
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        bot.send_message(voter_id, f"✅ <b>{target.name}</b>ga ovoz berdingiz.", parse_mode="HTML")

        # Guruhga kim ovoz berganini e'lon qilish
        voter = game.get_player(voter_id)
        if voter:
            bot.send_message(
                game.chat_id,
                f"🗳 <b>{voter.name}</b> ovoz berdi.",
                parse_mode="HTML"
            )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("skip_"))
    def cb_skip(call: CallbackQuery):
        voter_id = int(call.data.split("_")[1])

        if call.from_user.id != voter_id:
            bot.answer_callback_query(call.id, "❌ Bu sizning tugmangiz emas!")
            return

        from game_state import games
        game = None
        for g in games.values():
            if g.get_player(voter_id):
                game = g
                break

        if not game or game.phase != "vote":
            bot.answer_callback_query(call.id, "❌ Ovoz berish vaqti emas!")
            return

        game.skip_votes.add(voter_id)
        bot.answer_callback_query(call.id, "⏭ O'tkazib yubordingiz!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    # ── Oxirgi so'z handler (shaxsiy xabar) ──────────────────
    @bot.message_handler(func=lambda msg: msg.chat.type == "private", content_types=["text"])
    def private_message(msg: Message):
        user_id = msg.from_user.id
        from game_state import games

        for chat_id, game in games.items():
            if game.current_last_words == user_id:
                p = game.get_player(user_id)
                if p:
                    # Guruhga oxirgi so'zini yuborish
                    bot.send_message(
                        chat_id,
                        f"💬 <b>{p.name}ning oxirgi so'zi:</b>\n\n{msg.text}",
                        parse_mode="HTML"
                    )
                    game.current_last_words = None
                    game.cancel_timer()

                    # Keyingi navbat
                    from phases import _next_last_words
                    threading.Timer(1, _next_last_words, args=[bot, game]).start()
                return

        bot.reply_to(msg, "ℹ️ Hozir aktiv o'yin yo'q. Guruhda /game yozing!")
