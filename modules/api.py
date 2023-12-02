"""
API Interaction Module for Telegram Bot.

This module handles direct interactions with the API, facilitating data
retrieval and submission necessary for the bot's operations. It includes
functions to fetch accounts, currencies, and categories from the API, as
well as to post transaction data. The module abstracts API requests and
responses, offering a cleaner interface for the main bot functionality and
ensuring separation of concerns.

Functions:
    get_accounts(context, api_base_url): Fetches and returns a list of accounts
    with associated usernames.
    get_currencies(context, api_base_url): Retrieves available currencies from
    the API.
    ask_for_currency(update, context, api_base_url): Prompts the user to
    select a currency.
    get_categories(context, api_base_url): Fetches and returns the list of
    categories.
    post_transaction(data, context, api_base_url): Posts transaction data to
    the API.
"""
import logging

import requests
import urllib3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

import modules.constants
from modules.user_management import get_user_mapping

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_accounts(context, user_id=None):
    """
    Fetch and return the list of accounts from the API.

    This function includes the associated username with each account.
    It returns a list of account details, each including the username
    of the owner.

    Args:
        context (CallbackContext): The context of the bot.
        api_base_url (str): Base URL of the API.

    Returns:
        list: A list of account details, each including the username of
        the owner.
    """
    url = f"{modules.constants.API_BASE_URL}/account/"
    if user_id is not None:
        url += f"?owner={user_id}"

    user_mapping = get_user_mapping(context)
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        accounts = response.json()
        for account in accounts:
            owner_id = account.get('owner')
            account['username'] = user_mapping.get(owner_id, 'Unknown')
        return accounts
    else:
        logging.error(f"Failed to fetch accounts: {response.status_code}")
        return []


def get_currencies(context):
    """
    Fetch the list of currencies from the API.

    Sends a GET request to the API to retrieve available currencies.
    On success, returns a JSON response; on failure, logs an error and returns
    an empty list.

    Returns:
        list: A list of currency data, or an empty list if fetch fails.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(modules.constants.API_BASE_URL + "/currency/",
                            headers=headers,
                            verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch currencies: {response.status_code}")
        return []


async def ask_for_currency(update: Update,
                           context: CallbackContext):
    """
    Prompt the user to select a currency.

    Retrieves available currencies and displays them using an inline keyboard.
    Triggers `receive_currency` function upon selection.

    Args:
        update (Update): The incoming update.
        context (CallbackContext): The context of the callback.

    Returns:
        int: The next state, CURRENCY, in the conversation.
    """
    currencies = get_currencies(context)
    keyboard = [
        [InlineKeyboardButton(currency['title'],
                              callback_data=f"currency_{currency['id']}")]
        for currency in currencies
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a currency:",
                                    reply_markup=reply_markup)
    return modules.constants.CURRENCY


def get_categories(context):
    """
    Fetch and return the list of categories from the API.

    Logs an error if the fetch fails.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(
        modules.constants.API_BASE_URL + "/category/",
        headers=headers,
        verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch categories: {response.status_code}")
        return []


def post_transaction(data, context):
    """
    Post the transaction data to the API.

    Returns the success status of the operation.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.post(
        modules.constants.API_BASE_URL + "/transaction/",
        headers=headers, json=data, verify=False)
    return response.status_code == 201


def get_user_details(context):
    """
    Fetch the user's details from the API.

    Args:
        context (CallbackContext): Context object providing additional
                                   information.

    Returns:
        dict: User details including the user ID.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(modules.constants.API_BASE_URL + "/users/me/",
                            headers=headers,
                            verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_family_status(context):
    """
    Fetch the family status from the API.

    Args:
        context (CallbackContext): Context object providing additional
                                   information.

    Returns:
        list: A list of family status data.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(modules.constants.API_BASE_URL + "/family-state/",
                            headers=headers,
                            verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch family status: {response.status_code}")
        return []
