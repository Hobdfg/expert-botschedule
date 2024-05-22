import logging

import time
import requests
import config
from requests.exceptions import ConnectionError


class CRED:
    def __init__(self, iam_token=None):
        # iam_token для доступа к SpeechKit и Yandex GPT
        self.iam_token = iam_token
        self.token_expires_at = 0
        if self.iam_token:
            self.token_expires_at = -1

    def create_iam_token(self):
        url = config.URL_CRED
        headers = {"Metadata-Flavor": "Google"}
        try:
            response = requests.get(url, headers = headers)
        except ConnectionError as e:
            logging.error(f'Ошибка отправки запроса для получения IAM-token, {e}')
            return False, f'возникла ошибка отправки запроса для получения IAM-token'

        # Проверка статус кода
        if response.status_code != 200:
            logging.error(f'Ошибка получения IAM-token, '
                          f'status_code {response.status_code}, content: {response.content}')
            return False, 'возникла ошибка получения IAM-token'

        # Проверка json
        try:
            decoded_data = response.json()
            self.iam_token = decoded_data.get('access_token')
            self.token_expires_at = decoded_data.get('expires_in') + time.time()
        except Exception as e:
            logging.error(f'Ошибка получения атрибута access_token или expires_in, {e}')
            return False, 'возникла ошибка получения IAM-token'

        return True, [self.iam_token, self.token_expires_at]

    def get_iam_token(self):
        # Обновляем токен, если он не задан через параметр
        if -1 < self.token_expires_at < time.time():
            return self.create_iam_token()
        return True, [self.iam_token, self.token_expires_at]
