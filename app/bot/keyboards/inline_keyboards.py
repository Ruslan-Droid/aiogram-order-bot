from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fluentogram import TranslatorRunner


def get_help_keyboard(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    url_to_git_hub = "https://github.com/Ruslan-Droid/aiogram_bot_template"
    button_github = InlineKeyboardButton(text=i18n.get("github-button"), url=url_to_git_hub)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_github]])

    return keyboard
