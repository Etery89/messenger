import os
import logging
from logging.handlers import TimedRotatingFileHandler

format_log = logging.Formatter("%(asctime)-10s %(levelname)-5s %(filename)-10s %(message)s")

server_log = logging.getLogger("server")

path_for_log_list = os.path.dirname(os.path.abspath(__file__)).split("/")
path_for_log_list.remove(path_for_log_list[-1])
path_for_log_list.append("logs")
path_for_log_str = "/".join(path_for_log_list)
path_for_log = os.path.join(path_for_log_str, "server.log")

server_log_handler = TimedRotatingFileHandler(path_for_log, encoding="utf-8", interval=1, when="midnight")
server_log_handler.setFormatter(format_log)

server_log.addHandler(server_log_handler)
server_log.setLevel(logging.DEBUG)
