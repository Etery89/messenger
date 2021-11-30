import sys
import logging
import inspect
from logs.configs import client_config, server_config

if sys.argv[0].find("client") == -1:
    LOGGER = logging.getLogger("server")
else:
    LOGGER = logging.getLogger("client")


def log_function(function_to_log):
    def log_wrapper(*args, **kwargs):
        result = function_to_log(*args, **kwargs)
        LOGGER.debug(f"Была вызвана функция {function_to_log.__name__} с параметрами: {args}, {kwargs}."
                     f"Вызов был произведён из модуля: {function_to_log.__module__} ."
                     f"Функция вызвана в: {inspect.stack()[1][3]}", stacklevel=2)
        return result
    return log_wrapper


class LogFunctions:

    def __call__(self, function_to_log):
        def log_wrapper(*args, **kwargs):
            result = function_to_log(*args, **kwargs)
            LOGGER.debug(f"Была вызвана функция {function_to_log.__name__} с параметрами: {args}, {kwargs}."
                         f"Вызов был произведён из модуля: {function_to_log.__module__} ."
                         f"Функция вызвана в: {inspect.stack()[1][3]}", stacklevel=2)
            return result
        return log_wrapper

