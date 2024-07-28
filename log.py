import logging

# http://patorjk.com/software/taag/#p=display&h=0&v=1&f=Big%20Money-ne&t=CsCN
banner = r"""
  /$$$$$$            /$$$$$$  /$$   /$$
 /$$__  $$          /$$__  $$| $$$ | $$
| $$  \__/ /$$$$$$$| $$  \__/| $$$$| $$
| $$      /$$_____/| $$      | $$ $$ $$
| $$     |  $$$$$$ | $$      | $$  $$$$
| $$    $$\____  $$| $$    $$| $$\  $$$
|  $$$$$$//$$$$$$$/|  $$$$$$/| $$ \  $$
 \______/|_______/  \______/ |__/  \__/

"""


def initLogger(logPath=None, loggerName=__name__, encoding='utf-8') -> logging.Logger:
    """
    获取一个logging对象, 会同时在命令行和文件输出log
    :param logPath: 指定的log文件路径, 不会创建途径目录
    :param loggerName: logger名字, 默认是本模块的名字
    :return: logging.Logger
    """
    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if logPath is not None:
        # add FileHandler to log to file
        fileHandler = logging.FileHandler(logPath, encoding=encoding)
        fileHandler.setLevel(logging.INFO)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    # add StreamHandler to log to console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    return logger


def getNullLogger(loggerName=__name__) -> logging.Logger:
    """
    获取一个啥也不干的logger, 用来忽悠cbjSqlFunc.MysqlConnector
    :param loggerName: logger名字, 默认是本模块的名字, 最好不要和别的logger重复, 不然可能会莫名其妙被改了
    :return: 一个啥也不干的logger
    """
    logger = logging.getLogger(loggerName)
    logger.addHandler(logging.NullHandler())
    return logger
