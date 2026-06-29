import telebot
import threading
import os
from config import BOT_TOKEN
from handlers import register_handlers

bot = telebot.TeleBot(8840892305:AAExPeCpVhH5a4i46kPF9jPpIJvFZxxUGXc), parse_mode="HTML")

register_handlers(bot)

if __name__ == "__main__":
    print("🎭 Mafia Bot ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    print("🎭 Mafia Bot ishga tushdi...")
    bot.remove_webhook()   # ← shu qatorni qo'shing
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
