import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging

from gpt import ask_gpt
from database import add_user, get_username, start_story, set_param, get_story_settings, get_story_history
from tokens import check_tokens_data, start_session
from tokens_const import MAX_GPT_TOKENS, MAX_SESSIONS, MAX_TOKENS_IN_SESSION
from config import BOT_TOKEN


bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='logs.txt', filemode='w')

genres = ['Комедия', 'Приключения', 'Фэнтези', 'Сказка', 'Детектив', 'Хоррор', 'Научная фантастика']
main_characters = ['Гарри Поттер', 'Фродо Бэггинс', 'Лея Органа', 'Чёрная вдова', 'Капитан Джек Воробей']
settings = ['Мегаполис', 'Деревня', 'Тёмный лес', 'Луна', 'Горная пещера', 'Остров в океане', 'Параллельная вселенная']


def create_markup(buttons: list[str]):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(buttons)):
        if i % 2 == 0:
            try:
                markup.row(KeyboardButton(buttons[i]), KeyboardButton(buttons[i + 1]))
            except IndexError:
                markup.row(KeyboardButton(buttons[i]))
    return markup


@bot.message_handler(commands=['start'])
def send_start_message(message):
    if add_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id, 'Привет! Ну что, готов приступить к твоей первой истории, написанной вместе '
                                          'с нейросетью? Тогда, ПОЕХАЛИ! Только сначала прочитай инструкцию '
                                          'по использованию бота - жми /help', reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'Извини, но на данный момент все свободные места для пользователей заняты :( '
                                          'Попробуй снова через некоторое время', reply_markup=ReplyKeyboardRemove())
        logging.warning('Достигнут лимит пользователей бота')


@bot.message_handler(commands=['help'])
def send_help_message(message):
    if add_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id, 'Итак, чтобы начать написание истории воспользуйся командой /newstory. После '
                                          'этого последовательно выбери жанр истории, главного героя, вокруг которого '
                                          'будет закручен сюжет, и место действий. Затем, если хочешь, напиши '
                                          'дополнительной информации: например, в какое время разворачиваются события, '
                                          'или на какие ещё детали стоит обратить внимание читателя, и смело жми '
                                          '/begin, и нейросеть начнёт писать начало твоей истории.\n\nКак только ты '
                                          'проделаешь эти действия, начнётся твоя сессия общения с нейросетью. Да, у '
                                          f'каждого пользователя есть {MAX_SESSIONS} сессий, а значит {MAX_SESSIONS} '
                                          'историй. И ещё одно ограничение - токены. В каждой сессии их '
                                          f'{MAX_TOKENS_IN_SESSION}. Не волнуйся, тебе не придётся ничего считать! Бот '
                                          'сам предупредит тебя, когда токены будут заканчиваться, чтобы ты мог '
                                          'завершить историю. А также ты можешь посмотреть свой баланс с помощью '
                                          '/tokens\n\nАх да, после каждого кусочка истории ты можешь либо попросить '
                                          'нейросеть продолжить рассказ (/continue), либо завершить (/end). А после '
                                          'сможешь получить весь получившийся текст командой /wholestory',
                         reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'Извини, но на данный момент все свободные места для пользователей заняты :( '
                                          'Попробуй снова через некоторое время', reply_markup=ReplyKeyboardRemove())
        logging.warning('Достигнут лимит пользователей бота')


@bot.message_handler(commands=['newstory'])
def start_new_story(message):
    if add_user(message.chat.id, message.from_user.username):
        start_story(message.chat.id)
        current_sessions = check_tokens_data(message.chat.id, 'sessions')
        if current_sessions < 1:
            bot.send_message(message.chat.id, 'К сожалению, у тебя закончились все сессии!',
                             reply_markup=ReplyKeyboardRemove())
            logging.warning(f'У пользователя {get_username(message.chat.id)} закончились сессии')
        else:
            if current_sessions < 2:
                bot.send_message(message.chat.id, 'Предупреждаем, у тебя осталась только одна сессия. Используй её '
                                                  'правильно!')
            bot.send_message(message.chat.id, 'Что ж, давай начнём настраивать твою новую историю. Для начал, выбери '
                                              'наиболее подходящий жанр', reply_markup=create_markup(genres))
    else:
        bot.send_message(message.chat.id, 'Извини, но на данный момент все свободные места для пользователей заняты :( '
                                          'Попробуй снова через некоторое время', reply_markup=ReplyKeyboardRemove())
        logging.warning('Достигнут лимит пользователей бота')


@bot.message_handler(commands=['begin'])
def start_writing_story(message):
    if check_tokens_data(message.chat.id, 'sessions') > 0:
        start_session(message.chat.id)
        logging.info(f'Пользователь {get_username(message.chat.id)} запросил начало истории')
        story_params = get_story_settings(message.chat.id)[0]
        bot.send_message(message.chat.id, f'Итак,\nжанр - {story_params[0]}\nглавный герой - {story_params[1]}\nместо '
                                          f'действия - {story_params[2]}\nдополнительная информация - {story_params[3]}'
                                          '\n\nПрекрасный выбор! Нейросеть уже начинает генерировать...')
        bot.send_message(message.chat.id, ask_gpt(message.chat.id, mode='start'),
                         reply_markup=create_markup(['/continue', '/end']))
    else:
        bot.send_message(message.chat.id, 'К сожалению, у тебя закончились все сессии!',
                         reply_markup=ReplyKeyboardRemove())


@bot.message_handler(commands=['continue'])
def continue_story(message):
    if check_tokens_data(message.chat.id, 'tokens') < MAX_GPT_TOKENS * 3:
        bot.send_message(message.chat.id, ask_gpt(message.chat.id, mode='continue'))
        bot.send_message(message.chat.id, 'В этой сессии осталось совсем немного токенов! Пора заканчивать историю',
                         reply_markup=create_markup(['/end']))
    else:
        bot.send_message(message.chat.id, ask_gpt(message.chat.id, mode='continue'),
                         reply_markup=create_markup(['/continue', '/end']))


@bot.message_handler(commands=['end'])
def finish_story(message):
    bot.send_message(message.chat.id, ask_gpt(message.chat.id, mode='end'),
                     reply_markup=create_markup(['/wholestory', '/tokens', '/newstory']))


@bot.message_handler(commands=['wholestory'])
def send_whole_story(message):
    story = get_story_history(message.chat.id)[0][0]
    try:
        if len(story) < 4096:
            bot.send_message(message.chat.id, story, reply_markup=create_markup(['/tokens', '/newstory']))
        else:
            for i in range(len(story) // 4096 + 1):
                bot.send_message(message.chat.id, story[4096*i:4096*(i+1)],
                                 reply_markup=create_markup(['/tokens', '/newstory']))
            logging.warning('Слишком длинная целая история')
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(message.chat.id, 'Произошла непредвиденная ситуация. Возможно, твоя история получилась '
                                          'слишком длинной для Telegram. Попробуй повторить попытку позже',
                         reply_markup=create_markup(['/tokens', '/newstory']))


@bot.message_handler(commands=['tokens'])
def send_tokens_info(message):
    if add_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id, f'У тебя осталось сессий: {check_tokens_data(message.chat.id, "sessions")}\n'
                                          'На последнюю историю ты потратил токенов: '
                                          f'{MAX_TOKENS_IN_SESSION - check_tokens_data(message.chat.id, "tokens")}',
                         reply_markup=create_markup(['/newstory']))
    else:
        bot.send_message(message.chat.id, 'Извини, но на данный момент все свободные места для пользователей заняты :( '
                                          'Попробуй снова через некоторое время', reply_markup=ReplyKeyboardRemove())
        logging.warning('Достигнут лимит пользователей бота')


@bot.message_handler(commands=['debug'])
def send_logs(message):
    with open('logs.txt', 'r') as f:
        bot.send_document(message.chat.id, f, reply_markup=ReplyKeyboardRemove())
    f.close()


def set_info(info):
    if info.text == '/begin':
        start_writing_story(info)
    elif info.text.startswith('/'):
        pass
    else:
        set_param('info', info.text, info.chat.id)
        bot.send_message(info.chat.id, 'Отлично! Можем начинать', reply_markup=create_markup(['/begin']))


@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.text in genres:
        set_param('genre', message.text, message.chat.id)
        bot.send_message(message.chat.id, 'Так-с, а теперь выбери главного героя',
                         reply_markup=create_markup(main_characters))
    elif message.text in main_characters:
        set_param('main_character', message.text, message.chat.id)
        bot.send_message(message.chat.id, 'А где будут разворачиваться события?', reply_markup=create_markup(settings))
    elif message.text in settings:
        set_param('setting', message.text, message.chat.id)
        msg = bot.send_message(message.chat.id,
                               'Теперь ты можешь добавить от себя уточнения. Если не хочешь, нажимай на кнопку',
                               reply_markup=create_markup(['/begin']))
        bot.register_next_step_handler(msg, set_info)
    else:
        bot.send_message(message.chat.id,
                         'Тебе следует воспользоваться командой или кнопкой, другого бот не понимает :(',
                         reply_markup=ReplyKeyboardRemove())


@bot.message_handler(content_types=['photo', 'audio', 'document', 'sticker', 'video', 'voice', 'location', 'contact'])
def error_message(message):
    bot.send_message(message.chat.id, 'Тебе следует воспользоваться командой или кнопкой, другого бот не понимает :(',
                     reply_markup=ReplyKeyboardRemove())


try:
    logging.info('Бот запущен')
    bot.polling()
except Exception as e:
    logging.critical(e)
