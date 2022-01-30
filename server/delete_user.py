from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt


class DelUserDialog(QDialog):

    """
    A dialog box class that allows you to select a user
    and delete it from the database.
    The class constructor takes positional arguments
    of the server database objects and the server itself.
    """

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setFixedSize(350, 120)
        self.setWindowTitle('Удаление пользователя')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel(
            'Выберите пользователя для удаления:', self)
        self.selector_label.setFixedSize(300, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 30)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 30)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 80)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):

        """A method that selects users and databases and fills in the selection list in the window"""

        self.selector.addItems([item[0]
                                for item in self.database.users_list()])

    def remove_user(self):

        """The method that removes the user from the database"""

        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)

        # A function that sends information to clients about updating the list of registered users
        self.server.service_update_lists()
        self.close()

