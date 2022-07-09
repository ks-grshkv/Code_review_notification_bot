import logging
import os
import time
from http import HTTPStatus

import requests
import telegram.ext
from dotenv import load_dotenv

from exceptions import APIResponseStatusCodeError, EmptyAPIResponseError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Message {message} sent successfully')
    except Exception as error:
        message = f'Failed to send a message! {error}'
        logger.error(message)


def get_api_answer(current_timestamp):
    """Получаем ответ от API."""
    logger.info('Trying to get an API response')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        message = f'Failed making a request to API! {error}'
        logger.error(message)
        raise EmptyAPIResponseError(f'Failed making a request to API! {error}')

    if response.status_code != HTTPStatus.OK:
        message = (
            f'Response status code is not OK! {response.status_code}',
            f'More info: {response.headers}, {response.url}'
        )
        raise APIResponseStatusCodeError(message)
    try:
        return response.json()
    except Exception as error:
        message = f'Failed returning response.json()! {error}'
        logger.error(message)
        raise Exception(message)


def check_response(response):
    """Проверяем корректность ответа от API."""
    logger.info('Starting to check API response')
    if not isinstance(response, dict):
        raise TypeError('Response is not dict!')
    if response is None:
        raise Exception('No homeworks found')
    if not response['current_date']:
        raise Exception('current_date key doesnt exist!')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks is not list!')
    return homeworks


def parse_status(homework):
    """Выясняем статус домашки."""
    logger.info('Parsing homework status')
    try:
        homework_name = homework.get('homework_name')
    except Exception:
        raise Exception('Couldnt retrieve homework name!')
    homework_status = homework.get('status')
    if HOMEWORK_STATUSES[homework_status] is not None:
        verdict = HOMEWORK_STATUSES[homework_status]
    else:
        raise Exception(
            f'Couldnt parsе {homework_name} status: {homework_status}'
        )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия необходимых переменных."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if check_tokens() is False:
        exit()
    prev_report = {
        'name_messages': None,
        'output': None
    }
    current_report = {
        'name_messages': None,
        'output': None
    }
    while True:
        try:
            homeworks = check_response(
                get_api_answer(current_timestamp)
            )
            current_report['homework_name'] = homeworks[0].get('homework_name')
            current_report['output'] = parse_status(homeworks[0])
            if not (current_report == prev_report):
                send_message(bot, current_report['output'])
            else:
                logger.debug('No new homework statuses')
            prev_report = current_report.copy()

        except Exception as error:
            message = f'Critical fail! {error}'
            send_message(bot, message)
            logger.error(message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
