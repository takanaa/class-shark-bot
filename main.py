import telebot # Работа с ботом
import csv # Работа с базой пользователей
import tensorflow as tf
from config import token, model

# Создание бота
bot = telebot.TeleBot(token)
model = tf.keras.models.load_model(model)

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
    user_id = message.from_user.id
    ID, row = find_user(user_id)
    if row == None:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    elif row['Status'] == '1':
        bot.send_message(chat_id, "Вы уже авторизованы.\n\nЧтобы воспользоваться классификатором, введите команду /predict\nЧтобы выйти из системы, введите команду /logout")
    else:
        bot.send_message(chat_id, f"Здравствуйте, {row['Username']}!\n\nВведите пароль")
        bot.register_next_step_handler(message, valid_password, row, 5)

# Обработчик команды /predict
@bot.message_handler(commands=['predict'])
def predict(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    ID, row = find_user(user_id)
    if row == None:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    elif row['Status'] == '0':
        bot.send_message(chat_id, "Сначала войдите с помощью /login.")
    else:
        bot.send_message(chat_id, "Пришлите фотографию")
        bot.register_next_step_handler(message, recog_image, 1)

# Обработчик команды /logout
@bot.message_handler(commands=['logout'])
def logout(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    ID, row = find_user(user_id)
    if row == None:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью /register.")
    else:
        if row['Status'] == '0':
            bot.send_message(chat_id, "Сначала войдите с помощью /login.")
        else:
            update_user(user_id, 0)
            bot.send_message(chat_id, f"До свидания, {row['Username']}! До новых встреч!")

def find_user(user_id):
    user_count = 0
    try:
        with open('base/users.csv', 'r', encoding='utf-8') as base:
            reader = csv.DictReader(base)  # Читаем как словарь (удобно для работы с колонками)
            for row in reader:
                user_count = user_count + 1
                if row['User_ID'] == str(user_id):
                    return row['ID'], row
        return user_count + 1, None
    except PermissionError:
        print("Нет прав на запись в файл!")
    except csv.Error as e:
        print(f"Ошибка парсинга CSV: {e}")
    except Exception as e:
        print(e)

def add_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.username
    password = message.text
    ID, row = find_user(user_id)
    try:
        if row == None:
            with open('base/users.csv', 'a', newline='', encoding='utf-8') as base:
                writer = csv.writer(base)
                writer.writerow([ID, user_id, chat_id, user_name, password, 0])
            bot.send_message(chat_id, "Поздравляю, вы успешно зарегистрированы!\n\nЧтобы войти в систему введите команду /login")
        else:
            bot.send_message(chat_id, "Вы уже ранее были зарегистрированы")
    except PermissionError:
        print("Нет прав на запись в файл!")
    except csv.Error as e:
        print(f"Ошибка парсинга CSV: {e}")
    except Exception as e:
        print(e)


def update_user(user_id, new_status):
    rows = []
    with open('base/users.csv', 'r', encoding='utf-8') as base:
        reader = csv.DictReader(base)
        for row in reader:
            if row['User_ID'] == str(user_id):
                row['Status'] = new_status
            rows.append(row)
    # Перезаписываем файл
    with open('base/users.csv', 'w', newline='', encoding='utf-8') as base:
        writer = csv.DictWriter(base, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def valid_password(message, row, step):
    chat_id = message.chat.id
    user_id = message.from_user.id
    password = message.text
    if password == row['Password']:
        update_user(user_id, 1)
        bot.send_message(chat_id, "Поздравляю, вы успешно вошли в систему!\n\nЧтобы воспользоваться классификатором, введите команду /predict\nЧтобы закончить работу, введите команду /logout")
    else:
        if step == 0:
            bot.send_message(chat_id, "Пароль неверный. Повторите попытку позже, когда вспомните пароль...")
        else:
            step = step - 1
            bot.send_message(chat_id, f"Пароль неверный. Повторите попытку ещё раз.\n\nОсталось попыток: {step}")
            bot.register_next_step_handler(message, valid_password, row, step)

def recog_image(message, step):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.photo:
        try:
            # Берём фото в максимальном качестве
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Сохраняем в папку `photos`
            image = f"photos/{message.from_user.id}.jpg"
            
            with open(image, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.send_message(chat_id, "Hey bro, nice pic")

            img = tf.keras.preprocessing.image.load_img(image, target_size=(200, 200))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.expand_dims(img_array, 0)  # Create batch axis
            predictions = model.predict(img_array)
            # Определение класса изображения
            if predictions[0] < 0.5:
                prediction_text = "акула"
            else:
                prediction_text = "человек"
            bot.send_message(message.chat.id,f'Это {prediction_text}')
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")
    else:
        if step == 1:
            step = step - 1
            bot.send_message(chat_id, "Я же просил картинку :(\nПопробуй ещё раз")
            bot.register_next_step_handler(message, recog_image, step)
        elif step == 0:
            bot.send_message(chat_id, "Это опять не картинка. Поговорим потом")

#Non-stop working mode
bot.infinity_polling()
