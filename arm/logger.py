#!/usr/bin/env python3

import logging
import datetime as dt

LOGFILE = "{}-botrobi.log".format(dt.date.today())
FILE_LEVEL = logging.DEBUG
CONSOLE_LEVEL = logging.DEBUG

def mylogger(name, console_level = CONSOLE_LEVEL, file_level = FILE_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOGFILE)
    fh.setLevel(file_level)
    
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s::%(funcName)s:\t %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger
        
def main():
    logger = mylogger(__name__)
    logger.debug('test debug message')
    logger.info('test info message')
    logger.warn('test warn message')
    logger.error('test error message')
    logger.critical('test critical message')
    
if __name__=="__main__":
    main()
    