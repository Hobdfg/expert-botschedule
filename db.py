import sqlite3
import logging
import config
import json

import utils
from datetime import datetime

database = config.DATABASE_FILENAME


# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(sql_query, data=None):
    rows = []
    try:
        utils.prepare_folder(database)
        connection = sqlite3.connect(database)
        cursor = connection.cursor()
        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)
        rows = cursor.fetchall()
        connection.commit()
        connection.close()
    except Exception as e:
        logging.error(f'Ошибка выполнения sql-запроса: {sql_query}, values={str(data)}, {e}')
    return rows


def create_messages_table():
    sql_query = '''
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        message TEXT,
        stt_blocks INTEGER,
        tokens INTEGER)
    '''
    execute_query(sql_query)


def create_schedules_table():
    sql_query = '''
        CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        day TEXT,
        time TEXT,
        lesson TEXT)
    '''
    execute_query(sql_query)


def prepare_db():
    create_messages_table()
    create_schedules_table()


def insert_message_row(user_id, message, cell, value):
    # Вставляем в таблицу сообщение и заполняем ячейку cell значением value
    sql_query = f'''INSERT INTO messages (user_id, message, {cell}) VALUES (?, ?, ?)'''
    execute_query(sql_query, data=(user_id, message, value))


def insert_schedule_row(user_id, day, time, lesson):
    # Вставляем в таблицу расписание
    sql_query = f'''INSERT INTO schedules (user_id, day, time, lesson) VALUES (?, ?, ?, ?)'''
    execute_query(sql_query, data=(user_id, day, time, lesson))


def update_schedule_row(user_id, day, time, cell, value):
    # Обновляем информацию в таблице расписания
    sql_query = f'''
        UPDATE schedules
        SET {cell}=?
        WHERE user_id=? AND day=? AND time=?
    '''
    execute_query(sql_query, data=(value, user_id, day, time))


def delete_schedule_row(user_id, day, time):
    day = day.lower()
    # Удаляем из таблицы расписания
    sql_query = f'''DELETE FROM schedules WHERE user_id=? AND day=? AND time=?'''
    execute_query(sql_query, data=(user_id, day, time))


def get_rows_value(rows, row=0, field=0, default=None):
    # Проверяем rows на наличие хоть какого-то результата запроса и на то,
    # что в результате мы получили какое-то значение в rows[row][field]
    if rows and rows[row] and rows[row][field]:
        return rows[row][field]
    else:
        # Результата нет, так как у нас ещё нет записей
        return default


def count_user_blocks(user_id):
    sql_query = f'''SELECT SUM(stt_blocks) FROM messages WHERE user_id=?'''
    rows = execute_query(sql_query, (user_id,))
    return get_rows_value(rows, row=0, field=0, default=0)


def count_project_blocks():
    sql_query = f'''SELECT SUM(stt_blocks) FROM messages'''
    rows = execute_query(sql_query)
    return get_rows_value(rows, row=0, field=0, default=0)


def count_user_tokens(user_id):
    sql_query = f'''SELECT SUM(tokens) FROM messages WHERE user_id=?'''
    rows = execute_query(sql_query, (user_id,))
    return get_rows_value(rows, row=0, field=0, default=0)


def count_project_tokens():
    sql_query = f'''SELECT SUM(tokens) FROM messages'''
    rows = execute_query(sql_query)
    return get_rows_value(rows, row=0, field=0, default=0)


def count_users():
    sql_query = f'''SELECT DISTINCT user_id FROM messages'''
    rows = execute_query(sql_query)
    return len(rows)


def is_user_exists(user_id):
    sql_query = f'''SELECT COUNT(*) FROM messages WHERE user_id=?'''
    rows = execute_query(sql_query, (user_id,))
    if get_rows_value(rows, row=0, field=0, default=0) > 0:
        return True
    else:
        return False


def load_gpt_message(user_id):
    sql_query = '''
        SELECT message FROM messages
        WHERE user_id=? AND tokens IS NOT NULL
        ORDER BY id DESC LIMIT 1
    '''
    rows = execute_query(sql_query, (user_id,))
    json_string = get_rows_value(rows, row=0, field=0, default='[]')

    # Преобразуем json-строку в нужный нам формат списка словарей
    messages = json.loads(json_string)
    return messages


def store_gpt_message(user_id, message, tokens):
    # Преобразуем список словарей сообщений к виду json
    json_string = json.dumps(message, ensure_ascii=False)

    insert_message_row(user_id, message=json_string, cell= 'tokens', value=tokens)


def store_stt_message(user_id, message, stt_blocks):
    insert_message_row(user_id, message=message, cell= 'stt_blocks', value=stt_blocks)


def load_schedule(user_id, day):
    day = day.lower()
    sql_query = '''
        SELECT time, lesson FROM schedules
        WHERE user_id=? AND day=?
        ORDER BY time
    '''
    rows = execute_query(sql_query, (user_id, day,))
    return rows


def store_schedule(user_id, day, time, lesson):
    day = day.lower()
    time = datetime.strptime(time, '%H:%M').strftime('%H:%M')

    sql_query = '''
        SELECT lesson FROM schedules
        WHERE user_id=? AND day=? AND time=?
    '''
    rows = execute_query(sql_query, (user_id, day, time,))

    if len(rows) == 0:
        insert_schedule_row(user_id, day, time, lesson)
    else:
        update_schedule_row(user_id, day, time, cell='lesson', value=lesson)


def delete_schedule(user_id, day, time):
    day = day.lower()
    time = datetime.strptime(time, '%H:%M').strftime('%H:%M')

    delete_schedule_row(user_id, day, time)


def load_schedule_days(user_id):
    sql_query = '''
        SELECT DISTINCT day FROM schedules
        WHERE user_id=?
    '''
    rows = execute_query(sql_query, (user_id,))
    days = []
    for row in rows:
        days.append(row[0])
    days = list(filter(lambda it: it in days, utils.day_of_week()))
    return days


def load_schedule_now():
    now = datetime.now()
    day_num = utils.to_int(now.strftime('%w')) - 1
    if day_num < 0:
        day_num = 6
    day = utils.day_of_week()[day_num]
    time = now.strftime('%H:%M')

    # time = '11:00'

    sql_query = '''
        SELECT user_id, time, lesson FROM schedules
        WHERE day=? AND time=?
    '''
    rows = execute_query(sql_query, (day, time))
    return rows
