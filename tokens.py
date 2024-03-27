import requests

import logging
from database import get_username, get_user_tokens_data, update_sessions, update_tokens
from tokens_const import MAX_GPT_TOKENS
from config import IAM_TOKEN, FOLDER_ID


def count_tokens(text):
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize'
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f'gpt://{FOLDER_ID}/yandexgpt/latest',
        'maxTokens': MAX_GPT_TOKENS,
        'text': text
    }
    response = requests.post(url, headers=headers, json=data)
    return len(response.json()['tokens'])


def check_tokens_data(user_id, param):
    return get_user_tokens_data(user_id, param)[0][0]


def start_session(user_id):
    current_sessions = check_tokens_data(user_id, 'sessions')
    update_sessions(user_id, current_sessions - 1)


def cut_tokens(user_id, response):
    tokens = count_tokens(response)
    update_tokens(user_id, tokens)
    logging.info(f'Пользователю {get_username(user_id)} уменьшены токены на {tokens}')
