import os
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt


class ConfigWindow(QDialog):

    """
    The class of the server configuration settings window.
    The class constructor takes as a positional argument
    the configuration object of the basic server settings
    (parse from .ini file).
    """

    def __init__(self, config):
        super().__init__()
        self.config = config

        self.setFixedSize(390, 260)
        self.setWindowTitle('Настройки сервера')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(260, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(280, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(298, 28)

        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(230, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(220, 15)

        self.port = QLineEdit(self)
        self.port.move(230, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('IP для приёма соединений:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(230, 15)

        self.ip_label_note = QLabel(
            '(оставьте это поле пустым, чтобы\n принимать соединения с любых адресов).',
            self)
        self.ip_label_note.move(10, 170)
        self.ip_label_note.setFixedSize(500, 35)

        self.ip = QLineEdit(self)
        self.ip.move(230, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(180, 220)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.db_path_select.clicked.connect(self.open_file_dialog)

        self.show()

        self.db_path.insert(self.config['SETTINGS']['Database_path'])
        self.db_file.insert(self.config['SETTINGS']['Database_file'])
        self.port.insert(self.config['SETTINGS']['Default_port'])
        self.ip.insert(self.config['SETTINGS']['Listen_Address'])
        self.save_btn.clicked.connect(self.save_server_config)

    def open_file_dialog(self):

        """Method of processing the user opening a directory to select a database file."""

        global dialog
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_config(self):

        """
        The method of saving settings in .ini file.
        Enables validation of user-entered values.
        """
        
        global config_window
        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '..')
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    self.config.write(conf)
                    message.information(
                        self, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    self, 'Ошибка', 'Порт должен быть от 1024 до 65536')


