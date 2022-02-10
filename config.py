# bot token
TOKEN = ''

# path where all data is saving
DATA_PATH = 'C:\\Users\\super\\PycharmProjects\\bot\\data\\'
DATA_NAME = 'train.csv\\train.csv'
DATA_FILE = DATA_PATH + DATA_NAME

# prediction files
MODEL_FILE = 'train.csv\\1.pkl'
VAR_FILE = 'train.csv\\1.json'

# send this graph to user
GRAPH_NAME = 'graph\\1.jpeg'
GRAPH_FILE = DATA_PATH + GRAPH_NAME

# safe file from user to predict
SAFE_NAME = 'graph\\safe.csv'
SAFE_FILE = DATA_PATH + SAFE_NAME
SAFE_FILE_ = 'graph\\predicted.csv'

LOCAL = {'_user_id', '__state', '__filter_parameter', '__safe_parameter'}

PARAM_LIMIT = 14  # 'price_doc' will be included anyway
ROW_LIMIT = 1000
SHOW_LIMIT = 4
PREDICT_LIMIT = 100
HASH_KEY = '_safe'
PREDICTOR_EDGE_MIN = 0
PREDICTOR_EDGE_MAX = 1000000

STATES = {
    'safe': '__state_to_safe_params',
    'filter': '__state_to_filter_params',
    'graph': '__state_to_graph_params'
}

TARGET_COLUMN = 'price_doc'
ID_PROPERTY_NAME = '_user_id'
NA_SYMBOL = 'NA'

INFO_TEXT = 'This bot is telling the info about the apartments sale price.\n' \
            ' - to start using bot print /start\n' \
            ' - to get info about prices print /search. ' \
            'You can search prices for specific apartments. ' \
            'For example, you can filter only one-room apartments or define the floor.\n' \
            ' - to see the result of the search print /show. If there are too many apartments, ' \
            'we can predict the price for apartments or build the dependency graphs by using command /predict\n' \
            ' - you can save data in our database. To do this you need to save parameters one by one.\n' \
            ' - you can predict the price for the CSV file by sending it to us\n\n' \
            'Parameters for search we have:\n'
