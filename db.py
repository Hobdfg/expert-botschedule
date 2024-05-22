import sqlite3
import logging
import config
import json


database = config.DATABASE_FILENAME


# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(sql_query, data=None):
    rows = []
    try:
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


def create_table():
    sql_query = '''
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        stt_blocks INTEGER,
        tokens INTEGER)
    '''
    execute_query(sql_query)


def create_table_schedule():
    sql_query = '''
        CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        days INTEGER,
        time INTEGER,
        schedule INTEGER)
    '''
    execute_query(sql_query)


def create_table_homework():
    sql_query = '''
        CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        days INTEGER,
        homework INTEGER)
    '''
    execute_query(sql_query)


def insert_row(user_id, message, cell, value):
    # Вставляем в таблицу сообщение и заполняем ячейку cell значением value
    sql_query = f'''INSERT INTO messages (user_id, message, {cell}) VALUES (?, ?, ?)'''
    execute_query(sql_query, data=(user_id, message, value))


def get_rows_value(rows, row=0, field=0, default=None):
    # Проверяем rows на наличие хоть какого-то результата запроса и на то,
    # что в результате мы получили какое-то значение в rows[row][field]
    if rows and rows[row] and rows[row][field]:
        return rows[row][field]
    else:
        # Результата нет, так как у нас ещё нет записей
        return default


def count_user_blocks(user_id):
    sql_query = f'SELECT SUM(stt_blocks) FROM messages WHERE user_id=?'
    rows = execute_query(sql_query, (user_id,))
    return get_rows_value(rows, row=0, field=0, default=0)


def count_project_blocks():
    sql_query = f'SELECT SUM(stt_blocks) FROM messages'
    rows = execute_query(sql_query)
    return get_rows_value(rows, row=0, field=0, default=0)


def count_user_symbols(user_id):
    sql_query = '''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?'''
    rows = execute_query(sql_query, (user_id,))
    return get_rows_value(rows, row=0, field=0, default=0)


def count_user_tokens(user_id):
    sql_query = f'SELECT SUM(tokens) FROM messages WHERE user_id = ?'
    rows = execute_query(sql_query, (user_id,))
    return get_rows_value(rows, row=0, field=0, default=0)


def count_project_tokens():
    sql_query = f'SELECT SUM(tokens) FROM messages'
    rows = execute_query(sql_query)
    return get_rows_value(rows, row=0, field=0, default=0)


def count_users():
    sql_query = f'SELECT DISTINCT user_id FROM messages'
    rows = execute_query(sql_query)
    return len(rows)


def store_gpt_message(user_id, message, tokens):
    # Преобразуем список словарей сообщений к виду json
    json_string = json.dumps(message, ensure_ascii=False)

    insert_row(user_id, message=json_string, cell='tokens', value=tokens)


def store_stt_message(user_id, message, stt_blocks):
    insert_row(user_id, message=message, cell='stt_blocks', value=stt_blocks)
