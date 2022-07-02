import time
# import logging
import requests
import os
import telegram

# from telegram import Bot
# from telegram.ext import Filters, MessageHandler, Updater
# from dotenv import load_dotenv

# load_dotenv()


# PRACTICUM_TOKEN = ...
# TELEGRAM_TOKEN = ...
# TELEGRAM_CHAT_ID = ...

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
    # bot.send_message(chat_id, message)
    bot.send_message(chat_id, 'test')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return response.json


def check_response(response):
    return response.json['homeworks']


def parse_status(homework):
    homework_name = homework.get('name')
    homework_status = homework.get('status')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if not (practicum_token and telegram_token and chat_id):
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=telegram_token)
    current_timestamp = int(time.time())
    # new:
    homeworks = check_response(get_api_answer(current_timestamp))
    message = parse_status(homeworks[0])
    send_message(bot, message)

    # while True:
    #     try:
    #         response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    #         ...

    #         current_timestamp = ...
    #         time.sleep(RETRY_TIME)

    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'
    #         ...
    #         time.sleep(RETRY_TIME)
    #     else:
    #         ...


if __name__ == '__main__':
    main()
