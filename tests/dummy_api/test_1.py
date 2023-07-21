


from utils.api_helpers.api_request_helper import ApiRequestHelper


def test_get_users(api_request: ApiRequestHelper):
    r = api_request.by_name('GetProjectUsers') \
                   .with_query_params(limit=3) \
                   .perform(True) \
                   .latency_is_lower_than(1500)

    print('\n\n Responmse JSON')
    print(r.get_json())
