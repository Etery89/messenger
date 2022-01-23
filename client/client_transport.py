import socket
import sys
sys.path.append("../")
import logging
import json
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal
from errors import ServerError
from utils import send_message, get_message
from commons import *


sys.path.append("../")

logger = logging.getLogger("client")
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, host, port, database, client_name):

        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.client_name = client_name
        self.transport = None
        self.host = host
        self.port = port

        self.connection_init()

        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as os_err:
            if os_err.errno:
                logger.critical("Loose connection with server.")
                raise ServerError("Loose connection with server!")
            logger.error("Timeout error by update users or contacts list")
        except json.JSONDecodeError:
            logger.critical("Loose connection with server.")
            raise ServerError("Loose connection with server!")

        self.running = True

    def connection_init(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False

        for attempt in range(5):
            logger.info(f"Try connect № {attempt + 1}")
            try:
                self.transport.connect((self.host, self.port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            logger.critical("Failed connection with server")
            raise ServerError("Failed connection with server")

        logger.debug("Established connection with server")

        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            logger.critical("Loose connection with server")
            raise ServerError("Loose connection with server")

        logger.info("Established connection with server success")

    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        logger.debug(f"Create {PRESENCE} message for client {self.client_name}")
        return out

    def process_server_ans(self, message):
        logger.debug(f'Handle message from server: {message}')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                logger.debug(f'Unknown code {message[RESPONSE]}')
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
            logger.debug(f'Получено сообщение от пользователя {message[SENDER]}:{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

    def user_list_update(self):
        logger.debug(f'Get list known users {self.username}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.database.add_users(answer[LIST_INFO])
        else:
            logger.error('Do not update users list.')

    def contacts_list_update(self):
        logger.debug(f'Get contact list for {self.client_name}')
        request = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        logger.debug(f'Create query {request}')
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        logger.debug(f'Получен ответ {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            logger.error('Do not update contacts list.')

    def add_contact(self, contact):
        logger.debug(f'Create contact {contact}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, request)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        logger.debug(f'Delete contact {contact}')
        request = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, request)
            self.process_server_ans(get_message(self.transport))

    def shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Exit client.')
        time.sleep(0.5)

    def send_message_to(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Create message dictionary: {message_dict}')

        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Send message to {to}')

    def run(self):
        logger.debug('Run process get message from server.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as os_err:
                    if os_err.errno:
                        logger.critical(f'Loose connection with server')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Loose connection with server')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.debug(f'Receive message from server: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
