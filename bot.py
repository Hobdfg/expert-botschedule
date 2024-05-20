import telebot
from info import about_bot, guide

gpt = GPT()
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def introduce(message):
    bot.send_message(message.chat.id, f"{about_bot}")


@bot.message_handler(commands=['help'])
def sendhelp(message):
    bot.send_message(message.chat.id, f"{guide}")