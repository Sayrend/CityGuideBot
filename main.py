# Необходимые библиотеки
import telebot
from telebot import types
import webbrowser
import logging
import requests
import ipinfo
from geopy.geocoders import Nominatim
import json
import os

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot('8137672279:AAEV7GXa-SkT6kALay2N29dSvU2tgkoGIV4') 

# API
IPINFO = 'f52507bbfd74da'
WEATHER = 'c9f078e70661690986911a690bfcb0fe'
USER_DATA_FILE = 'user_info.json'  # Файл для хранения данных пользователя

# Инициализация гео кодера
geocoder = Nominatim(user_agent="city_gide_bot")

# Функции для работы с данными пользователя
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки user_data: {e}")
            return {}
    return {}

def save_user_data():
    """Сохраняет данные пользователей в файл"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка сохранения user_data: {e}")

# Загрузка данных при запуске
user_data = load_user_data()

# Функция нормализации названий городов
def normalize_city_name(city):
    city_mapping = {
        "Moscow": "Москва",
        "Saint Petersburg": "Санкт-Петербург",
        "St. Petersburg": "Санкт-Петербург",
        "Tyumen": "Тюмень",
        "Samara": "Самара",
        "Tymen": "Тюмень",
        "Tyumen'": "Тюмень",
        "SPB": "Санкт-Петербург",
        "Питер": "Санкт-Петербург",
        "Санкт-Петербург": "Санкт-Петербург"
    }
    return city_mapping.get(city, city)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def greeting_user(message):
    try:
        text = (
            f"Здравствуй {message.from_user.first_name}!\n"
            "Что хочешь найти или узнать?\n"
            "Если не знаешь, как пользоваться ботом, введи команду /main_commands."
        )
        bot.send_message(message.chat.id, text)
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

# Обработчик команды /main_commands
@bot.message_handler(commands=['main_commands'])
def show_commands_from_user(message):
    try:
        commands = (
            "Доступные команды:\n"
            "/help - Получить помощь\n"
            "/find_city - Определить город по IP\n"
            "/weather - Узнать погоду\n"
            "/catalog - Показать достопримечательности"
        )
        bot.send_message(message.chat.id, commands)
    except Exception as e:
        logger.error(f"Ошибка в /main_commands: {e}")
        bot.send_message(message.chat.id, "Ошибка при загрузке команд")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def helping_user(message):
    help_text = (
        "Помощь:\n"
        "1. Используй /main_commands для списка команд.\n"
        "2. FAQ будет добавлен в ближайшем обновлении.\n"
        "3. По вопросам пиши сюда @Max1m_ML."
    )
    bot.send_message(message.chat.id, help_text)

# Обработчик команды /find_city
@bot.message_handler(commands=['find_city'])
def find_city_by_ip(message):
    try:
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) > 1:
            city = command_parts[1].strip()
            user_data[str(message.chat.id)] = {
                'city': city,
                'confirmed': True
            }
            save_user_data()
            bot.reply_to(message, f"✅ Город {city} сохранен!")
            return
            
        handler = ipinfo.getHandler(IPINFO)
        details = handler.getDetails()
        
        if details.city:
            city = normalize_city_name(details.city)
            user_data[str(message.chat.id)] = {
                'city': city,
                'confirmed': False
            }
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton('✅ Да', callback_data=f'confirm_{city}'),
                types.InlineKeyboardButton('❌ Нет', callback_data='ask_manual')
            )
            bot.reply_to(
                message, 
                f"📍 Мы определили ваш город как: {city}\nЭто верно?", 
                reply_markup=markup
            )
        else:
            bot.reply_to(message, "Не удалось определить город. Введите вручную: /find_city Москва")
            
    except Exception as e:
        logger.error(f"Ошибка определения города: {e}")
        bot.reply_to(message, "⚠️ Ошибка определения города")

# Обработчик кнопок подтверждения города
@bot.callback_query_handler(func=lambda call: True)
def handle_city_confirmation(call):
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        
        if call.data.startswith('confirm_'):
            city = call.data.split('_', 1)[1]
            user_data[str(call.message.chat.id)] = {
                'city': city,
                'confirmed': True
            }
            save_user_data()
            bot.send_message(
                call.message.chat.id,
                f"✅ Город {city} сохранен!\n"
                "Теперь вы можете использовать /catalog"
            )
            
        elif call.data == 'ask_manual':
            bot.send_message(
                call.message.chat.id,
                "✏️ Введите город в формате:\n/find_city Москва"
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка")

# Каталог достопримечательностей
CITY_CATALOG = {
    "Москва": {
        "Основные": ["Красная площадь", "Кремль", "Арбат"],
        "Кафе": ["Кафе Пушкин", "Му-Му", "Чайхона №1"],
        "Рестораны": ["Twins Garden", "White Rabbit", "Selfie"],
        "Парки": ["Парк Горького", "ВДНХ", "Царицыно"],
        "Музеи": ["Третьяковская галерея", "Музей современного искусства «Гараж»", "Пушкинский музей"]
    },
    "Санкт-Петербург": {
        "Основные": ["Эрмитаж", "Дворцовая площадь", "Петропавловская крепость"],
        "Кафе": ["Гастрономика", "Буше", "КоКоКо"],
        "Рестораны": ["Probka", "Сад", "Il Lago dei Cigni."],
        "Парки": ["Летний сад", "Марсово поле", "Елагин остров"],
        "Музеи": ["Музей железных дорог России", "Военно-морской музей", "Эрмитаж"]
    },
    "Тюмень": {
        "Основные": ["Мост влюблённых", "Набережная реки Туры", "Сквер Сибирских кошек"],
        "Рестораны": ["150 meters", "Calcutta wine club", "Cafe 15/86"],
        "Кафе": ["Кацо Хинкальная", "Баши Грузинское бистро", "Кахети Кафе"],
        "Парки": ["Экопарк «Затюменский»", "Гилёвская роща", "Цветной бульвар"],
        "Музеи": ["Музейный комплекс имени И. Я. Словцова", "Музей «Городская Дума»", "Россия — Моя история"]
    }
}

# Команда /catalog
@bot.message_handler(commands=['catalog', 'достопримечательности'])
def handle_catalog_command(message):
    try:
        chat_id = str(message.chat.id)
        
        # Проверка наличия сохранённого города
        if chat_id not in user_data or not user_data[chat_id].get('confirmed'):
            bot.reply_to(message, "❌ Сначала определите ваш город через /find_city")
            return
            
        city = user_data[chat_id]['city']
        normalized_city = normalize_city_name(city)
        
        # Проверка наличия данных о городе
        if normalized_city not in CITY_CATALOG:
            bot.reply_to(message, f"❌ К сожалению, у меня нет данных по городу {normalized_city}")
            return
            
        # Формирование списка категорий
        categories = list(CITY_CATALOG[normalized_city].keys())
        categories_list = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(categories)])
        
        # Сохранение состояния для этого пользователя
        user_data[chat_id]['catalog'] = {
            'city': normalized_city,
            'categories': categories
        }
        save_user_data()
        
        # Создание клавиатуры с кнопками категорий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for i, category in enumerate(categories):
            markup.add(types.KeyboardButton(f"{i+1}. {category}"))
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        bot.send_message(
            chat_id,
            f"🏙️ Достопримечательности города {normalized_city}:\n\n"
            "Выберите категорию, отправив её номер:\n\n"
            f"{categories_list}\n\n"
            "Просто нажмите на нужную кнопку ниже 👇",
            reply_markup=markup
        )
        
    except Exception as e:
        logging.error(f"Ошибка показа каталога: {e}")
        bot.reply_to(message, "⚠️ Ошибка при загрузке каталога")

# Обработчик выбора категории через кнопки
@bot.message_handler(func=lambda message: message.text.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')))
def handle_category_selection(message):
    try:
        chat_id = str(message.chat.id)
        
        # Проверка состояния каталога
        if 'catalog' not in user_data.get(chat_id, {}):
            bot.reply_to(message, "❌ Сначала запустите /catalog")
            return
            
        catalog_data = user_data[chat_id]['catalog']
        city = catalog_data['city']
        categories = catalog_data['categories']
        
        # Получие номера категории из текста
        try:
            category_num = int(message.text.split('.')[0]) - 1
        except:
            bot.reply_to(message, "❌ Неверный формат выбора категории")
            return
            
        # Проверка валидности номера
        if category_num < 0 or category_num >= len(categories):
            bot.reply_to(message, "❌ Неверный номер категории")
            return
            
        category = categories[category_num]
        
        # Получение места для категории
        places = CITY_CATALOG[city][category]
        places_text = "\n".join([f"• {place}" for place in places])
        
        # Замена клавиатуры
        remove_keyboard = types.ReplyKeyboardRemove()
        
        bot.send_message(
            chat_id,
            f"📍 {category} в городе {city}:\n\n{places_text}\n\n"
            "Чтобы посмотреть другие достопримечательности, снова используйте /catalog",
            reply_markup=remove_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка показа категории: {e}")
        bot.reply_to(message, "⚠️ Ошибка при загрузке категории")

# Обработчик кнопки "Отмена"
@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def handle_cancel(message):
    try:
        chat_id = str(message.chat.id)
        if 'catalog' in user_data.get(chat_id, {}):
            del user_data[chat_id]['catalog']
            save_user_data()
        
        remove_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(
            chat_id,
            "❌ Выбор категории отменен",
            reply_markup=remove_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка отмены: {e}")

# Обработчик команды /weather
@bot.message_handler(commands=['weather'])
def get_weather(message):
    try:
        chat_id = message.chat.id
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) > 1:
            city = command_parts[1]
        else:
            if str(chat_id) in user_data and user_data[str(chat_id)].get('confirmed'):
                city = user_data[str(chat_id)]['city']
            else:
                bot.reply_to(message, "❌ Город не указан и не сохранён.\n"
                                      "Укажите город: /weather Москва")
                return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        if data.get('cod') != 200:
            error_msg = data.get('message', 'Неизвестная ошибка')
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                text="✏️ Ввести другой город", 
                callback_data="weather_manual"
            ))
            
            bot.reply_to(
                message, 
                f"⚠️ Не удалось получить погоду для {city}: {error_msg}", 
                reply_markup=markup
            )
            return
            
        weather = (
            f"⛅ Погода в {city}:\n"
            f"🌡️ Температура: {data['main']['temp']}°C\n"
            f"😓 Ощущается как: {data['main']['feels_like']}°C\n"
            f"💧 Влажность: {data['main']['humidity']}%\n"
            f"💨 Ветер: {data['wind']['speed']} м/с\n"
            f"☁️ {data['weather'][0]['description'].capitalize()}"
        )
        bot.reply_to(message, weather)
        
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка при получении погоды")

# Обработчик ручного ввода для погоды
@bot.callback_query_handler(func=lambda call: call.data == 'weather_manual')
def handle_weather_manual(call):
    bot.send_message(
        call.message.chat.id,
        "✏️ Введите команду в формате: /weather Москва"
    )

# Запуск бота
if __name__ == "__main__":
    try:
        logger.info("Бот запущен!")
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        
        logger.error(f"Ошибка запуска бота: {e}")
