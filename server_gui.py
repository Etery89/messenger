import sys
import os
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QApplication, QLabel, QTableView, QDialog


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


if __name__ == "__main__":
    my_app = QApplication(sys.argv)
    win = MainWindow()
    # his = HistoryWindow()
    my_app.exec_()



