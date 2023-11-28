"""
Constants for the Family Budget Management Telegram Bot.

This module defines a set of constants used throughout the bot's application.
These constants primarily represent the states in the conversation handler
of the bot, allowing for clear and maintainable state management. Each constant
corresponds to a specific step in the bot's transaction processing workflow.

Constants:
    TITLE: Represents the state for receiving the transaction's title.
    CATEGORY: Represents the state for selecting the transaction's category.
    WHO: Represents the state for selecting the user involved in the
    transaction.
    ACCOUNT: Represents the state for selecting the account for the
    transaction.
    AMOUNT: Represents the state for inputting the transaction's amount.
    CURRENCY: Represents the state for selecting the transaction's currency.
    DATE: Represents the state for selecting the date of the transaction.
"""

(TITLE, CATEGORY, WHO, ACCOUNT, AMOUNT, CURRENCY, DATE) = range(7)

API_BASE_URL = None
API_TOKEN = None
TELEGRAM_TOKEN = None
