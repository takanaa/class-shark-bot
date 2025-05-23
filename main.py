from telebot import types, TeleBot # Работа с ботом
import tensorflow as tf
from config import token, model, webhook_url, main_admins
from flask import Flask, request
import mysql.connector
from mysql.connector import Error
import hashlib
import uuid
import os
from PIL import Image

# Создание бота
bot = TeleBot(token)
model = tf.keras.models.load_model(model)

# Flask приложение
app = Flask(__name__)

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
    helpText = "Вот основные функции бота:\n\n/register -- Регистрация в системе бота\n/login -- Вход в систему бота\n/logout -- Выход из системы\n/predict -- Определение класса объекта на картинке. Пользоваться функцией могут только заригестрированные и авторизованные пользователи\n/admin -- Панель админа для управления пользователями. Функция доступна только администраторам бота"
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
    user_id = message.from_user.id
    stat = find_user(user_id)
    if stat == -1:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    elif stat == 1:
        bot.send_message(chat_id, "Вы уже авторизованы.\n\nЧтобы воспользоваться классификатором, введите команду /predict\nЧтобы выйти из системы, введите команду /logout")
    else:
        bot.send_message(chat_id, f"Здравствуйте, {message.from_user.username}!\n\nВведите пароль")
        bot.register_next_step_handler(message, valid_password, 5)

# Обработчик команды /predict
@bot.message_handler(commands=['predict'])
def predict(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    stat = find_user(user_id)
    if stat == -1:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    elif stat == 0:
        bot.send_message(chat_id, "Сначала войдите с помощью /login.")
    else:
        bot.send_message(chat_id, "Пришлите фотографию")
        bot.register_next_step_handler(message, recog_image, 1)

# Обработчик команды /logout
@bot.message_handler(commands=['logout'])
def logout(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    stat = find_user(user_id)
    if stat == -1:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    else:
        if stat == 0:
            bot.send_message(chat_id, "Сначала войдите с помощью /login.")
        else:
            update_user(user_id, 0)
            bot.send_message(chat_id, f"До свидания, {message.from_user.username}! До новых встреч!")

# Обработчик команды /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admin = admin_stat(user_id)
    if admin == 1:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # one_time_keyboard=True – клавиатура скроется после нажатия
        markup.add(types.KeyboardButton("Список пользователей"))
        markup.add(types.KeyboardButton("Добавить администратора"))
        markup.add(types.KeyboardButton("Удалить пользователя"))
        bot.send_message(message.chat.id, "Выберете действие с пользователями", reply_markup=markup)
        bot.register_next_step_handler(message, admin_options)
    elif admin == -1:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    else:
        bot.send_message(chat_id, "У вас нет прав, чтобы воспользоваться этой командой\n\nТребуется роль администратора. Запросите права администратора у ")

def admin_options(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    option = message.text.strip()
    all_users = get_users()
    if (option == "Список пользователей"):
        users_list = "Все пользователи бота:\n"
        for user in all_users:
            users_list = users_list + "@" + user['username'].strip() + " : " + str(user['predictions']) + " predictions"
            if user['admin'] == 1:
                users_list = users_list + " (admin)\n"
            else:
                users_list = users_list + "\n"
        bot.send_message(chat_id, users_list)
    elif (option == "Добавить администратора"):
        users_list = "Введите username пользователя, которого хотите сделать администратором:\n"
        for user in all_users:
            users_list = users_list + "@" + user['username'].strip()
            if user['admin'] == 1:
                users_list = users_list + " (admin)\n"
            else:
                users_list = users_list + "\n"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, users_list, reply_markup=markup)
        bot.register_next_step_handler(message, make_admin)
    elif (option == "Удалить пользователя"):
        users_list = "Введите username пользователя, которого хотите удалить:\n"
        for user in all_users:
            users_list = users_list + "@" + user['username'].strip()
            if user['admin'] == 1:
                users_list = users_list + " (admin)\n"
            else:
                users_list = users_list + "\n"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, users_list, reply_markup=markup)
        bot.register_next_step_handler(message, delete_user)
    else:
        bot.send_message(chat_id, "Неверная опция администратора")

def get_users():
    """ Получить список всех пользователей """
    connection = connect_db()
    if connection is None:
        return None, "Database connection failed"
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, predictions, admin FROM users")
        current_user = cursor.fetchall()
        if current_user:
            return current_user
        else:
            return -1
    except Error as e:
        connection.rollback()
        print(f"Error fetching users: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def make_admin(message):
    """ Обновляет статус администратора """
    username = message.text.strip()
    if (username == "Отмена"):
        return
    connection = connect_db()
    if connection is None:
        print("Database connection failed")
    cursor = connection.cursor(dictionary=True)
    try:
        if username[0] == '@':
            username = username[1:]
        update_query = "UPDATE users SET admin = %s WHERE username = %s"
        cursor.execute(update_query, ("1", str(username)))
        connection.commit()
        if cursor.rowcount == 0:
            print("Admin status wasn't updated")
        else:
            cursor.execute("SELECT id, user FROM users WHERE username = %s", (str(username),))
            new_admin = cursor.fetchone()
            bot.send_message(new_admin['user'], "Вас назначили администратором. Теперь вам доступна команда /admin")
            print(f"User {username} is admin now")
    except Error as e:
        connection.rollback()
        print(f"Error updating status: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_user(message):
    """ Удаляет пользователя """
    username = message.text.strip()
    if (username == "Отмена"):
        return
    connection = connect_db()
    if connection is None:
        print("Database connection failed")
    cursor = connection.cursor(dictionary=True)
    try:
        if username[0] == '@':
            username = username[1:]
        cursor.execute("SELECT id, user FROM users WHERE username = %s", (str(username),))
        old_user = cursor.fetchone()
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        connection.commit()
        if cursor.rowcount == 0:
            print("User wasn't deleted")
        else:
            bot.send_message(old_user['user'], "Вас выгнали из рая. Придётся зарегистрироваться ешё раз: /register")
            print(f"User {username} deleted")
    except Error as e:
        connection.rollback()
        print(f"Error deleting user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def admin_stat(user_id):
    """
    Поиск пользователя в базе данных
    Возвращает статус админа: 1 -- если админ; 0 -- если нет
    -1 -- пользователь не найден
    """
    connection = connect_db()
    if connection is None:
        return None, "Database connection failed"
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, admin FROM users WHERE user = %s", (str(user_id),))
        current_user = cursor.fetchone()
        if current_user:
            return int(current_user['admin'])
        else:
            return -1
    except Error as e:
        connection.rollback()
        print(f"Error setting admin status: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def find_user(user_id):
    """
    Поиск пользователя в базе данных
    Возвращает статус пользователя или -1, если пользователь ещё не зарегистрирован
    """
    connection = connect_db()
    if connection is None:
        return None, "Database connection failed"
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, status FROM users WHERE user = %s", (str(user_id),))
        current_user = cursor.fetchone()
        if current_user:
            return int(current_user['status'])
        else:
            return -1
    except Error as e:
        connection.rollback()
        print(f"Error finding user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_user(message):
    """ Добавляет нового пользователя в систему """
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    password = hash_pass(message.text.strip())
    connection = connect_db()
    if connection is None:
        return None, "Database connection failed"
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE user = %s", (str(user_id),))
        if cursor.fetchone():
            bot.send_message(chat_id, "Вы уже ранее были зарегистрированы")
            return

        insert_query = "INSERT INTO users (user, username, password) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (str(user_id), str(username), password))
        connection.commit()
        for main_adm in main_admins:
            if str(user_id) == main_adm:
                update_query = "UPDATE users SET admin = 1 WHERE username = %s"
                cursor.execute(update_query, (str(username),))
                connection.commit()
        print("New user registered")
        bot.send_message(chat_id, "Поздравляю, вы успешно зарегистрированы!\n\nЧтобы войти в систему введите команду /login")
    except Error as e:
        connection.rollback()
        print(f"Error adding user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_user(user_id, new_status):
    """ Обновляет статус пользователя """
    connection = connect_db()
    if connection is None:
        print("Database connection failed")
    cursor = connection.cursor(dictionary=True)
    try:
        update_query = "UPDATE users SET status = %s WHERE user = %s"
        cursor.execute(update_query, (str(new_status), str(user_id)))
        connection.commit()
        if cursor.rowcount == 0:
            print("Status wasn't updated")
    except Error as e:
        connection.rollback()
        print(f"Error updating status: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_predict_counter(user_id):
    """ Инкрементирует счётчик """
    connection = connect_db()
    if connection is None:
        print("Database connection failed")
    cursor = connection.cursor(dictionary=True)
    try:
        update_query = "UPDATE users SET predictions = predictions + 1 WHERE user = %s"
        cursor.execute(update_query, (str(user_id),))
        connection.commit()
        if cursor.rowcount == 0:
            print("Counter wasn't updated")
    except Error as e:
        connection.rollback()
        print(f"Error updating counter: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def valid_password(message, step):
    """ Получает пароль от пользователя и проверяет его """
    chat_id = message.chat.id
    user_id = message.from_user.id
    password = message.text

    connection = connect_db()
    if connection is None:
        return None, "Database connection failed"
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password FROM users WHERE user = %s", (str(user_id),))
        current_user = cursor.fetchone()
        if current_user:
            if check_hash_pass(current_user['password'], password):
                update_user(user_id, 1)
                bot.send_message(chat_id, "Поздравляю, вы успешно вошли в систему!\n\nЧтобы воспользоваться классификатором, введите команду /predict\nЧтобы закончить работу, введите команду /logout")
            else:
                if step == 0:
                    bot.send_message(chat_id, "Пароль неверный. Повторите попытку позже, когда вспомните пароль...")
                else:
                    step = step - 1
                    bot.send_message(chat_id, f"Пароль неверный. Повторите попытку ещё раз.\n\nОсталось попыток: {step}")
                    bot.register_next_step_handler(message, valid_password, step)
    except Error as e:
        connection.rollback()
        print(f"Error finding user: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def hash_pass(password):
    """ Функция хэширования паролей """
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_hash_pass(hash_password, user_password):
    """ Проверка хэшированного пароля """
    password, salt = hash_password.split(':')
    if password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest():
        return 1
    else:
        return 0

def recog_image(message, step):
    """ Распознаёт изображение на фотографии """
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.photo:
        try:
            # Берём фото в максимальном качестве
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Сохраняем в папку `photos`
            image_dir = "photos"  # Название папки
            os.makedirs(image_dir, exist_ok=True)  # Создаём папку, если её нет
            image = os.path.join(image_dir, f"{message.from_user.id}.jpg")
            
            with open(image, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.send_message(chat_id, "Hey bro, nice pic")
 
            img = Image.open(image)  # Проверка, что изображение валидно
            img = img.resize((200, 200))  # Ресайз
            img = tf.keras.preprocessing.image.load_img(image, target_size=(200, 200))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.expand_dims(img_array, 0) / 255.0 # Create batch axis
            predictions = model.predict(img_array, verbose=0)
            probability = float(predictions[0][0])  # Преобразуем numpy.float32 в обычный float
            percent = round(probability * 100, 2)  # Преобразуем в проценты с 2 знаками после запятой

            # Определение класса изображения с выводом вероятности
            if probability >= 0.7:  # человек
                bot.send_message(message.chat.id,
                                 f"На картинке человек (вероятность: {probability:.2f})")
            elif probability <= 0.2:  # акула
                bot.send_message(message.chat.id,
                                 f"На картинке акула! (Вероятность: {1 - probability:.2f})")
            else:
                bot.send_message(message.chat.id,
                                 f"Не уверен... Вероятность: {probability:.2f}. Может быть хот-дог?")
            update_predict_counter(user_id)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")
    else:
        if step == 1:
            step = step - 1
            bot.send_message(chat_id, "Я же просил картинку :(\nПопробуй ещё раз")
            bot.register_next_step_handler(message, recog_image, step)
        elif step == 0:
            bot.send_message(chat_id, "Это опять не картинка. Поговорим потом")

# Webhook setup
@app.route("/webhook", methods=["GET", "POST"])
def webhook_handler():
    if request.method == "GET":
        return "Webhook works", 200
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK', 200
    
@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        return "It's a home page", 200
    return 'OK', 200


def connect_db():
    """ Функция подключения к базе данных """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='baby_shark',
            user='root',
            password='0000'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """ Инициализирует базу данных """
    try:
        connection = connect_db()
        if connection.is_connected():
            cursor = connection.cursor()

            # Создание таблицы
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(100) NOT NULL UNIQUE COMMENT 'Telegram user id',
                username VARCHAR(100) NOT NULL UNIQUE COMMENT 'Telegram chat id',
                password TEXT COMMENT 'Password after hash func',
                status INT DEFAULT 0 COMMENT 'If user is logged in',
                predictions INT DEFAULT 0 COMMENT 'Count of predictions',
                admin INT DEFAULT 0 COMMENT 'If user id admin'
            )
            """)
            connection.commit()
            print("Table was done successfully.")

    except Error as e:
        print(f"MySQL error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    init_db()
    bot.remove_webhook()
    print(f"    (DEBUG)    {webhook_url}")
    bot.set_webhook(url=webhook_url)
    app.run(host='127.0.0.1', port=8000)