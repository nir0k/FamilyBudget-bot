"""
Authentication Module for Telegram Bot.

This module provides functionalities for authenticating users of a Telegram bot
using their Telegram user ID. It includes a function that sends a POST request
to an authentication endpoint, passing the user's Telegram ID. On successful
authentication, the function retrieves an API token which can be used for
subsequent requests to the API.

The module is designed to be used in conjunction with the main script of the
Telegram bot, where it assists in the process of managing user authentication
for various bot functionalities. It separates the authentication logic from the
main script, adhering to the principles of modularity and single
responsibility.

Functions:
    authenticate_user(telegram_user_id, api_token, api_base_url): Authenticate
    a user and retrieve an API token based on the given Telegram user ID.
"""
import logging

import requests

import modules.constants


def authenticate_user(telegram_user_id):
    """
    Authenticate a user via their Telegram user ID and retrieve a token.

    This function sends a POST request to the authentication endpoint of the
    API, including the Telegram user ID in the payload. If authentication
    succeeds, it returns the API token. In case of failure, logs an error
    with the response status code and returns None.

    Args:
        telegram_user_id (int): The Telegram user ID used for authentication.

    Returns:
        str or None: The API token if authentication is successful, otherwise
        None.
    """
    payload = {"telegram_userid": telegram_user_id}
    headers = {'Authorization': f'Token {modules.constants.API_TOKEN}'}
    response = requests.post(
        f"{modules.constants.API_BASE_URL}/auth/telegram/",
        headers=headers,
        json=payload, verify=False)

    if response.status_code == 200:
        return response.json().get('token')
    else:
        logging.error(f"Authentication failed: {response.status_code}")
        return None
