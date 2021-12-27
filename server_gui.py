import sys
import os
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QApplication, QLabel, QTableView, QDialog, QLineEdit, \
    QFileDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_user_interface()

    def init_user_interface(self):
        self.setWindowTitle("Messenger. Server App")

        self.exit_button = QAction("Выход (Ctrl+Q)", self)
        self.exit_button.setShortcut("Ctrl+Q")
        self.exit_button.triggered.connect(self.close)

        self.refresh_button = QAction("Обновить список клиентов (Ctrl+F)", self)
        self.refresh_button.setShortcut("Ctrl+F")

        self.history_button = QAction("История клиентов (Ctrl+H)", self)
        self.history_button.setShortcut("Ctrl+H")

        self.config_server_button = QAction("Настройки сервера (Ctrl+S)")
        self.config_server_button.setShortcut("Ctrl+S")

        self.tool_bar = self.addToolBar("MainBar")
        self.tool_bar.addAction(self.exit_button)
        self.tool_bar.addAction(self.config_server_button)
        self.tool_bar.addAction(self.refresh_button)
        self.tool_bar.addAction(self.history_button)

        self.statusBar()

        self.clients_table_title = QLabel("Список подключённых клиентов", self)
        self.clients_table_title.setFixedSize(300, 15)
        self.clients_table_title.move(20, 45)

        self.clients_table = QTableView(self)
        self.clients_table.setFixedSize(810, 500)
        self.clients_table.move(20, 65)

        self.setFixedSize(850, 650)
        self.show()


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_window()

    def init_window(self):
        self.setWindowTitle("История подключений")
        self.setFixedSize(600, 700)

        self.close_button = QPushButton("Закрыть", self)
        self.close_button.setFixedSize(300, 30)
        self.close_button.move(155, 650)
        self.close_button.clicked.connect(self.close)

        self.history_table = QTableView(self)
        self.history_table.setFixedSize(560, 610)
        self.history_table.move(20, 20)

        self.show()


class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(395, 270)
        self.setWindowTitle('Настройки сервера')

        self.db_path_label = QLabel('Выбрать файл базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(285, 28)

        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        self.db_file_label = QLabel('Название файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(220, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(230, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(220, 15)

        self.port = QLineEdit(self)
        self.port.move(230, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('IP для приёма соединения:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(220, 15)

        self.ip_label_note = QLabel('(оставьте это поле пустым, чтобы\nпринимать соединения с любых адресов)', self)
        self.ip_label_note.move(10, 175)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(230, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Сохранить' , self)
        self.save_btn.move(80, 225)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(225, 225)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == "__main__":
    my_app = QApplication(sys.argv)
    # win = MainWindow()
    # his = HistoryWindow()
    config = ConfigWindow()
    my_app.exec_()



