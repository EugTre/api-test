# API Test exercises

# TODO:
 - Matchers: Add assertrepr_compare methods and add to conftest.py
 - DB Logger
 - ApiRequest tests
 - Review ApiResponse to use with matchers

## How to use
### Installation
1. Download Python 3.10+ (see https://www.python.org/downloads/)
2. Download and unpack project.
3. Navigate to project directory using terminal/cmd
4. Create virtual environment:
```cmd
python -m venv venv
```
5. Activate virtual environment:
```
# Windows
venv\Scripts\activate

# Linux
venv/bin/activate
```
6. Install dependencies:
```cmd
pip install -r requirements.txt
```
7. Install Allure commandline - see https://docs.qameta.io/allure/#_installing_a_commandline

### Run tests
For 'DummyAPI' test one need to get `app-id` value for header. Go to https://dummyapi.io/ and SignIn using prefered method, then generate `app-id` and add it as headers in DummyAPI section of API configuration (see below).

Start **tests from specific file**:
```
pytest .\tests\dummy_api\test_1.py --alluredir=./tmp --clean-alluredir -vv -s
```

Start **all tests**:
```
pytest --alluredir=./tmp --clean-alluredir -vv -s
```

Check **Allure** report:
```
allure serve .\tmp\
```

# Framework Overview

Framework contains of:
1. API client, that wraps `requests` lib with some extra logic and logging.
2. API request and response helpers that provide helpful methods to run requests and verify responses. Each valuable action is decorated with `allure.step`, making test results easy to check and understand.
3. Configuration system that allows to prepare requests and set expectation for response.

## API Client

TBD

## API Request and Response Helpers
Classes:
- `utils.api_helpers.api_request_helper.ApiRequestHelper`
- `utils.api_helpers.api_response_helper.ApiResponseHelper`

`ApiRequestHelper` provides simple interface for running pre-configured or custom requests. Class depends on configuration system, which provide possibility to set up requests details in external files.

`ApiResponseHelper` provides number of methods for response validation and verification, including validation via JSON Schema (which may be configured in external files and accessed by name).

Both classes use `allure.step` to store actions and checks information in test report.

### Usage:
In order to access instance of `ApiRequestHelper` configured for a needed API one need to:
1. On package level `conftest.py` re-define `api_client` fixture:
```python
import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.basic_api_client import BasicApiClient

API_NAME = 'MyAPI'  # Define your API name from api_config.ini

@pytest.fixture(scope='package')
def api_client(setup_loggers, api_clients_configurations) -> BasicApiClient:
    return setup_api_client(API_NAME, api_clients_configurations)

```
2. Add `api_request` as test function paramereter to access `api_request` fixture:
```python
from utils.api_helpers.api_request_helper import ApiRequestHelper

def test_random_image(self, api_request: ApiRequestHelper):
    api_request.by_name("GetRandomImage") \
               .perform() \
               .validate_against_schema() \
               .latency_is_lower_than(1500) \
               .is_not_empty() \
               .value_equals('status', 'success')

```


## Framewrok Configuration

### API Client configuration (api_config.ini)

*Note*: `Auth` related configurations are very unfinished, just ignore them except very simple cases like user-pass authentication.

#### Base config

Path to this file should be passed as CLI argument `--api-config` (default is *config/api_config.ini*).

Each API client should be configured under it's own section:
```ini
[DummyAPI]
url = https://dummyapi.io/data
endpoint = /v1
client = utils.api_client.basic_api_client.BasicApiClient
logger=api_test
requests = config/DummyAPI/requests.json
headers = config/DummyAPI/headers.json
timeout = 120
```

- The **name** of the section is considered as API name.
- **url** - base URL for API to test. ***Required***.
- **endpoint** - base URL and path for API to test. Default is `/`.
- **client** - module and classname of API client class to use. Default `utils.api_client.basic_api_client.BasicApiClient`.
- **logger** - name of the logger to use for API client. See 'logging.ini'. Default is ''.
- **requests** - path to JSON file with pre-configured *request catalog*.
- **timeout** - default request timeout for API client. If defined - value will be applied to *every* request made by API Client. Default is 240 seconds.
- **headers** - path to JSON file with headers, OR headers as comma-separated key-value pairs. If defined - values will be applied to *every* request made by API Client.
- **cookies** - path to JSON file with cookies, OR cookies as comma-separated key-value pairs. If defined - values will be applied to *every* request made by API Client.
- **auth** - path to file with auth data, OR auth param, e.g. *("user","path")*. If defined - values will be applied to *every* request made by API Client.

##### Example:
```ini
[DummyAPI]
url = https://dummyapi.io/data
endpoint = /v1
...
; headers and cookies may be JSON key-value pairs
headers =
    "app-id": "441112",
    "Content-Type": "text/html; charset=utf-8"
cookies =
    "cookie1": "1",
    "cookie2": "2"
```

#### Request catalog
It's possible to pre-configure requests and use them later with just a little touch. Requests, and properties of each particular request defined in catalog will be used by `ApiRequestHelper` and 'ApiResponseHelper` as default values.

Each entity is nested under unique key (*name* of the request) and should contain 2 section:
- `request`: contains setup data for request - method, path, params, headers, cookies, etc.
- `response`: contains data for response validation - status code, schema, expected headers, etc.

#### `request` object
Property | Value Example | Description
--- | --- | ---
`method` | *"GET"* | HTTP method for request. One of: GET, POST, PUT, PATCH, DELETE.
`path` | *"/user"* | Path to specific API method. May have placeholders - e.g. */user/{amount}*.
`path_params` | *{"amount": 3, "@use": ["amount"]}* | List of key-value pairs for path placeholder. By default values won't be used anyhow, but if key is listed in *"@use"* array -- path will be automatically formatted using defined value.
`query_params` | *{"amount": 3, "@use": ["amount"]}* | List of key-values pairs for request params. Same as `path_params` - only params listed in *"@use"* will be automatically added to request
`headers`* | *{"Content-Type": "text/html; charset=utf-8"}* | Headers to add in request. Will be combined with base config level headers, overwritting headers with the same name.
`cookies`* | *{"cookie1": "1"}* | Cookies to add in request. Will be combined with base config level cookies, overwritting cookies with the same name.
`auth` | *["user","path"]* | Auth params to add in request. Overwrittes base config level auth values.
`json` | *{"key": "value"}* | Default JSON payload for request.

#### `response` object
Property | Value Example | Description
--- | --- | ---
`status_code` | *200* | Expected status code number for response.
`schema` | *{...}* | Expected JSON Schema (see https://json-schema.org/) for response.
`json` | *{"key": "value"}* | Expected JSON payload for response.


****Note:*** both `headers` and `cookies` properties may be a reference to *.json* file with actual data in JSON format. Property value should be in format `"path/to/file.json"`. E.g.
```json
"request": {
    "method": "GET",
    "path": "/users",
    "headers": "config/MyAPI/headers_non_authorized.json"
}
```

#### Reference values and on-load compilation
Request catalog file will be compiled on load - all references to properties or files will be resolved, and replaced with actual values.

Reference type | Reference syntax | Description
--- | --- | ---
Reference | `!ref <JSONPointer>` | Value is JSON Pointer (see https://www.rfc-editor.org/rfc/rfc6901), will be replaced with value refered by pointer. JSON Pointer should be valid and should present in request catalog.
File reference | `!file path/to/file.json` | Value is relative or absolute path to file, will be replaced with file's content. File should exists and be valid JSON file.

For purpose of storing common values a special key `$defs` is allowed in request catalog root (other keys in root should be names of the objects). E.g.
```json
/* request catalog content */
{
    "$defs": {
        "get": "GET",
        "get_schema": "!file config/Api/schema.json"
    },

    "GetApiCall": {
        "request": {
            "method": "!ref /$defs/get"
        },
        "response": {
            "status_code": 200,
            "schema": "!ref /$defs/get_schema"
        }
    }
}
/* will be compiled to */
{
    "GetApiCall": {
        "request": {
            "method": "GET"
        },
        "response": {
            "status_code": 200,
            "schema": {/* schema from config/Api/schema.json */}
        }
    }
}
```

#### Headers and Cookies files
JSON file with key-values pairs to use for every request. May be overwritten by pre-configured request or directly in API client method parameters.


### Logging configuration (logging.ini)
Path to logging configuration file should be passed as CLI argument `--logging-config` (default is *config/logging.ini*).

See https://docs.python.org/3/library/logging.config.html#configuration-file-format





