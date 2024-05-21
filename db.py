import sqlite3
import logging
import config


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
