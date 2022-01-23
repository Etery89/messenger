from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, qApp, QApplication


class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle("Hello")
        self.setFixedSize(220, 140)

        self.label = QLabel("Введите имя пользователя: ", self)
        self.label.move(10, 10)
        self.label.setFixedSize(200, 20)

        self.client_name_line = QLineEdit(self)
        self.client_name_line.move(10, 30)
        self.client_name_line.setFixedSize(200, 20)

        self.ok_button = QPushButton("Начать", self)
        self.ok_button.move(10, 105)
        self.ok_button.clicked.connect(self.click)

        self.exit_button = QPushButton("Выход", self)
        self.exit_button.move(129, 105)
        self.exit_button.clicked.connect(qApp.exit)

        self.label_passwd = QLabel('Введите пароль:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(200, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.show()

    def click(self):
        if self.client_name_line.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit(0)


if __name__ == "__main__":
    app = QApplication([])
    test_dialog = UserNameDialog()
    app.exec_()


