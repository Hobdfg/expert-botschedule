import telebot
from info import about_bot, guide
from db import create_table

gpt = GPT()
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def introduce(message):
    bot.send_message(message.chat.id, f"{about_bot}")


@bot.message_handler(commands=['help'])
def sendhelp(message):
    bot.send_message(message.chat.id, f"{guide}")


try:
    create_table()
    # logging.info('Бот запущен')
    bot.polling(non_stop=True)
except Exception as e:
    # logging.error(f'Ошибка бота, {e}')
    exit()