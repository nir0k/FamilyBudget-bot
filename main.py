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
import calendar
import logging
import os
from datetime import datetime

import requests
import urllib3
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, MessageHandler,
                          filters)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_TOKEN = os.getenv('API_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(TITLE, CATEGORY, WHO, ACCOUNT, AMOUNT, DATE) = range(6)


async def start(update: Update, context: CallbackContext):
    """
    Handle the /start command.

    Sends a message with a keyboard offering different transaction options.
    """
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


async def add_transaction(update: Update, context: CallbackContext):
    """
    Initiate the Add Transaction process.

    Asks the user to enter the title of the transaction.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Enter the title of the transaction:")
    return TITLE


async def receive_title(update: Update, context: CallbackContext):
    """
    Receive the title of the transaction.

    Prompts for the category selection after receiving the title.
    """
    if 'transaction_data' not in context.user_data:
        context.user_data['transaction_data'] = {}
    text = update.message.text
    context.user_data['transaction_data']['title'] = text

    categories = get_categories()
    keyboard = [
        [InlineKeyboardButton(
            category['title'], callback_data=f"category_{category['id']}")]
        for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select a category:", reply_markup=reply_markup)
    return CATEGORY


async def receive_category(update: Update, context: CallbackContext):
    """
    Handle the category selection for the transaction.

    Prompts for selecting the user involved after choosing the category.
    """
    context.user_data['transaction_data']['category'] = (
        update.callback_query.data.split("_")[1])
    users = get_users()
    keyboard = [
        [InlineKeyboardButton(user['username'],
                              callback_data=f"who_{user['id']}")]
        for user in users
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Who is this transaction for?", reply_markup=reply_markup)
    return WHO


def get_users():
    """
    Fetch and return the list of users from the API.

    Logs an error if the fetch fails.
    """
    headers = {'Authorization': f'Token {API_TOKEN}'}
    response = requests.get(
        API_BASE_URL + "/users/", headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch users: {response.status_code}")
        return []


async def receive_who(update: Update, context: CallbackContext):
    """
    Receive the user involved in the transaction.

    Prompts for selecting the account after receiving the user.
    """
    text = update.message.text
    context.user_data['transaction_data']['who'] = text
    await update.message.reply_text("Select an account (enter the number):")
    accounts = get_accounts()
    for account in accounts:
        await update.message.reply_text(f"{account['id']}: {account['title']}")
    return ACCOUNT


def get_accounts():
    """
    Fetch and return the list of accounts from the API.

    Logs an error if the fetch fails.
    """
    headers = {'Authorization': f'Token {API_TOKEN}'}
    url = API_BASE_URL + "/account/"
    print(f'url:{url}, headers: {headers}')
    response = requests.get(API_BASE_URL + "/account/",
                            headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch accounts: {response.status_code}")
        return []


async def receive_account(update: Update, context: CallbackContext):
    """
    Handle the account selection for the transaction.

    Prompts for entering the amount after selecting the account.
    """
    account_id = update.message.text
    context.user_data['transaction_data']['account'] = account_id

    await update.message.reply_text("Enter the amount (format: 123.45):")
    return AMOUNT


async def receive_amount(update: Update, context: CallbackContext):
    """
    Receive the transaction amount from the user.

    Initiates the date selection process after receiving the amount.
    """
    amount_text = update.message.text
    context.user_data['transaction_data']['amount'] = amount_text

    return await ask_for_date(update, context)


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


def get_categories():
    """
    Fetch and return the list of categories from the API.

    Logs an error if the fetch fails.
    """
    headers = {'Authorization': f'Token {API_TOKEN}'}
    response = requests.get(
        API_BASE_URL + "/category/", headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch categories: {response.status_code}")
        return []


def post_transaction(data):
    """
    Post the transaction data to the API.

    Returns the success status of the operation.
    """
    headers = {'Authorization': f'Token {API_TOKEN}'}
    response = requests.post(
        API_BASE_URL + "/transaction/",
        headers=headers, json=data, verify=False)
    return response.status_code == 200


def confirm_transaction(update: Update, context: CallbackContext):
    """
    Confirm the posting of a transaction.

    Sends a success or failure message to the user.
    """
    data = context.user_data['transaction_data']
    if post_transaction(data):
        update.message.reply_text("Transaction successfully added.")
    else:
        update.message.reply_text("Transaction failed to add.")
    return ConversationHandler.END


async def error(update: Update, context: CallbackContext):
    """Log errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


async def handle_category_selection(update: Update, context: CallbackContext):
    """
    Handle the user's selection of a transaction category.

    Prompts for the next step after the selection.
    """
    query = update.callback_query
    await query.answer()

    category_id = query.data.split("_")[1]
    context.user_data['transaction_data']['category'] = category_id

    await query.edit_message_text(text=f"Selected category ID: {category_id}\n"
                                  "Who is this transaction for?")
    users = get_users()
    keyboard = [
        [InlineKeyboardButton(
            user['username'], callback_data=f"who_{user['id']}")]
        for user in users
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "Choose a person:", reply_markup=reply_markup)
    return WHO


async def handle_who_selection(update: Update, context: CallbackContext):
    """
    Handle the user's selection of who the transaction is for.

    Prompts for the next step after the selection.
    """
    query = update.callback_query
    await query.answer()

    who_id = query.data.split("_")[1]
    context.user_data['transaction_data']['who'] = who_id

    await query.edit_message_text(
        text=f"Selected person ID: {who_id}\nSelect an account:")

    accounts = get_accounts()
    keyboard = [
        [InlineKeyboardButton(
            account['title'], callback_data=f"account_{account['id']}")]
        for account in accounts
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "Choose an account:", reply_markup=reply_markup)
    return ACCOUNT


async def handle_account_selection(update: Update, context: CallbackContext):
    """
    Handle the user's selection of an account for the transaction.

    Prompts for the next step after the selection.
    """
    query = update.callback_query
    await query.answer()

    account_id = query.data.split("_")[1]
    context.user_data['transaction_data']['account'] = account_id

    await query.edit_message_text(
        text=f"Selected account ID: {account_id}\n"
             "Enter the amount (format: 123.45):")
    return AMOUNT


def create_calendar(year, month):
    """
    Create an inline keyboard calendar.

    Generates a calendar for the specified year and month.
    """
    keyboard_structure = []
    keyboard_structure.append(
        (InlineKeyboardButton(
            f"{calendar.month_name[month]} {year}",
            callback_data="ignore"),))

    days_of_week = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    keyboard_structure.append(
        tuple(InlineKeyboardButton(day, callback_data="ignore")
              for day in days_of_week))

    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = tuple(
            InlineKeyboardButton(
                str(day),
                callback_data=f"calendar-day-{year}-{month}-{day}")
            if day != 0 else InlineKeyboardButton(
                " ", callback_data="ignore") for day in week)
        keyboard_structure.append(row)

    previous_month = month - 1 if month > 1 else 12
    previous_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    navigation_row = (
        InlineKeyboardButton(
            "<",
            callback_data=f"calendar-month-{previous_year}-{previous_month}"),
        InlineKeyboardButton(
            ">",
            callback_data=f"calendar-month-{next_year}-{next_month}")
    )
    keyboard_structure.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=tuple(keyboard_structure))


async def handle_calendar_callback(update: Update, context: CallbackContext):
    """
    Handle the user's interaction with the calendar.

    Processes either date selection or navigation between months.
    """
    query = update.callback_query
    callback_data = query.data
    await query.answer()

    parts = callback_data.split("-")

    if parts[0] == "calendar" and parts[1] == "day" and len(parts) == 5:
        year, month, day = map(int, parts[2:5])
        selected_date = datetime(year, month, day).date()
        context.user_data['transaction_data']['date'] = (
            selected_date.strftime("%Y-%m-%d"))
        data = context.user_data['transaction_data']
        if post_transaction(data):
            await query.message.reply_text("Transaction successfully added.")
        else:
            await query.message.reply_text("Transaction failed to add.")
        return ConversationHandler.END
    elif parts[0] == "calendar" and parts[1] == "month" and len(parts) == 4:
        year, month = map(int, parts[2:4])
        new_calendar = create_calendar(year, month)
        await query.edit_message_reply_markup(reply_markup=new_calendar)


async def ask_for_date(update: Update, context: CallbackContext):
    """
    Prompt the user to select a date.

    Uses a calendar for date selection.
    """
    today = datetime.today()
    calendar_markup = create_calendar(today.year, today.month)
    await update.message.reply_text(
        "Please choose a date:", reply_markup=calendar_markup)
    return DATE


def main():
    """
    Create and run the bot application.

    Sets up handlers and starts the bot.
    """
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            add_transaction, pattern='^add_transaction$')],
        states={
            TITLE: [MessageHandler(filters.TEXT, receive_title)],
            CATEGORY: [CallbackQueryHandler(handle_category_selection,
                                            pattern='^category_')],
            WHO: [CallbackQueryHandler(handle_who_selection, pattern='^who_')],
            ACCOUNT: [CallbackQueryHandler(handle_account_selection,
                                           pattern='^account_')],
            AMOUNT: [MessageHandler(filters.TEXT, receive_amount)],
            DATE: [CallbackQueryHandler(
                handle_calendar_callback, pattern='^calendar-')]
        },
        fallbacks=[CommandHandler('start', start)],
        per_chat=True,
        per_user=True,
        per_message=False
    )

    category_handler = CallbackQueryHandler(
        handle_category_selection, pattern='^category_')
    who_handler = CallbackQueryHandler(handle_who_selection, pattern='^who_')
    account_handler = CallbackQueryHandler(
        handle_account_selection, pattern='^account_')

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(category_handler)
    application.add_handler(who_handler)
    application.add_handler(account_handler)
    application.add_handler(CallbackQueryHandler(
        handle_calendar_callback,
        pattern="^calendar-"))

    application.add_error_handler(error)
    application.run_polling()


if __name__ == '__main__':
    main()
