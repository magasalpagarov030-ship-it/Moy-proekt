from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import User, ShortLink
import bcrypt
import telebot
import random
import string
# 🔹 Временная функция, чтобы получить chat_id группы
def get_chat_id_demo():
    import telebot

    BOT_TOKEN = "8223028525:AAH4vKgBbGFz7fh9fyWpoFR4Kx17qI8GQPw"
    bot = telebot.TeleBot(BOT_TOKEN)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        print(f"✅ Chat ID этой группы: {message.chat.id}")
        bot.reply_to(message, f"Ваш Chat ID: {message.chat.id}")

    print("🤖 Бот запущен. Напиши что-нибудь в Telegram-группу.")
    bot.polling()

# === Настройки Telegram ===
BOT_TOKEN = "8223028525:AAH4vKgBbGFz7fh9fyWpoFR4Kx17qI8GQPw"
GROUP_CHAT_ID = "-1003284328559"

bot = telebot.TeleBot(BOT_TOKEN)

# === Инициализация БД ===
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Short Link Service + Telegram Auth")

# === Сессия БД ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Генерация случайного кода ===
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

# === Генерация короткой ссылки ===
def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# === Регистрация пользователя ===
@app.post("/register")
def register(phone: str, password: str, telegram_id: str, db: Session = Depends(get_db)):
    if len(password) > 72:
        password = password[:72]

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(phone=phone, hashed_password=hashed_pw, telegram_id=telegram_id)
    db.add(user)
    db.commit()

    bot.send_message(GROUP_CHAT_ID, f"📱 Новый пользователь: {phone}")

    return {"message": "✅ Пользователь успешно зарегистрирован"}

# === Запрос кода ===
@app.post("/get_code")
def get_code(phone: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Пользователь не найден")

    code = generate_code()
    user.verification_code = code
    db.commit()

    # Отправляем код в Telegram-группу
    bot.send_message(GROUP_CHAT_ID, f"🔐 Код для {phone}: {code}")

    return {"message": "📨 Код отправлен в Telegram-группу"}

# === Авторизация по коду ===
@app.post("/login_with_code")
def login_with_code(phone: str, code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == phone).first()
    if not user or user.verification_code != code:
        raise HTTPException(status_code=400, detail="❌ Неверный код")

    bot.send_message(GROUP_CHAT_ID, f"✅ Успешная авторизация: {phone}")
    return {"message": f"Добро пожаловать, {phone}!"}

# === Создание короткой ссылки ===
@app.post("/shorten")
def shorten_link(phone: str, original_url: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Пользователь не найден")

    short_code = generate_short_code()
    short_link = ShortLink(original_url=original_url, short_code=short_code, owner_phone=phone)
    db.add(short_link)
    db.commit()

    bot.send_message(GROUP_CHAT_ID, f"🔗 Новый линк от {phone}: /{short_code}")
    return {"short_url": f"http://127.0.0.1:8000/{short_code}"}

# === Переход по короткой ссылке ===
@app.get("/{short_code}")
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(ShortLink).filter(ShortLink.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="❌ Ссылка не найдена")

    link.clicks += 1
    db.commit()

    return {"original_url": link.original_url, "clicks": link.clicks}
