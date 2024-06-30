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
