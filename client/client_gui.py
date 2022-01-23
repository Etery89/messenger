import sys
sys.path.append('../')
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSlot
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
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.current_chat = None
        self.history_model = None
        self.contacts_model = None

        self.messages = QMessageBox()

        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def send_message(self):
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
        contact_for_delete = item.selector.currentText()
        try:
            self.client_transport.remove_contact(contact_for_delete)
        except ServerError as err:
            self.messages.critical(self, 'Server error', err.message)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Loose connect to servet')
                self.close()
            self.messages.critical(self, 'Error', 'Timeout error')
        else:
            self.database.del_contact(contact_for_delete)
            self.clients_list_update()
            logger.info(f'Delete contact {contact_for_delete}')
            self.messages.information(self, 'Success', 'Contact is delete.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if contact_for_delete == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def set_disabled_input(self):
        self.ui.label_new_message.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()

        if self.history_model:
            self.history_model.clear()

        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        self.ui.label_new_message.setText(f'Введите сообщение для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        self.history_list_update()

    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)




