import os

# Bot token - Render environment variable da qo'ying
BOT_TOKEN = os.getenv("8840892305:AAExPeCpVhH5a4i46kPF9jPpIJvFZxxUGXc", "8840892305:AAExPeCpVhH5a4i46kPF9jPpIJvFZxxUGXc")

# BB (asosiy bot) API
BB_API_URL = os.getenv("BB_API_URL", "http://your-bb-server.onrender.com")
BB_API_KEY = os.getenv("BB_API_KEY", "your_secret_key")

# O'yin sozlamalari
MIN_PLAYERS = 3
MAX_PLAYERS = 30

JOIN_TIMEOUT = 60       # Qo'shilish vaqti (sekund)
NIGHT_TIMEOUT = 45      # Tun vaqti (sekund)
LAST_WORDS_TIMEOUT = 60 # Oxirgi so'z vaqti (sekund)
VOTE_TIMEOUT = 45       # Ovoz berish vaqti (sekund)

# G'olib uchun mukofot (BB pul)
WIN_REWARD = 50
LOSE_REWARD = 0

# GIF havolalari (o'zingiznikini qo'ying)
GIF_NIGHT = "https://media.giphy.com/media/night.gif"
GIF_DAY = "https://media.giphy.com/media/day.gif"
GIF_START = "https://media.giphy.com/media/start.gif"
