import sys
sys.path.append('../')
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from client_main_window import Ui_MainClientWindow
from errors import ServerError

logger = logging.getLogger("client")


class ClientMainWindow(QMainWindow):
    def __init__(self, database, client_transport):
        super().__init__()
        self.database = database
        self.client_transport = client_transport

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)
        self.ui.btn_send.clicked.connect(self.send_message)


        self.current_chat = None

        self.messages = QMessageBox()

    def send_massage(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.client_transport.send_message(self.current_chat, message_text)
        except ServerError as server_err:
            self.messages.critical(self, "Error", server_err.message)
        except OSError as os_err:
            if os_err.errno:
                self.messages.critical(self, "Error", "Loose connect from server")
                self.close()
            self.messages.critical(self, "Error", "Timeout error")
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, "Error", "Loose connect from server")
            self.close()
        else:
            self.database.save_message(self.current_chat, "out", message_text)
            logger.debug(f"Send message: {message_text}, for {self.current_chat}")
            self.history_list_update()

    def history_list_update(self):
        pass


