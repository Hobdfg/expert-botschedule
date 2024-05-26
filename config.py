LOG_FILENAME = 'logs/bot_schedule.log'
DATABASE_FILENAME = 'db/bot_schedule.db'
URL_CRED = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'

URL_STT = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'
URL_GPT = 'https://llm.api.cloud.yandex.net/foundationModels/v1'

MODEL_NAME = 'yandexgpt-lite'
MAX_USERS = 4  # максимальное количество пользователей на весь проект
MAX_USER_TOKENS = 3000  # Максимальное количество токенов на пользователя
MAX_PROJECT_TOKENS = 15000  # Максимальное количество токенов на проект
MAX_MODEL_TOKENS = 50  # Максимальный размер ответа
SYSTEM_PROMPT_SCHEDULE = (
    'Ты только умеешь преобразовывать текстовый запрос пользователя в объект json. '
    'В запросе пользователя содержится информацию: день, время, предмет. '
    'Например, запрос "Химия в пятницу в 13:25" должен быть преобразован в '
    '{"day": "пятница", "time": "13:25", "lesson": "Химия"}. '
    'Ответ не должен начинаться с комментариев или поясняющего текста.'
)
SYSTEM_PROMPT_MOTIVATION = (
    'Ты дружелюбный учитель умеешь поддержать ученика. '
    'Напиши короткое мотивационное сообщение для ученика, у которого начинается урок. '
    'Ответ не должен начинаться с комментариев или поясняющего текста. '
    'Ответ должен состоять только из одного предложения.'
)

AUDIO_BLOCK = 15
MAX_USER_STT_BLOCKS = 20

SUPERUSERS = [6325574999]

SCHEDULER_PERIODS = 60
