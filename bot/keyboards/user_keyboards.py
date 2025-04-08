from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
consent_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Согласен", callback_data="consent_yes"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data="consent_no")
        ]
    ]
)

# Клавиатура согласия
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📷 Загрузить фото")],
        [KeyboardButton(text="ℹ️ Инструкция"), KeyboardButton(text="📝 Обратная связь")]
    ],
    resize_keyboard=True
)

# Клавиатура загрузки
upload_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

# Клавиатура отмены
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

upload_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена"), KeyboardButton(text="✅ Готово")]
    ],
    resize_keyboard=True
)


feedback_request_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="ask_feedback")],
        [InlineKeyboardButton(text="🚫 Пропустить", callback_data="skip_feedback")]
    ]
)


feedback_request_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="ask_feedback")],
        [InlineKeyboardButton(text="🚫 Пропустить", callback_data="skip_feedback")]
    ]
)

# Клавиатура для загрузки фото через Inline-кнопку
inline_upload_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Загрузить фото", callback_data="start_upload")
        ]
    ]
)