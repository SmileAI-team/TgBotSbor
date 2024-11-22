from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

upload_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Загрузить фото", callback_data="upload_photo"),
            InlineKeyboardButton(text="Пропустить", callback_data="skip_photo")
        ]
    ]
)

comment_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Пропустить комментарий", callback_data="skip_comment")
        ]
    ]
)

start_upload_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Загрузить фото", callback_data="start_upload")
        ]
    ]
)
# Кнопка согласия на обработку данных
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

consent_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, я согласен", callback_data="consent_yes"),
            InlineKeyboardButton(text="Нет, не согласен", callback_data="consent_no")
        ]
    ]
)
# Кнопка готовности пользователя к диагностике
ready_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Готово", callback_data="ready")
        ]
    ]
)