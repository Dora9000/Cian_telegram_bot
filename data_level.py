import csv
from pandas import read_csv
import numpy as np
import matplotlib.pyplot as plt
from pandas import to_numeric
from prediction import predictor
from config import DATA_FILE, LOCAL, PARAM_LIMIT, ROW_LIMIT, HASH_KEY, \
    SHOW_LIMIT, GRAPH_FILE, TARGET_COLUMN, NA_SYMBOL


def dl_form_message(data) -> str:
    text = f'There are {len(data)} apartments:\n'
    for i, row in data.iterrows():
        text += f'\nRoom number {i + 1}:\n'
        for col in data.columns:
            if row.get(col) != row.get(col):
                continue
            else:
                text += f' - {col} : {row[col]}\n'
    return text


def dl_safe_user(id, context) -> int:
    if id == -1:
        if context.bot_data.get('max_id') is None:
            context.bot_data['_max_id'] = 1
        else:
            context.bot_data['_max_id'] += 1
    return context.bot_data['_max_id']


def dl_clear_user(context, filter_mode=False, safe_mode=False):
    local_params = LOCAL
    params_to_safe = {}
    for param in local_params:
        params_to_safe[param] = context.user_data.get(param)
    if filter_mode:  # safe 'saving params'
        for param in dl_params(context):
            if context.user_data.get(param + HASH_KEY):
                params_to_safe[param + HASH_KEY] = context.user_data.get(param + HASH_KEY)
    if safe_mode:  # safe 'filter params'
        for param in dl_params(context):
            if context.user_data.get(param) and param[-len(HASH_KEY):] != HASH_KEY:
                params_to_safe[param] = context.user_data.get(param)
    context.user_data.clear()
    for name, val in params_to_safe.items():
        context.user_data[name] = val


def dl_params(context=None):
    if context and context.bot_data.get('PARAMS'):
        return context.bot_data.get('PARAMS')

    with open(DATA_FILE, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        data = next(reader)
        if not isinstance(data, list):
            data = []
        else:
            data = data[:min(len(data), PARAM_LIMIT)]
            if TARGET_COLUMN not in data:
                data.append(TARGET_COLUMN)
    if context is not None:
        context.bot_data['PARAMS'] = data
    return data


def dl_get_room(context):
    data = read_csv(DATA_FILE, nrows=ROW_LIMIT, dtype=str)
    filter_l = []
    for param in dl_params(context):
        if param in LOCAL: continue
        if param[-len(HASH_KEY):] == HASH_KEY: continue
        if context.user_data.get(param) is not None:
            filter_l.append(param)
            data = data.loc[data[param] == context.user_data.get(param)]
    for col in filter_l:
        data = data.drop(columns=col)
    for col in data.columns:
        if col not in dl_params(context):
            data = data.drop(columns=col)
    print(f'Show with filters: {filter_l}. Rows number : {len(data)}')
    data = data[:min(len(data), SHOW_LIMIT)]
    return dl_form_message(data)


def dl_get_room_properties(context):
    data = read_csv(DATA_FILE, nrows=ROW_LIMIT, dtype=str)
    for param in dl_params(context):
        if param in LOCAL: continue
        if param[-len(HASH_KEY):] == HASH_KEY: continue
        if context.user_data.get(param) is not None:
            data = data.loc[data[param] == context.user_data.get(param)]
    number = len(data)
    data = data[TARGET_COLUMN].apply(float)
    if number == 0:
        return 0, -1, -1, -1
    min_val, max_val, avg_val = min(data), max(data), sum(data) / number
    return number, min_val, max_val, avg_val


def dl_safe_data(context):
    data = read_csv(DATA_FILE, nrows=ROW_LIMIT, dtype=str)
    new_row = {}
    for p in data.columns:
        new_row[p] = context.user_data.get(p + HASH_KEY) \
            if context.user_data.get(p + HASH_KEY) is not None \
            else NA_SYMBOL
    print('New row saved: ', new_row)
    data = data.append(new_row, ignore_index=True)
    data.to_csv(DATA_FILE, index=False, na_rep=NA_SYMBOL)


def dl_predict(context) -> str:
    x = predictor.predict_x(context.user_data)
    return f'Predicted value = {round(x, 2)}$'


def dl_graph(context, p) -> str:
    data = read_csv(DATA_FILE, nrows=ROW_LIMIT, dtype=str)
    if context.user_data.get(p) is None:
        # fix all known params and get prices to make graph
        for param in dl_params(context):
            if param in LOCAL: continue
            if param[-len(HASH_KEY):] == HASH_KEY: continue
            if context.user_data.get(param) is not None:
                data = data.loc[data[param] == context.user_data.get(param)]

    # make graph
    y = data[TARGET_COLUMN].apply(lambda x: int(x))
    x = data[p]
    try:
        x = to_numeric(x)
        x = x.replace(np.nan, 0)
    except Exception as e:
        x = x.replace(np.nan, '')

    try:
        x, y = zip(*sorted(zip(x, y)))
    except Exception as e:
        pass

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6, 4))
    ax.set_xlabel(p)
    ax.set_ylabel('price')
    ax.plot(x, y)

    try:
        plt.yticks(range(min(y), max(y), (max(y) - min(y)) // 20), size=7)
        plt.xticks(range(min(x), max(x), (max(x) - min(x)) // 10), size=7)
    except Exception:
        try:
            N = len(plt.xticks()[0])
            ax.set_xticks(np.arange(0, N, N // 10))
            plt.xticks(size=7)
            fig.autofmt_xdate(rotation=45)
        except Exception:
            pass

    ax.set_title(f'Price dependence of {p}')
    fig.savefig(GRAPH_FILE)
    plt.close(fig)
    return GRAPH_FILE
