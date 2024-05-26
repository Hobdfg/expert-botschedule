import logging
import config

import requests
from requests.exceptions import ConnectionError


class GPT:
    def __init__(self, url, cred, folder_id):
        self.url = url
        self.cred = cred
        self.folder_id = folder_id
        self.result_data = {}

        self.max_model_tokens = config.MAX_MODEL_TOKENS
        self.model_name = config.MODEL_NAME

    def get_headers(self, iam_token):
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        return headers

    @staticmethod
    def copy_messages(data, messages):
        for row in messages:
            data["messages"].append(
                {
                    "role": row["role"],
                    "text": row["text"]
                }
            )

    # Подсчитываем количество токенов в промте
    def count_tokens_in_dialog(self, messages):
        data = {
            "modelUri": f"gpt://{self.folder_id}/{self.model_name}",
            "maxTokens": self.max_model_tokens,
            "messages": []
        }

        # Проходимся по всем сообщениям и добавляем их в список
        self.copy_messages(data, messages)

        status, response = self.send_tokenize_request(data)
        if not status:
            return status, response

        tokens = len(response['tokens'])
        logging.debug(f'GPT tokens: {tokens}, messages: {messages}')
        return True, tokens

    # Проверка ответа на возможные ошибки и его обработка
    def process_response(self, response):
        # Проверка сообщения об ошибке
        if 'result' not in response:
            logging.error(f'Ошибка обращения к GPT, {response}')
            return False, 'возникла ошибка обращения к GPT'

        # Результат
        self.result_data = response['result']
        logging.debug(f'GPT result_data: {self.result_data}')

        result = response['result']['alternatives'][0]['message']['text']
        return True, result

    def get_result_data(self):
        return self.result_data

    # Формирование промта
    def make_request(self, messages):
        data = {
            "modelUri": f"gpt://{self.folder_id}/{self.model_name}",  # модель для генерации текста
            "completionOptions": {
                # потоковая передача частично сгенерированного текста выключена
                "stream": False,
                # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
                "temperature": 0.6,
                # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
                "maxTokens": self.max_model_tokens,
            },
            "messages": []
        }

        # Проходимся по всем сообщениям и добавляем их в список
        self.copy_messages(data, messages)

        return data

    def request(self, url, data):
        status, result = self.cred.get_iam_token()
        if not status:
            return status, result
        iam_token = result[0]

        # Выполняем запрос
        try:
            response = requests.post(url=url, headers=self.get_headers(iam_token), json=data)
        except ConnectionError as e:
            logging.error(f'Ошибка отправки запроса в Yandex GPT, {e}')
            return False, f'возникла ошибка отправки запроса в Yandex GPT'

        # Проверка статус кода
        if response.status_code != 200:
            logging.error(f'Ошибка обращения к API Yandex GPT, '
                          f'status_code {response.status_code}, content: {response.content}')
            return False, 'возникла ошибка обращения к Yandex GPT'

        # Проверка json
        try:
            response_data = response.json()
        except Exception as e:
            logging.error(f'Ошибка получения JSON от Yandex GPT, {e}')
            return False, 'возникла ошибка получения JSON от Yandex GPT'

        return True, response_data

    # Отправка запроса
    def send_tokenize_request(self, data):
        response = self.request(url=self.url + '/tokenizeCompletion', data=data)
        return response

    # Отправка запроса
    def send_request(self, data):
        response = self.request(url=self.url + '/completion', data=data)
        return response
