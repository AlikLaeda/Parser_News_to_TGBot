# -*- coding: utf-8 -*-

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_inline_keys():
    keys_build = InlineKeyboardBuilder()
    
    keys_build.button(text='Reprint', callback_data='Yes')
    keys_build.button(text='No', callback_data='No')
    keys_build.button(text='Delete', callback_data='Delete')
    keys_build.button(text='Comment', callback_data='Comment')
    keys_build.button(text='Text', callback_data='Text')
    keys_build.button(text='Com&Text', callback_data='Com&Text')
    keys_build.adjust(3)
    return keys_build.as_markup()