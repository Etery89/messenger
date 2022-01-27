import dis
import socket


# Верификация в метакласах работает только при отключении декоратора @log_function в классе TCPClient
class ClientVerifier(type):

    def __init__(self, clsname, bases, clsdict):

        invalid_methods = ['accept', 'listen']
        for key, value in clsdict.items():
            # Checking the creation of a socket at the class level
            if isinstance(value, socket.socket):
                raise TypeError(f'{key}: The socket should not be created at the class level')
            try:
                instructions = dis.get_instructions(value)
            except TypeError:
                continue
            for instruction in instructions:
                # Checking the socket for compliance with the TCP-protocol
                if instruction.opname == "LOAD_GLOBAL" and instruction.argval == 'SOCK_DGRAM':
                    raise TypeError(f'{key}, {instruction.argval}: To create a socket, the TCP-protocol must be used')
                # Checking invalid methods
                if instruction.opname == 'LOAD_METHOD' and instruction.argval in invalid_methods:
                    raise TypeError(f'{key}: The method {instruction.argval} is not allowed when creating this class ')

        type.__init__(self, clsname, bases, clsdict)


class ServerVerifier(type):

    def __init__(self, clsname, bases, clsdict):

        invalid_method = 'connect'
        for key, value in clsdict.items():
            try:
                instructions = dis.get_instructions(value)
            except TypeError:
                continue
            for instruction in instructions:
                # Checking the socket for compliance with the TCP-protocol
                if instruction.opname == "LOAD_GLOBAL" and instruction.argval == 'SOCK_DGRAM':
                    raise TypeError(f'{key}, {instruction.argval}: To create a socket, the TCP-protocol must be used')
                # Checking invalid methods
                if instruction.opname == 'LOAD_METHOD' and instruction.argval == invalid_method:
                    raise TypeError(f'{key}: The method {instruction.argval} is not allowed when creating this class ')

        type.__init__(self, clsname, bases, clsdict)

