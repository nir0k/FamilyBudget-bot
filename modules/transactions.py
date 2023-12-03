"""
Transaction Management Module for the Family Budget Management Telegram Bot.

This module is dedicated to managing the transaction addition process within
the bot. It includes functions to initiate the transaction process and handle
user inputs for transaction details like title and category. The module uses
Telegram's InlineKeyboard for interactive user responses and efficiently
guides users through the process of adding a new transaction.

Functions:
    add_transaction(update, context): Initiates the Add Transaction process
                                      by asking the user to enter the title
                                      of the transaction.
    receive_title(update, context, api_base_url): Receives the transaction
                                                  title from the user and
                                                  prompts for category
                                                  selection.

Note:
    The functions in this module are designed to work within the context of a
    Telegram bot and rely on the bot's update and context objects, as well as
    the API's base URL for fetching necessary data.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from modules.api import get_categories
from modules.constants import CATEGORY, TITLE


async def add_transaction(update: Update, context: CallbackContext):
    """
    Initiate the Add Transaction process.

    Asks the user to enter the title of the transaction.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=(
        "Add new transaction:\n"
        "  Enter the title of the transaction:"))
    return TITLE


async def receive_title(update: Update,
                        context: CallbackContext):
    """
    Receive the title of the transaction.

    Prompts for the category selection after receiving the title.
    """
    if 'transaction_data' not in context.user_data:
        context.user_data['transaction_data'] = {}
    text = update.message.text
    context.user_data['transaction_data']['title'] = text

    categories = get_categories(context)
    keyboard = [
        [InlineKeyboardButton(
            category['title'], callback_data=f"category_{category['id']}")]
        for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a category:", reply_markup=reply_markup)
    return CATEGORY
