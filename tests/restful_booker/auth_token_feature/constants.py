import pytest
from ..constants import API_NAME

AUTH_REQUEST_PAYLOAD_REFERENCE = \
    pytest.api_config.configs[API_NAME]\
    .request_catalog['Auth'].request.json
