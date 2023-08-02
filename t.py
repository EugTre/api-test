import logging.handlers
import logging.config

import utils.log_database_handler


logging.config.fileConfig("config/logging.ini")
logging.debug("KEK")

from utils.json_content.json_content import JsonContent

cfg = {
    'a': 1,
    'b': {
        'c': [1,2,3]
    }
}

cnt = JsonContent(cfg)
#cnt.delete()
cnt.update('/b/d', 100)
print(cnt.get())


'''
from utils.api_client.api_configuration_reader import ApiConfigurationReader

api = ApiConfigurationReader('config/api_clients.ini')
api_collection = api.read_configurations()

print(api_collection)
print('-' * 200)
print(api_collection.configs['DOG.CEO'].request_catalog['GetRandomImage'].response)
'''
