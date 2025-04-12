import telebot # Работа с ботом
import csv # Работа с базой пользователей
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
    bot.register_next_step_handler(message, add_user)

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

def find_user(user_id):
    user_count = 0
    with open('base/users.csv', 'r', encoding='utf-8') as base:
        reader = csv.DictReader(base)  # Читаем как словарь (удобно для работы с колонками)
        for row in reader:
            user_count = user_count + 1
            if row['User_ID'] == str(user_id):
                return row['ID'], row
    return user_count + 1, None

def add_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.username
    password = message.text
    try:
        ID, row = find_user(user_id)
        if row == None:
            with open('base/users.csv', 'a', newline='', encoding='utf-8') as base:
                writer = csv.writer(base)
                writer.writerow([ID, user_id, chat_id, user_name, password])
            bot.send_message(chat_id, "Поздравляю, вы успешно зарегистрированы!")
        else:
            bot.send_message(chat_id, "Вы уже ранее были зарегистрированы")
    except PermissionError:
        print("Нет прав на запись в файл!")
    except csv.Error as e:
        print(f"Ошибка парсинга CSV: {e}")
    except Exception as e:
        print(e)

#Non-stop working mode
bot.infinity_polling()
