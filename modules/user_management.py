"""
User Management Module for the Family Budget Management Telegram Bot.

This module is responsible for fetching and managing user data from the API.
It contains functions to retrieve the list of users and to create a mapping
of user IDs to their respective usernames. These functions are essential for
identifying users and associating transactions with the correct user accounts
in the bot's operation.

Functions:
    get_users(context, api_base_url): Fetches and returns a list of users from
    the API.
    get_user_mapping(context, api_base_url): Creates a dictionary mapping user
    IDs to usernames.

Note:
    Both functions require the bot's context and the API's base URL to function
    correctly. They also handle potential errors by logging failed fetch
    attempts.
"""

import logging

import requests

import modules.constants


def get_users(context):
    """
    Fetch and return the list of users from the API.

    Logs an error if the fetch fails.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(
        modules.constants.API_BASE_URL + "/users/",
        headers=headers,
        verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch users: {response.status_code}")
        return []


def get_user_mapping(context):
    """
    Fetch and return a mapping of user IDs to usernames from the API.

    Returns:
        dict: A dictionary mapping user IDs to usernames.
    """
    headers = {'Authorization': f'Token {context.user_data.get("api_token")}'}
    response = requests.get(modules.constants.API_BASE_URL + "/users/",
                            headers=headers, verify=False)
    if response.status_code == 200:
        users = response.json()
        return {user['id']: user['username'] for user in users}
    else:
        logging.error(f"Failed to fetch users: {response.status_code}")
        return {}
