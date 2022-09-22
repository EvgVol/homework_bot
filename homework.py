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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
STATUS_IS_CHANGED = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""

    try:
        logging.info('Отправляем сообщение в телеграм')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        user_username = bot.get_chat_member(
            TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID).user.username
        logging.info(
            f'Пользователю @{user_username} отправлено сообщение: {message}'
        )
    except telegram.error.TelegramError as error:
        logging.error(f'Сообщение: {message} не удалось отправить')
        logging.error(f'Ошибка: {error}')


def get_api_answer(current_timestamp):
    """Функция делает запрос к единственному эндпоинту."""
    timestamp = current_timestamp
    api_with_homework = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    try:
        logging.info(
            'Делаем запрос к {url} с параметрами: {params}'
                .format(**api_with_homework)
            )
        response = requests.get(**api_with_homework)
        logging.info('Ответ от сервера получен успешно')
        if response.status_code != HTTPStatus.OK:
            logging.error(f'Ошибка {response.status_code}')
            raise exceptions.NoCorrectCodeRequest(
                f'Ошибка: {response.status_code}, '
                f'причина: {response.reason}, '
                f'текст: {response.text}'
            )
        return response.json()
    except Exception as error:
        raise ConnectionError(
            'Произошёл сбой сети: {error}, '
            'url={url}'
            'headers={headers}, '
            'params={params}'.format(
                error=error, **api_with_homework
            )
        )


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    logging.info('Список домашних работ успешно получен')
    if not isinstance(response, dict):
        raise TypeError('Ответ API отличен от словаря')
    if response['homeworks'] is None:
        raise exceptions.EmptyValuesFromAPI(
            'Пустой ответ от API'
        )
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        raise TypeError(
            'Список домашних работ не является списком'
        )
    return homework


def parse_status(homework):
    """Функция извлекает cтатус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(
            'Отсутствует ключ "homework_name" в ответе API'
        )
    if 'status' not in homework:
        raise exceptions.ParseStatusException(
            'Отсутствует ключ "status" в ответе API'
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in VERDICTS:
        raise ValueError(
            f'Неожиданный статус работы: {homework_status}')
    return (
        STATUS_IS_CHANGED.format(
            homework_name=homework_name,
            verdict=VERDICTS[homework_status]
        )
    )


def check_tokens():
    """Функция проверяет переменные окружения."""
    environment_variables = (
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
    )
    flag = True
    for name, token in environment_variables:
        if token is None:
            flag = False
            logging.critical('Отсутствует токен переменной {name}')
    return flag

def main():
    """Описание основной логики работы бота."""
    if not check_tokens():
        logging.CRITICAL(
            'Отсутствуют обязательные переменные окружения!'
        )
        raise KeyError('Ошибка в ТОКЕНАХ')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_report = {}
    prev_report = {}

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                homework_name = response.get("homework_name")
                homework_status = response.get("status")
                current_report[homework_name] = homework_status
            else:
                logging.info('Нет новых статусов')
            if current_report != prev_report:
                logging.info('Статус домашней работы изменился')
                send_message(bot, message)
                prev_report = current_report.copy()
                current_report[homework_name] = homework_status
            else:
                logging.info('Изменений нет')
            current_timestamp = response.get("current_date")

        except exceptions.EmptyValuesFromAPI as error:
            logging.info('Пустой ответ от API. Ошибка: {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s, %(name)s, %(filename)s, '
            '%(funcName)s[%(lineno)d], %(levelname)s, '
            '%(message)s'
        ),
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler(f'{BASE_DIR}/outlook.log')
        ]
    )
    main()
