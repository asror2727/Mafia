import telebot
import threading
import os
from config import BOT_TOKEN
from handlers import register_handlers

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

register_handlers(bot)

if __name__ == "__main__":
    print("🎭 Mafia Bot ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
