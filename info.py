about_bot_text = "Привет! Я Бот-Расписание, я помогу тебе организовать твою неделю!"


def get_commands(handlers):
    commands = [
        {
            'command': '/start',
            'description': 'запуск бота',
            'keywords': ['start', 'старт', 'поехали'],
            'handler': handlers['response_start'],
            'hidden': False
        },
        {
            'command': '/help',
            'description': 'перечень поддерживаемых мной команд',
            'keywords': ['help', 'помощь', 'справка'],
            'handler': handlers['response_help'],
            'hidden': False
        },
        {
            'command': '/stt',
            'description': 'перевести голосовое сообщение в текст',
            'keywords': ['stt'],
            'handler': handlers['response_stt'],
            'hidden': False
        },
        {
            'command': '/stats',
            'description': 'статистика использования блоков и токенов',
            'keywords': [],
            'handler': handlers['response_stats'],
            'hidden': True
        },
        {
            'command': '/debug',
            'description': 'получить журнал выполнения',
            'keywords': [],
            'handler': handlers['response_debug'],
            'hidden': True
        },
        {
            'command': '/schedule',
            'description': 'посмотреть расписание',
            'keywords': ['schedule'],
            'handler': handlers['response_get_schedule'],
            'hidden': False
        },
        {
            'command': '/add',
            'description': 'добавить запись в расписание',
            'keywords': ['add'],
            'handler': handlers['response_add_schedule'],
            'hidden': False
        },
        {
            'command': '/delete',
            'description': 'удалить запись из расписания',
            'keywords': ['delete'],
            'handler': handlers['response_delete_schedule'],
            'hidden': False
        },
    ]
    return commands
