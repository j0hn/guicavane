'''helpers for logging, now you don't have excuse to use logging

https://github.com/marianoguerra/me/blob/master/code/python/mlog/mlog.py
'''

import inspect
import logging
import logging.handlers

SECOND   = SECONDS   = 'S'
MINUTE   = MINUTES   = 'M'
HOUR     = HOURS     = 'H'
DAY      = MIDNIGHT  = MIDNIGHTS = 'midnight'

DEFAULT_FORMAT = '[%(asctime)s] %(name)s %(levelname)s: %(message)s'

class ColouredFormatter(logging.Formatter):
    COLOR_MAP = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    LEVEL_MAP = {
        logging.DEBUG: (None, 'blue', True),
        logging.INFO: (None, 'green', True),
        logging.WARNING: (None, 'yellow', True),
        logging.ERROR: (None, 'red', True),
        logging.CRITICAL: ('red', 'white', True),
    }

    def colorize(self, lvl, string):
        csi = '\x1b['
        reset = '\x1b[0m'

        params = []
        bg, fg, bold = self.LEVEL_MAP[lvl]
        if bg in self.COLOR_MAP:
            params.append(str(self.COLOR_MAP[bg] + 40))
        if fg in self.COLOR_MAP:
            params.append(str(self.COLOR_MAP[fg] + 30))
        if bold:
            params.append('1')
        if params:
            string = ''.join((csi, ';'.join(params), 'm', string, reset))
        return string

    def format(self, record):
        record.levelname = self.colorize(record.levelno, record.levelname)
        return logging.Formatter.format(self, record)

def every(interval, when):
    return (interval, when)

def istty(handler):
    return getattr(handler.stream, 'isatty', lambda: False)()

def _get_logger(name, logger, handler, level, format):
    if logger is None:
        if name is None:
            name = get_caller_module(3)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

    if format is None:
        format = DEFAULT_FORMAT

    # Do not insert ansi colours in a non tty handler
    if istty(handler):
        formatter = ColouredFormatter(format)
    else:
        formatter = logging.Formatter(format)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def console(name=None, level=logging.INFO, logger=None, format=None):
    handler = logging.StreamHandler()
    return _get_logger(name, logger, handler, level, format)

def file(path, when=None, name=None, level=logging.DEBUG, logger=None,
        format=None):
    if when is None:
        handler = logging.FileHandler(path)
    else:
        interval, when_type = when
        handler = logging.handlers.TimedRotatingFileHandler(path, when_type, interval)

    return _get_logger(name, logger, handler, level, format)

def get_caller_module(level=2):
    '''
    return the name of the module that called the function that called this
    function, by default it assumes that the function that called this function
    was called from another module, to change this set level to the value
    of nested calls
    '''
    return inspect.getmoduleinfo(inspect.stack()[level][1]).name
