import sys
import os
import json
import time
import logging
import argparse
import select
import logs.configs.server_config
import socket
import threading
import configparser
from commons import *
from decorators import LogFunctions
from metaclasses import ServerVerifier
from descriptors import Port
from utils import get_message, send_message
from server_db import ServerWarehouse
from server_gui import MainWindow, HistoryWindow, ConfigWindow, create_users_model, create_history_model
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer

logger = logging.getLogger("server")

# lock for db
new_connection = False
conflag_lock = threading.Lock()


@LogFunctions()
def parse_args_for_tcp_server(default_host, default_port):
    parser = argparse.ArgumentParser(description="Run tcp server")
    parser.add_argument("--host", default=default_host, type=str, help="Server ip-address")
    parser.add_argument("--port", default=default_port, type=int, help="Server port number")
    parser.add_argument("-t", "--timeout", default=DEFAULT_TIMEOUT, type=float, help="Timeout for new \
    connection, type may be int or float")
    server_args_namespace = parser.parse_args()
    return server_args_namespace.host, server_args_namespace.port, server_args_namespace.timeout


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, host, port, timeout, database):

        self.addr = host
        self.port = port
        self.timeout = timeout

        self.clients = []
        self.messages = []
        self.names = dict()

        self.database = database

        super().__init__()

    def init_socket(self):
        logger.info(f"Start server with params: {self.addr}, {self.port}")
        print(f"Start server with params: {self.addr}, {self.port}")
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(self.timeout)

        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def run(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Established connection in PC: {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        logger.info(f'Client {client_with_message.getpeername()} disconnected.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                        self.clients.remove(client_with_message)
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Loose connection with client {message[DESTINATION]}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Send message to user {message[DESTINATION]} from user {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'User {message[DESTINATION]} not registered in server, can not send message.')

    def process_client_message(self, message, client):
        global new_connection
        logger.debug(f'Parse message from client : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_host, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_host, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Еhe username has already been taken.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            self.database.fix_user_message(message[SENDER], message[DESTINATION])
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            with conflag_lock:
                new_connection = True
            return

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        else:
            response = RESPONSE_400
            response[ERROR] = 'Incorrect response.'
            send_message(client, response)
            return


@LogFunctions()
def run_server():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    host, port, timeout = parse_args_for_tcp_server(config['SETTINGS']['default_host'], config['SETTINGS']['default_port'])

    database = ServerWarehouse(os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    my_server = Server(host, port, timeout, database)
    my_server.daemon = True
    my_server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.clients_table.setModel(create_users_model(database))
    main_window.clients_table.resizeColumnsToContents()
    main_window.clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.clients_table.setModel(
                create_users_model(database))
            main_window.clients_table.resizeColumnsToContents()
            main_window.clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_history_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # config server
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.ip.insert(config['SETTINGS']['default_host'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['default_host'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.history_button.triggered.connect(show_statistics)
    main_window.config_server_button.triggered.connect(server_config)

    # start app
    server_app.exec_()


if __name__ == "__main__":
    run_server()
