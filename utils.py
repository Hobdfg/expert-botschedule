import os
import logging
import config
from dotenv import load_dotenv


def get_env_value(param, required=True):
    value = os.getenv(param)
    if not value and required:
        logging.error(f'Не задана переменная окружения {param}')
        exit()
    return value


def get_iam_token():
    return get_env_value('IAM_TOKEN', required=False)


def get_folder_id():
    return get_env_value('FOLDER_ID')


def get_telegram_token():
    return get_env_value('TELEGRAM_TOKEN')


def to_int(value):
    try:
        result = int(value)
    except ValueError:
        result = 0
    return result


def to_int(value):
    try:
        result = int(value)
    except ValueError:
        result = 0
    return result


load_dotenv()

logging.basicConfig(level=logging.INFO, filename= config.LOG_FILENAME, filemode= 'w',
                    format='%(asctime)s %(levelname)s %(message)s')
