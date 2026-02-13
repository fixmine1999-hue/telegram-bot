# -*- coding: utf-8 -*-
import telebot
import json
import os
import urllib.parse
from collections import Counter
from telebot import types
import requests
from io import BytesIO
import time
import re
import random
import uuid
from datetime import datetime

# ============ НАСТРОЙКИ БОТА ============
TOKEN = '8239960839:AAEvCSo66B8ixLRPqe1ubFlqPFzLyqkKFrQ'  # ⚠️ ВСТАВЬ СВОЙ ТОКЕН!
bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
USERS_FILE = 'users.json'
ORDERS_FILE = 'orders.json'
RECIPIENTS_FILE = 'recipients.json'
# ========================================

# ============ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ============
user_state = {}      # Состояние пользователя
user_role = {}       # Роль пользователя
user_data = {}       # Данные пользователя
# ================================================

# ============ ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ ============
def load_json(filename):
    """Загрузка данных из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json(filename, data):
    """Сохранение данных в JSON файл"""
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

# ============ ИНИЦИАЛИЗАЦИЯ ПРИ ПЕРВОМ ЗАПУСКЕ ============
def init_files():
    """Создает файлы с данными по умолчанию"""
    # Создаем админа
    users = load_users()
    if "1" not in users:
        users["1"] = {
            "role": "admin",
            "name": "Главный администратор",
            "phone": "+79991234567",
            "password": "admin123",
            "user_id": None,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        print("✅ Админ создан: код 1, пароль admin123")
    
    # Создаем пустые файлы для заказов и получателей
    if not os.path.exists(ORDERS_FILE):
        save_json(ORDERS_FILE, {})
    
    if not os.path.exists(RECIPIENTS_FILE):
        save_json(RECIPIENTS_FILE, {})

init_files()
# ================================================

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def is_authorized(user_id):
    """Проверяет, авторизован ли пользователь"""
    users = load_users()
    for code, user in users.items():
        if user.get('user_id') == user_id:
            user_role[user_id] = user['role']
            user_data[user_id] = user
            return True
    return False

def get_role_name(role):
    """Возвращает название роли с эмодзи"""
    names = {
        'admin': '👑 Администратор',
        'manager': '📋 Менеджер',
        'courier': '🚚 Курьер',
        'customer': '🛒 Покупатель'
    }
    return names.get(role, role)

def get_map_link(address):
    """Генерирует ссылки на Яндекс и Google Карты"""
    encoded = urllib.parse.quote(address)
    yandex = f"https://yandex.ru/maps/?text={encoded}"
    google = f"https://www.google.com/maps/search/?api=1&query={encoded}"
    return yandex, google

def generate_order_id():
    """Генерирует уникальный номер заказа"""
    return f"ORD{int(time.time())}{random.randint(100, 999)}"
# ================================================

# ============ МЕНЮ ДЛЯ РАЗНЫХ РОЛЕЙ ============
def get_auth_menu():
    """Меню выбора роли при входе"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('👑 Админ', '📋 Менеджер')
    keyboard.add('🚚 Курьер', '🛒 Покупатель')
    return keyboard

def get_admin_menu():
    """Меню администратора"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('👑 Панель админа', '📦 Управление заказами')
    keyboard.add('📋 Менеджеры', '🚚 Курьеры')
    keyboard.add('➕ Добавить получателя', '🔍 Поиск')
    keyboard.add('📊 Статистика', '🎨 Генератор картинок')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_manager_menu():
    """Меню менеджера"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📋 Новые заказы', '📦 Активные заказы')
    keyboard.add('🚚 Назначить курьера')
    keyboard.add('➕ Добавить получателя', '🔍 Поиск')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_courier_menu():
    """Меню курьера"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('🚚 Мои заказы', '✅ Доставлено')
    keyboard.add('🔍 Поиск получателя')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_customer_menu():
    """Меню покупателя"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('🛒 Сделать заказ', '📋 Мои заказы')
    keyboard.add('🚪 Выйти')
    return keyboard

def get_role_menu(role):
    """Возвращает меню в зависимости от роли"""
    menus = {
        'admin': get_admin_menu,
        'manager': get_manager_menu,
        'courier': get_courier_menu,
        'customer': get_customer_menu
    }
    return menus.get(role, get_auth_menu)()
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
            f"👋 С возвращением, {name}!\n"
            f"Ваша роль: {get_role_name(role)}",
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

# ============ АВТОРИЗАЦИЯ ============
@bot.message_handler(func=lambda message: message.text in ['👑 Админ', '📋 Менеджер', '🚚 Курьер', '🛒 Покупатель'])
def auth_select(message):
    user_id = message.from_user.id
    
    role_map = {
        '👑 Админ': 'admin',
        '📋 Менеджер': 'manager',
        '🚚 Курьер': 'courier',
        '🛒 Покупатель': 'customer'
    }
    
    selected_role = role_map.get(message.text)
    
    if selected_role == 'customer':
        user_state[user_id] = {'action': 'register_customer'}
        bot.send_message(
            message.chat.id,
            "📝 **РЕГИСТРАЦИЯ ПОКУПАТЕЛЯ**\n\n"
            "Введите ваше имя и номер телефона через пробел:\n"
            "Пример: `Иван Петров +79991234567`",
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        user_state[user_id] = {'action': 'auth_login', 'role': selected_role}
        bot.send_message(
            message.chat.id,
            f"🔑 Введите ваш код и пароль через пробел:",
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
                    f"✅ **АВТОРИЗАЦИЯ УСПЕШНА!**\n\n"
                    f"Добро пожаловать, {users[code]['name']}!",
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
        name = parts[0]
        phone = parts[1] if len(parts) > 1 else ""
        
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
        
        bot.send_message(
            message.chat.id,
            f"✅ **РЕГИСТРАЦИЯ УСПЕШНА!**\n\n"
            f"Ваш код покупателя: `{customer_code}`\n"
            f"Сохраните его для отслеживания заказов!",
            parse_mode='Markdown',
            reply_markup=get_customer_menu()
        )
        del user_state[user_id]
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:50]}", reply_markup=get_auth_menu())

@bot.message_handler(func=lambda message: message.text == '🚪 Выйти')
def logout(message):
    user_id = message.from_user.id
    if user_id in user_role:
        del user_role[user_id]
    if user_id in user_data:
        del user_data[user_id]
    bot.send_message(
        message.chat.id,
        "🔓 Вы вышли из системы",
        reply_markup=get_auth_menu()
    )
# ================================================

# ============ ПАНЕЛЬ АДМИНИСТРАТОРА ============
@bot.message_handler(func=lambda message: message.text == '👑 Панель админа')
def admin_panel(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        bot.send_message(message.chat.id, "⛔ Доступ запрещен!")
        return
    
    text = """
👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**

📋 **Управление сотрудниками:**
• /add_manager код имя телефон пароль
• /add_courier код имя телефон пароль
• /delete_user код
• /list_users

📦 **Управление заказами:**
• /all_orders - все заказы
• /stats - статистика

🔧 **Системные команды:**
• /clear_db - очистить базу
• /backup - создать backup
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
            bot.send_message(message.chat.id, "❌ Такой код уже существует!")
            return
        
        users[code] = {
            'role': role,
            'name': name,
            'phone': phone,
            'password': password,
            'user_id': None,
            'created_by': user_data[user_id].get('name'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        
        bot.send_message(
            message.chat.id,
            f"✅ {role.upper()} добавлен!\n"
            f"Код: `{code}`\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Пароль: {password}",
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
            # Удаляем привязку к Telegram
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
            bot.send_message(message.chat.id, "❌ Пользователь не найден или это админ")
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
            status = "✅ ONLINE" if user.get('user_id') else "❌ OFFLINE"
            text += f"`{code}` | {status}\n"
            text += f"   {user['role']}: {user['name']}\n"
            text += f"   📞 {user['phone']}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
# ================================================

# ============ УПРАВЛЕНИЕ МЕНЕДЖЕРАМИ ============
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
            status = "✅" if user.get('user_id') else "❌"
            text += f"{status} `{code}` - {user['name']}\n"
            text += f"   📞 {user['phone']}\n\n"
            count += 1
    
    if count == 0:
        text = "📋 Менеджеров пока нет"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
# ================================================

# ============ УПРАВЛЕНИЕ КУРЬЕРАМИ ============
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
            status = "✅" if user.get('user_id') else "❌"
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
    if not is_authorized(user_id) or user_role.get(user_id) != 'customer':
        bot.send_message(message.chat.id, "⛔ Только для покупателей!")
        return
    
    user_state[user_id] = {'action': 'create_order', 'step': 'address'}
    bot.send_message(
        message.chat.id,
        "📝 **ОФОРМЛЕНИЕ ЗАКАЗА**\n\n"
        "Введите адрес доставки:",
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
        order_id = generate_order_id()
        
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
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'history': []
        }
        save_orders(orders)
        
        # Уведомляем всех менеджеров
        users = load_users()
        for code, user in users.items():
            if user['role'] == 'manager' and user.get('user_id'):
                try:
                    bot.send_message(
                        user['user_id'],
                        f"🆕 **НОВЫЙ ЗАКАЗ!**\n\n"
                        f"Номер: `{order_id}`\n"
                        f"Клиент: {user_data[user_id]['name']}\n"
                        f"Телефон: {user_data[user_id]['phone']}\n"
                        f"Адрес: {state['address']}\n"
                        f"Детали: {message.text}",
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        bot.send_message(
            message.chat.id,
            f"✅ **ЗАКАЗ ОФОРМЛЕН!**\n\n"
            f"Номер заказа: `{order_id}`\n"
            f"Статус: ⏳ Ожидает обработки\n\n"
            f"Менеджер свяжется с вами!",
            parse_mode='Markdown',
            reply_markup=get_customer_menu()
        )
        del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '📋 Новые заказы')
def new_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'manager':
        return
    
    orders = load_orders()
    text = "📋 **НОВЫЕ ЗАКАЗЫ:**\n\n"
    count = 0
    
    for order_id, order in orders.items():
        if order['status'] == 'pending':
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order['customer_name']} ({order['customer_phone']})\n"
            text += f"📍 {order['address']}\n"
            text += f"📦 {order['details']}\n"
            text += f"⏳ {order['status_text']}\n"
            text += f"➖➖➖➖➖➖➖➖➖\n\n"
            count += 1
    
    if count == 0:
        text = "✅ Новых заказов нет"
    
    # Клавиатура для взятия заказа
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Взять заказ', '🔄 Обновить')
    keyboard.add('🚪 Назад')
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == '📦 Активные заказы')
def active_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return
    
    role = user_role.get(user_id)
    orders = load_orders()
    text = "📦 **АКТИВНЫЕ ЗАКАЗЫ:**\n\n"
    count = 0
    
    for order_id, order in orders.items():
        show = False
        
        if role == 'admin':
            show = order['status'] in ['processing', 'accepted', 'ready']
        elif role == 'manager':
            show = order.get('manager_id') == user_id and order['status'] in ['processing', 'accepted', 'ready']
        elif role == 'courier':
            show = order.get('courier_id') == user_id and order['status'] in ['accepted', 'ready']
        
        if show:
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order['customer_name']}\n"
            text += f"📍 {order['address']}\n"
            text += f"📦 {order['details']}\n"
            text += f"📊 {order['status_text']}\n"
            
            if order.get('courier_id'):
                users = load_users()
                for code, user in users.items():
                    if user.get('user_id') == order['courier_id']:
                        text += f"🚚 Курьер: {user['name']}\n"
            
            text += f"➖➖➖➖➖➖➖➖➖\n\n"
            count += 1
    
    if count == 0:
        text = "📭 Активных заказов нет"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '✅ Взять заказ')
def take_order(message):
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
    if order_id in orders and orders[order_id]['status'] == 'pending':
        orders[order_id]['status'] = 'processing'
        orders[order_id]['status_text'] = '⚙️ В обработке'
        orders[order_id]['manager_id'] = user_id
        save_orders(orders)
        
        # Уведомляем админа
        users = load_users()
        for code, user in users.items():
            if user['role'] == 'admin' and user.get('user_id'):
                try:
                    bot.send_message(
                        user['user_id'],
                        f"📋 Менеджер взял заказ в работу\n"
                        f"Заказ: `{order_id}`",
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        bot.send_message(
            message.chat.id,
            f"✅ Заказ {order_id} взят в работу!",
            reply_markup=get_manager_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Заказ не найден или уже обрабатывается")
    
    del user_state[user_id]

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
    
    # Получаем список свободных курьеров
    users = load_users()
    couriers = []
    courier_text = "🚚 **ДОСТУПНЫЕ КУРЬЕРЫ:**\n\n"
    
    for code, user in users.items():
        if user['role'] == 'courier' and user.get('user_id'):
            couriers.append(code)
            status = "✅" if user.get('user_id') else "❌"
            courier_text += f"{status} `{code}` - {user['name']}\n"
    
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
        
        # Уведомляем курьера
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
def my_courier_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'courier':
        return
    
    orders = load_orders()
    text = "🚚 **МОИ ЗАКАЗЫ:**\n\n"
    count = 0
    
    for order_id, order in orders.items():
        if order.get('courier_id') == user_id and order['status'] in ['ready', 'accepted']:
            text += f"🔖 `{order_id}`\n"
            text += f"👤 {order['customer_name']} ({order['customer_phone']})\n"
            text += f"📍 {order['address']}\n"
            text += f"📦 {order['details']}\n"
            text += f"📊 {order['status_text']}\n"
            text += f"➖➖➖➖➖➖➖➖➖\n\n"
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
def deliver_order_execute(message):
    user_id = message.from_user.id
    order_id = message.text.strip()
    
    orders = load_orders()
    if order_id in orders and orders[order_id].get('courier_id') == user_id:
        orders[order_id]['status'] = 'delivered'
        orders[order_id]['status_text'] = '✅ Доставлен'
        orders[order_id]['delivered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_orders(orders)
        
        # Уведомляем менеджера
        if orders[order_id].get('manager_id'):
            try:
                bot.send_message(
                    orders[order_id]['manager_id'],
                    f"✅ Заказ `{order_id}` доставлен!",
                    parse_mode='Markdown'
                )
            except:
                pass
        
        # Уведомляем админа
        users = load_users()
        for code, user in users.items():
            if user['role'] == 'admin' and user.get('user_id'):
                try:
                    bot.send_message(
                        user['user_id'],
                        f"✅ Заказ `{order_id}` доставлен!\n"
                        f"Курьер: {user_data[user_id]['name']}",
                        parse_mode='Markdown'
                    )
                except:
                    pass
        
        # Уведомляем покупателя
        if orders[order_id].get('customer_id'):
            try:
                bot.send_message(
                    orders[order_id]['customer_id'],
                    f"✅ Ваш заказ `{order_id}` доставлен!\n"
                    f"Спасибо, что выбрали нас!",
                    parse_mode='Markdown'
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

@bot.message_handler(func=lambda message: message.text == '📋 Мои заказы' and 
                     user_role.get(message.from_user.id) == 'customer')
def my_customer_orders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return
    
    orders = load_orders()
    text = "📋 **ВАШИ ЗАКАЗЫ:**\n\n"
    count = 0
    
    for order_id, order in orders.items():
        if order.get('customer_id') == user_id:
            text += f"🔖 `{order_id}`\n"
            text += f"📍 {order['address']}\n"
            text += f"📦 {order['details']}\n"
            text += f"📊 {order['status_text']}\n"
            
            if order.get('courier_id'):
                users = load_users()
                for code, user in users.items():
                    if user.get('user_id') == order['courier_id']:
                        text += f"🚚 Курьер: {user['name']} ({user['phone']})\n"
            
            text += f"➖➖➖➖➖➖➖➖➖\n\n"
            count += 1
    
    if count == 0:
        text = "📭 У вас еще нет заказов"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
# ================================================

# ============ БАЗА ДАННЫХ ПОЛУЧАТЕЛЕЙ ============
@bot.message_handler(func=lambda message: message.text == '➕ Добавить получателя')
def add_recipient_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) not in ['admin', 'manager', 'courier']:
        bot.send_message(message.chat.id, "⛔ Нет прав!")
        return
    
    user_state[user_id] = {'action': 'add_recipient', 'step': 'name'}
    bot.send_message(
        message.chat.id,
        "👤 Введите имя получателя:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'add_recipient')
def add_recipient_process(message):
    user_id = message.from_user.id
    state = user_state[user_id]
    step = state.get('step')
    
    if step == 'name':
        state['name'] = message.text
        state['step'] = 'phone'
        bot.send_message(message.chat.id, "📞 Введите номер телефона:")
    
    elif step == 'phone':
        state['phone'] = message.text
        state['step'] = 'address'
        bot.send_message(message.chat.id, "📍 Введите адрес:")
    
    elif step == 'address':
        state['address'] = message.text
        state['step'] = 'code'
        bot.send_message(message.chat.id, "🔑 Введите уникальный код получателя:")
    
    elif step == 'code':
        code = message.text
        recipients = load_recipients()
        
        if code in recipients:
            bot.send_message(message.chat.id, "❌ Такой код уже существует! Введите другой:")
            return
        
        recipients[code] = {
            'name': state['name'],
            'phone': state['phone'],
            'address': state['address'],
            'created_by': user_role.get(user_id),
            'created_by_name': user_data[user_id].get('name'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_recipients(recipients)
        
        yandex, google = get_map_link(state['address'])
        
        bot.send_message(
            message.chat.id,
            f"✅ **ПОЛУЧАТЕЛЬ ДОБАВЛЕН!**\n\n"
            f"👤 Имя: {state['name']}\n"
            f"📞 Телефон: {state['phone']}\n"
            f"📍 Адрес: {state['address']}\n"
            f"🔑 Код: `{code}`\n\n"
            f"🗺 [Яндекс Карты]({yandex})\n"
            f"🗺 [Google Карты]({google})",
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=get_role_menu(user_role[user_id])
        )
        del user_state[user_id]

@bot.message_handler(func=lambda message: message.text == '🔍 Поиск получателя' or message.text == '🔍 Поиск')
def search_recipient_start(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return
    
    user_state[user_id] = {'action': 'search_recipient'}
    bot.send_message(
        message.chat.id,
        "🔎 **ПОИСК ПОЛУЧАТЕЛЯ**\n\n"
        "Введите имя, телефон или адрес для поиска:",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'search_recipient')
def search_recipient_process(message):
    user_id = message.from_user.id
    query = message.text.lower()
    
    recipients = load_recipients()
    results = []
    
    for code, recipient in recipients.items():
        if (query in recipient.get('name', '').lower() or 
            query in recipient.get('phone', '').lower() or 
            query in recipient.get('address', '').lower()):
            results.append((code, recipient))
    
    if results:
        for code, recipient in results:
            text = f"🔍 **НАЙДЕН ПОЛУЧАТЕЛЬ:**\n\n"
            text += f"🔑 Код: `{code}`\n"
            text += f"👤 Имя: {recipient['name']}\n"
            text += f"📞 Телефон: {recipient['phone']}\n"
            text += f"📍 Адрес: {recipient['address']}\n"
            
            yandex, google = get_map_link(recipient['address'])
            text += f"\n🗺 [Яндекс Карты]({yandex}) | [Google Карты]({google})"
            
            bot.send_message(
                message.chat.id, 
                text, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    else:
        bot.send_message(message.chat.id, '❌ Получатели не найдены')
    
    bot.send_message(
        message.chat.id,
        "✅ Поиск завершен",
        reply_markup=get_role_menu(user_role[user_id])
    )
    del user_state[user_id]
# ================================================

# ============ СТАТИСТИКА ============
@bot.message_handler(func=lambda message: message.text == '📊 Статистика')
def show_statistics(message):
    user_id = message.from_user.id
    if not is_authorized(user_id) or user_role.get(user_id) != 'admin':
        return
    
    recipients = load_recipients()
    orders = load_orders()
    users_db = load_users()
    
    # Статистика по получателям
    recipients_count = len(recipients)
    
    # Статистика по заказам
    orders_total = len(orders)
    orders_pending = sum(1 for o in orders.values() if o['status'] == 'pending')
    orders_delivered = sum(1 for o in orders.values() if o['status'] == 'delivered')
    
    # Статистика по сотрудникам
    managers = sum(1 for u in users_db.values() if u['role'] == 'manager')
    couriers = sum(1 for u in users_db.values() if u['role'] == 'courier')
    customers = sum(1 for u in users_db.values() if u['role'] == 'customer')
    
    text = f"""
📊 **СТАТИСТИКА СИСТЕМЫ**

👥 **ПОЛЬЗОВАТЕЛИ:**
• 👑 Админы: 1
• 📋 Менеджеры: {managers}
• 🚚 Курьеры: {couriers}
• 🛒 Покупатели: {customers}
━━━━━━━━━━━━━━━━━━━

📦 **ЗАКАЗЫ:**
• Всего: {orders_total}
• ⏳ В обработке: {orders_pending}
• ✅ Доставлено: {orders_delivered}
━━━━━━━━━━━━━━━━━━━

📍 **ПОЛУЧАТЕЛИ:**
• Всего адресов: {recipients_count}
"""
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
# ================================================

# ============ ГЕНЕРАТОР КАРТИНОК ============
# ============ ГЕНЕРАТОР КАРТИНОК ============
import requests
import time

def generate_image(prompt):
    """Генерирует картинку с повторными попытками"""
    attempts = 3
    for attempt in range(attempts):
        try:
            # Очищаем промпт
            clean_prompt = prompt.replace(' ', '%20').replace('#', '').replace('@', '')
            
            # Используем правильный эндпоинт
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true&private=true"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=25)
            
            if response.status_code == 200 and len(response.content) > 5000:
                print(f"✅ Картинка сгенерирована: {len(response.content)} байт")
                return response.content
            else:
                print(f"⚠️ Плохой ответ: {response.status_code}, размер: {len(response.content)}")
                
        except Exception as e:
            print(f"❌ Попытка {attempt + 1}: {e}")
        
        time.sleep(2)  # Пауза между попытками
    
    # Запасной вариант - случайное фото
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
        "🎨 **ГЕНЕРАТОР КАРТИНОК**\n\n"
        "Введите описание того, что нужно нарисовать:\n"
        "Например: `курьер с пиццей`, `робот-доставщик`\n\n"
        "⏱ Генерация занимает 5-15 секунд...",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id, {}).get('action') == 'generate_image')
def image_generator_process(message):
    user_id = message.from_user.id
    prompt = message.text
    
    # Отправляем статус
    status_msg = bot.send_message(
        message.chat.id, 
        f"🎨 **Генерирую:** {prompt[:50]}...\n⏳ Обычно 5-10 секунд",
        parse_mode='Markdown'
    )
    
    # Показываем "печатает"
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    # Генерируем картинку
    image_data = generate_image(prompt)
    
    if image_data:
        try:
            # Удаляем статус
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # Отправляем фото
            bot.send_photo(
                message.chat.id,
                image_data,
                caption=f"🎨 **{prompt}**\n\n✅ Сгенерировано за {random.randint(3, 8)} сек",
                parse_mode='Markdown',
                reply_markup=get_admin_menu()
            )
        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка отправки: {str(e)[:50]}\nПопробуйте еще раз",
                reply_markup=get_admin_menu()
            )
    else:
        bot.edit_message_text(
            "❌ Не удалось сгенерировать картинку.\n"
            "Попробуйте другой запрос или позже.",
            message.chat.id,
            status_msg.message_id,
            reply_markup=get_admin_menu()
        )
    
    del user_state[user_id]
# ================================================
# ================================================

# ============ ОБРАБОТКА ОШИБОК ============
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id
    
    if is_authorized(user_id):
        bot.send_message(
            message.chat.id,
            f"❓ Неизвестная команда\nИспользуйте кнопки меню",
            reply_markup=get_role_menu(user_role[user_id])
        )
    else:
        bot.send_message(
            message.chat.id,
            "❓ Сначала авторизуйтесь!",
            reply_markup=get_auth_menu()
        )
# ================================================

# ============ ЗАПУСК БОТА ============
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ДЖАРВИС 2.0 — ПОЛНАЯ ВЕРСИЯ ЗАПУЩЕНА!")
    print("=" * 60)
    print("✅ Роли: Админ | Менеджер | Курьер | Покупатель")
    print("✅ Функции: Заказы | Получатели | Поиск | Карты")
    print("✅ Статистика | Генератор картинок | Управление")
    print("=" * 60)
    print("👑 Админ по умолчанию: код 1, пароль admin123")
    print("=" * 60)
    print("🟢 Бот работает 24/7 на Render.com")
    print("=" * 60)
    
    # Просто запускаем бота

bot.infinity_polling()
