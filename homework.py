import os
import sys
import requests

from http import HTTPStatus
import time
import logging
import telegram

import exceptions
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    UsrInfo = bot.get_chat_member(
        TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID).user.username
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(
            f'Пользователю @{UsrInfo}'
             'отправлено сообщение: {message}')
    except telegram.error.TelegramError:
        logger.error(f'Сообщение: {message} не удалось отправить')


def get_api_answer(current_timestamp):
    """Функция делает запрос к единственному эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
        logger.info('Ответ от сервера получен успешно')
    except exceptions.GetAPIException:
        logger.error(f'Сбой при запросе к {ENDPOINT}')
    if response.status_code != HTTPStatus.OK:
        logger.error(f'Ошибка {response.status_code}')
        raise exceptions.GetAPIException(
            f'Ошибка {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    if type(response) is not dict:
        raise TypeError('Ответ API отличен от словаря')
    try:
        homeworks_list = response.get('homeworks')
        logger.info('Список домашних работ успешно получен')
    except KeyError:
        logger.error(
            f'Ошибка доступа по ключу homeworks: {KeyError}'
        )
        raise exceptions.CheckResponseException(
            f'Ошибка доступа по ключу homeworks: {KeyError}'
        )
    try:
        homework = homeworks_list[0]
        logger.info('Получена успешно последняя домашняя работа')
        return homework
    except IndexError:
        raise IndexError('Список домашних работ пуст')


def parse_status(homework):
    """Функция извлекает cтатус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(
            'Отсутствует ключ "homework_name" в ответе API'
        )
    if 'status' not in homework:
        raise Exception('Отсутствует ключ "status" в ответе API')

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(
            f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return (
        f'Изменился статус проверки работы "{homework_name}".{verdict}'
    )


def check_tokens():
    """Функция проверяет переменные окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        logger.critical(
            f'Отсутствует обязательная переменная окружения'
        )
        return False


def main():
    """Описание основной логики работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    STATUS = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            message = parse_status(check_response(response))
            if message != STATUS:
                send_message(bot, message)
                logger.info('Статус изменилсч')
                STATUS = message
            else:
                logger.info('Изменений нет')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if errors:
                errors = False
                send_message(bot, message)
            logger.critical(message)
            time.sleep(RETRY_TIME)
        else:
            exit()


if __name__ == '__main__':
    main()
