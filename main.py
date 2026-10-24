import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = "8268662609:AAE0amVm4aRZGC-HcHC5G4ktq1h7EybTWTc"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def get_bottom_keyboard():
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add(types.KeyboardButton("Меню"))
    return reply_kb

def get_main_inline_keyboard():
    inline_kb = types.InlineKeyboardMarkup(row_width=2)

    it1 = types.InlineKeyboardButton("Моя ферма", callback_data="farm")
    it2 = types.InlineKeyboardButton("Грядки", callback_data="beds")
    it3 = types.InlineKeyboardButton("Кухня", callback_data="kitchen")
    it4 = types.InlineKeyboardButton("Магазин", callback_data="shop")
    it5 = types.InlineKeyboardButton("Рандом-квест", callback_data="random")
    it6 = types.InlineKeyboardButton("Заказы", callback_data="order")
    it7 = types.InlineKeyboardButton("Амбар", callback_data="barn")
    it8 = types.InlineKeyboardButton("Премиум", callback_data="premium")
    it9 = types.InlineKeyboardButton("Правила", callback_data="rules")

    inline_kb.add(it1, it2, it3, it4, it5, it6, it7, it8)
    inline_kb.add(it9)
    return inline_kb

async def send_main_menu(chat_id):
    caption_text = (
        "Добро пожаловать в мир Ашет-Фермы!🎨🌿\n"
        "Здесь магия красок оживляет реальность. Я — твой цифровой помощник в этом медитативном путешествии.\n\n"
        "Как играть? Всё просто:\n"
        "1️⃣ Выбирай растения - раскрась картинку.\n"
        "2️⃣ Присылай фото готовой работы на проверку Хозяйке.\n"
        "3️⃣ Собирай урожай, готовь на Кухне и выполняй заказы сказочных героев!\n\n"
        "🧩 Разгадывай загадки в разделе «Рандом», чтобы было еще интереснее.\n\n"
        "Твоё приключение начинается прямо сейчас. Маркеры готовы?\n\n"
        "👇 Выбирай действие на панели ниже!"
    )

    await bot.send_message(
        chat_id, 
        "Панель управления активирована! 🕹", 
        reply_markup=get_bottom_keyboard()
    )
    
    try:
        with open('start.png.png', 'rb') as photo: # Твоё имя файла
            await bot.send_photo(
                chat_id, 
                photo, 
                caption=caption_text,
                reply_markup=get_main_inline_keyboard(),
                parse_mode="Markdown"
            )
    except Exception:
        await bot.send_message(
            chat_id, 
            caption_text, 
            reply_markup=get_main_inline_keyboard(), 
            parse_mode="Markdown"
        )

@dp.message_handler(commands=['start'])
async def welcome(massage: types.Message):
    await send_main_menu(massage.chat.id)

@dp.message_handler(lambda message: message.text == "Меню")
async def menu_button_pressed(message: types.Message):
    await send_main_menu(message.chat.id)

@dp.callback_query_handler(lambda c: c.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    rules_text = (
        "Правила игры Hachette Farm\n\n"
        "Раскрашивай: Выбирай рисунок, разкрашивай его марекрами, ручками или карандашами.\n"
        "Отправляй: Загружай фото готовой работы в бот\n"
        "Получай ресурсы: За каждую работу Хозяйка дает монеты, семена и опыт.\n"
        "Розвивайся: Покупай новые грядки, готовь блюда на кухне и выпоняй заказы!\n\n"
        "Соблюдай порядок и не читери!\n\n"
        "Чтобы вернуться назад, нажми кнопку 'Меню' внизу экрана!"
        )
    
    try:
        await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption=rules_text,
        reply_markup=None,
        parse_mode="Markdown"
    )
    except Exception:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=rules_text,
            reply_markup=None,
            parse_mode="Markdown"
        )

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Ферма запущена!")
    executor.start_polling(dp, skip_updates=True, loop=loop)
