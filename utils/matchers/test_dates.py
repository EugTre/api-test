"""Tests for Dates matchers"""
import re
import datetime

import pytest
import utils.matchers.matcher as match

class TestMatcherDate:
    """Test for Date Matchers"""
    PAST_DATES = (
        '2020-03-04',
        '20111104',
        '2011-11-04T00:05:23',
        '2011-11-04T00:05:23Z',
        '20111104T000523',
        '2011-11-04 00:05:23.283',
        '2011-11-04 00:05:23.283+00:00',
        '2011-11-04T00:05:23+04:00'
    )
    FUTURE_DATES = (
        '2040-03-04',
        '20411104',
        '2041-11-04T00:05:23',
        '2041-11-04T00:05:23Z',
        '20411104T000523',
        '2040-11-04 00:05:23.283',
        '2040-11-04 00:05:23.283+00:00',
        '2040-11-04T00:05:23+04:00'
    )

    """Tests date matchers"""
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date(self, compare_to):
        matcher_instance = match.AnyDate()
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    # Any Date Before
    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2022-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date_before(self, date, compare_to):
        matcher_instance = match.AnyDateBefore(date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("before_date, compare_to", (
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556124).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat()
        ),
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 54, 556123).isoformat()
        ),
    ), ids=["milliseconds", "seconds"])
    def test_any_date_before_precise(self, before_date, compare_to):
        matcher_instance = match.AnyDateBefore(before_date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("offset", (
        '+500ms',
        '+1s',
        '+1.5s',
        '+1m',
        '+1.5m',
        '+1.23h',
        '+2d',
        '+1y',
    ))
    def test_any_date_before_by_offset_to_now(self, offset):
        utc = datetime.timezone.utc
        matcher_instance = match.AnyDateBefore(offset)
        assert matcher_instance == datetime.datetime.now(utc).isoformat()
        assert datetime.datetime.now(utc).isoformat() == matcher_instance

    # Any Date After
    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2023-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", FUTURE_DATES)
    def test_any_date_after(self, date, compare_to):
        matcher_instance = match.AnyDateAfter(date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("after_date, compare_to", (
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556124).isoformat()
        ),
        (
            datetime.datetime(2023, 10, 15, 12, 30, 54, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat()
        ),
    ), ids=["milliseconds", "seconds"])
    def test_any_date_after_precise(self, after_date, compare_to):
        matcher_instance = match.AnyDateAfter(after_date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("offset", (
        '-500ms',
        '-1s',
        '-1.5s',
        '-1m',
        '-1.5m',
        '-1.23h',
        '-2d',
        '-1y',
    ))
    def test_any_date_after_by_offset_to_now(self, offset):
        utc = datetime.timezone.utc
        matcher_instance = match.AnyDateAfter(offset)
        assert matcher_instance == datetime.datetime.now(utc).isoformat()
        assert datetime.datetime.now(utc).isoformat() == matcher_instance

    # Any Date In Range
    @pytest.mark.parametrize("left, right", (
        ('-1d', '+1d'),
        ('-1y', '+1y'),
        ('-1s', '+1s'),
        ('now', '+1d'),
        ('-1d', 'now')
    ))
    def test_any_date_in_range(self, left, right):
        matcher_instance = match.AnyDateInRange(left, right)
        assert matcher_instance == datetime.datetime.now().isoformat()

    @pytest.mark.parametrize("left, right, exception, match_pattern", (
        ('+1d', '+2d', AssertionError, r'.*Date In Range.*earlier than.*left limit'),
        ('+100ms', '+500ms', AssertionError, r'.*Date In Range.*earlier than.*left limit'),
        ('-2d', '-1d', AssertionError,r'.*Date In Range.*later than.*right limit'),
        ('-500ms', '-100ms', AssertionError,r'.*Date In Range.*later than.*right limit'),
        ('+100ms', '-100ms', ValueError,
            r'Invalid matcher range limits!.*')
    ))
    def test_any_date_in_range_fails(self, left, right, exception, match_pattern):
        with pytest.raises(exception, match=re.compile(match_pattern, re.S)):
            matcher_instance = match.AnyDateInRange(left, right)
            assert matcher_instance == datetime.datetime.now().isoformat()

    # --- Negative tests
    # ------------------
    @pytest.mark.parametrize("compare_to", (
        12412,
        [1,2,3],
        'kkk',
        -414.424,
        True
    ))
    def test_any_date_fails(self, compare_to):
        matcher_instance = match.AnyDate()
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2022-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", FUTURE_DATES)
    def test_any_date_before_fails(self, date, compare_to):
        matcher_instance = match.AnyDateBefore(date)
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2023-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date_after_fails(self, date, compare_to):
        matcher_instance = match.AnyDateAfter(date)
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    # --- Negative on initialization
    @pytest.mark.parametrize("params", (12, 2.23, [], {}, type, False, None))
    @pytest.mark.parametrize("kls", (
        match.AnyDateAfter,
        match.AnyDateBefore
    ))
    def test_any_date_before_after_init_fails(self, params, kls):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*date.*',
            re.S
        )):
            kls(params)

    @pytest.mark.parametrize("params", (12, 2.23, [], {}, type, False, None))
    def test_any_date_in_range_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*date_from.*date_to.*',
            re.S
        )):
            match.AnyDateInRange(params, params)
