import asyncio
import requests
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
TOKEN = "7683602550:AAEkXyWgUbmbHO3dL3SwHj9X-dozMdnjE9A"  # Tokenni o'zgartiring
API_KEY = "pub_74681e9b6af54da545e4da910e630cc7c3726"
NEWS_URL = f"https://newsdata.io/api/1/news?apikey={API_KEY}&country=UZ&language=uz"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

latest_news_id = None  # Oxirgi yangilik ID sini saqlash

# Database connection
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

async def get_news():
    global latest_news_id
    logging.info("Yangiliklar olinmoqda...")
    response = requests.get(NEWS_URL)
    if response.status_code != 200:
        logging.error("Newsdata.io API ishlamadi!")
        return None
    data = response.json()
    if not data.get("results"):
        return None
    article = data["results"][0]  # Faqat 1 ta yangilik
    news_id = article.get("article_id")  # Yangilik ID si
    if news_id == latest_news_id:
        return None  # Yangilik avvalgisi bilan bir xil bo'lsa, yubormaymiz
    latest_news_id = news_id
    title = article.get("title", "❓ Noma'lum sarlavha")
    description = article.get("description", "ℹ️ Batafsil ma'lumot yo'q")
    image_url = article.get("image_url", None)
    return title, description, image_url

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    await message.answer("📰 <b>Assalomu alaykum!</b> 🇺🇿\n\n📢 <i>O‘zbekiston yangiliklari botiga xush kelibsiz!</i>\n\n🔍 <b>Yangiliklarni olish uchun</b> /news buyrug'ini bosing!", parse_mode="HTML")

@dp.message_handler(commands=["news"])
async def send_news(message: types.Message):
    news = await get_news()
    if not news:
        await message.answer("🚫 Hozircha yangiliklar topilmadi.")
        return
    title, description, image_url = news
    text = f"📰 <b>{title}</b>\n\n📌 {description}\n\n✅ <i>Eng so‘nggi yangiliklar!</i>"
    if image_url:
        await message.answer_photo(photo=image_url, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")

async def auto_send_news():
    while True:
        await asyncio.sleep(600)  # Har 10 daqiqada tekshirish
        news = await get_news()
        if news:
            title, description, image_url = news
            text = f"📰 <b>{title}</b>\n\n📌 {description}\n\n✅ <i>Eng so‘nggi yangiliklar!</i>"
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            for user in users:
                user_id = user[0]
                try:
                    if image_url:
                        await bot.send_photo(user_id, photo=image_url, caption=text, parse_mode="HTML")
                    else:
                        await bot.send_message(user_id, text, parse_mode="HTML")
                except Exception as e:
                    logging.error(f"Xatolik: {e}")

async def main():
    asyncio.create_task(auto_send_news())
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())