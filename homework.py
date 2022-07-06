from http import HTTPStatus
import time
import logging
# from urllib import response
import requests
import os
import telegram.ext

# from telegram import Bot
# from telegram.ext import Filters, MessageHandler, Updater
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = ...
TELEGRAM_TOKEN = ...
TELEGRAM_CHAT_ID = ...

practicum_token = os.getenv('PRACTICUM_TOKEN')
telegram_token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {practicum_token}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    bot.send_message(chat_id, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise Exception(f'Failed making a request to API! {error}')

    if response.status_code != HTTPStatus.OK:
        raise Exception(
            f'Response status code is not OK! {response.status_code}'
        )
    return response.json()


def check_response(response):
    if not isinstance(response, dict):
        raise TypeError('Response is not dict!')
    if response is None:
        raise Exception('No homeworks found')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks is not list!')
    return response['homeworks']


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if practicum_token and telegram_token and chat_id:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=telegram_token)
    current_timestamp = int(time.time())
    prev_status_message = ''
    # new:
    while True:
        try:
            homeworks = check_response(
                get_api_answer(current_timestamp - 100000000)
            )
            message = parse_status(homeworks[0])
            if not (message == prev_status_message):
                send_message(bot, message)

        except Exception as error:
            message = f'Critical fail! {error}'
            send_message(bot, message)
            logging.error(message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
