"""
Telegram Bot for Managing Family Budget Transactions.

This script implements a Telegram bot that assists users in managing their
family budget. It provides functionalities like adding transactions, selecting
categories, users, and accounts, and confirming transaction details.
The bot uses a conversation handler to guide users through a series of steps
for each transaction. It also includes features for error logging and
interactive date selection using a calendar interface.

Features:
- Start command to initiate interaction.
- Add transaction command with multiple steps.
- Inline keyboards for user-friendly interaction.
- Dynamic calendar for date selection.
- Error logging for troubleshooting.

Usage:
Run this script to start the bot. Interact with the bot in Telegram by sending
commands like /start and following the prompts.
"""
import logging
import os
from datetime import datetime

import urllib3
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, MessageHandler,
                          filters)

import modules.constants
from modules.api import ask_for_currency, get_accounts, post_transaction
from modules.auth import authenticate_user
from modules.handlers import (handle_account_selection,
                              handle_calendar_callback,
                              handle_category_selection, handle_who_selection)
from modules.transactions import add_transaction, receive_title
from modules.user_management import get_users
from modules.utils import create_calendar

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

modules.constants.API_BASE_URL = os.getenv('API_BASE_URL')
modules.constants.API_TOKEN = os.getenv('API_TOKEN')
modules.constants.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext):
    """
    Handle the /start command.

    Sends a message with a keyboard offering different transaction options.
    """
    telegram_user_id = update.effective_user.id
    token = authenticate_user(telegram_user_id)
    if token:
        context.user_data['api_token'] = token
        await update.message.reply_text("Authenticated successfully.")
        keyboard = [
            [InlineKeyboardButton("Add Transaction",
                                  callback_data='add_transaction')],
            [InlineKeyboardButton("Account Status",
                                  callback_data='account_status')],
            [InlineKeyboardButton("Family Status",
                                  callback_data='family_status')],
            [InlineKeyboardButton("Profile",
                                  callback_data='profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            'Please choose:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("Authentication failed.")


async def cancel(update: Update, context: CallbackContext):
    """
    Handle the /cancel command to abort an ongoing transaction process.

    This asynchronous function is triggered when a user sends the /cancel
    command. It sends a message to the user indicating that the transaction
    addition has been cancelled. This function also terminates the current
    conversation, bringing the user back to the initial state of the bot's
    conversation flow.

    Args:
        update (Update): The incoming update that triggered the command.
        context (CallbackContext): The context of the callback, providing
        additional information and capabilities.

    Returns:
        int: The end state of the conversation handler, signaling the
        termination of the current conversation flow.
    """
    await update.message.reply_text('Transaction addition cancelled.')
    return ConversationHandler.END


async def receive_category(update: Update, context: CallbackContext):
    """
    Handle the category selection for the transaction.

    Prompts for selecting the user involved after choosing the category.
    """
    context.user_data['transaction_data']['category'] = (
        update.callback_query.data.split("_")[1])
    users = get_users(context)
    keyboard = [
        [InlineKeyboardButton(user['username'],
                              callback_data=f"who_{user['id']}")]
        for user in users
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Who is this transaction for?", reply_markup=reply_markup)
    return modules.constants.WHO


async def receive_who(update: Update, context: CallbackContext):
    """
    Receive the user involved in the transaction.

    Prompts for selecting the account by displaying a list of accounts
    in the format "<Account title> - <Username>".
    """
    text = update.message.text
    context.user_data['transaction_data']['who'] = text
    await update.message.reply_text("Select an account:")
    accounts = get_accounts(context)
    for account in accounts:
        account_display = f"{account['title']} - {account['username']}"
        await update.message.reply_text(account_display)
    return modules.constants.ACCOUNT


async def receive_account(update: Update, context: CallbackContext):
    """
    Handle the account selection for the transaction.

    Prompts for entering the amount after selecting the account.
    """
    account_id = update.message.text
    context.user_data['transaction_data']['account'] = account_id

    await update.message.reply_text("Enter the amount (format: 123.45):")
    return modules.constants.AMOUNT


async def receive_amount(update: Update, context: CallbackContext):
    """
    Receive the transaction amount from the user.

    Initiates the date selection process after receiving the amount.
    """
    amount_text = update.message.text
    context.user_data['transaction_data']['amount'] = amount_text

    return await ask_for_currency(update, context)


async def receive_date(update: Update, context: CallbackContext):
    """
    Receive the transaction date from the user.

    Attempts to post the transaction after receiving the date.
    """
    text = update.message.text
    context.user_data['transaction_data']['date'] = text
    data = context.user_data['transaction_data']
    if post_transaction(data):
        await update.message.reply_text("Transaction successfully added.")
    else:
        await update.message.reply_text("Transaction failed to add.")
    return ConversationHandler.END


async def receive_currency(update: Update, context: CallbackContext):
    """
    Handle the user's currency selection.

    Captures the selected currency ID from the callback query and stores it
    in the user's context. Prompts the user to select a date next.
    Logs an error if no message is associated with the callback query.

    Args:
        update (Update): The incoming update.
        context (CallbackContext): The context of the callback.
    """
    query = update.callback_query
    await query.answer()

    currency_id = query.data.split("_")[1]
    context.user_data['transaction_data']['currency'] = currency_id

    if query.message:
        await query.edit_message_text(
            text=f"Selected currency ID: {currency_id}\nPlease choose a date:",
            reply_markup=None)
    else:
        logger.error("No message associated with the callback query")

    return await ask_for_date(update, context)


async def error(update: Update, context: CallbackContext):
    """Log errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


async def ask_for_date(update: Update, context: CallbackContext):
    """
    Prompt the user to select a date.

    Uses a calendar for date selection.
    """
    today = datetime.today()
    calendar_markup = create_calendar(today.year, today.month)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Please choose a date:", reply_markup=calendar_markup)
    else:
        await update.message.reply_text(
            "Please choose a date:", reply_markup=calendar_markup)
    return modules.constants.DATE


def main():
    """
    Create and run the bot application.

    Sets up handlers and starts the bot.
    """
    application = Application.builder().token(
        modules.constants.TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            add_transaction, pattern='^add_transaction$')],
        states={
            modules.constants.TITLE: [MessageHandler(
                filters.TEXT, receive_title)],
            modules.constants.CATEGORY: [
                CallbackQueryHandler(handle_category_selection,
                                     pattern='^category_')],
            modules.constants.WHO: [
                CallbackQueryHandler(handle_who_selection, pattern='^who_')],
            modules.constants.ACCOUNT: [
                CallbackQueryHandler(handle_account_selection,
                                     pattern='^account_')],
            modules.constants.AMOUNT: [
                MessageHandler(filters.TEXT, receive_amount)],
            modules.constants.CURRENCY: [
                CallbackQueryHandler(receive_currency,
                                     pattern='^currency_')],
            modules.constants.DATE: [
                CallbackQueryHandler(handle_calendar_callback,
                                     pattern='^calendar-')]
        },
        # fallbacks=[CommandHandler('start', start)],
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_user=True,
        per_message=False
    )

    category_handler = CallbackQueryHandler(
        handle_category_selection, pattern='^category_')
    who_handler = CallbackQueryHandler(handle_who_selection, pattern='^who_')
    account_handler = CallbackQueryHandler(
        handle_account_selection, pattern='^account_')
    currency_handler = CallbackQueryHandler(receive_currency,
                                            pattern='^currency_')
    cancel_handler = CommandHandler('cancel', cancel)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(category_handler)
    application.add_handler(who_handler)
    application.add_handler(account_handler)
    application.add_handler(CallbackQueryHandler(
        handle_calendar_callback,
        pattern="^calendar-"))
    application.add_handler(currency_handler)
    application.add_handler(cancel_handler)
    application.add_error_handler(error)
    application.run_polling()


if __name__ == '__main__':
    main()
