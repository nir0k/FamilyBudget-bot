"""
Handlers for Family Budget Management Telegram Bot.

This module contains handlers for various stages of the transaction process
within the bot. These handlers manage user interactions for selecting
categories, users, accounts, and dates for transactions. They use Telegram's
InlineKeyboard for interactive responses, guiding users through the transaction
creation process.

Functions:
    handle_category_selection(update, context): Manages user's category choice
                                                and prompts for user selection.
    handle_who_selection(update, context): Manages user's beneficiary selection
                                           and prompts for account selection.
    handle_account_selection(update, context): Manages account selection for
                                               the transaction and prompts for
                                               amount.
    handle_calendar_callback(update, context): Manages user interaction with
                                               the inline calendar for date
                                               selection.

Each function ensures a smooth transition to the next transaction stage,
providing a seamless user experience within the bot's conversation flow.
"""
import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler

from modules.api import (get_accounts, get_currencies, get_family_status,
                         get_user_details, post_transaction)
from modules.constants import ACCOUNT, AMOUNT, WHO
from modules.user_management import get_users
from modules.utils import create_calendar


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
    users = get_users(context)
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

    Prompts for the next step after the selection by displaying a list of
    accounts in the format "<Account title> - <Username>".
    """
    query = update.callback_query
    await query.answer()

    who_id = query.data.split("_")[1]
    context.user_data['transaction_data']['who'] = who_id

    await query.edit_message_text("Select an account:")
    accounts = get_accounts(context)
    keyboard = []
    for account in accounts:
        account_display = f"{account['title']} - {account['username']}"
        keyboard.append([InlineKeyboardButton(
            account_display,
            callback_data=f"account_{account['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Choose an account:",
                                   reply_markup=reply_markup)
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


async def handle_account_status(update: Update, context: CallbackContext):
    """
    Fetch and display account status information to the user.

    This function is triggered by the "Account Status" button in the Telegram
    bot. It retrieves account information using the get_accounts API call and
    formats this information into a readable format for the user. The function
    then sends this formatted account data back to the user.

    Args:
        update (Update): The Telegram update object containing message details.
        context (CallbackContext): Context object providing additional
                                   information and states for handling the
                                   update.
    """
    query = update.callback_query
    await query.answer()

    user_details = get_user_details(context)
    if not user_details:
        await query.message.edit_text("Unable to fetch user details.")
        return

    currency_data = get_currencies(context)
    currency_map = {currency['id']: currency['code']
                    for currency in currency_data}

    user_id = user_details['id']
    account_data = get_accounts(context, user_id=user_id)
    if not account_data:
        await query.message.edit_text("No account data available.")
        return

    response_message = "\n".join([
        f"  {account['title']}: {account['balance']}"
        f" {currency_map.get(account['currency'], 'Unknown')}"
        for account in account_data
    ])
    await query.message.edit_text("Account status:\n" + response_message)


async def handle_calendar_callback(update: Update, context: CallbackContext):
    """
    Process the user's interaction with the inline calendar.

    Handles two types of interactions: selection of a specific date and
    navigation between months. For date selection, it stores the selected date
    in the user's context and attempts to post the transaction. For month
    navigation, it updates the calendar to display the selected month.

    Args:
        update (Update): The incoming update.
        context (CallbackContext): The context of the callback.

    Returns:
        int: The END state of the conversation if a date is selected, or
             maintains the current state for month navigation.
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

        if query.message:
            if post_transaction(data, context):
                await query.edit_message_text(
                    text="Transaction successfully added.", reply_markup=None)
            else:
                await query.edit_message_text(
                    text="Transaction failed to add.", reply_markup=None)
        else:
            logging.error("No message associated with the callback query")

        return ConversationHandler.END

    elif parts[0] == "calendar" and parts[1] == "month" and len(parts) == 4:
        year, month = map(int, parts[2:4])
        new_calendar = create_calendar(year, month)
        await query.edit_message_reply_markup(reply_markup=new_calendar)


async def handle_profile(update: Update, context: CallbackContext):
    """
    Handle the 'Profile' button click in the Telegram bot.

    This function retrieves the user's profile information from the API and
    formats it into a readable message. It includes details like username,
    name, email, Telegram user ID, role, and family information with usernames
    of family members. The function replaces the message with the inline
    keyboard with this profile information.

    Args:
        update (Update): The Telegram update object containing message details.
        context (CallbackContext): Context object providing additional
                                   information and states for handling
                                   the update.
    """
    query = update.callback_query
    await query.answer()

    user_details = get_user_details(context)
    if not user_details:
        await query.message.reply_text("Unable to fetch user details.")
        return

    all_users = get_users(context)
    user_mapping = {user['id']: user['username'] for user in all_users}

    family_members = [user_mapping.get(member_id, "Unknown")
                      for member_id in user_details['family']['members']]

    response_message = (
        f"Profile:\n"
        f"  Username: {user_details['username']}\n"
        f"  First Name: {user_details['first_name']}\n"
        f"  Last Name: {user_details.get('last_name', '-')}\n"
        f"  Email: {user_details['email']}\n"
        f"  Telegram User ID: {update.effective_user.id}\n"
        f"  Role: {user_details['role']}\n"
        f"  Family: {user_details['family']['title']}\n"
        f"    - Members: {', '.join(family_members)}"
    )

    await query.message.edit_text(response_message)


async def handle_family_status(update: Update, context: CallbackContext):
    """
    Handle the 'Family Status' button click in the Telegram bot.

    Fetches the family's current status from the API and displays it to the
    user.
    The information includes the title of the family and the current balance.

    Args:
        update (Update): The Telegram update object containing message details.
        context (CallbackContext): Context object providing additional
                                   information.
    """
    query = update.callback_query
    await query.answer()

    family_status = get_family_status(context)
    if not family_status:
        await query.message.edit_text("Unable to fetch family status.")
        return

    status = family_status[0]
    response_message = (f"Family status:\n"
                        f"  Title: {status['title']}\n"
                        f"  Current Balance: {status['current']}"
                        f" {status['currency']}")

    await query.message.edit_text(response_message)
