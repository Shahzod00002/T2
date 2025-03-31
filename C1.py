
import telebot
import sqlite3
import os
import uuid
from telebot import types
from datetime import datetime

ADMIN_CHAT_ID = 1966713544 # Замените на настоящий chat_id администратора
# Создание экземпляра бота
API_TOKEN = '7603865848:AAFyUS_D7XqKR6eUkvhsJHZnCSDflOKnotA'
bot = telebot.TeleBot(API_TOKEN)

def create_action_log_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_log (
            user_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()



# Функция для создания таблицы заказов с номером
def create_orders_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_number TEXT,
            total_price REAL,
            status TEXT DEFAULT 'waiting',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Функция для создания соединения с базой данных
def create_connection():
    conn = sqlite3.connect(r'/home/shah2003/T1/bot1 (4).db')  # Укажите свой путь к базе данных
    return conn
# Функция для добавления нового столбца в таблицу
def add_order_number_column():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            ALTER TABLE orders ADD COLUMN order_number TEXT
        ''')
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

add_order_number_column()
# Функция для генерации уникального номера заказа
def generate_order_number():
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
# Функция для добавления заказа
def create_order(user_id, total_price):
    order_number = generate_order_number()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, order_number, total_price)
        VALUES (?, ?, ?)
    ''', (user_id, order_number, total_price))
    conn.commit()
    conn.close()

    return order_number

def log_user_action(user_id, action):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO action_log (user_id, action)
        VALUES (?, ?)
    ''', (user_id, action))
    conn.commit()
    conn.close()

# Путь к файлу для хранения истории действий
log_file_path = 'user_actions_log.txt'

# Функция для записи действий пользователя в текстовый файл
def log_user_action(user_id, action, ):
    # Открываем файл в режиме добавления
    with open(log_file_path, 'a', encoding='utf-8') as file:
        # Получаем текущую дату и время
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Формируем строку для записи
        log_entry = f"{current_time} | User ID: {user_id} | Action: {action}\n"

        # Записываем в файл
        file.write(log_entry)


@bot.message_handler(commands=['v'])
def view_user_actions(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM action_log ORDER BY timestamp DESC')
    actions = cursor.fetchall()
    conn.close()

    if not actions:
        bot.send_message(message.chat.id, "Нет доступных действий.")
        return

    action_text = "История действий пользователей:\n"
    for action in actions:
        user_id, action_name, timestamp = action
        action_text += f"ID: {user_id}, Действие:\ {action_name}, Время: {timestamp}\n"

    bot.send_message(message.chat.id, action_text)

# Подключение к базе данных
def create_connection():
    conn = sqlite3.connect(r'/home/shah2003/T1/bot1 (4).db')
    return conn
def add_frozen_column():
    conn = create_connection()
    cursor = conn.cursor()

    # Проверяем, есть ли уже столбец frozen
    cursor.execute("PRAGMA table_info(menu)")
    columns = cursor.fetchall()

    # Если столбец frozen не найден, добавляем его
    if not any(column[1] == "frozen" for column in columns):
        cursor.execute('ALTER TABLE menu ADD COLUMN frozen INTEGER DEFAULT 0')  # Добавляем столбец frozen
        conn.commit()
    conn.close()
# Функция для добавления или обновления данных пользователя
def add_user_data(user_id, phone, address):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO users (id, phone, address)
                      VALUES (?, ?, ?)''', (user_id, phone, address))
    conn.commit()
    conn.close()

# Функция для добавления блюда в корзину
def add_to_cart(user_id, dish_name, price):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO cart (user_id, dish_name, price) VALUES (?, ?, ?)''', (user_id, dish_name, price))
    conn.commit()
    conn.close()

# Логируем действие
    log_user_action(user_id, f"Добавил в корзину блюдо: {dish_name}")
# Функция для получения корзины пользователя
def get_cart(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cart WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

# Get menu items that are not frozen
def get_menu():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu WHERE frozen = 0')  # Only available dishes
    items = cursor.fetchall()
    conn.close()
    return items

# Function to freeze a dish (set frozen = 1)
@bot.message_handler(func=lambda message: message.text == "Заморозить")
def freeze_dish(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    bot.send_message(message.chat.id, "Введите название блюда, которое вы хотите заморозить:")

    # Ask for the dish name
    bot.register_next_step_handler(message, freeze_dish_step)

def freeze_dish_step(message):
    dish_name = message.text

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu WHERE name = ?', (dish_name,))
    dish = cursor.fetchone()

    if dish:
        cursor.execute('UPDATE menu SET frozen = 1 WHERE name = ?', (dish_name,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"Блюдо '{dish_name}' теперь он заморожен и недоступен.")
    else:
        conn.close()
        bot.send_message(message.chat.id, "Этого блюда нет в меню.")

# Function to unfreeze a dish (set frozen = 0)
@bot.message_handler(func=lambda message: message.text == "Разморозить")
def unfreeze_dish(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    bot.send_message(message.chat.id, "Введите название блюда, которое вы хотите разморозить:")

    # Ask for the dish name
    bot.register_next_step_handler(message, unfreeze_dish_step)

def unfreeze_dish_step(message):
    dish_name = message.text

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu WHERE name = ?', (dish_name,))
    dish = cursor.fetchone()

    if dish:
        cursor.execute('UPDATE menu SET frozen = 0 WHERE name = ?', (dish_name,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"Блюдо '{dish_name}' теперь он снова доступен.")
    else:
        conn.close()
        bot.send_message(message.chat.id, "Этого блюда нет в меню.")

# Function to add a dish to the cart
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart_'))
def add_to_cart_handler(call):
    data = call.data.split('_')

    if len(data) < 5:
        bot.send_message(call.message.chat.id, "Ошибка при добавлении блюда в корзину. Неверный формат данных.")
        return

    dish_name = data[3]
    try:
        price = float(data[4])
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка при расчете цены блюда. Пожалуйста, попробуйте снова.")
        return

    # Check if the dish is frozen
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT frozen FROM menu WHERE name = ?', (dish_name,))
    dish_status = cursor.fetchone()
    conn.close()

    if dish_status and dish_status[0] == 1:  # Dish is frozen
        bot.send_message(call.message.chat.id, f"Блюдо '{dish_name}' временно недоступен. Пожалуйста, выберите другой вариант.")
    else:
        user_id = call.message.chat.id
        try:
            add_to_cart(user_id, dish_name, price)
            bot.send_message(call.message.chat.id, f"Блюдо '{dish_name}' было добавлено в вашу корзину.")
        except Exception as e:
            bot.send_message(call.message.chat.id, "При добавлении блюда в корзину произошла ошибка. Пожалуйста, повторите попытку позже.")
            print(f"Ошибка при добавлении в корзину: {e}")

# Функция для показа замороженных блюд
@bot.message_handler(func=lambda message: message.text == "Список замороженных блюд📜")
def show_frozen_dishes(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    # Получаем список всех замороженных блюд
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu WHERE frozen = 1')  # Только замороженные блюда
    frozen_dishes = cursor.fetchall()
    conn.close()

    if not frozen_dishes:
        bot.send_message(message.chat.id, "В данный момент никакие блюда не замораживаются.")
        return

    # Отправляем список замороженных блюд
    frozen_text = "Заморожение блюды:\n"
    for dish in frozen_dishes:
        frozen_text += f"{dish[1]} - {dish[2]} руб.\n"  # Предполагаем, что dish[1] - название и dish[2] - цена
    bot.send_message(message.chat.id, frozen_text)


@bot.message_handler(func=lambda message: message.text == "Разморозить все блюды")
def unfreeze_all_dishes(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    # Обновляем все замороженные блюда, устанавливая frozen = 0
    cursor.execute('UPDATE menu SET frozen = 0 WHERE frozen = 1')
    conn.commit()

    # Проверяем, сколько строк было обновлено
    if cursor.rowcount > 0:
        bot.send_message(message.chat.id, f"Все замороженные блюда ({cursor.rowcount} шт.) были разморожены.")
    else:
        bot.send_message(message.chat.id, "Нет замороженных блюд для разморозки.")

    conn.close()

# Function to unfreeze all dishes (set frozen = 0)
@bot.message_handler(func=lambda message: message.text == "Заморозить все блюды")
def unfreeze_all_dishes(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    # Подключаемся к базе данных
    conn = create_connection()
    cursor = conn.cursor()

    # Обновляем все замороженные блюда (frozen = 1) на доступные (frozen = 0)
    cursor.execute('UPDATE menu SET frozen = 1 WHERE frozen = 0')
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Все  блюда теперь недоступны.")
# Обработчик команды /start

def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    menu_button = types.KeyboardButton("📋Меню")
    b1 = types.KeyboardButton("Указать номер 📱 и 🏠 адрес")
    b2 = types.KeyboardButton("🛒Корзина")
    b3 = types.KeyboardButton("🗑Очистить корзину")
    b5 = types.KeyboardButton("💳Оплатить")
    b6 = types.KeyboardButton("🏠Указать только адрес")
    b7 = types.KeyboardButton("📩Написать доставщику")
    b8 = types.KeyboardButton("💡Помощь")
    b9 = types.KeyboardButton("Назад")
    admin_button = types.KeyboardButton("Только для 👤Админ")
    markup.add(menu_button)
    markup.add(b1, b2, b3, b5, b6, b7, b8, b9)
    markup.add(admin_button)
    bot.send_message(chat_id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

# Обработчик команды /help
@bot.message_handler(func=lambda message: message.text == "💡Помощь")
def send_help(message):
    bot.send_message(message.chat.id, "Доступные команды:\n"
                                      "/start - Начало работы с ботом\n"
                                      "/order - Указать номер телефона и  адрес доставки\n"
                                      "/menu - Просмотр меню\n"
                                      "/view_cart - Просмотр корзины\n"
                                      "/clear_cart - Очистить корзину\n"
                                       "/help - Помощь\n"
                                      "/pay - Оплатить заказ")



# Функция для запроса номера телефона и адреса перед оформлением заказа
@bot.message_handler(func=lambda message: message.text == "Указать номер 📱 и 🏠 адрес")
def order_start(message):
    bot.send_message(message.chat.id, "Пожалуйста, поделитесь своим контактом (номер телефона):",
                     reply_markup=types.ReplyKeyboardMarkup(
                         one_time_keyboard=True, resize_keyboard=True).add(
                         types.KeyboardButton("Отправить контакт", request_contact=True)))

# Обработчик для получения контакта
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    # Проверяем, что контакт был отправлен
    if message.contact:
        phone = message.contact.phone_number
        bot.send_message(message.chat.id, f"Спасибо! Ваш номер телефона: {phone}. Теперь введите ваш адрес:")
        bot.register_next_step_handler(message, process_order, phone)
    else:
        bot.send_message(message.chat.id, "Не удалось получить ваш контакт. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, order_start)

def process_order(message, phone):
    address = message.text
    user_id = message.chat.id

    # Сохраняем данные пользователя
    add_user_data(user_id, phone, address)

    # После того как данные сохранены, можно показать меню
    bot.send_message(message.chat.id, "Спасибо! Теперь вы можете выбрать блюда из меню.")
    view_menu(message)


def get_menu():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu')
    items = cursor.fetchall()
    conn.close()
    return items
def update_user_address(user_id, new_address):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET address = ? WHERE id = ?''', (new_address, user_id))
    conn.commit()
    conn.close()

def get_user_address(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT address FROM users WHERE id = ?', (user_id,))
    address = cursor.fetchone()
    conn.close()
    return address[0] if address else None

# Функция для добавления блюда в меню
def add_menu_item(name, price):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO menu (name, price)
                      VALUES (?, ?)''', (name, price))
    conn.commit()
    conn.close()

# Функция для удаления блюда
def delete_menu_item(dish_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM menu WHERE name = ?''', (dish_name,))
    conn.commit()
    conn.close()
# Функция для отправки команд администратору
@bot.message_handler(func=lambda message: message.text == "Только для 👤Админ")
def admin(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "Вы не имеете доступа к админским командам.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton("Добавить блюдо в меню🍽️")
    itembtn2 = types.KeyboardButton("Удалить блюдо из меню❌")
    itembtn3 = types.KeyboardButton("Заморозить")
    itembtn4 = types.KeyboardButton("Разморозить")
    itembtn5 = types.KeyboardButton("Заморозить все блюды")
    itembtn6 = types.KeyboardButton("Разморозить все блюды")
    itembtn7 = types.KeyboardButton("Список замороженных блюд📜")
    itembtn8 = types.KeyboardButton("Написать доставщику")
    back_button = types.KeyboardButton("Назад")  # Кнопка назад
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6, itembtn7, itembtn8, back_button)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    main_menu(message.chat.id)  # Возвращаемся в главное меню

# Стартовое сообщение с главным меню
@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)
# Добавление блюда в меню
@bot.message_handler(func=lambda message: message.text == "Добавить блюдо в меню🍽️")
def add_dish_step1(message):
    bot.send_message(message.chat.id, "Введите название блюда:")
    bot.register_next_step_handler(message, add_dish_step2)

def add_dish_step2(message):
    dish_name = message.text
    bot.send_message(message.chat.id, "Введите цену блюда:")
    bot.register_next_step_handler(message, save_dish, dish_name)

def save_dish(message, dish_name):
    price = message.text
    add_menu_item(dish_name, price)
    bot.send_message(message.chat.id, f"Блюдо {dish_name} добавлено в меню с ценой {price}!")


# Удаление блюда из меню
@bot.message_handler(func=lambda message: message.text == "Удалить блюдо из меню❌")
def delete_dish_step1(message):
    bot.send_message(message.chat.id, "Введите название блюда, которое нужно удалить:")
    bot.register_next_step_handler(message, delete_dish_step2)

def delete_dish_step2(message):
    dish_name = message.text
    delete_menu_item(dish_name)
    bot.send_message(message.chat.id,f"Блюдо с названием {dish_name} было удалено из меню.")
# Просмотр меню
@bot.message_handler(func=lambda message: message.text == "📋Меню")
def view_menu(message):
    items = get_menu()  # Получаем список блюд из базы данных

    if not items:
        bot.send_message(message.chat.id, "Меню пока пусто.")
        return

    markup = types.InlineKeyboardMarkup()
    for item in items:
        markup.add(types.InlineKeyboardButton(f"{item[1]} - {item[2]} руб.", callback_data=f"add_to_cart_{item[1]}_{item[2]}"))


    bot.send_message(message.chat.id, "📋Меню:", reply_markup=markup)

# Добавить блюдо в корзину
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart_'))
def add_to_cart_handler(call):
    data = call.data.split('_')

    if len(data) < 5:
        bot.send_message(call.message.chat.id, "Ошибка при добавлении блюда в корзину. Неверный формат данных.")
        return

    dish_name = data[3]
    try:
        price = float(data[4])
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка при обработке цены блюда. Пожалуйста, попробуйте снова.")
        return

    user_id = call.message.chat.id
    try:
        add_to_cart(user_id, dish_name, price)
        bot.send_message(call.message.chat.id, f"Блюдо '{dish_name}' добавлено в вашу корзину.")
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении блюда в корзину. Попробуйте позже.")
        print(f"Ошибка при добавлении в корзину: {e}")

# Просмотр корзины
@bot.message_handler(func=lambda message: message.text == "🛒Корзина")
def view_cart(message):
    user_id = message.chat.id
    cart_items = get_cart(user_id)

    if not cart_items:
        bot.send_message(message.chat.id, "Ваша корзина пуста.")
        return

    cart_text = ""
    total_price = 0
    for item in cart_items:
        cart_text += f"{item[2]} - {item[3]} руб.\n"
        total_price += item[3]

    bot.send_message(message.chat.id, f"Ваша корзина:\n{cart_text}\nОбщая сумма: {total_price} руб.")

# Запрос адреса доставки
@bot.message_handler(func=lambda message: message.text == "🏠Указать только адрес")
def ask_for_address(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш адрес для доставки.")
    bot.register_next_step_handler(message, save_address)

# Сохранение адреса
def save_address(message):
    address = message.text
    user_id = message.chat.id
    update_user_address(user_id, address)
    bot.send_message(message.chat.id, f"Ваш адрес {address} успешно сохранен.")

# Оплата
@bot.message_handler(func=lambda message: message.text == "💳Оплатить")
def payment(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Перевод💳", callback_data='pay_card'))
    markup.add(types.InlineKeyboardButton("Наличными💵", callback_data='pay_cash'))
    markup.add(types.InlineKeyboardButton("Позже🕞", callback_data='pay_later'))
    bot.send_message(message.chat.id, "Способ оплаты:", reply_markup=markup)




# Список курьеров для отправки заказов
courier_chat_ids = [
    5720193588,# chat_id курьера 1
    1587278794,# chat_id курьера 2

]

# Функция для поиска доступных курьеров
def find_available_courier():
    # Здесь можно добавить логику поиска доступного курьера. Пока выберем случайного.
    return courier_chat_ids[0]  # Пример, всегда выбираем первого курьера.

# Функция для отправки сообщения курьеру с номером заказа
def send_order_to_courier(user_id, payment_method):
    cart_items = get_cart(user_id)
    if not cart_items:
        return

    total_price = sum([item[3] for item in cart_items])
    order_number = create_order(user_id, total_price)  # Создаем заказ и получаем номер

    # Получаем номер телефона пользователя из базы данных
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT phone FROM users WHERE id = ?', (user_id,))
    phone_row = cursor.fetchone()
    conn.close()

    # Проверка на наличие телефона
    if phone_row:
        phone = phone_row[0]
    else:
        phone = "Не указан"

    user_address = get_user_address(user_id)

    message = f"Новый заказ:{order_number}\nАдрес: {user_address}\nНомер телефона: +{phone}\nСумма: {total_price} руб.\nСпособ оплаты: {payment_method}\n\nСписок блюд:\n"

    for item in cart_items:
        message += f"{item[2]} - {item[3]} руб.\n"

    # Выбираем доступного курьера
    courier_chat_id = find_available_courier()

    # Отправляем сообщение курьеру с номером заказа
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅Принять", callback_data=f"accept_{user_id}_{order_number}"))
    markup.add(types.InlineKeyboardButton("❌Отклонить", callback_data=f"reject_{user_id}_{order_number}"))

    bot.send_message(courier_chat_id, message, reply_markup=markup)

    # Отправляем номер заказа пользователю
    bot.send_message(user_id, f"Ваш номер заказа : {order_number}.Бот ищет свободного доставщика.Подождите минуту.....")


# Обработчик команды оплаты
@bot.callback_query_handler(func=lambda call: call.data == 'pay_card' or call.data == 'pay_cash' or call.data == 'pay_later')
def payment(call):
    if call.data == 'pay_card':
        payment_method = "Перевод"
    elif call.data == 'pay_cash':
        payment_method = "Наличными"
    elif call.data == 'pay_later':
        payment_method = "Позже"

    user_id = call.message.chat.id



    # Отправляем заказ курьеру
    send_order_to_courier(user_id, payment_method)


# Обработчик для принятия заказа курьером
@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def accept_order(call):
    user_id, order_number = call.data.split('_')[1], call.data.split('_')[2]

    # Сообщаем курьеру, что он принял заказ
    bot.send_message(call.message.chat.id, f"Вы приняли заказ {order_number}.")

    # Отправляем сообщение пользователю
    bot.send_message(user_id, f"Доставщик принял ваш заказ {order_number}. Ожидайте доставщика...")

    # Очистка корзины пользователя
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Обработчик для отклонения заказа курьером
@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_order(call):
    user_id, order_number = call.data.split('_')[1], call.data.split('_')[2]

    # Сообщаем курьеру, что он отклонил заказ
    bot.send_message(call.message.chat.id, f"Вы отклонили заказ {order_number}.")

    # Отправляем сообщение пользователю
    bot.send_message(user_id, f"Доставщик отклонил ваш заказ {order_number}. Попробуйте позже.")

    # Очистка корзины пользователя
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()



# Оплата картой
@bot.callback_query_handler(func=lambda call: call.data == 'pay_card')
def pay_card(call):
    bot.send_message(call.message.chat.id, "Вы выбрали оплату картой.")
    send_order_to_couriers(call.message.chat.id, "Картой")

# Оплата наличными
@bot.callback_query_handler(func=lambda call: call.data == 'pay_cash')
def pay_cash(call):
    bot.send_message(call.message.chat.id, "Вы выбрали оплату наличными.")
    send_order_to_couriers(call.message.chat.id, "Наличными")

# Отложенная оплата
@bot.callback_query_handler(func=lambda call: call.data == 'pay_later')
def pay_later(call):
    bot.send_message(call.message.chat.id, "Вы выбрали отложенную оплату.")
    send_order_to_couriers(call.message.chat.id, "Отложенная оплата")

# Функция для отправки сообщения курьерам
def send_message_to_couriers(message_text):
    courier_chat_ids = [
        6393461209,  # chat_id курьера 1
        5720193588,  # chat_id курьера 2
        1587278794,  # chat_id курьера 3
    ]

    for courier_chat_id in courier_chat_ids:
        try:
            bot.send_message(courier_chat_id, message_text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения курьеру с chat_id {courier_chat_id}: {e}")


# Список chat_id курьеров (это должны быть реальные chat_id курьеров)
COURIER_CHAT_IDS = [6393461209, 5720193588]  # Замените на реальные chat_id курьеров
# Функция для проверки, является ли отправитель курьером
def is_courier(chat_id):
    return chat_id in COURIER_CHAT_IDS

# Команда для курьера отправить сообщение пользователю
# Список chat_id курьеров
courier_chat_ids = [5720193588, 7211194096]

# Функция проверки, является ли пользователь курьером
def is_courier(chat_id):
    return chat_id in courier_chat_ids

# Обработчик сообщений от курьеров (без команды)
@bot.message_handler(func=lambda message: is_courier(message.chat.id))
def message_user(message):
    command_parts = message.text.split(' ', 1)

    if len(command_parts) < 2:
        bot.send_message(message.chat.id, "Введите chat_id пользователя и сообщение через пробел.")
        return

    # Извлекаем chat_id пользователя
    user_chat_id_text, user_message = command_parts

    try:
        user_chat_id = int(user_chat_id_text)
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: chat_id пользователя должен быть числом.")
        return

    # Отправляем сообщение пользователю
    try:
        bot.send_message(user_chat_id, f"🚴‍♂️ *Доставщик:* {user_message}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Сообщение успешно отправлено пользователю *{user_chat_id}.*", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при отправке сообщения: {e}")


# Функция для отправки сообщения курьеру
@bot.message_handler(func=lambda message: message.text == "📩Написать доставщику")
def message_to_courier(message):
    # Проверка, что сообщение отправлено не курьером (если нужно)
    if message.chat.id in courier_chat_ids:
        bot.send_message(message.chat.id, "Вы не можете использовать эту команду, будучи курьером.")
        return

    bot.send_message(message.chat.id, "Введите текст сообщения для курьера:")

    # Регистрация следующего шага, чтобы пользователь мог ввести сообщение
    bot.register_next_step_handler(message, send_message_to_courier)

def send_message_to_courier(message):
    user_message = message.text

    # Выбираем курьера (например, можно всегда отправлять первому курьеру в списке)
    courier_chat_id = courier_chat_ids[0]

    try:
        # Отправляем сообщение курьеру
        bot.send_message(courier_chat_id, f"Сообщение от пользователя *{message.chat.id}:* {user_message}", parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅Ваше сообщение успешно отправлено курьеру!")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при отправке сообщения.")
        print(f"Ошибка при отправке сообщения курьеру: {e}")

# Отправка сообщения курьеру
def send_order_to_couriers(user_id, payment_method):
    cart_items = get_cart(user_id)
    if not cart_items:
        return

    # Получаем номер телефона пользователя из базы данных
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT phone FROM users WHERE id = ?', (user_id,))
    phone_row = cursor.fetchone()
    conn.close()

    # Проверка на наличие телефона
    if phone_row:
        phone = phone_row[0]
    else:
        phone = "Не указан"

    total_price = sum([item[3] for item in cart_items])
    user_address = get_user_address(user_id)

    message = f"Новый заказ:\nАдрес: {user_address}\nНомер телефона: +{phone}\nСумма: {total_price} руб.\nСпособ оплаты: {payment_method}\n\nСписок блюд:\n"

    for item in cart_items:
        message += f"{item[2]} - {item[3]} руб.\n"

    # Отправляем сообщение курьерам
    send_message_to_couriers(message)

    # Отправляем сообщение пользователю
    bot.send_message(user_id, "Ваш заказ передан курьеру. Спасибо за ваш заказ!")

    # Очистка корзины после оформления заказа
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()



@bot.message_handler(func=lambda message: message.text == "Написать доставщику")
def chat_with_couriers(message):
    if message.chat.id != ADMIN_CHAT_ID:  # Только администратор может использовать эту команду
        bot.send_message(message.chat.id, "У вас нет разрешения на использование этой команды.")
        return

    bot.send_message(message.chat.id, "Введите сообщение для курьеров:")
    bot.register_next_step_handler(message, forward_to_couriers)

def forward_to_couriers(message):
    # Отправляем сообщение всем курьерам
    send_message_to_couriers(f"👤Админ: {message.text}")
    bot.send_message(message.chat.id, "Сообщение отправлено курьерам.")

# Очистка корзины
@bot.message_handler(func=lambda message: message.text == "🗑Очистить корзину")
def clear_cart(message):
    user_id = message.chat.id
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Ваша корзина была очищена.")

# Запуск бота
if __name__ == '__main__':
    create_action_log_table()  # Создаем таблицу для логов действий
    bot.polling(none_stop=True, timeout=600)










