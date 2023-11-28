"""
Utilities Module for Telegram Bot.

This module contains utility functions that assist in various operations of
the Telegram bot, primarily focusing on user interface elements like creating
inline keyboard calendars. These utilities are designed to be reusable and
can be easily integrated into different parts of the bot for consistent
functionality and reduced code duplication.

The modular approach ensures that specific functionalities are encapsulated
within these utility functions, making the codebase cleaner and more
manageable as the bot scales up in complexity.

Functions:
    create_calendar(year, month): Generates an inline keyboard calendar for
    the specified year and month, providing an interactive and user-friendly
    method for date selection in the bot.
"""
import calendar

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
