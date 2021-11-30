import sys
import json
import time
import argparse
import logging
import threading
from socket import *
import logs.configs.client_config
from errors import *
from decorators import log_function
from metaclasses import ClientVerifier
from utils import get_message, send_message
from commons import *

logger = logging.getLogger("client")


@log_function
def parse_args_for_tcp_client():
    parser = argparse.ArgumentParser(description="Run tcp client in connect to tcp server")
    parser.add_argument("--host", default=DEFAULT_HOST, type=str, help="Server host address")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help="Server port number")
    parser.add_argument("--name", type=str, help="Name client module")
    client_args_namespace = parser.parse_args()
    return client_args_namespace.host, client_args_namespace.port, client_args_namespace.name


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, username, sock_obj):
        self.client_name = username
        self.sock = sock_obj
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }

    def create_message(self):
        to = input('Input name destination user: ')
        message = input('Input message: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f"Create message dictionary: {message_dict}")
        try:
            send_message(self.sock, message_dict)
            logger.info(f"Send message to user {to}")
        except:
            logger.critical("Lost connection with server")
            exit(1)

    def run(self):
        self.get_help()
        while True:
            command = input("Please input command: ")
            if command == "message":
                self.create_message()
            elif command == "help":
                self.get_help()
            elif command == "exit":
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print("Goodbye!")
                logger.info("User exit program")
                time.sleep(0.5)
                break
            else:
                print("Your command not in messenger commands")

    def get_help(self):
        print("Commands")
        print("message - send message")
        print("help - show help")
        print("exit - exit messenger")


class ClientReader(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, username, sock_obj):
        self.client_name = username
        self.sock = sock_obj
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                    print(f"\n Get message from user {message[SENDER]}: \n{message[MESSAGE_TEXT]}")
                    logger.info(f"\n Get message from user {message[SENDER]}: \n{message[MESSAGE_TEXT]}")
                else:
                    logger.error(f"Get bad message from server: {message}")
            except IncorrectDataReceivedError:
                logger.error("Do not decode message from server")
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical("Lost connection with server")
                break


@log_function
def create_presence(client_name):
    presence_massage = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: client_name
        }
    }
    logger.debug(f"Create {PRESENCE} message for user {client_name}")
    return presence_massage


@log_function
def response_handler(message):
    logger.debug(f"Parse presence message from server: {message}")
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return "200 : OK"
        elif message[RESPONSE] == 400:
            raise ServerError(f"400 : {message[ERROR]}")
    raise ReqFieldMissingError(RESPONSE)


def main():
    print("Star messenger")
    server_host, server_port, username = parse_args_for_tcp_client()
    if not username:
        username = input('Please, input name client: ')
    print(f'Run client with name: {username}')
    logger.info(
        f'Run client with parameters: server host: {server_host} , server port: {server_port},'
        f' name user: {username}')
    try:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((server_host, server_port))
        send_message(client_sock, create_presence(username))
        server_answer = response_handler(get_message(client_sock))
        logger.info(f"Established connection with server. Server answer: {server_answer}")
        print("Connection established.")
    except json.JSONDecodeError:
        logger.error("Json decode error. Json string not decode")
        exit(1)
    except ServerError as err:
        logger.error(f"Server return error: {err.message}")
        exit(1)
    except ReqFieldMissingError as m_err:
        logger.error(f"Server answer not in JIM field: {m_err.missing_field}")
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(f"Failed to connect to the server (host: {server_host}, port: {server_port}")
        exit(1)
    else:
        # reader thread
        receiver = ClientReader(username, client_sock)
        receiver.daemon = True
        receiver.start()
        # sender thread
        sender = ClientSender(username, client_sock)
        sender.daemon = True
        sender.start()
        logger.debug("Start processes sender and receiver")

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == "__main__":
    main()



