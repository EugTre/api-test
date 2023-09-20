"""Constants for DOG.CEO tests"""
from utils.api_client.models import HTTPMethod

API_NAME = 'DOG.CEO'

NOT_ALLOWED_METHODS = (
    HTTPMethod.POST,
    HTTPMethod.PATCH,
    HTTPMethod.PUT,
    HTTPMethod.DELETE,
)
