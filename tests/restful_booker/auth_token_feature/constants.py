import pytest
from ..constants import API_NAME, REQ_AUTH


AUTH_REQUEST_PAYLOAD_REFERENCE: dict = \
    pytest.api_config.configs[API_NAME]\
    .request_catalog[REQ_AUTH].request.json
