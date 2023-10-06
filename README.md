# API Test exercises

This repository is an exercies in automation of API testing using public test APIs.

Repository contains:
- testing framework
- framework's unit tests
- test suites for [DOG.CEO API](https://dog.ceo/dog-api/) and [Restful-Booker](https://restful-booker.herokuapp.com/apidoc/index.html) [TBD]

# <a name='toc'></a>Table of content
1. [How to use](#howto)
2. [Framework Overview](#overview)
    - [Framework Configuration](#overview_config)
    - [API Client](#overview_client)
    - [Request and Response Helpers](#overview_helpers)
    - [Matchers](#overview_matchers)
    - [Framework Unit Tests](#overview_unittest)

## <a name='howto'></a>How to use
### Installation
1. Download Python 3.11+ (see https://www.python.org/downloads/)
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

Run **tests from specific directory** with **Allure** logging:
```bash
pytest .\tests\dog_ceo_api\list_breeds_feature\ --alluredir=./tmp
```

Run **all tests**:
```bash
pytest --alluredir=./tmp
```

Check **Allure** report:
```bash
allure serve .\tmp\
```

#### Params

- `--clean-alluredir` - cleans Allure dir from previous runs.

- `--api-config=path/to/file` - path to API clients config file (defaults to *config/api_clients.json*).

- `--logging-config=path/to/file` - path to configuration file for logging (defaults to *config/logging.ini*).

- `--api-config-export=path/to/file` -- filename to dump composed api configuration. If not set - do not dump any data.

# <a name='overview'></a>Framework Overview [↑](#toc)

Framework contains of:
1. Configuration system that allows to prepare requests and set expectation for response, setup API client class and logging.
2. **API client**, that wraps `requests` lib with some extra logic and logging.
3. API **request and response helpers** that provide helpful methods to run requests and verify responses. Each valuable action is decorated with `allure.step`, making test results easy to check and understand.

Both request parameters and expected response values may be pre-configured and applied automatically, making general verification process pretty simple. However user can set up new request directly in test or override any parameter from pre-configured request.

Configuration system helps to compose data from various sources: by referencing to common nodes, read data from file or generate content via functions.

Framework and it's unit tests are located in `utils` directory.


## <a name='overview_config'></a>Framework Configuration [↑](#toc)

### Implementation note
Core part of configuration system is the `utisl.json_content` sub-module and a content wrapper class `JsonContent`. This class wraps pythonic dict/list and provide number of features critical to building configuration system:
- representation of dict/list as flat structure with access to any key/element by JSON pointer, making nested subsection easy to access and manipulate (handled by `JsonWrapper` class)
- ability to parse compositions (dict objects of specific structure) into values using special set of rules (handled by `Composer` class and composition handler classes)

Using both it's possible to create JSON structures dynamically, by composing files and generating data in runtime.

One may use `JsonContent` object during the tests, as many test methods provided by framework by default allows to pass `JsonContent` objects as parameters.

#### Available JSON compositions
Compositions are JSON objects of specific structure described below.
##### Reference to document node
Handled by: `utils.json_content.composition_handlers.ReferenceCompositionHandler`
```json
{
    "!ref": "/path/to/node"
}
```
Allows to re-use value at given node. Compositor will search for given JSON pointer and replace composition with copy of found value.

For common values it's recommended to store values in special node at root called `$defs` and refer to it.  After successful composition of document this node will be automatically removed.

##### Extended Reference to document node
Handled by: `utils.json_content.composition_handlers.ExtendReferenceCompositionHandler`
```json
{
   "!xref": "/path/to/node",
   "extend": {
       "/sub-node4": 100
   },
   "delete": ["/sub-node3"],
   "ifPresent": ["/sub-node"],
   "ifMissing": ["/sub-node2"]
}
```
Allows to re-use value at given node and to modify referenced dictionary value.

Compositor will search for given JSON pointer and replace composition with copy of found value. If value is a dictionary and if `extend` or `delete` params defined - copied value will be modified (nodes will be updated, added or removed), otherwise `!xref` works exactly as `!ref`.

Note, that pointers listed in `extend` and `delete` params must be constructed relative to referenced value, not to entire document!
Modifications are done via `JsonWrapper` class, and must follow same logic (e.g. update only existing node or add node to existing dict).

In case if one is referencing to non-static content (e.g. another ref or generator compositions), the `ifPresent` and `ifMissing` params allow to define a list of pointers that expected to present (or to be missing) in referenced value. If conditions are not met, composition will be returned untouched and be waiting until document will be processed before next try.

After successful composition of document this node will be automatically removed.


##### Reference to JSON file
Handled by: `utils.json_content.composition_handlers.FileReferenceCompositionHandler`
```json
{
    "!file": "/path/to/file.json"
}
```
Composition will be replaced with JSON content read from given file. Reference to file may be absolute or relative.

File's JSON may also contain composition which will be resolved in context of the current document (meaning one can refer to nodes in current document from content of external file).

Handler supports caching of the content, this might be helpful if same file is used often in the same document.

##### Include content from file
Handled by: `utils.json_content.composition_handlers.IncludeFileCompositionHandler`
```json
{
    "!include": "/path/to/file.json",
    "!compose": true/false,
    "!format": "json"/"text"
}
```
Reads content of given file and replace composition with it. Similar to previous composition, but provide way to configure import of content.

`!compose` flag (optional, defaults to `False`): if set to `False` - content will be added as is; otherwise - content will be composed in it's own context and only after that resulting content will be added to current document.

`!format` (optional, defaults to `None`) - sets expected format of data in file, if not set - format is guessed by file extension.

##### Generator
Handled by: `utils.json_content.composition_handlers.GeneratorCompositionHandler`
```java
{
    "!gen": "GeneratorName",
    "!args": [],
    "!id": "any_text",
    "kwargs": "value"
}
```
Looks for generator registered as given name and executes generator functions with given arguments (`!args`) and keyword arguments (any parameter without `!`). Then replaces composition with generated data.

`!gen` (str) - name of the generator in the `GeneratorManager`.

`!args` (list) - list of positional arguments for generator function.

`!id` (str, optional) - tag to mark several compositions to retrieve the very same result of generation function. Use it to ensure that request and response generated values will be the same. In context of the single document `!id` is used to identify generated result in the generator cache and to set `random.seed`. This means that if generator uses random package, one may retrieve same results using same `!id` across any part of the code (see `utils.generators.GeneratorManager` for details).

Other composition parameters will be passed to generation function as keyword arguments.

##### Matcher
Handled by: `utils.json_content.composition_handlers.MatcherCompositionHandler`
```json
{
    "!match": "AnyTextLike",
    "!args": [".*"],
    "case_sensitive": true
}
```
Looks for Matcher object of given class name, instantiate it with given `!args` and keyword args (any parameter without `!`). Then replaces composition with matcher object.

`!match` (str) - name of the matcher..

`!args` (list) - list of positional arguments for matcher constructor.

Other composition parameters will be passed to matcher constructor as keyword arguments.


### API Client configuration (api_config.json)

*Note*: `Auth` related configurations are very basic, just ignore them except very simple cases like user-pass authentication.

#### Base config

Path to this file should be passed as CLI argument `--api-config` (default is *config/api_config.json*).

Each API client should be configured under it's own section, where section name is name of the API used in pytest fixture to retrieve configured `ApiRequestHelper` object:
```javascript
{
    // Note: JS-like one line comments are allowed in json configs of project!

    // $defs section may be used as storage of common elements
    // for referencing from other nodes
    "$defs": {}

    // Defines configuration os specific API
    // Name is used for selection of pre-configured client in fixtures
    "DummyAPI": {
        // Base URL of the API
        "url": "https://dummyapi.io/data/",
        // Endpoint of the APU
        "endpoint": "/v1",
        // Class for API Client to be used (optional, defaults to SimpleApiClient)
        "client": "utils.api_client.simple_api_client.SimpleApiClient",
        // Logger for API Client (optional), logger name from 'logging.ini'
        "logger": "api_test",
        // Defaults for API Client:
        // - Request catalog as external file
        "requests": {
            "!include": "config/DummyAPI/requests.json",
            "!compse": true
        },
        // - Headers to include with every request to API
        "headers": {
            "!include": "config/DummyAPI/headers/headers_authorized.json"
        },
        // - Cookies to include with every request to API
        "cookies": {
            "!include": "config/DummyAPI/default_cookies.json"
        },
        // - Basic auth (username-pass) to include with every request
        "auth": ['username', 'password']
        // - Timeout for requests
        "timeout": 30,
    },

    // Additional configuration of API
    "DummyAPI_2": {
        ...
    }
}
```

#### Request catalog
It's possible to pre-configure requests and use them later with just a little touch. Requests, and properties of each particular request defined in catalog will be used by `ApiRequestHelper` and `ApiResponseHelper` as default values.

Each entity is nested under unique key (*name* of the request) and should contain 2 section:
- `request`: contains setup data for request - method, path, path and query params, headers, cookies, etc.
- `response`: contains data for response validation - status code, schema, expected headers, etc.

#### `request` object
Property | Value Example | Description
--- | --- | ---
`method` | *"GET"* | HTTP method for request. One of: GET, POST, PUT, PATCH, DELETE.
`path` | *"/user"* | Path to specific API method. May have placeholders - e.g. */user/{amount}*.
`path_params` | *{"amount": 3, "@use": ["amount"]}* | List of key-value pairs for path placeholder. By default values won't be used anyhow, but if key is listed in *"@use"* array -- path will be automatically formatted using defined value.
`query_params` | *{"amount": 3, "@use": ["amount"]}* | List of key-values pairs for request params. Same as `path_params` - only params listed in *"@use"* will be automatically added to request
`headers` | *{"Content-Type": "text/html; charset=utf-8"}* | Headers to add in request. Will be combined with base config level headers, overwritting headers with the same name.
`cookies` | *{"cookie1": "1"}* | Cookies to add in request. Will be combined with base config level cookies, overwritting cookies with the same name.
`auth` | *["user","passw"]* | Auth params to add in request. Overwrittes base config level auth values.
`json` | *{"key": "value"}* | Default JSON payload for request. Use `text` or `json`, but not both.
`text` | *"any text"* | Raw text to be added as request body. Use `text` or `json`, but not both.

#### `response` object
Property | Value Example | Description
--- | --- | ---
`status_code` | *200* | Expected status code number for response.
`schema` | *{...}* | Expected JSON Schema (see https://json-schema.org/) for response.
`json` | *{"key": "value"}* | Expected JSON payload for response.
`text` | *"any text"* | Expected response body (in case response is not formatted as JSON).
`headers` | *{"Content-Type": "text/html; charset=utf-8"}* | Expected headers for response.

****Note:*** It's recommended to use `!include` composition with `!compose: True` param for including request catalog. This also allows to use catalog-specific `$defs` section to share common values.

**Exmple:**
<details>
<summary>Request example under cut</summary>

```javascript
{
    // $defs content is read from extenal file
    "$defs": { "!file": "config/DOG.CEO/defines.json" },

    "GetSingleRandomImage": {

        "request": {
            "method": "GET",
            "path": "breeds/image/random"
        },

        "response": {
            "status_code": 200,
            // Reference to not yet existing node, but on composition
            // $defs will contain schema we are referencing to
            "schema": {"!ref": "/$defs/schema/SingleImage"},
            "json": {
                "status": "success",
                // Defining matcher to check response content
                "message": {
                    "!match": "AnyTextLike",
                    "pattern": "^(http|https)://.*(\\.jpg)$"
                }
            }
        }
    },
    ...
}
```
</details>

#### API default headers and cookies
Only use for limited number of headers/cookies that really must be sent on each request.
Anyway, headers/cookies may be overwritten by re-defining same header/cookie in request catalog or directly in API client method parameters.

### Logging configuration (logging.ini)
Path to logging configuration file should be passed as CLI argument `--logging-config` (default is *config/logging.ini*).

See https://docs.python.org/3/library/logging.config.html#configuration-file-format


## <a name='overview_client'></a>API Client [↑](#toc)

Class: `utils.api_client.simple_api_client.SimpleApiClient`

API client class is a wrapper for `requests` lib, which provide next features:
- default request parameters that applies to every request (appending, but not overriding user-specified values; defaults may be overwritten with empty values to disable specific values)
- composes URL using default API base URL, endpoint and user-provided path
- if logger provided - logs request/response data

Client may be configured using framework's configuration system.

In order to log request data a specific log handler was implements at `utils/log_database_handler.py`. This handler is designed to write data to SQLite database for history and to avoid over bloating Allure reports. Handler may be configured using `configs/logging.ini` (to specify database name).

## <a name='overview_helpers'></a>Request and Response Helpers [↑](#toc)
Classes:
- `utils.api_helpers.api_request_helper.ApiRequestHelper`
- `utils.api_helpers.api_response_helper.ApiResponseHelper`

`ApiRequestHelper` provides simple interface for running pre-configured or custom requests. Class depends on configuration system, which provide possibility to set up requests details in external files.

`ApiResponseHelper` provides number of methods for response validation and verification, including validation via JSON Schema (which may be configured in external files and accessed by name) and using Matcher objects (see below).

Both classes use `allure.step` to log actions and verification results in test report.

### Usage:
In order to access instance of `ApiRequestHelper` configured for a needed API one need to:
1. On package level `conftest.py` re-define `api_client` fixture:
```python
import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.simple_api_client import SimpleApiClient

API_NAME = 'MyAPI'  # Define your API name from api_config.ini

@pytest.fixture(scope='package')
def api_client(setup_loggers, api_clients_configurations) -> SimpleApiClient:
    return setup_api_client(API_NAME, api_clients_configurations)

```
2. Add `api_request` as test function parameter to access `api_request` fixture:
```python
from utils.api_helpers.api_request_helper import ApiRequestHelper

def test_random_image(self, api_request: ApiRequestHelper):
    api_request.by_name("GetRandomImage") \
               .perform() \
               # .perform() method returns ApiResponseHelper object
               .validate_against_schema() \
               .latency_is_lower_than(1500) \
               .is_not_empty() \
               .json.param_equals('/status', 'success')

```

### `ApiRequestHelper`
Class wraps API Client of specific configured API with user-friendly interface to select and perform requests (defined in configuration or composed directly in code).

Almost all methods of class return instance of class, allowing call chaining.

#### Initialize new request

See `utils.api_helpers.api_request_helper` for detailed documentation of methods.

###### `.by_name(name: str)`
searches for request with given name in configuration for API, and apply pre-configured values.

###### `.by_path(path: str|None, method: str = 'get')`
defines new request to given sub-path and using given method. Note that actual request path will be prepended with API's base URL and endpoint.

One must invoke any of the methods before further request's parameters setup.

#### Configure request
Number of methods provide user with ability to specify request parameters:
###### `.with_path_params(**kwargs)`
pre-configured request path may contain placeholders and this methods allows to set actual values to path.

Use key=values to specify value for each placeholder. Values should be strings.
By setting param to `None` one may remove previously defined path param.

Note: ValueError will be raised on missing/extra path params.

###### `.with_query_params(**kwargs)`
applies query params to request.
By setting param to `None` one may remove previously defined query param.

###### `.with_headers(dict, overwrite: bool = False)`
Sets or adds dict of headers to request's headers. If overwrite flag is set to False - current request headers and new will be merged, overwriting same headers with new values. Otherwise old headers will be completely replaced with given dict.

###### `.with_cookies(dict, overwrite: bool = False)`
Sets/adds given dict to request cookies in similar manner as `.with_headers()` method.

###### `.with_json_payload(dict|list)`
Sets JSON payload of the request.

###### `.with_expected(status_code: int, schema: dict, headers: dict, json: dict)`
Sets expected response parameters.

#### Perform request
###### `.perform(override_defaults: bool = Flase, **kwargs) -> ApiResponseHelper`
Performs request to API by passing configured request to API Client. Response will be wrapped with `ApiResponseHelper` instance and tested against expected status code, then instance will be returned as result of the method execution.

User may pass any additional keyword arguments that will be passed to underlaying `requests.request()` method. However `headers=` and `cookies=` will be merged with current request's params.

If `override_defaults` flag is set to True - request's `headers` and `cookies` will not be extended by API's defaults.


### `ApiResponseHelper`
Class wraps `requests.Response` object with various verification methods.

Almost all methods of class return instance of class, allowing call chaining.

See `utils.api_helpers.api_response_helper` for detailed documentation of methods.

#### General functions
`.set_expected()` - sets expected values (status_code, json content, cookies and headers) to test against.

`.get_response()` - returns wrapped `requests.Response` object.

`.get_headers()` - returns headers of wrapped response object.

`.get_json()` - returns parsed JSON content of wrapped response object. If no JSON content was parsed from response - ValueError will be raised.

`.get_json_value()` - returns value by given JSON pointer (see https://datatracker.ietf.org/doc/html/rfc6901). ValueError will be raised on missing JSON or invalid pointer.

#### Response verification
Functions decorated with Allure step and will raise `AssertionError` if test fails.

`.status_code_equals()` - tests status code against given/expected.

`.validate_against_schema()` - tests JSON content  against  given/expected JSON schema.

`.is_empty()`/`.is_not_empty()` - tests response's raw body content is empty or not.

`.equals()` - test response's body text to be equal given/expected text.

`.latency_is_lower_than()` - tests response's elapsed time against given value in milliseconds.

#### Response body JSON verification
Methods are available under `json` property of `ApiResponseHelper`. All methods return parent instance of `ApiResponseHelper`, allowing call chaining.

Methods that tests for equals are assumed to be used with Matcher objects for specific data type validation.

Params must be accessed using JSON Pointer syntax (see https://datatracker.ietf.org/doc/html/rfc6901).

`.json.set_expected()` - sets expected dict|list of JSON to test against.

`.json.equals()` - tests that JSON is equal to given/expected. Asserts on missing/extra keys or non-equal values.
`.json.is_like()` - tests that JSON contains all given keys and values as given/expected. Asserts if any given key is missing or value is not equals.

`.json.params_present()`/`.json.params_not_present()` - tests that all given params are present/absent in JSON.

`.json.params_are_empty()`/`.json.params_are_not_empty()` - tests that all given params are empty (`None`, `[]`, `{}`, `''`) or not.

`.json.param_equals()` - tests that given param equals to given value/Matcher. Asserts if not.

#### Response headers verification
Methods are available under `headers` property of `ApiResponseHelper`. All methods return parent instance of `ApiResponseHelper`, allowing call chaining.

Methods that tests for equals are assumed to be used with Matcher objects for specific data type validation.

`.headers.set_expected()` - sets expected dict of headers to test against.

`.headers.are_like()` - tests that headers have all given/expected keys and it's values. Asserts if keys are missing or values are not equal.

`.headers.equals()`- test that headers are equal to given/expected. Asserts if there are missing/extra keys or values doesn't match.

`.headers.present()` / `.not_present()` - tests that all headers from given list are present/missing in response headers.

`.headers.header_contains()` - check that given header is present and it's value contains given substring.

`.headers.header_equals()` - check that given header is present and it's value is equal to given.


## <a name='overview_matchers'></a>Matchers [↑](#toc)
Class: `utils.matchers.matcher`
Matchers are special classes that implements specific equality check methods and provide user with ability to make rough comparison with some data.

Matcher may:
- match to anything (except `None`) like `Anything`
- be type-specific (e.g. match to number, but not to string) like `AnyNumber`, `AnyText`, `AnyBool`, `AnyList`, `AnyDict`, `AnyDate`
- by value-specific (e.g. match to value in range or of pattern, etc.) like `AnyTextLike`, `AnyTextWith`, `AnyNumberInRange`, `AnyNumberGreaterThan`, `AnyNumberLessThan`, `AnyDateBefore`, `AnyDateAfter`, `AnyDateInRange`
- or be even more picky  like `AnyListOf`, `AnyListOfRange`, `AnyListLongerThan`, `AnyListShorterThan`, `AnyListOfMatchers`, `AnyListOfMatchersLongerThan`, `AnyListOfMatchersShorterThan` (match by elements size and/or type)

Matchers also implements **pytest's**  assertion explanation, providing detailed information about assertion reason.

One may add custom matchers by inheriting from `utils.matchers.base_matcher.BaseMatcher` class and implementing all abstract methods.

## <a name='overview_unittest'></a>Framework Unit Tests [↑](#toc)
Framework is covered with plenty of unit tests to ensure it's stability and suitability.

Tests are using **pytest** and supports parallel run using **xdist**.
#### Launch
```
pytest .\utils -n auto --dist loadgroup
```
Some tests are using localhost server and should be run as group.
