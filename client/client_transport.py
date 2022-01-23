import socket
import sys
sys.path.append("../")
import logging
import json
import threading
import time
import hashlib
import hmac
import binascii
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

    def __init__(self, host, port, database, client_name, password, keys):

        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.client_name = client_name
        self.transport = None
        self.host = host
        self.port = port
        self.password = password
        self.keys = keys

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

        bytes_password = self.password.encode("utf-8")
        bytes_salt = self.client_name.lower().encode("utf-8")
        password_hash = hashlib.pbkdf2_hmac("sha512", bytes_password, bytes_salt, 10000)
        password_hash_str = binascii.hexlify(password_hash)
        logger.debug(f'Create rassword hash: {password_hash_str}')

        pub_key = self.keys.publickey().export_key().decode('ascii')

        # Authorisation
        with socket_lock:
            presence = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pub_key
                }
            }
            logger.debug(f"Create presence message to authorisation: {presence}")
            try:
                send_message(self.transport, presence)
                answer = get_message(self.transport)
                logger.debug(f'Server response = {answer}.')
                if RESPONSE in answer:
                    if answer[RESPONSE] == 400:
                        raise ServerError(answer[ERROR])
                    elif answer[RESPONSE] == 511:
                        answer_data = answer[DATA]
                        hash_to_client_answer = hmac.new(password_hash_str, answer_data.encode('utf-8'), 'MD5')
                        digest_to_client_answer = hash_to_client_answer.digest()
                        client_answer = RESPONSE_511
                        client_answer[DATA] = binascii.b2a_base64(digest_to_client_answer).decode('ascii')
                        send_message(self.transport, client_answer)
                        self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                logger.debug(f'Connection error.', exc_info=err)
                raise ServerError('Loose connect from authorisation.')
        logger.info("Authorisation success. Established connection with server success")

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
