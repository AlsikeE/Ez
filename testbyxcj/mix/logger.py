
import sys
import time
import copy
import platform
import traceback

import logging


class ColoredConsoleHandler(logging.StreamHandler):
    def __init__(self, stream=sys.stderr):
        logging.StreamHandler.__init__(self, stream)

    def emit( self, record ):
        # Need to make a actual copy of the record 
        # to prevent altering the message for other loggers
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if( levelno >= 50 ): # CRITICAL / FATAL
            color = '\x1b[31m' # red
        elif( levelno >= 40 ): # ERROR
            color = '\x1b[31m' # red
        elif( levelno >= 30 ): # WARNING
#           color = '\x1b[35m' # pink
            color = '\x1b[33m' # yellow
        elif( levelno >= 20 ): # INFO
            color = '\x1b[0m' # normal
        elif( levelno >= 10 ): # DEBUG
            color = '\x1b[32m' # green
        else: # NOTSET and anything else
            color = '\x1b[0m' # normal
        myrecord.msg = color + str( myrecord.msg ) + '\x1b[0m'  # normal
        logging.StreamHandler.emit( self, myrecord )

def getLogger(name, level):
    global file_handler

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not (len(logger.handlers) > 0 and type(logger.handlers[0]) == logging.StreamHandler):
        if platform.system() != 'Windows':
            # all non-Windows platforms are supporting ANSI escapes so we use them
            con_handler = ColoredConsoleHandler(sys.stdout)
            con_formatter = logging.Formatter('\x1b[1;33m%(name)s:\x1b[0m %(message)s')
        else:
            con_handler = logging.StreamHandler(sys.stdout)
            con_formatter = logging.Formatter('%(name)s: %(message)s')

        con_handler.setFormatter(con_formatter)
        con_handler.setLevel(level)
        logger.addHandler(con_handler)
    if level == logging.DEBUG:
        try:
            import SimPy.Simulation as Simulation
            class SimPyAdapter(logging.LoggerAdapter):
                def __init__(self, log, extra):
                    logging.LoggerAdapter.__init__(self, log, extra)

                def process(self, msg, kwargs):
                    return '[%f] %s' % (Simulation.now(), msg), kwargs

            logger = SimPyAdapter(logger,{})
        except:
            pass
    return logger

def init(outfile="stdout", level=logging.INFO):
    root_logger = logging.getLogger()

    if outfile != "stdout" and outfile != "stderr":
        file_handler = logging.FileHandler(outfile, mode="w")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(name)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

