# -*- coding: utf-8 -*-
import telebot
import json
import os
import time
import random
import uuid
import requests
from telebot import types
from datetime import datetime

# ============ НАСТРОЙКИ ============
TOKEN = '8239960839:AAEvNh2tUp9uOLrYYVYOgAZVRS0YRsLDH00'
bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
ORDERS_FILE = 'orders.json'
RECIPIENTS_FILE = 'recipients.json'
# ====================================

# ============ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ============
user_role = {}
user_data = {}
user_state = {}
# ================================================

# ============ ИНИЦИАЛИЗАЦИЯ ФАЙЛОВ ============
def init_files():
    if not os.path.exists(USERS_FILE):
        users = {
            "1": {
                "role": "admin",
                "name": "Администратор",
                "phone": "+79991234567",
                "password": "admin123",
                "user_id": None,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        print("✅ Админ создан: код 1, пароль admin123")

    for file in [ORDERS_FILE, RECIPIENTS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)

init_files()
# ================================================

# ============ ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ ============
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def load_orders():
    return load_json(ORDERS_FILE)

def save_orders(orders):
    save_json(ORDERS_FILE, orders)

def load_recipients():
    return load_json(RECIPIENTS_FILE)

def save_recipients(recipients):
    save_json(RECIPIENTS_FILE, recipients)
# ================================================

# ============ ПРОВЕРКА АВТОРИЗАЦИИ ============
def is_authorized(user_id):
    users = load_users()
    for code, user in users.items():
        if user.get('user_id') == user_id:
            user_role[user_id] = user['role']
            user_data[user_id] = user
            return True
    return False

def get_role_name(role):
    names = {
        'admin': '👑 Администратор',
        'manager': '📋 Менеджер',
        'courier': '🚚 Курьер',
        'customer': '🛒 Покупатель'
    }
    return names.get(role, role)
# ================================================

# ============ МЕНЮ ============
def get_auth_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('👑 Админ', '📋 Менеджер')
    keyboard.add('🚚 Курьер', '🛒 Покупатель')
    return keyboard

def get_admin_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('👑 Панель админа', '📦 Все заказы')
    keyboard.add('📋 Менеджеры', '🚚 Курьеры')
    keyboard.add('🎨 Генератор картинок')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_manager_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📋 Новые заказы', '📦 Активные заказы')
    keyboard.add('🚚 Назначить курьера')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_courier_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('🚚 Мои заказы', '✅ Доставлено')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_customer_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('🛒 Сделать заказ', '📋 Мои заказы')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_role_menu(role):
    if role == 'admin':
        return get_admin_menu()
    elif role == 'manager':
        return get_manager_menu()
    elif role == 'courier':
        return get_courier_menu()
    elif role == 'customer':
        return get_customer_menu()
    return get_auth_menu()
# ================================================

# ============ КОМАНДА СТАРТ ============
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        role = user_role.get(user_id)
        name = user_data[user_id].get('name', 'Пользователь')
        bot.send_message(
            message.chat.id,
            f"👋 С возвращением, {name}!\nВаша роль: {get_role_name(role)}",
            reply_markup=get_role_menu(role)
        )
    else:
        bot.send_message(
            message.chat.id,
            "🔐 **ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ ДОСТАВКИ!**\n\n"
            "👑 **Админ:** код 1, пароль admin123\n"
            "📋 **Менеджер:** создает администратор\n"
            "🚚 **Курьер:** создает менеджер\n"
            "🛒 **Покупатель:** регистрация без пароля\n\n"
            "Выберите вашу роль:",
            parse_mode='Markdown',
            reply_markup=get_auth_menu()
        )
# ================================================

# ============ АВТОРИЗАЦИЯ ============
@bot.message_handler(func=lambda message: message.text in ['👑 Админ', '📋 Менеджер', '🚚 Курьер', '🛒 Покупатель'])
def auth_select(message):
    user_id = message.from_user.id
    if message.text == '🛒 Покупатель':
        user_state[user_id] = {'action': 'register_customer'}
        bot.send_message(
            message.chat.id,
            "📝 **РЕГИСТРАЦИЯ ПОКУПАТЕЛЯ**\n\n"
            "Введите ваше имя и телефон через пробел:\n"
            "Пример: `Иван Петров +79991234567`",
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        role_map = {'👑 Админ': 'admin', '📋 Менеджер': 'manager', '🚚 Курьер': 'courier'}
        user_state[user_id] = {'action': 'auth_login', 'role': role_map[message.text]}
        bot.send_message(
            message.chat.id,
            "🔑 Введите код и пароль через пробел:",
            reply_markup=types.ReplyKeyboardRemove()
        )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'auth_login')
def auth_login(message):
    user_id = message.from_user.id
    role = user_state[user_id].get('role')
    try:
        code, password = message.text.split(' ', 1)
        users = load_users()
        if code in users and users[code].get('role') == role:
            if users[code].get('password') == password:
                users[code]['user_id'] = user_id
                save_users(users)
                user_role[user_id] = role
                user_data[user_id] = users[code]
                bot.send_message(
                    message.chat.id,
                    f"✅ **АВТОРИЗАЦИЯ УСПЕШНА!**\n\nДобро пожаловать, {users[code]['name']}!",
                    parse_mode='Markdown',
                    reply_markup=get_role_menu(role)
                )
                del user_state[user_id]
            else:
                bot.send_message(message.chat.id, "❌ Неверный пароль", reply_markup=get_auth_menu())
        else:
            bot.send_message(message.chat.id, "❌ Неверный код или роль", reply_markup=get_auth_menu())
    except:
        bot.send_message(message.chat.id, "❌ Неверный формат! Используйте: код пароль", reply_markup=get_auth_menu())

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'register_customer')
def register_customer(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "❌ Введите имя И телефон через пробел!\nПример: `Иван Петров +79991234567`",
                parse_mode='Markdown'
            )
            return
        name = parts[0]
        phone = parts[1]
        customer_code = f"cust_{uuid.uuid4().hex[:6]}"
        users = load_users()
        users[customer_code] = {
            'role': 'customer',
            'name': name,
            'phone': phone,
            'password': '',
            'user_id': user_id,
            'registered': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        user_role[user_id] = 'customer'
        user_data[user_id] = users[customer_code]
        print(f"✅ ПОКУПАТЕЛЬ ЗАРЕГИСТРИРОВАН: {user_id} -> {customer_code}")
        bot.send_message(
            message.chat.id,
            f"✅ **РЕГИСТРАЦИЯ УСПЕШНА!**\n\n"
            f"👤 Имя: {name}\n"
            f"📞 Телефон: {phone}\n"
            f"🔑 Ваш код: `{customer_code}`\n\n"
            f"🛒 Теперь вы можете делать заказы!",
            parse_mode='Markdown',
            reply_markup=get_customer_menu()
        )
        del user_state[user_id]
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка: {str(e)[:100]}\nПопробуйте еще раз:",
            reply_markup=get_auth_menu()
        )
# ================================================

# ============ ВЫХОД ИЗ СИСТЕМЫ ============
@bot.message_handler(func=lambda message: message.text == '🚪 Выйти')
def logout(message):
    user_id = message.from_user.id
    if user_id in user_role:
        print(f"👤 Выход: удалена роль {user_role[user_id]} для {user_id}")
        del user_role[user_id]
    if user_id in user_data:
        del user_data[user_id]
    if user_id in user_state:
        del user_state[user_id]
    bot.send_message(
        message.chat.id,
        "🔓 **Вы успешно вышли из системы**\n\nДля повторного входа выберите роль:",
        parse_mode='Markdown',
        reply_markup=get_auth_menu()
    )

@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def back_button(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        role = user_role.get(user_id)
        bot.send_message(
            message.chat.id,
            "🔙 Возврат в меню",
            reply_markup=get_role_menu(role)
        )
    else:
        bot.send_message(
            message.chat.id,
            "🏠 Главное меню",
            reply_markup=get_auth_menu()
        )
# ============================================

# ============ ПАНЕЛЬ АДМИНА ============
@bot.message_handler(func=lambda message: message.text == '👑 Панель админа')
def admin_panel(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        bot.send_message(message.chat.id, "❌ Сначала авторизуйтесь!")
        return
    if user_role.get(user_id) != 'admin':
        bot.send_message(message.chat.id, "⛔ Только для администратора!")
        return
    text = """
👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**

📋 **УПРАВЛЕНИЕ СОТРУДНИКАМИ:**
• `/add_manager код имя телефон пароль` - добавить менеджера
• `/add_courier код имя телефон пароль` - добавить курьера
• `/delete_user код` - удалить сотрудника
• `/list_users` - список сотрудников

📦 **УПРАВЛЕНИЕ ЗАКАЗАМИ:**
• `/orders` - все заказы
• `/stats` - статистика

🎨 **ГЕНЕРАТОР:**
• Нажми кнопку 🎨 Генератор картинок
"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['add_manager', 'add_courier'])
def add_employee(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        bot.send_message(message.chat.id, "⛔ Нет прав!")
        return
    try:
        parts = message.text.split()
        if len(parts) != 5:
            bot.send_message(message.chat.id, "❌ Формат: /add_manager код имя телефон пароль")
            return
        role = 'manager' if message.text.startswith('/add_manager') else 'courier'
        code, name, phone, password = parts[1], parts[2], parts[3], parts[4]
        users = load_users()
        if code in users:
            bot.send_message(message.chat.id, "❌ Код уже существует!")
            return
        users[code] = {
            'role': role,
            'name': name,
            'phone': phone,
            'password': password,
            'user_id': None,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        bot.send_message(
            message.chat.id,
            f"✅ {role.upper()} ДОБАВЛЕН!\nКод: `{code}`\nИмя: {name}\nПароль: `{password}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:50]}")

@bot.message_handler(commands=['delete_user'])
def delete_user(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    try:
        code = message.text.split()[1]
        users = load_users()
        if code in users and users[code]['role'] != 'admin':
            if users[code].get('user_id'):
                uid = users[code]['user_id']
                if uid in user_role:
                    del user_role[uid]
                if uid in user_data:
                    del user_data[uid]
            del users[code]
            save_users(users)
            bot.send_message(message.chat.id, f"✅ Пользователь {code} удален")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Используйте: /delete_user код")

@bot.message_handler(commands=['list_users'])
def list_users(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    users = load_users()
    text = "📋 **СПИСОК СОТРУДНИКОВ:**\n\n"
    for code, user in users.items():
        if user['role'] in ['admin', 'manager', 'courier']:
            status = "🟢 ONLINE" if user.get('user_id') else "🔴 OFFLINE"
            text += f"`{code}` | {status}\n"
            text += f"   👤 {user['role']}: {user['name']}\n"
            text += f"   📞 {user['phone']}\n\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['orders'])
def admin_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    orders = load_orders()
    if not orders:
        bot.send_message(message.chat.id, "📭 Заказов пока нет")
        return
    text = "📦 **ВСЕ ЗАКАЗЫ:**\n\n"
    for order_id, order in list(orders.items())[-10:]:
        text += f"🔖 `{order_id}`\n"
        text += f"👤 {order.get('customer_name', 'Нет')}\n"
        text += f"📍 {order.get('address', 'Нет')[:30]}\n"
        text += f"📊 {order.get('status_text', '⏳')}\n"
        text += f"➖➖➖➖➖➖➖\n\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    users = load_users()
    orders = load_orders()
    managers = sum(1 for u in users.values() if u['role'] == 'manager')
    couriers = sum(1 for u in users.values() if u['role'] == 'courier')
    customers = sum(1 for u in users.values() if u['role'] == 'customer')
    total_orders = len(orders)
    delivered = sum(1 for o in orders.values() if o.get('status') == 'delivered')
    text = f"""
📊 **СТАТИСТИКА СИСТЕМЫ**

👥 **ПОЛЬЗОВАТЕЛИ:**
• 👑 Админ: 1
• 📋 Менеджеры: {managers}
• 🚚 Курьеры: {couriers}
• 🛒 Покупатели: {customers}

📦 **ЗАКАЗЫ:**
• Всего: {total_orders}
• ✅ Доставлено: {delivered}
    """
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📦 Все заказы')
def admin_orders_button(message):
    admin_orders(message)
# ================================================

# ============ УПРАВЛЕНИЕ МЕНЕДЖЕРАМИ И КУРЬЕРАМИ ============
@bot.message_handler(func=lambda message: message.text == '📋 Менеджеры')
def managers_list(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    users = load_users()
    text = "📋 **СПИСОК МЕНЕДЖЕРОВ:**\n\n"
    count = 0
    for code, user in users.items():
        if user['role'] == 'manager':
            status = "🟢" if user.get('user_id') else "🔴"
            text += f"{status} `{code}` - {user['name']}\n"
            text += f"   📞 {user['phone']}\n\n"
            count += 1
    if count == 0:
        text = "📋 Менеджеров пока нет"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🚚 Курьеры')
def couriers_list(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    users = load_users()
    text = "🚚 **СПИСОК КУРЬЕРОВ:**\n\n"
    count = 0
    for code, user in users.items():
        if user['role'] == 'courier':
            status = "🟢" if user.get('user_id') else "🔴"
            text += f"{status} `{code}` - {user['name']}\n"
            text += f"   📞 {user['phone']}\n\n"
            count += 1
    if count == 0:
        text = "🚚 Курьеров пока нет"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
# ================================================

# ============ СИСТЕМА ЗАКАЗОВ ============
@bot.message_handler(func=lambda message: message.text == '🛒 Сделать заказ')
def create_order_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        bot.send_message(message.chat.id, "❌ Сначала авторизуйтесь!")
        return
    role = user_role.get(user_id)
    if role != 'customer':
        bot.send_message(
            message.chat.id,
            f"⛔ Эта функция только для покупателей!\nВаша роль: {get_role_name(role)}"
        )
        return
    user_state[user_id] = {'action': 'create_order', 'step': 'address'}
    bot.send_message(
        message.chat.id,
        "📝 **ОФОРМЛЕНИЕ ЗАКАЗА**\n\nВведите адрес доставки:",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'create_order')
def create_order_process(message):
    user_id = message.from_user.id
    state = user_state[user_id]
    step = state.get('step')
    if step == 'address':
        state['address'] = message.text
        state['step'] = 'details'
        bot.send_message(message.chat.id, "📦 Введите, что нужно доставить:")
    elif step == 'details':
        order_id = f"ORD{int(time.time())}{random.randint(100, 999)}"
        orders = load_orders()
        orders[order_id] = {
            'order_id': order_id,
            'customer_id': user_id,
            'customer_name': user_data[user_id]['name'],
            'customer_phone': user_data[user_id]['phone'],
            'address': state['address'],
            'details': message.text,
            'status': 'pending',
            'status_text': '⏳ Ожидает обработки',
            'manager_id': None,
            'courier_id': None,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_orders(orders)
        bot.send_message(
            message.chat.id,
            f"✅ **ЗАКАЗ ОФОРМЛЕН!**\n\nНомер заказа: `{order_id}`\nСтатус: ⏳ Ожидает обработки",
            parse_mode='Markdown',
            reply_markup=get_customer_menu()
        )
        del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '📋 Новые заказы')
def manager_new_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'manager':
        bot.send_message(message.chat.id, "⛔ Только для менеджеров!")
        return
    orders = load_orders()
    text = "📋 **НОВЫЕ ЗАКАЗЫ:**\n\n"
    count = 0
    for order_id, order in orders.items():
        if order.get('status') == 'pending':
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order.get('customer_name', '')}\n"
            text += f"📞 {order.get('customer_phone', '')}\n"
            text += f"📍 {order.get('address', '')}\n"
            text += f"📦 {order.get('details', '')}\n"
            text += f"➖➖➖➖➖➖➖➖➖\n\n"
            count += 1
    if count == 0:
        text = "✅ Новых заказов нет"
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Взять заказ', '🔄 Обновить')
    keyboard.add('🚪 Назад')
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == '✅ Взять заказ')
def take_order_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'manager':
        return
    user_state[user_id] = {'action': 'take_order'}
    bot.send_message(
        message.chat.id,
        "📝 Введите номер заказа:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'take_order')
def take_order_process(message):
    user_id = message.from_user.id
    order_id = message.text.strip()
    orders = load_orders()
    if order_id in orders and orders[order_id].get('status') == 'pending':
        orders[order_id]['status'] = 'processing'
        orders[order_id]['status_text'] = '⚙️ В обработке'
        orders[order_id]['manager_id'] = user_id
        save_orders(orders)
        bot.send_message(
            message.chat.id,
            f"✅ Заказ {order_id} взят в работу!",
            reply_markup=get_manager_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Заказ не найден или уже обрабатывается")
    del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '📦 Активные заказы')
def manager_active_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'manager':
        return
    orders = load_orders()
    text = "📦 **АКТИВНЫЕ ЗАКАЗЫ:**\n\n"
    count = 0
    for order_id, order in orders.items():
        if order.get('manager_id') == user_id and order['status'] in ['processing', 'accepted', 'ready']:
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order['customer_name']}\n"
            text += f"📍 {order['address']}\n"
            text += f"📊 {order['status_text']}\n"
            if order.get('courier_id'):
                users = load_users()
                for code, user in users.items():
                    if user.get('user_id') == order['courier_id']:
                        text += f"🚚 Курьер: {user['name']}\n"
            text += f"➖➖➖➖➖➖➖\n\n"
            count += 1
    if count == 0:
        text = "📭 Активных заказов нет"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🚚 Назначить курьера')
def assign_courier_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'manager':
        return
    user_state[user_id] = {'action': 'assign_courier_start'}
    bot.send_message(
        message.chat.id,
        "📦 Введите номер заказа:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'assign_courier_start')
def assign_courier_order(message):
    user_id = message.from_user.id
    order_id = message.text.strip()
    orders = load_orders()
    if order_id not in orders:
        bot.send_message(message.chat.id, "❌ Заказ не найден")
        del user_state[user_id]
        return
    users = load_users()
    couriers = []
    courier_text = "🚚 **ДОСТУПНЫЕ КУРЬЕРЫ:**\n\n"
    for code, user in users.items():
        if user['role'] == 'courier' and user.get('user_id'):
            couriers.append(code)
            courier_text += f"`{code}` - {user['name']} ({user['phone']})\n"
    if not couriers:
        bot.send_message(message.chat.id, "❌ Нет доступных курьеров")
        del user_state[user_id]
        return
    user_state[user_id] = {'action': 'assign_courier', 'order_id': order_id}
    bot.send_message(
        message.chat.id,
        courier_text + "\n📝 Введите код курьера:",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'assign_courier')
def assign_courier_execute(message):
    user_id = message.from_user.id
    courier_code = message.text.strip()
    order_id = user_state[user_id]['order_id']
    users = load_users()
    if courier_code not in users or users[courier_code]['role'] != 'courier':
        bot.send_message(message.chat.id, "❌ Неверный код курьера")
        return
    orders = load_orders()
    courier_id = users[courier_code]['user_id']
    if courier_id:
        orders[order_id]['courier_id'] = courier_id
        orders[order_id]['status'] = 'ready'
        orders[order_id]['status_text'] = '🚚 Передан курьеру'
        save_orders(orders)
        try:
            bot.send_message(
                courier_id,
                f"🚚 **НОВЫЙ ЗАКАЗ!**\n\n"
                f"Номер: `{order_id}`\n"
                f"Клиент: {orders[order_id]['customer_name']}\n"
                f"Телефон: {orders[order_id]['customer_phone']}\n"
                f"Адрес: {orders[order_id]['address']}\n"
                f"Детали: {orders[order_id]['details']}",
                parse_mode='Markdown',
                reply_markup=get_courier_menu()
            )
        except:
            pass
        bot.send_message(
            message.chat.id,
            f"✅ Курьер назначен на заказ {order_id}",
            reply_markup=get_manager_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Курьер не авторизован в боте")
    del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '🚚 Мои заказы')
def courier_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'courier':
        bot.send_message(message.chat.id, "⛔ Только для курьеров!")
        return
    orders = load_orders()
    text = "🚚 **МОИ ЗАКАЗЫ:**\n\n"
    count = 0
    for order_id, order in orders.items():
        if order.get('courier_id') == user_id and order['status'] in ['ready', 'accepted']:
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order['customer_name']}\n"
            text += f"📍 {order['address']}\n"
            text += f"📞 {order['customer_phone']}\n"
            text += f"📦 {order['details']}\n"
            text += f"➖➖➖➖➖➖➖\n\n"
            count += 1
    if count == 0:
        text = "📭 У вас нет активных заказов"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '✅ Доставлено')
def deliver_order_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'courier':
        return
    user_state[user_id] = {'action': 'deliver_order'}
    bot.send_message(
        message.chat.id,
        "📦 Введите номер доставленного заказа:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'deliver_order')
def deliver_order_process(message):
    user_id = message.from_user.id
    order_id = message.text.strip()
    orders = load_orders()
    if order_id in orders and orders[order_id].get('courier_id') == user_id:
        orders[order_id]['status'] = 'delivered'
        orders[order_id]['status_text'] = '✅ Доставлен'
        orders[order_id]['delivered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_orders(orders)
        if orders[order_id].get('manager_id'):
            try:
                bot.send_message(
                    orders[order_id]['manager_id'],
                    f"✅ Заказ {order_id} доставлен курьером {user_data[user_id]['name']}!"
                )
            except:
                pass
        if orders[order_id].get('customer_id'):
            try:
                bot.send_message(
                    orders[order_id]['customer_id'],
                    f"✅ Ваш заказ {order_id} доставлен!\nСпасибо за покупку!"
                )
            except:
                pass
        bot.send_message(
            message.chat.id,
            f"✅ Заказ {order_id} отмечен как доставленный!",
            reply_markup=get_courier_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Заказ не найден")
    del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '📋 Мои заказы')
def customer_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'customer':
        return
    orders = load_orders()
    text = "📋 **ВАШИ ЗАКАЗЫ:**\n\n"
    count = 0
    for order_id, order in orders.items():
        if order.get('customer_id') == user_id:
            text += f"🔖 `{order_id}`\n"
            text += f"📍 {order['address']}\n"
            text += f"📦 {order['details'][:50]}\n"
            text += f"📊 {order['status_text']}\n"
            text += f"➖➖➖➖➖➖➖\n\n"
            count += 1
    if count == 0:
        text = "📭 У вас еще нет заказов"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🔄 Обновить')
def refresh_orders(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        if user_role.get(user_id) == 'manager':
            manager_new_orders(message)
        elif user_role.get(user_id) == 'courier':
            courier_orders(message)
        elif user_role.get(user_id) == 'customer':
            customer_orders(message)

@bot.message_handler(func=lambda message: message.text == '🚪 Назад')
def back_to_menu(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        bot.send_message(
            message.chat.id,
            "🔙 Возврат в меню",
            reply_markup=get_role_menu(user_role[user_id])
        )
# ================================================

# ============ ГЕНЕРАТОР КАРТИНОК ============
def generate_image(prompt):
    try:
        clean_prompt = prompt.replace(' ', '%20').replace('#', '').replace('@', '').replace('&', '')
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200 and len(response.content) > 5000:
            return response.content
    except Exception as e:
        print(f"Ошибка генерации: {e}")
    try:
        fallback = "https://picsum.photos/1024/1024"
        return requests.get(fallback, timeout=10).content
    except:
        return None

@bot.message_handler(func=lambda message: message.text == '🎨 Генератор картинок')
def image_generator_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        bot.send_message(message.chat.id, "⛔ Только для администратора!")
        return
    user_state[user_id] = {'action': 'generate_image'}
    bot.send_message(
        message.chat.id,
        "🎨 **ГЕНЕРАТОР КАРТИНОК**\n\nВведите что нарисовать:\nНапример: `курьер с пиццей`, `робот доставщик`\n\n⏱ Генерация: 5-15 секунд",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'generate_image')
def image_generator_process(message):
    user_id = message.from_user.id
    prompt = message.text
    status = bot.send_message(
        message.chat.id,
        f"🎨 Рисую: {prompt[:50]}...\n⏳ Подождите...",
        parse_mode='Markdown'
    )
    bot.send_chat_action(message.chat.id, 'upload_photo')
    image = generate_image(prompt)
    if image:
        try:
            bot.delete_message(message.chat.id, status.message_id)
            bot.send_photo(
                message.chat.id,
                image,
                caption=f"🎨 **{prompt}**\n✅ Готово!",
                parse_mode='Markdown',
                reply_markup=get_admin_menu()
            )
        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка отправки: {str(e)[:50]}",
                reply_markup=get_admin_menu()
            )
    else:
        bot.edit_message_text(
            "❌ Не удалось сгенерировать картинку.\nПопробуйте другой запрос.",
            message.chat.id,
            status.message_id,
            reply_markup=get_admin_menu()
        )
    del user_state[user_id]
# ================================================

# ============ ВЕБ-ЗАГЛУШКА ДЛЯ RENDER ============
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = f'''
        <html>
            <head><title>Telegram Bot</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #4CAF50;">✅ БОТ РАБОТАЕТ!</h1>
                <p>🤖 @bottoarmwhloe_bot</p>
                <p>⚡ Статус: активен 24/7 на Render</p>
                <p>📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
        </html>
        '''
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_webserver():
    try:
        port = 10000
        server = HTTPServer(('0.0.0.0', port), PingHandler)
        print(f"✅ Веб-сервер запущен на порту {port}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Ошибка веб-сервера: {e}")

threading.Thread(target=run_webserver, daemon=True).start()
# ================================================

# ============ ОБРАБОТКА ОШИБОК ============
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        bot.send_message(
            message.chat.id,
            "❓ Неизвестная команда\nИспользуйте кнопки меню",
            reply_markup=get_role_menu(user_role[user_id])
        )
    else:
        bot.send_message(
            message.chat.id,
            "❓ Используйте /start для начала работы",
            reply_markup=get_auth_menu()
        )
# ================================================

# ============ ЗАПУСК ============
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ДЖАРВИС 2.0 — ПОЛНАЯ ВЕРСИЯ ЗАПУЩЕНА!")
    print("=" * 60)
    print("✅ Роли: Админ | Менеджер | Курьер | Покупатель")
    print("✅ Заказы: Создание | Назначение | Доставка")
    print("✅ Генератор картинок | Управление сотрудниками")
    print("=" * 60)
    print("👑 Админ: код 1, пароль admin123")
    print("=" * 60)

    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)
# ================================================
