

import pytest
from utils.api_helpers.api_request_helper import ApiRequestHelper

@pytest.mark.skip()
def test_create_user(api_request: ApiRequestHelper):
    r = api_request.by_name("PostCreateUser_RequiredOnly")\
                .perform()\
                .is_not_empty()
    print('\n\n\n')
    print(r.get_json())
    print('\n\n\n')
    r.json_equals(ignore=('id', 'registerDate', 'updatedDate'))


@pytest.mark.skip()
def test_get_users(api_request: ApiRequestHelper):
    r = api_request.by_name('GetUsers') \
                    .perform()

    print('\n\n Responmse JSON')
    print(r.get_json())


#@pytest.mark.skip()
def test_get_user_by_id(api_request: ApiRequestHelper):
    r = api_request.by_name('GetUserByID') \
                    .with_path_params(user_id='64bffa8c43c8e61c70dc0d2d')\
                    .perform()

    print('\n\n Responmse JSON')
    print(r.get_json())


@pytest.mark.skip()
def test_delete_user(api_request: ApiRequestHelper):
    user_id = '64bffa8c43c8e61c70dc0d2d'
    r = api_request.by_name("DeleteUser")\
        .with_path_params(user_id=user_id)\
        .perform() \
        .validates_against_schema() \
        .is_not_empty() \
        .json_equals({'id': user_id})
    print('\n\n Responmse JSON')
    print(r.get_json())
