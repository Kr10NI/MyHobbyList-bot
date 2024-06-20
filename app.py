import telebot
from telebot import types
import requests
import random
import psycopg2
from contextlib import closing
with closing(psycopg2.connect(dbname='films_bot', user='projectuser', password='password', host='localhost')) as conn:
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM filmlist ')
        for row in cursor:
            print(row) 
            # проверка работы бд
bot = telebot.TeleBot('7390621130:AAGaN0szPdQb2dFSxGwJargEDUcSnZggxI0')
api_key = "66c4bb59-6228-4ba6-a93e-90506aeb9bfe"
api_url = "https://kinopoiskapiunofficial.tech/api/v2.2/films/top?type=TOP_250_BEST_FILMS&page=1"
search_api_url = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"

headers = {
    'X-API-KEY': api_key
}

films_data = []
watch_later_list = []
searched_films = []

def load_top_films():
    global films_data
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        films_data = data.get('films', [])
        print(f"Loaded {len(films_data)} films.")
    else:
        print(f"Failed to load films: {response.status_code}")

load_top_films()

@bot.message_handler(commands=['start', 'main', 'hello'])
def start(message):
    button1 = types.InlineKeyboardButton("Топ чарты 🔥", callback_data='chart')
    button6 = types.InlineKeyboardButton("Поиск фильма 🔥", callback_data='research_film')
    button2 = types.InlineKeyboardButton("Рекомендации 🍿", callback_data='films')
    button3 = types.InlineKeyboardButton("Моя фильмография 🎬", callback_data='watch')
    button4 = types.InlineKeyboardButton("Удиви меня ✨", callback_data='surprise')
    button5 = types.InlineKeyboardButton("Посмотреть позже 🕐", callback_data='watch_later')

    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button6)
    markup.add(button4, button5)

    user_first_name = str(message.chat.first_name)
    bot.reply_to(message, f"Привет, {user_first_name}", reply_markup = markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        global films_data
        if call.data == 'chart':
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                films_data = data['films'][:20]
                top_films = ""
                for i, film in enumerate(films_data, start=1):
                    genres = ", ".join([genre['genre'] for genre in film['genres']])
                    countries = ", ".join([country['country'] for country in film['countries']])
                    top_films += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"
                bot.send_message(call.message.chat.id, top_films)

                backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_menu')
                selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_number')
                markup = types.InlineKeyboardMarkup()
                markup.add(backButton, selectButton)
                bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)

            else:
                bot.send_message(call.message.chat.id, "Не удалось получить данные о фильмах.")

        elif call.data == 'back_to_menu':
            start(call.message)

        elif call.data == 'select_number':
            msg = bot.send_message(call.message.chat.id, "Введите номер фильма из списка:")
            bot.register_next_step_handler(msg, process_film_number)

        elif call.data == 'back_to_film_list':
            display_top_films(call.message)

        elif call.data == 'watch_later':
            display_watch_later(call.message)

        elif call.data.startswith('add_to_watch_later_'):
            add_to_watch_later(call)

        elif call.data == 'surprise':
            random_film(call.message)

        elif call.data == 'research_film':
            msg = bot.send_message(call.message.chat.id, "Введите название фильма:")
            bot.register_next_step_handler(msg, search_film_by_keyword)

        elif call.data == 'information_surprise':
            get_film_details(call.message)
def display_top_films(message):
    top_films = ""
    for i, film in enumerate(films_data, start=1):
        genres = ", ".join([genre['genre'] for genre in film['genres']])
        countries = ", ".join([country['country'] for country in film['countries']])
        top_films += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"
    bot.send_message(message.chat.id, top_films)

    backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_menu')
    selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_number')
    markup = types.InlineKeyboardMarkup()
    markup.add(backButton, selectButton)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def process_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(films_data):
            film = films_data[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)

            backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_film_list')
            watchLaterButton = types.InlineKeyboardButton("Добавить в Посмотреть позже",
                                                          callback_data=f'add_to_watch_later_{film_index}')
            markup = types.InlineKeyboardMarkup()
            markup.add(backButton, watchLaterButton)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма")
            display_top_films(message)
            button_back = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(button_back)
            bot.send_message(message.chat.id, "Назад", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер")
        display_top_films(message)
        markup.add(button_back)
        bot.send_message("Назад", reply_markup=markup)

def get_film_details(film, chat_id):
    film_id = film['filmId']
    api_url_details = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{film_id}"
    response = requests.get(api_url_details, headers=headers)

    if response.status_code == 200:
        data = response.json()
        film_details = (
            f"Название: {film['nameRu']}\n"
            f"Год: {film['year']}\n"
            f"Рейтинг: {film.get('rating', 'N/A')}\n"
            f"Описание: {data.get('description', 'Нет описания')}\n"
            f"Продолжительность: {data.get('filmLength', 'N/A')} минут\n"
            f"Возрастное ограничение: {data.get('ratingAgeLimits', 'N/A')}\n"
        )
        if 'posterUrl' in data:
            bot.send_photo(chat_id = chat_id, photo=data['posterUrl'])
        return film_details
    else:
        return "Не удалось получить подробную информацию о фильме."

def display_watch_later(message):
    if watch_later_list:
        watch_later_films = "Фильмы в списке 'Посмотреть позже':\n"
        for film in watch_later_list:
            watch_later_films += f"{film['nameRu']} ({film['year']})\n"
        bot.send_message(message.chat.id, watch_later_films)
        button_back = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(button_back)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Список 'Посмотреть позже' пуст.")
        button_back = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(button_back)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def add_to_watch_later(call):
    film_index = int(call.data.split('_')[-1])
    if "searched" in call.data:
        film = searched_films[film_index]
    else:
        film = films_data[film_index]
    watch_later_list.append(film)
    bot.send_message(call.message.chat.id, f"Фильм '{film['nameRu']}' добавлен в список 'Посмотреть позже'.")

def random_film(message):
    if films_data:
        film = random.choice(films_data)
        film_index = films_data.index(film)
        genres = ", ".join([genre['genre'] for genre in film['genres']])
        countries = ", ".join([country['country'] for country in film['countries']])
        bot.send_message(message.chat.id, f"Советую посмотреть: {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}")
        button_back = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
        button_information = types.InlineKeyboardButton("Узнать подробнее", callback_data="information_surprise")
        button_add_to_watch_later = types.InlineKeyboardButton("Добавить в посмотреть позже", callback_data=f"add_to_watch_later_{film_index}")
        markup = types.InlineKeyboardMarkup()
        markup.add(button_information)
        markup.add(button_add_to_watch_later)
        markup.add(button_back)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Не удалось получить данные о фильмах.")
        button_back = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(button_back)
        bot.send_message(message.chat.id, "Выберите действие", reply_markup=markup)

def search_film_by_keyword(message):
    keyword = message.text
    global searched_films
    response = requests.get(f"{search_api_url}?keyword={keyword}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        searched_films = data.get('films', [])
        if searched_films:
            search_results = ""
            for i, film in enumerate(searched_films[:10], start=1):
                genres = ", ".join([genre['genre'] for genre in film['genres']])
                countries = ", ".join([country['country'] for country in film['countries']])
                search_results += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"
            bot.send_message(message.chat.id, search_results)
            msg = bot.send_message(message.chat.id, "Введите номер фильма из списка для получения подробной информации:")
            bot.register_next_step_handler(msg, process_search_film_number)
        else:
            bot.send_message(message.chat.id, "Фильмы не найдены. Попробуйте другой запрос.")
            start(message)
    else:
        bot.send_message(message.chat.id, "Не удалось выполнить поиск фильма. Попробуйте позже.")
        start(message)


def process_search_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(searched_films):
            film = searched_films[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)

            backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_menu')
            watchLaterButton = types.InlineKeyboardButton("Добавить в Посмотреть позже", callback_data=f'add_to_watch_later_searched_{film_index}')
            markup = types.InlineKeyboardMarkup()
            markup.add(backButton, watchLaterButton)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма")
            search_film_by_keyword(message)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер")
        search_film_by_keyword(message)

bot.polling(none_stop=True)
