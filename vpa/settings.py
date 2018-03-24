import os

from vpa.utils import rel


LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')

PG_HOST = 'localhost'
PG_USER = 'vpa'
PG_PASSWORD = 'vpa'
PG_DB = 'bittrex_vpa'

ENV = os.getenv('ENV', 'development')
LOGS_DIR = os.getenv('LOGS_DIR', rel('logs'))
SERVER_PORT = os.getenv('SERVER_PORT', '8080')
