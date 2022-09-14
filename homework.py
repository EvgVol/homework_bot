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
ENDPOINT = (
    'https://practicum.yandex.ru/api/user_api/homework_statuses/'
)
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
    """Функция send_message() отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID. Принимает
    на вход два параметра: экземпляр класса Bot и строку с текстом
    сообщения.
    """
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
    """Функция get_api_answer() делает запрос к единственному
    эндпоинту API-сервиса. В качестве параметра функция получает
    временную метку. В случае успешного запроса должна вернуть ответ
    API, преобразовав его из формата JSON к типам данных Python.
    """
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
    """Функция check_response() проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API, приведенный к
    типам данных Python. Если ответ API соответствует ожиданиям, то
    функция должна вернуть список домашних работ (он может быть и
    пустым), доступный в ответе API по ключу 'homeworks'.
    """
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
    """Функция parse_status() извлекает из информации о конкретной
    домашней работе статус этой работы. В качестве параметра функция
    получает только один элемент из списка домашних работ. В случае
    успеха, функция возвращает подготовленную для отправки в
    Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
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
            f'Неизвестный статус работы: {homework_status}'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return (
        f'Изменился статус работы "{homework_name}".{verdict}'
    )


def check_tokens():
    """Функция check_tokens() проверяет доступность переменных
    окружения, которые необходимы для работы программы. Если
    отсутствует хотя бы одна переменная окружения — функция должна
    вернуть False, иначе — True.
    """
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        logger.critical(
            f'Отсутствует обязательная переменная окружения'
        )
        return False


def main():
    """Функция main(): в ней описана основная логика работы
    программы. Все остальные функции должны запускаться из неё.
    Последовательность действий должна быть примерно такой:
        Сделать запрос к API.
        Проверить ответ.
        Если есть обновления — получить статус работы из обновления
            и отправить сообщение в Telegram.
        Подождать некоторое время и сделать новый запрос.
    """
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
