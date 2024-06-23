import telebot
from telebot import types
import requests
import random
# app.py
from db import db

def get_films_for_user(user_id):
    conn = db.get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT films FROM filmlist WHERE id_list = %s', (user_id,))
        films = cursor.fetchone()
        if films:
            return films[0]
        else:
            return []
    except Exception as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        cursor.close()
        db.put_conn(conn)

def update_films_for_user(user_id, new_films):
    conn = db.get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE filmlist SET films = %s WHERE id_list = %s', (new_films, user_id))
        conn.commit()
        print("Запись успешно обновлена")
    except Exception as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        cursor.close()
        db.put_conn(conn)

def add_user_if_not_exists(user_first_name):
    conn = db.get_conn()
    try:
        cursor = conn.cursor()
        user = db.get_user_by_name(user_first_name)
        if not user:
            cursor.execute(
                """INSERT INTO users (name, filmlist, fav_genre, recommend, watch_later)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (user_first_name, 1, 1, 1, 1)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            print("Запись успешно добавлена ​​в таблицу Users, id:", user_id)
        else:
            user_id = user[0]
            print("Запись уже существует, id:", user_id)
        return user_id
    except Exception as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        cursor.close()
        db.put_conn(conn)




# ТОКЕНЫ
bot = telebot.TeleBot('7390621130:AAGaN0szPdQb2dFSxGwJargEDUcSnZggxI0')
api_key = "7fa8c3f5-59f4-4cef-ae3c-4b95d4378c10"
api_url = "https://kinopoiskapiunofficial.tech/api/v2.2/films/top?type=TOP_250_BEST_FILMS&page=1"
search_api_url = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"

headers = {
    'X-API-KEY': api_key
}

# ПУСТЫЕ МАССИВЫ
films_data = []
watch_later_list = []
searched_films = []
filmography = []


# API ТОП ФИЛЬМОВ
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


# ГЛАВНОЕ МЕНЮ
@bot.message_handler(commands=['start', 'main', 'hello'])
def start(message):
    button1 = types.InlineKeyboardButton("Топ чарты 🔥", callback_data='chart')
    button6 = types.InlineKeyboardButton("Поиск фильма 🔥", callback_data='research_film')
    button2 = types.InlineKeyboardButton("Рекомендации 🍿", callback_data='films')
    button3 = types.InlineKeyboardButton("Моя фильмография 🎬", callback_data='filmography')
    button4 = types.InlineKeyboardButton("Удиви меня ✨", callback_data='surprise')
    button5 = types.InlineKeyboardButton("Посмотреть позже 🕐", callback_data='watch_later')

    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button6)
    markup.add(button4, button5)

    bot.send_message(
        message.chat.id,
        f'Привет! Это MyHobbyList! \n \nДавай подберем тебе что-нибудь интересного!',
        reply_markup=markup
    )


# ОБРАБОТКА ТОП ЧАРТОВ (ПЕРВЫЙ ВЫЗОВ)
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

                backButton = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
                selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_number')
                markup = types.InlineKeyboardMarkup()
                markup.add(backButton, selectButton)
                bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)

            else:
                bot.send_message(call.message.chat.id, "Не удалось получить данные о фильмах.")


        # ОБРАБОТКА ВСЕХ ДЕЙСТВИЙ КНОПОК

        #ГЛАВНЫЕ КНОПКИ

        elif call.data == 'back_to_menu':
            start(call.message)

        elif call.data == 'back_to_film_list':
            display_top_films(call.message)

        elif call.data == 'filmography':
            display_filmography(call.message)

        elif call.data == 'watch_later':
            display_watch_later(call.message)

        elif call.data == 'surprise':
            random_film(call.message)

        #########

        ### ПОИСК ФИЛЬМА

        elif call.data == 'search_results':
            display_searched_films(call.message)

        #########

        ### ДОБАВЛЕНИЕ В ПОСМОТРЕТЬ ПОЗЖЕ И ФИЛЬМОГРАФИЮ

        elif call.data.startswith('add_to_filmography_'):
            add_to_filmography(call)

        elif call.data.startswith('add_searched_to_watch_later_'):
            add_searched_to_watch_later(call)

        elif call.data.startswith('add_to_watch_later_'):
            if 'random' in call.data:
                add_to_watch_later_random(call)
            else:
                add_to_watch_later(call)

        #######3

        # ОБРАБОТКА ДЛЯ КНОПКИ "ВЫБОР ФИЛЬМА"

        elif call.data == 'select_watch_later_number':
            msg = bot.send_message(call.message.chat.id, "Введите номер фильма из списка:")
            bot.register_next_step_handler(msg, process_watch_later_film_number)

        elif call.data == 'select_filmography_number':
            msg = bot.send_message(call.message.chat.id, "Введите номер фильма из списка:")
            bot.register_next_step_handler(msg, process_filmography_film_number)

        elif call.data == 'select_search_number':
            msg = bot.send_message(call.message.chat.id, "Введите номер фильма из списка:")
            bot.register_next_step_handler(msg, process_search_film_number)

        elif call.data == 'select_number':
            msg = bot.send_message(call.message.chat.id, "Введите номер фильма из списка:")
            bot.register_next_step_handler(msg, process_film_number)

        elif call.data == 'research_film':
            msg = bot.send_message(call.message.chat.id, "Введите название фильма:")
            bot.register_next_step_handler(msg, search_film_by_keyword)


# ПОДРОБНАЯ ИНФОРМАЦИЯ О ВЫБРАННОМ ФИЛЬМЕ
def get_film_details(film, chat_id):
    film_id = film['filmId']
    api_url_details = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{film_id}"
    response = requests.get(api_url_details, headers=headers)

    if response.status_code == 200:
        data = response.json()

        age_limit = data.get('ratingAgeLimits', 'N/A')
        if age_limit != 'N/A':
            age_limit = age_limit.replace("age", "")

        film_details = (
            f"Название: {film['nameRu']}\n"
            f"Год: {film['year']}\n"
            f"Рейтинг: {film.get('rating', 'N/A')}\n"
            f"Описание: {data.get('description', 'Нет описания')}\n"
            f"Продолжительность: {data.get('filmLength', 'N/A')} минут\n"
            f"Возрастное ограничение: {age_limit}\n"
        )
        if 'posterUrl' in data:
            bot.send_photo(chat_id=chat_id, photo=data['posterUrl'])
        return film_details
    else:
        return "Не удалось получить подробную информацию о фильме."



# ОБРАБОТКА ГЛАВНЫХ КНОПОК


# КНОПКА МОЯ ФИЛЬМОГРАФИЯ
def display_filmography(message):
    if not filmography:
        bot.send_message(message.chat.id, "Ваша фильмография пуста.")
        return

    filmography_details = ""
    for i, film in enumerate(filmography, start=1):
        genres = ", ".join([genre['genre'] for genre in film['genres']])
        countries = ", ".join([country['country'] for country in film['countries']])
        filmography_details += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"

    bot.send_message(message.chat.id, filmography_details)

    backButton = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
    selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_filmography_number')
    markup = types.InlineKeyboardMarkup()
    markup.add(selectButton)
    markup.add(backButton)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# ИНФОРМАЦИЯ О ВЫБРАННОМ ФИЛЬМЕ (ФУНКЦИЯ НУЖНА ДЛЯ ВОЗВРАЩЕНИЯ ЧЕРЕЗ КНОПКУ)
def display_top_films(message):
    top_films = ""
    for i, film in enumerate(films_data, start=1):
        genres = ", ".join([genre['genre'] for genre in film['genres']])
        countries = ", ".join([country['country'] for country in film['countries']])
        top_films += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"
    bot.send_message(message.chat.id, top_films)

    backButton = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
    selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_number')
    markup = types.InlineKeyboardMarkup()
    markup.add(backButton, selectButton)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# КНОПКА ПОСМОТРЕТЬ ПОЗЖЕ
def display_watch_later(message):
    if not watch_later_list:
        bot.send_message(message.chat.id, "Ваш список 'Посмотреть позже' пуст.")
        return

    watch_later_films = ""
    for i, film in enumerate(watch_later_list, start=1):
        genres = ", ".join([genre['genre'] for genre in film['genres']])
        countries = ", ".join([country['country'] for country in film['countries']])
        watch_later_films += f"{i}. {film['nameRu']}\nГод: {film['year']}\nЖанры: {genres}\nСтраны: {countries}\n\n"

    bot.send_message(message.chat.id, watch_later_films)

    buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
    selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_watch_later_number')
    markup = types.InlineKeyboardMarkup()
    markup.add(selectButton)
    markup.add(buttonBack)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# КНОПКА УДИВИ МЕНЯ
def random_film(message):
    if not films_data:
        bot.send_message(message.chat.id, "Не удалось загрузить данные о фильмах.")
        return

    film = random.choice(films_data)
    film_details = get_film_details(film, message.chat.id)
    bot.send_message(message.chat.id, film_details)

    backButton = types.InlineKeyboardButton("Веруться в меню", callback_data="back_to_menu")
    watchLaterButton = types.InlineKeyboardButton("Добавить в Посмотреть позже",
                                                  callback_data=f'add_to_watch_later_random_{film["filmId"]}')
    filmographyButton = types.InlineKeyboardButton("Добавить в мою фильмографию",
                                                   callback_data=f'add_to_filmography_random_{film["filmId"]}')
    markup = types.InlineKeyboardMarkup()
    markup.add(watchLaterButton, filmographyButton)
    markup.add(backButton)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# ВЫВОД НАЙДЕННЫХ ФИЛЬМОВ С ПОИСКА ФИЛЬМОВ

def display_searched_films(message):
    search_results = ""
    for i, film in enumerate(searched_films, start=1):
        genres = ", ".join([genre['genre'] for genre in film.get('genres', [])])
        countries = ", ".join([country['country'] for country in film.get('countries', [])])
        search_results += f"{i}. {film['nameRu']}\nГод: {film.get('year', 'N/A')}\nЖанры: {genres}\nСтраны: {countries}\n\n"
    bot.send_message(message.chat.id, search_results)

    backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_menu')
    selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_number')
    markup = types.InlineKeyboardMarkup()
    markup.add(backButton, selectButton)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# КНОПКИ ДОБАВЛЕНИЯ



# ДОБАВЛЕНИЕ В МОЮ ФИЛЬМОГРАФИЮ
def add_to_filmography(call):
    try:
        film_index = int(call.data.split('_')[-1])
        if 'search' in call.data:
            film = searched_films[film_index]
        elif 'random' in call.data:
            film_id = film_index
            film = next((film for film in films_data if film["filmId"] == film_id), None)
        else:
            film = films_data[film_index]

        if film:
            if film not in filmography:
                filmography.append(film)
                bot.send_message(call.message.chat.id, f"{film['nameRu']} добавлен в вашу фильмографию.")
                buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
                markup = types.InlineKeyboardMarkup()
                markup.add(buttonBack)
                bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, f"{film['nameRu']} уже находится в вашей фильмографии.")
        else:
            bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении фильма в фильмографию.")
    except (ValueError, IndexError):
        bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении фильма в фильмографию.")

# ДОБАВЛЕНИЕ ФИЛЬМА В ПОСМОТРЕТЬ ПОЗЖЕ (ФУНКЦИЯ)
def add_to_watch_later(call):
    try:
        film_index = int(call.data.split('_')[-1])
        film = films_data[film_index]
        if film not in watch_later_list:
            watch_later_list.append(film)
            bot.send_message(call.message.chat.id, f"{film['nameRu']} добавлен в список 'Посмотреть позже'.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, f"{film['nameRu']} уже находится в списке 'Посмотреть позже'.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
    except (ValueError, IndexError):
        bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении фильма в список.")
        buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(buttonBack)
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)


# ДОБАВЛЕНИЕ В ПОСМОТРЕТЬ ПОЗЖЕ ДЛЯ ПОИСКА ФИЛЬМА
def add_searched_to_watch_later(call):
    try:
        film_index = int(call.data.split('_')[-1])
        film = searched_films[film_index]
        if film not in watch_later_list:
            watch_later_list.append(film)
            bot.send_message(call.message.chat.id, f"{film['nameRu']} добавлен в список 'Посмотреть позже'.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            backButton = types.InlineKeyboardButton("Назад", callback_data="search_results")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
            markup.add(backButton)
            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, f"{film['nameRu']} уже находится в списке 'Посмотреть позже'.")
    except (ValueError, IndexError):
        bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении фильма в список.")


# ДОБАВЛЕНИЕ В ПОСМОТРЕТЬ ПОЗЖЕ ДЛЯ УДИВИ МЕНЯ
def add_to_watch_later_random(call):
    film_id = int(call.data.split('_')[-1])
    film = next((film for film in films_data if film["filmId"] == film_id), None)
    if film:
        if film not in watch_later_list:
            watch_later_list.append(film)
            bot.send_message(call.message.chat.id, f"{film['nameRu']} добавлен в список 'Посмотреть позже'.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
        else:
            bot.send_message(call.message.chat.id, f"{film['nameRu']} уже находится в списке 'Посмотреть позже'.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
    else:
        bot.send_message(call.message.chat.id, "Произошла ошибка при добавлении фильма в список.")
        buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(buttonBack)

######


# ПОИСК ФИЛЬМОВ


# КНОПКА ПОИСК ФИЛЬМА, ВЫВОД НАЙДЕННЫХ ФИЛЬМОВ
def search_film_by_keyword(message):
    keyword = message.text
    response = requests.get(f"{search_api_url}?keyword={keyword}&page=1", headers=headers)
    if response.status_code == 200:
        data = response.json()
        global searched_films
        searched_films = data.get('films', [])
        if not searched_films:
            bot.send_message(message.chat.id, "Фильмы не найдены.")
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
            return

        search_results = ""
        for i, film in enumerate(searched_films, start=1):
            genres = ", ".join([genre['genre'] for genre in film.get('genres', [])])
            countries = ", ".join([country['country'] for country in film.get('countries', [])])
            search_results += f"{i}. {film['nameRu']}\nГод: {film.get('year', 'N/A')}\nЖанры: {genres}\nСтраны: {countries}\n\n"

        bot.send_message(message.chat.id, search_results)

        backButton = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
        selectButton = types.InlineKeyboardButton("Выбрать фильм", callback_data='select_search_number')
        markup = types.InlineKeyboardMarkup()
        markup.add(backButton, selectButton)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Не удалось выполнить поиск фильмов.")




### ВВОД ЦИФР

# ВВОД ЦИФРЫ ДЛЯ ПОДРОБНОЙ ИНФОРМАЦИИ ПОЛЬЗОВАТЕЛЕМ В ФИЛЬМОГРАФИИ
def process_filmography_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(filmography):
            film = filmography[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            buttonBackFilm = types.InlineKeyboardButton("Назад", callback_data="filmography")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
            markup.add(buttonBackFilm)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма.")
            display_filmography(message)
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный ввод. Пожалуйста, введите номер фильма.")
        display_filmography(message)

# ВВОД ЦИФРЫ ДЛЯ ПОДРОБНОЙ ИНФОРМАЦИИ ПОЛЬЗОВАТЕЛЕМ В ПОИСКЕ
def process_search_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(searched_films):
            film = searched_films[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)

            backButton = types.InlineKeyboardButton("Назад", callback_data='search_results')
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
            watchLaterButton = types.InlineKeyboardButton("Добавить в Посмотреть позже",
                                                          callback_data=f'add_searched_to_watch_later_{film_index}')
            filmographyButton = types.InlineKeyboardButton("Добавить в мою фильмографию",
                                                           callback_data=f'add_to_filmography_search_{film_index}')
            markup = types.InlineKeyboardMarkup()
            markup.add( watchLaterButton, filmographyButton)
            markup.add(backButton)
            markup.add(buttonBack)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма.")
            display_searched_films(message)
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBack)
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный ввод. Пожалуйста, введите номер фильма.")
        display_searched_films(message)
        buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
        markup = types.InlineKeyboardMarkup()
        markup.add(buttonBack)


### ВВОД ЦИФРЫ ДЛЯ ПОДРОБНОЙ ИНФОРМАЦИИ ПОЛЬЗОВАТЛЕМ ДЛЯ ПОСМОТРЕТЬ ПОЗЖЕ
def process_watch_later_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(watch_later_list):
            film = watch_later_list[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)
            buttonBackWatch = types.InlineKeyboardButton("Назад", callback_data='watch_later')
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBackWatch)
            markup.add(buttonBack)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма.")
            display_watch_later(message)
            buttonBackWatch = types.InlineKeyboardButton("Назад", callback_data='watch_later')
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
            markup = types.InlineKeyboardMarkup()
            markup.add(buttonBackWatch)
            markup.add(buttonBack)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный ввод. Пожалуйста, введите номер фильма.")
        display_watch_later(message)
        buttonBackWatch = types.InlineKeyboardButton("Назад", callback_data='watch_later')
        buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
        markup = types.InlineKeyboardMarkup()
        markup.add(buttonBackWatch)
        markup.add(buttonBack)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


# ВВОД ЦИФРЫ ДЛЯ ПОДРОБНОЙ ИНФОРМАЦИИ ПОЛЬЗОВАТЕЛЕМ ДЛЯ ТОП ЧАРТОМ
def process_film_number(message):
    try:
        film_index = int(message.text) - 1
        if 0 <= film_index < len(films_data):
            film = films_data[film_index]
            film_details = get_film_details(film, message.chat.id)
            bot.send_message(message.chat.id, film_details)

            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_film_list')
            watchLaterButton = types.InlineKeyboardButton("Добавить в Посмотреть позже",
                                                          callback_data=f'add_to_watch_later_{film_index}')
            filmographyButton = types.InlineKeyboardButton("Добавить в мою фильмографию",
                                                           callback_data=f'add_to_filmography_{film_index}')
            markup = types.InlineKeyboardMarkup()
            markup.add( watchLaterButton, filmographyButton)
            markup.add(backButton)
            markup.add(buttonBack)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Неправильный номер. Пожалуйста, выберите правильный номер фильма")
            display_top_films(message)
            buttonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
            backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_film_list')
            markup = types.InlineKeyboardMarkup()
            markup.add(backButton)
            markup.add(buttonBack)
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный ввод. Пожалуйста, введите номер фильма.")
        display_top_films(message)
        ButtonBack = types.InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
        backButton = types.InlineKeyboardButton("Назад", callback_data='back_to_film_list')
        markup = types.InlineKeyboardMarkup()
        markup.add(backButton)
        markup.add(ButtonBack)

# app.py
def main():
    user_first_name = "ff6"  # пример имени пользователя
    user_id = add_user_if_not_exists(user_first_name)
    films = get_films_for_user(user_id)
    print(f"Список фильмов для пользователя {user_id}: {films}")
    
    new_films = [1, 2, 3]
    update_films_for_user(user_id, new_films)
    films = get_films_for_user(user_id)
    print(f"Обновленный список фильмов для пользователя {user_id}: {films}")

if __name__ == "__main__":
    main()


# ЗАПУСК БОТА
bot.polling(none_stop=True)
