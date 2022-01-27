import sys
import json
from commons import *
from commons.errors import IncorrectDataReceivedError, NonDictInputError
from commons.decorators import log_function

sys.path.append('../')


@log_function
def get_message(sock_obj):
    encoded_response = sock_obj.recv(MAX_BUFFER_SIZE)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise NonDictInputError
    else:
        raise IncorrectDataReceivedError


@log_function
def send_message(sock_obj, message):
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock_obj.send(encoded_message)


