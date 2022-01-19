import logging
import sys
sys.path.append("../")
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt

logger = logging.getLogger("client")


class AddContactsDialog(QDialog):
    def __init__(self, database, client_transport):
        super().__init__()
        self.database = database
        self.client_transport = client_transport

        self.setWindowTitle("Добавить контакт: ")
        self.setFixedSize(340, 120)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(250, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 30)
        self.selector.move(10, 30)

        self.refresh_button = QPushButton('Обновить список', self)
        self.refresh_button.setFixedSize(150, 30)
        self.refresh_button.move(30, 70)

        self.ok_button = QPushButton('Добавить', self)
        self.ok_button.setFixedSize(100, 30)
        self.ok_button.move(230, 30)

        self.exit_button = QPushButton('Выход', self)
        self.exit_button.setFixedSize(100, 30)
        self.exit_button.move(230, 70)
        self.exit_button.clicked.connect(self.close)

        self.fill_contacts()
        self.refresh_button.clicked.connect(self.update_contacts)
        # self.show()

    def fill_contacts(self):
        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        users_list.remove(self.client_transport.username)
        self.selector.addItems(users_list - contacts_list)

    def update_contacts(self):
        try:
            self.client_transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug("Update success")
            self.fill_contacts()


if __name__ == "__main__":
    app = QApplication([])
    add_dialog = AddContactsDialog("database", "socket")
    app.exec_()
