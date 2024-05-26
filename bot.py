import telebot
from telebot import types
import math
import json
import re

from time import sleep
from info import get_commands
from db import (prepare_db,
                count_user_blocks, count_project_blocks,
                count_user_tokens, count_project_tokens,
                count_users, is_user_exists,
                load_gpt_message, store_gpt_message,
                store_stt_message,
                load_schedule, store_schedule, delete_schedule,
                load_schedule_days,
                load_schedule_now)
from yandex_gpt import GPT
from creds import CRED
from speechkit import STT

import scheduler
import logging
import config
import utils


bot = telebot.TeleBot(token=utils.get_telegram_token())

cred = CRED(iam_token=utils.get_iam_token())

stt = STT(url=config.URL_STT,
          cred=cred,
          folder_id=utils.get_folder_id())

gpt = GPT(url=config.URL_GPT,
          cred=cred,
          folder_id=utils.get_folder_id())


def scheduler_handler():
    while True:
        sleep(config.SCHEDULER_PERIODS)
        tasks = load_schedule_now()
        for task in tasks:
            user_id = task[0]
            time = task[1]
            lesson = task[2]
            bot.send_message(user_id,
                             text=f'Напоминание о начале события\n'
                                  f'{time} - {lesson}')

            create_motivation_message(user_id, user_prompt=lesson)


def voice_to_text(message):
    user_id = message.from_user.id

    # Считаем аудиоблоки и проверяем сумму потраченных аудиоблоков
    status, result = is_stt_block_limit(user_id, message.voice.duration)
    if not status:
        return status, result

    stt_blocks = result
    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = stt.speech_to_text(file)  # преобразовываем голосовое сообщение в текст

    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        # Записываем сообщение и кол-во аудиоблоков в БД
        store_stt_message(user_id, text, stt_blocks)

    return status, text


def response_stt(message):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я перевел его в текст')
    bot.register_next_step_handler(msg, stt_handler)


# Переводим голосовое сообщение в текст после команды stt
def stt_handler(message):
    user_id = message.from_user.id
    text = message.text

    # Проверка и выполнение команды бота
    if process_command(message, text):
        return

    # Проверка, что сообщение действительно голосовое
    if message.content_type != 'voice':
        msg = bot.send_message(user_id, 'Отправь голосовое сообщение')
        bot.register_next_step_handler(msg, stt_handler)
        return

    status, text = voice_to_text(message)

    if status:
        msg = bot.send_message(user_id, text, reply_to_message_id=message.id)
        bot.register_next_step_handler(msg, stt_handler)
    else:
        keyboard = create_keyboard([{'text': 'Попробовать еще раз'}])
        send_error_message(user_id, text, keyboard, stt_handler)


def create_user_prompt(action, message):
    user_id = message.from_user.id
    text = 'Отправить мне голосовое или тестовое сообщение'
    if action == 'add':
        text += ' для добавления записи в расписание'
    elif action == 'delete':
        text += ' для удаления записи из расписания'
    msg = bot.send_message(user_id,
                           text=text,
                           reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_user_prompt, args=action)

    # Сбрасываем диалог с пользователем, записываем в БД пустое сообщение
    store_gpt_message(user_id, message=[], tokens=0)


def response_get_schedule(message):
    user_id = message.from_user.id

    days = load_schedule_days(user_id)
    if len(days) > 0:
        days_keys = []
        for day in days:
            days_keys.append({'text': day})
        keyboard = create_keyboard(days_keys)
        msg = bot.send_message(user_id,
                         text='Выбери день для просмотра расписания',
                         reply_markup=keyboard)
        bot.register_next_step_handler(msg, get_schedule_handler)
    else:
        bot.send_message(user_id,
                         text='К сожалению расписание отсутствует 🥲',
                         reply_markup=types.ReplyKeyboardRemove())


def get_schedule_handler(message):
    user_id = message.from_user.id
    text = message.text

    # Проверка и выполнение команды бота
    if process_command(message, text):
        return

    send_schedule(user_id, text)


def send_schedule(user_id, day):
    schedule = ''
    rows = load_schedule(user_id, day=day)
    for row in rows:
        if schedule:
            schedule += '\n'
        schedule += f'{row[0]} - {row[1]}'
    if schedule:
        bot.send_message(user_id,
                         text=f'Расписание на {day}:\n{schedule}',
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(user_id,
                         text='К сожалению расписание отсутствует 🥲',
                         reply_markup=types.ReplyKeyboardRemove())


def response_add_schedule(message):
    user_id = message.from_user.id

    # Проверяем количество уже зарегистрированных пользователей
    if not utils.is_superuser(user_id) and not is_user_exists(user_id):
        users_count = count_users()
        if users_count >= config.MAX_USERS:
            logging.warning(f'Количество зарегистрированных пользователей превышает {config.MAX_USERS}')
            bot.send_message(user_id,
                             text='К сожалению зарегистрировано максимальное количество пользователей :(',
                             reply_markup=types.ReplyKeyboardRemove())
            return

    # Создаем промт пользователя
    create_user_prompt(action='add', message=message)


def response_delete_schedule(message):
    # Создаем промт пользователя
    create_user_prompt(action='delete', message=message)


def generate_answer(user_id, messages):
    status, result = gpt.count_tokens_in_dialog(messages)
    if not status:
        return status, result
    messages_tokens = result

    if not utils.is_superuser(user_id):
        # Проверяем хватает ли токенов на запрос + ответ
        user_tokens = count_user_tokens(user_id)
        if user_tokens + messages_tokens + config.MAX_MODEL_TOKENS > config.MAX_USER_TOKENS:
            logging.warning(f'Количество токенов сессии пользователя {user_id} превышает {config.MAX_USER_TOKENS}')
            return False, (f'количество токенов сессии превышает максимальное количество {config.MAX_USER_TOKENS}, '
                           f'уменьши длину запроса и попробуй еще раз')

        # Проверяем хватает ли токенов выделенных на проект
        project_tokens = count_project_tokens()
        if project_tokens + messages_tokens + config.MAX_MODEL_TOKENS > config.MAX_PROJECT_TOKENS:
            logging.warning(f'Количество токенов проекта превышает {config.MAX_PROJECT_TOKENS}')
            return False, (f'количество токенов проекта превышает максимальное количество {config.MAX_PROJECT_TOKENS}, '
                           f'уменьши длину запроса и попробуй еще раз')

    # Создаем запрос к GPT
    request = gpt.make_request(messages)

    # Отправляем запрос к GPT
    status, response = gpt.send_request(request)
    if not status:
        return status, response

    # Обрабатываем полученный ответ от GPT
    status, content = gpt.process_response(response)
    if not status:
        return status, content

    message = gpt.get_result_data()['alternatives'][0]['message']
    messages.append(message)

    total_tokens = utils.to_int(gpt.get_result_data()['usage']['totalTokens'])

    # Записываем сообщение и кол-во токенов в БД
    store_gpt_message(user_id, messages, total_tokens)

    return True, content


def create_motivation_message(user_id, user_prompt):
    # Создаем системный промт при начале диалога
    messages = [
        {'role': 'system', 'text': config.SYSTEM_PROMPT_MOTIVATION},
        {'role': 'user', 'text': user_prompt}
    ]

    # Получаем статус и содержимое ответа от Yandex GPT
    status, result = generate_answer(user_id, messages)

    # Если ответ успешно сгенерирован
    if status:
        bot.send_message(user_id,
                         text=result,
                         reply_markup=types.ReplyKeyboardRemove())

    # Если не удалось сгенерировать ответ или не удалось разобрать ответ
    if not status:
        send_error_message(user_id, result)


def create_prompts(user_id, system_prompt, user_prompt):
    messages = load_gpt_message(user_id)

    # Создаем системный промт при начале диалога
    if len(messages) == 0:
        messages.append({'role': 'system', 'text': system_prompt})

    # Создаем пользовательский промт
    messages.append({'role': 'user', 'text': user_prompt})

    return messages


def create_answer(message, user_prompt, action):
    user_id = message.from_user.id

    # Создаем список с промтами
    messages = create_prompts(user_id, system_prompt=config.SYSTEM_PROMPT_SCHEDULE, user_prompt=user_prompt)

    # Получаем статус и содержимое ответа от Yandex GPT
    status, result = generate_answer(user_id, messages)

    # Если ответ успешно сгенерирован
    if status:
        status, result = process_answer(result)

    # Если успешно разобран ответ
    if status:
        day = result['day']
        time = result['time']
        lesson = result['lesson']
        if action == 'add':
            store_schedule(user_id, day, time, lesson)
            send_schedule(user_id, day)
        elif action == 'delete':
            delete_schedule(user_id, day, time)
            send_schedule(user_id, day)
        else:
            status = False
            result = f'действие {action} неизвестно'

    # Если не удалось сгенерировать ответ или не удалось разобрать ответ
    if not status:
        keyboard = create_keyboard([{'text': 'Попробовать еще раз'}])
        send_error_message(user_id, result, keyboard, create_answer_again, user_prompt)


def process_answer(answer):
    # Проверка json
    data = {}
    try:
        pattern = r"({[\w\W]+?})"
        jsons = re.findall(pattern, answer)
        if len(jsons) > 0:
            data = json.loads(jsons[0])
    except Exception as e:
        logging.error(f'Ошибка извлечения JSON из ответа Yandex GPT, {e}')
        return False, 'возникла ошибка извлечения JSON из ответа Yandex GPT'

    if 'day' not in data or 'time' not in data:
        return False, 'в ответе содержатся не все атрибуты'
    if 'lesson' not in data:
        data['lesson'] = None

    return True, data


def create_answer_again(message, args):
    if not process_command(message, message.text):
        if message.text == 'Попробовать еще раз':
            user_prompt = args
        else:
            user_prompt = message.text
        create_answer(message, user_prompt)


def send_error_message(user_id, error_message, keyboard=None, next_step_handler=None, next_step_args=None):
    if not keyboard:
        keyboard = types.ReplyKeyboardRemove()

    # отправляем сообщение
    msg = bot.send_message(user_id,
                           text=f'Я не могу тебе помочь, так как {error_message}',
                           reply_markup=keyboard)

    # регистрируем следующий "шаг"
    if next_step_handler and next_step_args:
        bot.register_next_step_handler(msg, next_step_handler, args=next_step_args)
    elif next_step_handler:
        bot.register_next_step_handler(msg, next_step_handler)



def is_stt_block_limit(user_id, duration):
    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / config.AUDIO_BLOCK)  # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = count_user_blocks(user_id) + audio_blocks

    # Проверяем, что аудио длится больше 1 секунд
    if duration < 1:
        return False, 'SpeechKit STT работает с голосовыми сообщениями больше 1 секунды'

    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        return False, 'SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд'

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= config.MAX_USER_STT_BLOCKS:
        msg = (f"Превышен общий лимит SpeechKit STT {config.MAX_USER_STT_BLOCKS}. "
               f"Использовано {all_blocks} блоков. Доступно: {config.MAX_USER_STT_BLOCKS - all_blocks}")
        return False, msg

    return True, audio_blocks


def get_user_prompt(message, args=None):
    user_id = message.from_user.id
    text = message.text
    action = args

    if process_command(message, text):
        return

    # Проверка, что сообщение действительно голосовое
    if message.content_type == 'voice':
        status, text = voice_to_text(message)
    elif message.content_type == 'video_note':
        text = 'пока не умею работать с кружками'
        status = False
    else:
        status = True

    if status:
        bot.send_message(user_id,
                         text='⌛️ Уже обрабатываю твой запрос',
                         reply_markup=types.ReplyKeyboardRemove())
        create_answer(message, user_prompt=text, action=action)
    else:
        send_error_message(user_id, text)


def create_keyboard(buttons_list):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    for button in buttons_list:
        keyboard.add(types.KeyboardButton(text=button['text']))
    return keyboard


def create_inline_keyboard(buttons_list):
    keyboard = types.InlineKeyboardMarkup()
    for button in buttons_list:
        keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['callback_data']))
    return keyboard


def response_start(message):
    user_id = message.from_user.id
    bot.send_message(user_id,
                     parse_mode='MarkdownV2',
                     text=f'Привет, я бот, который поможет тебе организовать неделю, '
                          'отправь команду /add, чтобы добавить расписание и я тебя уведомлю, в нужный момент, '
                          'буду тебя поддерживать и подбадривать для достижения цели\\.\n\n'
                          'А еще я понимаю такие команды:\n' +
                          commands_to_string(),
                     reply_markup=types.ReplyKeyboardRemove())


def response_help(message):
    user_id = message.from_user.id
    bot.send_message(user_id,
                     parse_mode='MarkdownV2',
                     text=f'Для работы со мной вы можете использовать одну из команд:\n\n' +
                          commands_to_string(),
                     reply_markup=types.ReplyKeyboardRemove())


def response_stats(message):
    user_id = message.from_user.id
    project_blocks = count_project_blocks()
    project_tokens = count_project_tokens()
    users_count = count_users()
    bot.send_message(user_id,
                     text=f'Общее количество использованных блоков SpeechKit STT: {project_blocks}\n'
                          f'Общее количество использованных токенов Yandex GPT: {project_tokens}\n'
                          f'Общее количество пользователей: {users_count}',
                     reply_markup=types.ReplyKeyboardRemove())


def response_debug(message):
    log_file_name = config.LOG_FILENAME
    with open(log_file_name, "rb") as f:
        bot.send_document(message.chat.id, f)


def process_command(message, text):
    is_processed = False
    if text:
        for command in commands:
            handler = None
            if command['command'] == text.lower():
                handler = command['handler']
            else:
                keywords = command['keywords']
                for keyword in keywords:
                    if keyword == text.lower():
                        handler = command['handler']
            if handler:
                handler(message)
                is_processed = True
    return is_processed


def process_message(message, text):
    if not process_command(message, text):
        bot.send_message(message.chat.id,
                         parse_mode='MarkdownV2',
                         text=f'К сожалению я не понял вас, попробуйте уточнить свой запрос\n' +
                              'Я понимаю следующие команды:\n\n' +
                              commands_to_string())

        reaction = telebot.types.ReactionTypeEmoji(emoji='😢')
        bot.set_message_reaction(message_id=message.id, chat_id=message.chat.id, reaction=[reaction])


def commands_to_string():
    result = ''
    for command in commands:
        if command['command'] and command['description'] and not command['hidden']:
            result += f"*{command['command']}* \\- {command['description']}\n"
    return result


@bot.message_handler(content_types=['text'])
def text_message(message):
    process_message(message, message.text)


@bot.message_handler(content_types=['voice'])
def media_message(message):
    process_message(message, message.text)


@bot.message_handler(content_types=['sticker'])
def media_message(message):
    bot.send_message(message.chat.id, text='Классный стикер👍')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Удаляем кнопку ответа на сообщение
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)

    process_message(call.message, call.data)
    bot.answer_callback_query(call.id)


menu_commands = []
commands = get_commands({'response_start': response_start,
                         'response_help': response_help,
                         'response_stt': response_stt,
                         'response_stats': response_stats,
                         'response_debug': response_debug,
                         'response_get_schedule': response_get_schedule,
                         'response_add_schedule': response_add_schedule,
                         'response_delete_schedule': response_delete_schedule
                         })
for command in commands:
    if command['command'] and command['description'] and not command['hidden']:
        menu_commands.append(telebot.types.BotCommand(command['command'], command['description']))

prepare_db()
scheduler.scheduler_start(scheduler_handler)
try:
    logging.info("Бот запущен")
    bot.set_my_commands(menu_commands)
    bot.polling(non_stop=True)
except Exception as e:
    logging.error(f'Ошибка обращения к Telegram, {e}')
    exit()
