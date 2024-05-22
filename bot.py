import logging
import telebot
import config
import utils

from info import about_bot, guide
from db import (prepare_db,
                count_user_blocks, count_project_blocks,
                count_user_tokens, count_project_tokens,
                count_users, is_user_exists,
                load_gpt_message, store_gpt_message,
                store_stt_message,
                load_schedule, store_schedule,
                change_schedule_day,
                change_schedule_time,
                change_schedule_lesson)
from creds import CRED
from speechkit import STT

cred = CRED(iam_token=utils.get_iam_token())

stt = STT(url=config.URL_STT,
          cred=cred,
          folder_id=utils.get_folder_id())

gpt = GPT()
bot = telebot.TeleBot(utils.get_telegram_token())


@bot.message_handler(commands=['start'])
def introduce(message):
    bot.send_message(message.chat.id, f"{about_bot}")


@bot.message_handler(commands=['help'])
def sendhelp(message):
    bot.send_message(message.chat.id, f"{guide}")


try:
    prepare_db()
    logging.info('Бот запущен')
    bot.polling(non_stop=True)
except Exception as e:
    logging.error(f'Ошибка бота, {e}')
    exit()
