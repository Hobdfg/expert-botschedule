import logging

import requests
from requests.exceptions import ConnectionError


class STT:
    def __init__(self, url, cred, folder_id):
        self.url = url
        self.cred = cred
        self.folder_id = folder_id  # folder_id для доступа к SpeechKit
        self.result_data = {}

    def speech_to_text(self, data):
        # Обновляем IAM-токен
        status, result = self.cred.get_iam_token()
        if not status:
            return status, result

        iam_token = result[0]

        # Указываем параметры запроса
        params = "&".join([
            'topic=general',  # используем основную версию модели
            f'folderId={self.folder_id}',
            'lang=ru-RU'  # распознаём голосовое сообщение на русском языке
        ])

        # Аутентификация через IAM-токен
        headers = {
            'Authorization': f'Bearer {iam_token}',
        }

        # Выполняем запрос
        try:
            response = requests.post(
                url = f'{self.url}?{params}',
                headers = headers,
                data = data
            )
        except ConnectionError as e:
            logging.error(f'Ошибка отправки запроса в SpeechKit, {e}')
            return False, f'возникла ошибка отправки запроса в SpeechKit'

        # Проверка статус кода
        if response.status_code != 200:
            logging.error(f'Ошибка обращения к SpeechKit, '
                          f'status_code {response.status_code}, content: {response.content}')
            return False, 'возникла ошибка обращения к SpeechKit'

        # Читаем json в словарь
        try:
            decoded_data = response.json()
        except Exception as e:
            logging.error(f'Возникла ошибка получения JSON от SpeechKit, {e}')
            return False, 'возникла ошибка получения JSON от SpeechKit'

        # Проверяем, не произошла ли ошибка при запросе
        if decoded_data.get("error_code") is None:
            return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
        else:
            logging.error(f'При запросе в SpeechKit возникла ошибка, {decoded_data.get("error_code")}')
            return False, "возникла ошибка при запросе в SpeechKit"
