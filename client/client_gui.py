import sys
sys.path.append('../')
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import Qt
from client_main_window import Ui_MainClientWindow
from errors import ServerError
from add_contacts_dialog import AddContactsDialog
from delete_contact_dialog import DeleteContactsDialog

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

        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)

        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        self.current_chat = None
        self.history_model = None

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
        history_list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        len_history_list = len(history_list)
        start_index = 0
        if len_history_list > 15:
            start_index = len_history_list - 20
        for num_index in range(start_index, len_history_list):
            item = history_list[num_index]
            if item[1] == 'in':
                message = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                message.setEditable(False)
                message.setBackground(QBrush(QColor(255, 213, 213)))
                message.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(message)
            else:
                message = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                message.setEditable(False)
                message.setTextAlignment(Qt.AlignRight)
                message.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(message)
            self.ui.list_messages.scrollToBottom()

    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactsDialog(self.database, self.client_transport)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, contact):
        try:
            self.client_transport.add_contact(contact)
        except ServerError as server_err:
            self.messages.critical(self, "Server error", server_err.message)
        except OSError as os_err:
            if os_err.errno:
                self.messages.critical(self, "Error", "Loose connection from server.")
                self.close()
            self.messages.critical(self, "Error", "Timeout error")
        else:
            self.database.add_contact(contact)
            new_contact = QStandardItem(contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Added contact {contact}')
            self.messages.information(self, 'Success', 'Added contact.')

    def delete_contact_window(self):
        global delete_dialog
        delete_dialog = DeleteContactsDialog(self.database)
        delete_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(delete_dialog))
        delete_dialog.show()

    def delete_contact(self, item):
        pass






