import logging
from sys import stdout


def setup_logger():
    logger = logging.getLogger("TgBot")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('{}'.format('Started'))
    return logger


log = setup_logger()
