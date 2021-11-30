
DEFAULT_PORT = 7777
DEFAULT_HOST = '127.0.0.1'
DEFAULT_TIMEOUT = 0.5
# arg for listen method
MAX_CONNECTIONS = 5
# arg for recv method
MAX_BUFFER_SIZE = 1024
ENCODING = 'utf-8'

# JIM protocol
# main keys
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

# additional keys
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'

# response dicts
# 200 success
RESPONSE_200 = {RESPONSE: 200}
# 400 failed
RESPONSE_400 = {
            RESPONSE: 400,
            ERROR: None
}
