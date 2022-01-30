from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
from server.stat_window import StatWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.delete_user import DelUserDialog


class MainWindow(QMainWindow):

    """
    The class of the main window of the server interface.
    The class constructor accepts three positional arguments:
    a database object, a server class object,
    and an object with server configuration settings
    """

    def __init__(self, database, server, config):
        super().__init__()

        self.database = database

        self.server_thread = server
        self.config = config

        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        self.refresh_button = QAction('Обновить список', self)

        self.config_btn = QAction('Настройки сервера', self)

        self.register_btn = QAction('Регистрация пользователя', self)

        self.remove_btn = QAction('Удаление пользователя', self)

        self.show_history_button = QAction('История клиентов', self)

        self.statusBar()
        self.statusBar().showMessage('Server Working')

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

        self.setFixedSize(800, 600)
        self.setWindowTitle('Messaging Server alpha release')

        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 40)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 60)
        self.active_clients_table.setFixedSize(780, 400)

        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        self.show()

    def create_users_model(self):

        """
        A method that implements the formation and filling of a table
        of active users from the server database.
        """

        list_users = self.database.get_active_users()
        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(
            ['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
        for row in list_users:
            user, host, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            host = QStandardItem(host)
            host.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list_table.appendRow([user, host, port, time])
        self.active_clients_table.setModel(list_table)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):

        """A method that creates a customer statistics window."""

        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def server_config(self):

        """The method that creates the server configuration settings window."""

        global config_window
        config_window = ConfigWindow(self.config)

    def reg_user(self):

        """Method that creates a new user registration window."""

        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):

        """Method that creates a user deletion window."""

        global del_window
        del_window = DelUserDialog(self.database, self.server_thread)
        del_window.show()
