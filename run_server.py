import sys
import os
import logging
import argparse
import select
import socket
import threading
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from commons.decorators import LogFunctions
from server.server_main_window import MainWindow
from server.server_db import ServerWarehouse
from server.server_core import MessageProcessor
from commons.utils import get_message, send_message
from commons.commons import *

logger = logging.getLogger("server")


@LogFunctions()
def parse_args_for_tcp_server(default_host, default_port):

    """Parse arguments command prompt"""

    logger.debug(f"Parse arguments {sys.argv}")
    parser = argparse.ArgumentParser(description="Run tcp server")
    parser.add_argument("-i", default=default_host, type=str, help="Server ip-address")
    parser.add_argument("-p", default=default_port, type=int, help="Server port number")
    server_args_namespace = parser.parse_args(sys.argv[1:])
    return server_args_namespace.i, server_args_namespace.p


@LogFunctions()
def config_load():

    """Configuration file parser (config.ini)."""

    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


@LogFunctions()
def main():

    """Application launch function."""

    config = config_load()

    print(type(config['SETTINGS']['Default_host']))
    print(type(config['SETTINGS']['Default_port']))

    listen_address, listen_port = parse_args_for_tcp_server(config['SETTINGS']['Default_host'],
                                                            config['SETTINGS']['Default_port'])

    database = ServerWarehouse(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(database, server, config)
    server_app.exec_()
    server.running = False


if __name__ == "__main__":
    main()
