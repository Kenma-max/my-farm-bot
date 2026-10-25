import asyncio
import sqlite3
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

# 1. Объявляем переменные
ADMIN_CHAT_ID = -5560765603
TOKEN = "8268662609:AAE0amVm4aRZGC-HcHC5G4ktq1h7EybTWTc"

# 2. Создаем бота и хранилище состояний
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 3. Состояния
class FarmStates(StatesGroup):
    waiting_for_photos = State()

# 4. База данных
if not os.path.exists('/data'):
    os.makedirs('/data', exist_ok=True)
db_conn = sqlite3.connect('/data/farm.db', check_same_thread=False)
db_cursor = db_conn.cursor()


if not os.path.exists('/data'):
    os.makedirs('/data', exist_ok=True)
    db_conn = sqlite3.connect('/data/farm.db', check_same_thread=False)
    db_cursor =db_conn.cursor()

PLANTS_DATA = {
    "carrot": {"name": "Морковь 🥕", "grow_time_minutes": 5},
    "potato": {"name": "Картофель 🥔", "grow_time_minutes": 10},
    "cabbage": {"name": "Капуста 🥬", "grow_time_minutes": 15},
    "seaweed": {"name": "Водоросли 🌿", "grow_time_minutes": 20},
    "mushrooms": {"name": "Грибы 🍄", "grow_time_minutes": 25},
    "strawberry": {"name": "Клубника 🍓", "grow_time_minutes": 30},
    "apple": {"name": "Яблоко 🍎", "grow_time_minutes": 60},
    "wheat": {"name": "Пшеница 🌾", "grow_time_minutes": 90},
    "onion": {"name": "Лук 🧅", "grow_time_minutes": 120},
    "pumpkin": {"name": "Тыква 🎃", "grow_time_minutes": 180},
}

def init_db():
    import os
    if not os.path.exists('/data'):
        os.makedirs('/data', exist_ok=True)
    
    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, level INTEGER DEFAULT 0, exp INTEGER DEFAULT 0, coins INTEGER DEFAULT 0, planted INTEGER DEFAULT 0, products INTEGER DEFAULT 0, cooking INTEGER DEFAULT 0, farmlands_count INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS farmlands (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, farmland_number INTEGER, plant_type TEXT, plant_time TEXT, harvest_time TEXT)''')
    
    conn.commit()

def get_user(user_id):
    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    cursor.execute('SELECT level, exp, coins, planted, products, cooking, farmlands_count FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        row = (0, 0, 0, 0, 0, 0, 1) 
        
    return {
        'level': row[0],
        'exp': row[1],
        'coins': row[2],
        'planted': row[3],
        'products': row[4],
        'cooking': row[5],
        'farmlands_count': row[6]
    }

def update_user_data(user_id, **kwargs):
    """Обновляет данные пользователя."""
    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    set_clauses = []
    values = []
    for key, value in kwargs.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)
    
    if set_clauses:
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
        values.append(user_id)
        cursor.execute(query, tuple(values))
        conn.commit()

def get_max_exp(level):
    if level == 0:
        return 50
    return level * 100

def add_rewards(user_id, exp_to_add, coins_to_add, planted_to_add=0):
    user = get_user(user_id)
    
    new_exp = user['exp'] + exp_to_add
    new_coins = user['coins'] + coins_to_add
    new_planted = user['planted'] + planted_to_add
    new_level = user['level']
    
    max_exp = get_max_exp(new_level)
    
    while new_exp >= max_exp:
        new_exp -= max_exp
        new_level += 1
        max_exp = get_max_exp(new_level)

    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET level = ?, exp = ?, coins = ?, planted = ?
        WHERE user_id = ?
    ''', (new_level, new_exp, new_coins, new_planted, user_id))
    conn.commit()

def get_farmlands(user_id):
    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    cursor.execute('SELECT farmland_number, plant_type, plant_time, harvest_time FROM farmlands WHERE user_id = ? ORDER BY farmland_number', (user_id,))
    farmlands = []
    for row in cursor.fetchall():
        farmlands.append({
            'number': row[0],
            'plant_type': row[1],
            'plant_time': datetime.fromisoformat(row[2]) if row[2] else None,
            'harvest_time': datetime.fromisoformat(row[3]) if row[3] else None
        })
    return farmlands

def get_farmland_status_text(farmland_data):
    """Формирует текст статуса грядки."""
    if farmland_data['plant_type']:
        plant_name = PLANTS_DATA.get(farmland_data['plant_type'], {}).get('name', farmland_data['plant_type'])
        
        # Проверяем, созрело ли
        if datetime.now() >= farmland_data['harvest_time']:
            return f"**{plant_name}** 🟢 ГОТОВО! (Собрать)"
        else:
            time_left = farmland_data['harvest_time'] - datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = []
            if hours > 0:
                time_str.append(f"{hours} ч")
            if minutes > 0:
                time_str.append(f"{minutes} мин")
            elif not hours: # Если часов нет, но есть секунды, показать секунды
                time_str.append(f"{seconds} сек")
            
            return f"**{plant_name}** 🟡 Дозревает... ({' '.join(time_str)})"
    else:
        return "Пусто ⚪ (Посадить)"

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

def get_farmland_keyboard(user_id):
    """Клавиатура с грядками пользователя."""
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    user_farmlands_count = get_user(user_id)['farmlands_count']
    current_farmlands = get_farmlands(user_id) # Получаем реальные данные грядок

    for i in range(1, user_farmlands_count + 1):
        # Находим данные для этой грядки
        farmland_data = next((f for f in current_farmlands if f['number'] == i), {'number': i, 'plant_type': None})
        
        status_text = get_farmland_status_text(farmland_data)
        
        if farmland_data['plant_type'] and datetime.now() >= farmland_data['harvest_time']:
            # Если растение созрело - кнопка "Собрать"
            inline_kb.add(types.InlineKeyboardButton(f"Грядка {i}: {status_text}", callback_data=f"harvest_{i}"))
        elif farmland_data['plant_type']:
            # Если растение растет - кнопка "Посмотреть статус" (или ничего)
            inline_kb.add(types.InlineKeyboardButton(f"Грядка {i}: {status_text}", callback_data=f"farmland_status_{i}"))
        else:
            # Если грядка пуста - кнопка "Посадить"
            inline_kb.add(types.InlineKeyboardButton(f"Грядка {i}: {status_text}", callback_data=f"plant_seed_{i}"))
            
    inline_kb.add(types.InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return inline_kb

def get_seeds_keyboard(farmland_number):
    """Клавиатура для выбора семян."""
    inline_kb = types.InlineKeyboardMarkup(row_width=2)
    for key, data in PLANTS_DATA.items():
        inline_kb.add(types.InlineKeyboardButton(data['name'], callback_data=f"seed_{key}_on_{farmland_number}"))
    inline_kb.add(types.InlineKeyboardButton("◀️ Назад к грядкам", callback_data="beds")) # Кнопка назад к грядкам
    return inline_kb

async def send_main_menu(chat_id):
    caption_text = (
        "Добро привет пожаловать в мир Ашет-Фермы!🎨🌿\n"
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

@dp.message_handler(commands=['add_test_crop'])
async def test_crop_reward(message: types.Message):
    add_rewards(message.from_user.id, exp_to_add=10, coins_to_add=15, planted_to_add=1)
    await message.reply("🥕 Вы вырастили морковь! Получено: +10 Опыта, +15 Монет!")

@dp.message_handler(commands=['reset_me'])
async def reset_user_profile(message: types.Message):
    conn = sqlite3.connect('/data/farm.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET level = 0, exp = 0, coins = 0, planted = 0, products = 0, cooking = 0
        WHERE user_id = ?
    ''', (message.from_user.id,))
    conn.commit()
    await message.reply("🧹 Твой профиль полностью обнулен! Ты снова бомж 0 уровня!")

@dp.callback_query_handler(lambda c: c.data == 'farm')
async def process_farm(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    user_id = callback_query.from_user.id
    user_data = get_user(user_id)
    max_exp = get_max_exp(user_data['level'])
    
    farm_text = (
        f"🌾 **Моя ферма**\n\n"
        f"Опыт: {user_data['exp']}/{max_exp}\n"
        f"Твой уровень: {user_data['level']}\n"
        f"Монеты: {user_data['coins']}\n"
        f"Всего посажено: {user_data['planted']}\n"
        f"Продукты: {user_data['products']}\n"
        f"Готовка: {user_data['cooking']}"
    )
    
    try:
        await bot.edit_message_caption(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            caption=farm_text,
            reply_markup=None,
            parse_mode="Markdown"
        )
    except Exception:
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=farm_text,
            reply_markup=None,
            parse_mode="Markdown"
        )

@dp.callback_query_handler(lambda c: c.data == 'beds')
async def process_beds(callback_query: types.CallbackQuery):
    await callback_query.answer() # Мгновенно отбиваем Телеграму
    
    user_id = callback_query.from_user.id
    user_data = get_user(user_id)
    
    beds_text = (
        f"🌱 **Твои грядки:**\n"
        f"У тебя {user_data['farmlands_count']} грядок. Выбери грядку, чтобы посмотреть статус или посадить семена.\n"
        f"💰 Монет: {user_data['coins']}\n"
    )
    
    try:
        await callback_query.message.edit_caption(
            caption=beds_text,
            reply_markup=get_farmland_keyboard(user_id),
            parse_mode="Markdown"
        )
    except Exception:
        await callback_query.message.edit_text(
            text=beds_text,
            reply_markup=get_farmland_keyboard(user_id),
            parse_mode="Markdown"
        )

@dp.callback_query_handler(lambda c: c.data.startswith('plant_seed_'))
async def select_seed_to_plant(callback_query: types.CallbackQuery):
    await callback_query.answer()
    farmland_number = int(callback_query.data.split('_')[2])
    
    plant_text = (
        f"Выбери семена для **Грядки {farmland_number}**:\n"
        f"Каждое семя имеет свое время созревания. Выбирай с умом!"
    )
    
    try:
        await callback_query.message.edit_caption(
            caption=plant_text,
            reply_markup=get_seeds_keyboard(farmland_number),
            parse_mode="Markdown"
        )
    except Exception:
        await callback_query.message.edit_text(
            text=plant_text,
            reply_markup=get_seeds_keyboard(farmland_number),
            parse_mode="Markdown"
        )

# 1. Когда юзер жмет на конкретное семя (например, "Морковь")
@dp.callback_query_handler(lambda c: c.data.startswith('seed_'))
async def choose_seed_finish(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    # Формат callback_data был: seed_carrot_on_1
    parts = callback_query.data.split('_')
    seed_key = parts[1]       # например, carrot
    farmland_number = parts[3] # например, 1
    
    plant_name = PLANTS_DATA.get(seed_key, {}).get('name', 'Растение')
    
    text = (
        f"🌱 Ты выбрала: **{plant_name}** для Грядки №{farmland_number}!\n\n"
        f"📝 **Задание от Хозяйки:**\n"
        f"1. Возьми раскраску и сфоткай чистую (ДО).\n"
        f"2. Раскрась и сфоткай готовую (ПОСЛЕ).\n"
        f"3. Нажми кнопку ниже и пришли оба фото!"
    )
    
    # Клавиатура с кнопкой "Сдать работу"
    kb = types.InlineKeyboardMarkup()
    # Зашиваем в callback семя и номер грядки: submit_carrot_1
    kb.add(types.InlineKeyboardButton("📤 Сдать работу", callback_data=f"submit_{seed_key}_{farmland_number}"))
    kb.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="beds"))

    try:
        await callback_query.message.edit_caption(caption=text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await callback_query.message.edit_text(text=text, reply_markup=kb, parse_mode="Markdown")


# 2. Когда юзер жмет "Сдать работу"
@dp.callback_query_handler(lambda c: c.data.startswith('submit_'))
async def submit_work(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    _, seed_key, farmland_number = callback_query.data.split('_')
    
    # Сохраняем в память бота, какое семя и на какую грядку он сажает
    await state.update_data(seed_key=seed_key, farmland_number=farmland_number, user_id=callback_query.from_user.id)
    await FarmStates.waiting_for_photos.set() # Включаем режим ожидания фото
    
    text = "📸 Жду твою работу с нетерпением! Пришли фото ДО и ПОСЛЕ (можно два фото по очереди или альбомом)."
    
    try:
        await callback_query.message.edit_caption(caption=text, reply_markup=None, parse_mode="Markdown")
    except Exception:
        await callback_query.message.edit_text(text=text, reply_markup=None, parse_mode="Markdown")


# 3. Прием фото от юзера и отправка в АДМИН-ЧАТ
@dp.message_handler(content_types=['photo'], state=FarmStates.waiting_for_photos)
async def get_photos(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    # Кнопки для тебя (админа) в админ-чате
    kb = types.InlineKeyboardMarkup()
    # Зашиваем в callback одобрения: approve_USERID_SEED_BED
    kb.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"approve_{data['user_id']}_{data['seed_key']}_{data['farmland_number']}"))
    kb.add(types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{data['user_id']}"))
    
    # Отправляем в админ-чат
    await bot.send_photo(
        ADMIN_CHAT_ID, 
        photo_id, 
        caption=f"🔔 Новая работа от игрока @{message.from_user.username or message.from_user.first_name}!\nСажает: {data['seed_key']} на грядку №{data['farmland_number']}", 
        reply_markup=kb
    )
    
    await message.reply("✅ Работа отправлена Хозяйке на проверку! Ожидай ответа.")
    await state.finish() # Выключаем режим ожидания


# 4. Когда админ жмет "Принять" в админ-чате
@dp.callback_query_handler(lambda c: c.data.startswith('approve_'))
async def approve_work(callback_query: types.CallbackQuery):
    await callback_query.answer("Работа принята!")
    
    _, user_id, seed_key, farmland_number = callback_query.data.split('_')
    user_id = int(user_id)
    farmland_number = int(farmland_number)
    
    grow_time_minutes = PLANTS_DATA.get(seed_key, {}).get('grow_time_minutes', 30)
    plant_name = PLANTS_DATA.get(seed_key, {}).get('name', 'Растение')
    
    # ТЕПЕРЬ САМА ПОСАДКА В БАЗУ (после одобрения админом!)
    plant_time = datetime.now()
    harvest_time = plant_time + timedelta(minutes=grow_time_minutes)
    
    db_cursor.execute('SELECT id FROM farmlands WHERE user_id = ? AND farmland_number = ?', (user_id, farmland_number))
    if db_cursor.fetchone():
        db_cursor.execute('''
            UPDATE farmlands 
            SET plant_type = ?, plant_time = ?, harvest_time = ? 
            WHERE user_id = ? AND farmland_number = ?
        ''', (seed_key, plant_time.isoformat(), harvest_time.isoformat(), user_id, farmland_number))
    else:
        db_cursor.execute('''
            INSERT INTO farmlands (user_id, farmland_number, plant_type, plant_time, harvest_time) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, farmland_number, seed_key, plant_time.isoformat(), harvest_time.isoformat()))
    db_conn.commit()
    
    # Сообщение игроку
    await bot.send_message(
        user_id, 
        f"🎉 Хозяйка приняла твою работу!\n"
        f"🌱 **{plant_name}** посажена на грядку №{farmland_number}!\n"
        f"⏳ Урожай созреет через **{grow_time_minutes} минут**."
    )
    
    # Обновляем сообщение в админ-чате
    await callback_query.message.edit_caption(
        caption=f"✅ Одобрено! Растение посажено на грядку №{farmland_number}.",
        reply_markup=None
    )


# 5. Когда админ жмет "Отказать"
@dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
async def reject_work(callback_query: types.CallbackQuery):
    await callback_query.answer("Работа отклонена.")
    _, user_id = callback_query.data.split('_')
    
    await bot.send_message(int(user_id), "❌ Хозяйка отклонила работу. Попробуй переделать фото и отправить заново!")
    await callback_query.message.edit_caption(caption="❌ Отклонено.", reply_markup=None)

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
    init_db()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Ферма запущена!")
    executor.start_polling(dp, skip_updates=True, loop=loop)
 