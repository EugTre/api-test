"""Re-import general constants for specific API"""
import pytest
from ..constants import API_NAME, REQ_CREATE


CREATE_REQUEST_PAYLOAD_REFERENCE: dict = \
    pytest.api_config.configs[API_NAME] \
    .request_catalog[REQ_CREATE].request.json
