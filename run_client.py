import sys
import argparse
import logging
from PyQt5.QtWidgets import QApplication
import logs.configs.client_config
from errors import *
from decorators import log_function
from metaclasses import ClientVerifier
from client.client_db import ClientWarehouse
from client.client_transport import ClientTransport
from client.client_gui import ClientMainWindow
from client.start_dialog import UserNameDialog
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


def main():
    server_host, server_port, client_name = parse_args_for_tcp_client()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name_line.text()
            del start_dialog
        else:
            sys.exit(0)

    logger.info(f"Running client module - {client_name} with server's parameters: host {server_host}, port {server_port}")
    database = ClientWarehouse(client_name)

    try:
        client_transport = ClientTransport(server_host, server_port, database, client_name)
    except ServerError as serv_err:
        print(serv_err.message)
        sys.exit(1)
    client_transport.setDaemon(True)
    client_transport.start()

    main_window = ClientMainWindow(database, client_transport)
    main_window.make_connection(client_transport)
    main_window.setWindowTitle(f"Мессенджер. Клиентский модуль - {client_name}")
    client_app.exec_()
    client_transport.transport_shutdown()
    client_transport.join()


if __name__ == "__main__":
    main()



