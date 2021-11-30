

class PortValueError(Exception):
    def __init__(self):
        self.message = "The port can only be specified by numbers in the range from 1024 to 65355"

    def __str__(self):
        return f"PortValueError: {self.message}"


class KeyJIMProtocolError(Exception):
    def __init__(self):
        self.message = "JIM protocol error: in dict not key include JIM protocol"

    def __str__(self):
        return f"{self.message}"


class NonDictInputError(Exception):
    def __init__(self):
        self.messsage = "Functions args must be dict"

    def __str__(self):
        return f"NonDictInputError: {self.messsage}"


class ServerError(Exception):
    def __init__(self, message):
        self.message = f"ServerError: Server return error: {message}"

    def __str__(self):
        return f"{self.message}"


class IncorrectDataReceivedError(Exception):
    def __init__(self):
        self.message = "Receive incorrect message in server"

    def __str__(self):
        return f"IncorrectDataReceivedError: {self.message}"


class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}.'

