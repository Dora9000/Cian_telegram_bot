from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from handler import *
from config import TOKEN


def setup_app():
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler('test_prediction', h_test_prediction))
    updater.dispatcher.add_handler(CommandHandler('search', h_search))
    updater.dispatcher.add_handler(CommandHandler('start', h_authorize))
    updater.dispatcher.add_handler(CommandHandler('commands', h_help))
    updater.dispatcher.add_handler(CommandHandler('safe', h_safe))
    updater.dispatcher.add_handler(CommandHandler('predict', h_predict))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', h_help))
    updater.dispatcher.add_handler(CommandHandler('show', h_show))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    dl_params()
    updater.dispatcher.add_handler(MessageHandler(Filters.document, h_predict_file))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), h_echo))
    updater.dispatcher.add_handler(MessageHandler(Filters.command, h_unknown))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    setup_app()
