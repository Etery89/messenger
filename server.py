import sys
import json
import time
import logging
import argparse
import select
import logs.configs.server_config
import socket
import threading
from commons import *
from decorators import LogFunctions
from metaclasses import ServerVerifier
from descriptors import Port
from utils import get_message, send_message
from server_db import ServerWarehouse

logger = logging.getLogger("server")


@LogFunctions()
def parse_args_for_tcp_server():
    parser = argparse.ArgumentParser(description="Run tcp server")
    parser.add_argument("--host", default=DEFAULT_HOST, type=str, help="Server ip-address")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help="Server port number")
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
                        self.clients.remove(client_with_message)
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Loose connection with client {message[DESTINATION]}')
                    self.clients.remove(self.names[message[DESTINATION]])
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
        logger.debug(f'Parse message from client : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_host, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_host, client_port)
                send_message(client, RESPONSE_200)
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
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Incorrect response.'
            send_message(client, response)
            return


def get_help():
    print("For stop server input 'exit', 'help' - for get list commands.")
    print("Query command:")
    print("users - get list all users are registered in server;")
    print("active - get list active users in server now;")
    print("history - get history connections in server.")


@LogFunctions()
def run_server():
    host, port, timeout = parse_args_for_tcp_server()
    database = ServerWarehouse()
    my_server = Server(host, port, timeout, database)
    my_server.daemon = True
    my_server.start()
    get_help()
    while True:
        command = input("Input command: ")
        if command == 'exit':
            break
        elif command == "users":
            users = database.get_users()
            print(users)
        elif command == "active":
            active_users = database.get_active_users()
            print(active_users)
        elif command == "history":
            users_history = database.get_history()
            print(users_history)
        elif command == "help":
            get_help()
        else:
            print("This command not in list commands. For get help input - 'help'.")


if __name__ == "__main__":
    run_server()
