import os
import logging

format_log = logging.Formatter("%(asctime)-10s %(levelname)-5s %(module)-10s %(message)s")

client_log = logging.getLogger("client")

path_for_log_list = os.path.dirname(os.path.abspath(__file__)).split("/")
path_for_log_list.remove(path_for_log_list[-1])
path_for_log_list.append("logs")
path_for_log_str = "/".join(path_for_log_list)
path_for_log = os.path.join(path_for_log_str, "client.log")

client_log_handler = logging.FileHandler(path_for_log, encoding="utf-8")
client_log_handler.setFormatter(format_log)

client_log.addHandler(client_log_handler)
client_log.setLevel(logging.DEBUG)
