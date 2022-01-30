from PyQt5.QtWidgets import QDialog, QPushButton, QTableView, QApplication
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class StatWindow(QDialog):

    """Class of the interface window displaying client statistics.
    The class constructor takes a server database object as a positional argument.
    """

    def __init__(self, database):
        super().__init__()

        self.database = database

        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.stat_table = QTableView(self)
        self.stat_table.move(10, 10)
        self.stat_table.setFixedSize(580, 620)

        self.create_stat_model()

    def create_stat_model(self):

        """A method that generates and fills a statistics table with data from the database"""

        stat_list = self.database.get_message_history()

        table_list = QStandardItemModel()
        table_list.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
        for row in stat_list:
            user, last_seen, sent, received = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            received = QStandardItem(str(received))
            received.setEditable(False)
            table_list.appendRow([user, last_seen, sent, received])
        self.stat_table.setModel(table_list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()


if __name__ == "__main__":
    app = QApplication([])
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    dial = StatWindow(None)
    app.exec_()
