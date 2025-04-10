# Необходимые библиотеки
import telebot
from telebot import types
import webbrowser
import logging

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Инициализация бота
bot = telebot.TeleBot('8137672279:AAF9uSfrT9AI_7xLnRfU32s4bE4WK4H9CmU')  # Замените на свой токен!

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def greeting_user(message):
    try:
        text = (
            f"Здравствуй {message.from_user.first_name} {message.from_user.last_name}!\n"
            "Что хочешь найти или узнать?\n"
            "Если не знаешь, как пользоваться ботом, введи команду /main_commands."
        )
        bot.send_message(message.chat.id, text)
    except Exception as e:
        logging.error(f"Ошибка в /start: {e}")

# Обработчик команды /main_commands
@bot.message_handler(commands=['main_commands'])
def show_commands_from_user(message):
    try:
        commands = (
            "Доступные команды:\n"
            "/start - Начать диалог\n"
            "/help - Получить помощь\n"
            "/site - Открыть сайт проекта\n\n"
            "Просто напиши мне название места или события!"
        )
        bot.send_message(message.chat.id, commands)
    except Exception as e:
        logging.error(f"Ошибка в /main_commands: {e}")
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

# Обработчик команды /site
@bot.message_handler(commands=['site', 'website'])
def site(message):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton(
            text='Да', 
            url='https://github.com/Sayrend/CityGuideBot.git'
        )
        btn_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        markup.add(btn_yes, btn_no)
        
        bot.send_message(
            message.chat.id,
            f"{message.from_user.first_name}, хочешь перейти на наш сайт?",
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"Ошибка в /site: {e}")

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def info(message):
    try:
        if message.text.lower() == 'привет':
            bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!")
        elif message.text.lower() == 'id':
            bot.reply_to(message, f"Ваш ID: {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка обработки текста: {e}")

# Обработчик фотографий
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    try:
        bot.reply_to(message, "Обрабатываю изображение...")
    except Exception as e:
        logging.error(f"Ошибка обработки фото: {e}")

# Обработчик кнопки "Нет"
@bot.callback_query_handler(func=lambda call: call.data == 'no')
def handle_no(call):
    try:
        bot.answer_callback_query(call.id, "Хорошо, остаемся здесь.")
    except Exception as e:
        logging.error(f"Ошибка обработки callback: {e}")

# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
