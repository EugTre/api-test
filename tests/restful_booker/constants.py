"""Constants for Restful-Booker tests"""
from utils.json_content.pointer import Pointer


API_NAME = "Restful-Booker"

USERNAME = "admin"
PASSWORD = "password123"

REQ_AUTH = "Auth"
REQ_GET = "GetBooking"
REQ_CREATE = "CreateBooking"
REQ_DELETE = "DeleteBooking"

# Pointers to fields
# CreateBooking:
FIELD_BOOKING_ID = Pointer.from_string("/bookingid")
FIELD_BOOKING_INFO = Pointer.from_string("/booking")
FIELD_TOTAL_PRICE = Pointer.from_string('/totalprice')
FIELD_BOOKING_DATES = Pointer.from_string('/bookingdates')
FIELD_ADDITIONAL_NEEDS = Pointer.from_string('/additionalneeds')
