from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from config import PREDICT_LIMIT, SAFE_FILE, STATES, ID_PROPERTY_NAME, INFO_TEXT
from data_level import *
from logger import log


def state(s, context):
    context.user_data['__state'] = STATES.get(s)


def is_authorized(context) -> bool:
    if context.user_data.get(ID_PROPERTY_NAME) is not None:
        return True
    return False


def recognize(context: CallbackContext) -> int:
    if context.user_data.get(ID_PROPERTY_NAME) is None:
        return -1
    return context.user_data.get(ID_PROPERTY_NAME)


def ask_parameter(update, context, params=None):
    if params is None:
        params = dl_params(context)
    k = [[InlineKeyboardButton(param, callback_data=param)] for param in params]
    reply_markup = InlineKeyboardMarkup(k)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Choose the parameter:', reply_markup=reply_markup)


def h_authorize(update: Update, context: CallbackContext) -> None:
    log.info(f'H_authorize - {update.effective_user.first_name}')
    _id = dl_safe_user(recognize(context), context)
    context.user_data[ID_PROPERTY_NAME] = _id
    update.message.reply_text(f'lets talk!')


def h_safe(update: Update, context: CallbackContext) -> None:
    """
    main function to safe new data
    """
    log.info('H_safe')
    if not is_authorized(context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to start")
        return
    params_to_ask = []
    text = ''
    for param in dl_params(context):
        if context.user_data.get(param + HASH_KEY) is None and \
                context.user_data.get(param + HASH_KEY) not in LOCAL:
            params_to_ask.append(param)
        if context.user_data.get(param + HASH_KEY) is not None and \
                context.user_data.get(param + HASH_KEY) not in LOCAL:
            text += f'{param} : {context.user_data.get(param + HASH_KEY)} \n'
    if len(params_to_ask) == 0:
        dl_safe_data(context)
        dl_clear_user(context, safe_mode=True)
        state(None, context)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Saved!')
    else:
        text = f'Params you entered:\n {text}\nYou can rewrite the previous param before choosing the next one'\
            if len(text) > 0 else 'You need to enter all parameters one by one'
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        state('safe', context)
        ask_parameter(update, context, params_to_ask)


def h_search(update: Update, context: CallbackContext) -> None:
    """
    main function to search data
    """
    log.info('H_search')
    state(None, context)
    if not is_authorized(context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to start")
        return
    statistic_values = dl_get_room_properties(context)
    if statistic_values['count'] == 0:
        dl_clear_user(context, filter_mode=True)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, no rooms found. '
                                                                        'Create new filter to search.')
        return
    text = f"We have {statistic_values['count']} rooms with range\n{statistic_values['min']} $ - " \
           f"{statistic_values['max']}$\naverage is {statistic_values['avg']}$ \n"
    params_to_ask = []
    for param in dl_params(context):
        if context.user_data.get(param) is not None:
            text += f'{param} : {context.user_data.get(param)} \n'
        else:
            params_to_ask.append(param)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    keyboard = []
    if statistic_values['count'] <= SHOW_LIMIT:
        keyboard.append([InlineKeyboardButton("See result", callback_data='show')])
    if len(params_to_ask) > 0 and statistic_values['count'] > 1:
        keyboard.append([InlineKeyboardButton("Add filter", callback_data='search')])
    if len(keyboard) == 0:  # return the cut result list
        keyboard.append([InlineKeyboardButton("See result", callback_data='show')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def h_show(update: Update, context: CallbackContext) -> None:
    log.info('H_show')
    if not is_authorized(context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to start")
        return
    count = dl_get_room_properties(context)['count']
    if count <= 0:
        dl_clear_user(context, filter_mode=True)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, no rooms found. '
                                                                        'Create new filter to search.')
        return
    if count <= SHOW_LIMIT:
        state(None, context)
        text = dl_get_room(context)
        dl_clear_user(context, filter_mode=True)
    elif count <= PREDICT_LIMIT:
        text = f'We have too many ({count}) apartments to show. If you want to predict the price, type /predict.'
    else:
        text = f'We have {count} apartments to show. Enter some more filters to find the best apartment!'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def h_predict(update: Update, context: CallbackContext) -> None:
    log.info('H_predict')
    if not is_authorized(context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to start")
        return
    count = dl_get_room_properties(context)['count']
    if count <= 1:
        h_show(update, context)
        return

    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Form the graph", callback_data='graph'),
            InlineKeyboardButton("Predict price", callback_data='predict'),
        ]
    ])
    update.message.reply_text(
        text="Do you want to predict the price or to build the graph?", reply_markup=reply_markup)


def h_predict_file(update: Update, context: CallbackContext) -> None:
    log.info('H_predict_file')
    file_id = update.message.effective_attachment.file_id
    f = context.bot.get_file(file_id)
    f.download(SAFE_FILE)
    log.info('downloaded')
    context.bot.send_message(chat_id=update.effective_chat.id, text='File saved. Starting prediction')
    file = predictor.predict_xs(0, 1e9, SAFE_FILE)
    with open(file, 'rb') as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=f)


def h_help(update: Update, context: CallbackContext) -> None:
    log.info('H_help')
    text = INFO_TEXT
    for param in dl_params(context):
        if param[-len(HASH_KEY):] != HASH_KEY:
            text += f' - {param}\n'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def h_echo(update, context):
    if is_authorized(context):
        return h_unknown(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to start")


def h_unknown(update, context):
    log.info('H_unknown')
    try:
        text = update.message.text.split()
    except Exception as e:
        text = []

    if len(text) > 1:
        context.bot.send_message(chat_id=update.effective_chat.id, text="I do not understand")
        return

    if context.user_data.get('__state') == STATES.get('safe'):
        if context.user_data.get('__safe_parameter') is None:
            return
        context.user_data[context.user_data['__safe_parameter']] = text[0]
        state(None, context)
        return h_safe(update, context)
    elif context.user_data.get('__state') == STATES.get('filter'):
        if context.user_data.get('__filter_parameter') is None:
            return
        context.user_data[context.user_data['__filter_parameter']] = text[0]
        state(None, context)
        return h_search(update, context)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="I do not understand \nTo see command "
                                                                        "instructions type /commands")


def button(update, context):
    query = update.callback_query
    variant = query.data
    query.answer()
    query.edit_message_text(text=f"Your answer: {variant}")
    if variant == 'graph':  # Form the graph
        state('graph', context)
        ask_parameter(update, context)

    elif variant[:len('predict')] == 'predict':  # Predict price
        if variant == 'predict':
            k = [
                [InlineKeyboardButton('predict value for your filter', callback_data='predict value')],
                [InlineKeyboardButton('upload the file', callback_data='predict file')]
                 ]
            reply_markup = InlineKeyboardMarkup(k)
            context.bot.send_message(chat_id=update.effective_chat.id, text='What do you want to do:',
                                     reply_markup=reply_markup)
        elif variant == 'predict value':
            text = dl_predict(context)
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        elif variant == 'predict file':
            context.bot.send_message(chat_id=update.effective_chat.id, text='Send the file please')
        else:
            log.error('Unknown case: ', variant)

    elif variant == 'show':
        h_show(update, context)

    elif variant == 'search':
        params_to_ask = []
        for param in dl_params(context):
            if context.user_data.get(param) is None:
                params_to_ask.append(param)
        state('filter', context)
        ask_parameter(update, context, params_to_ask)

    else:
        if context.user_data.get('__state') == STATES.get('safe'):
            context.user_data['__safe_parameter'] = variant + HASH_KEY
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Type the value of {variant}')

        elif context.user_data.get('__state') == STATES.get('filter'):
            context.user_data['__filter_parameter'] = variant
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Type the value of {variant}')

        elif context.user_data.get('__state') == STATES.get('graph'):
            try:
                filepath = dl_graph(context, variant)
                with open(filepath, 'rb') as photo:
                    context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
            except Exception as e:
                log.error(e)
                context.bot.send_message(chat_id=update.effective_chat.id, text='Try one more time')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Here is the graph for value {variant}')

        else:
            log.error(f"State: {context.user_data.get('__state')}")


def h_test_prediction(update, context):
    log.info('H_test_prediction')
    try:
        text = update.message.text.split()[1:]
        text = [int(text[0]), int(text[1])]
        if len(text) != 2:
            raise Exception('Error - Need 2 variables!')
    except Exception as e:
        print(e)
        text = [1, 10]

    log.info(f'Edges: {min(text)}, {max(text)}')
    score = predictor.predict_xs(min(text), max(text), test=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Tested with score {round(score, 5)}')
