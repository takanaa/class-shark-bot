import telebot
from config import token

# Создание бота
bot = telebot.TeleBot(token)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcomText = "Привет!\n\nЧтобы начать пользоваться ботом, необходимо зарегистрироваться, отправляй команду /register\n\nЧтобы узнать о всех функциях бота, отправляй /help"
    bot.send_message(chat_id, welcomText)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    helpText = "Вот основные функции бота:\n\n/register -- Регистрация в системе бота\n/login -- Вход в систему бота\n/logout -- Выход из системы\n/predict -- Определение класса объекта на картинке. Пользоваться функцией могут только заригестрированные и авторизованные пользователи"
    bot.send_message(chat_id, helpText)

# Обработчик команды /register
@bot.message_handler(commands=['register'])
def register(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите пароль для регистрации:")
    # Сохраняем пароль пользователя

# Обработчик команды /login
@bot.message_handler(commands=['login'])
def login(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")

# Обработчик команды /predict
@bot.message_handler(commands=['predict'])
def predict(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Сначала войдите с помощью /login.")

# Обработчик команды /logout
@bot.message_handler(commands=['logout'])
def logout(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Сначала войдите с помощью /login.")

#Non-stop working mode
bot.infinity_polling()
