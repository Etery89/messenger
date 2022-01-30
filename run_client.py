import sys
import os
import argparse
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from commons.decorators import log_function
from client.client_db import ClientWarehouse
from client.client_transport import ClientTransport
from client.client_gui import ClientMainWindow
from client.start_dialog import UserNameDialog
from commons.commons import *
from commons.errors import ServerError
from Crypto.PublicKey import RSA

logger = logging.getLogger("client")


@log_function
def parse_args_for_tcp_client():
    parser = argparse.ArgumentParser(description="Run tcp client in connect to tcp server")
    parser.add_argument("--host", default=DEFAULT_HOST, type=str, help="Server host address")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help="Server port number")
    parser.add_argument("--name", type=str, help="Name client module")
    parser.add_argument("--password", type=str, help="Client's password")
    client_args_namespace = parser.parse_args()
    return client_args_namespace.host, client_args_namespace.port,\
           client_args_namespace.name, client_args_namespace.password


def main():
    server_host, server_port, client_name, client_password = parse_args_for_tcp_client()
    client_app = QApplication(sys.argv)
    start_dialog = UserNameDialog()
    if not client_name or not client_password:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name_line.text()
            client_password = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_password}.')
        else:
            sys.exit(0)

    logger.info(f"Running client module: {client_name} with server's parameters: host {server_host}, port {server_port}")

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb', encoding='utf-8') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb', encoding='utf-8') as key:
            keys = RSA.import_key(key.read())
    logger.debug("Keys successfully loaded.")

    database = ClientWarehouse(client_name)

    try:
        client_transport = ClientTransport(server_host, server_port, database, client_name, client_password, keys)
        logger.debug("Client ready")
    except ServerError as serv_err:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', serv_err.message)
        sys.exit(1)
    client_transport.setDaemon(True)
    client_transport.start()

    del start_dialog

    main_window = ClientMainWindow(database, client_transport)
    main_window.make_connection(client_transport)
    main_window.setWindowTitle(f"Мессенджер. Клиентский модуль - {client_name}")
    client_app.exec_()

    client_transport.transport_shutdown()
    client_transport.join()


if __name__ == "__main__":
    main()



