"""Tests for Tistory Open API extractor."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest
import requests

from tistory_migrator.extractor.api import (
    ApiAuthError,
    ApiUnavailableError,
    TistoryApiExtractor,
    _RETRY_DELAYS,
)
from tistory_migrator.extractor.base import BaseExtractor
from tistory_migrator.models import TistoryPost


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


def ok_body(item: dict) -> dict:
    return {"tistory": {"status": "200", "item": item}}


def category_list_body(categories: list[dict]) -> dict:
    return ok_body({"categories": {"category": categories}})


def post_list_body(posts: list[dict], count: int = 10, total: int | None = None) -> dict:
    return ok_body({
        "posts": {"post": posts},
        "count": str(count),
        "totalCount": str(total if total is not None else len(posts)),
    })


def post_read_body(item: dict) -> dict:
    return ok_body(item)


def make_post_item(
    post_id: str = "1",
    title: str = "Test Post",
    content: str = "<p>Hello</p>",
    category_id: str = "10",
    date: str = "2024-01-15 10:30:00",
    tags: list[str] | None = None,
    url: str = "https://testblog.tistory.com/1",
) -> dict:
    tag_val: list[str] | str = tags if tags is not None else []
    return {
        "id": post_id,
        "title": title,
        "content": content,
        "categoryId": category_id,
        "date": date,
        "tags": {"tag": tag_val},
        "postUrl": url,
    }


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor() -> TistoryApiExtractor:
    """Extractor with rate_limit_sleep=0 for fast tests."""
    return TistoryApiExtractor(blog="testblog", access_token="TOKEN", rate_limit_sleep=0.0)


# ---------------------------------------------------------------------------
# Identity / interface
# ---------------------------------------------------------------------------

class TestIdentity:
    def test_name(self, extractor: TistoryApiExtractor) -> None:
        assert extractor.name == "api"

    def test_is_base_extractor(self, extractor: TistoryApiExtractor) -> None:
        assert isinstance(extractor, BaseExtractor)

    def test_default_rate_limit_sleep(self) -> None:
        e = TistoryApiExtractor(blog="b", access_token="t")
        assert e._rate_limit_sleep == 1.0


# ---------------------------------------------------------------------------
# _request: sleep ordering
# ---------------------------------------------------------------------------

class TestRequestSleep:
    def test_sleeps_rate_limit_on_first_attempt(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(200, ok_body({"url": "x"}))
        with patch("tistory_migrator.extractor.api.time.sleep") as mock_sleep, \
             patch.object(extractor._session, "get", return_value=resp):
            extractor._request("/category/list", {"blogName": "testblog"})
        mock_sleep.assert_called_once_with(0.0)

    def test_sleeps_retry_delay_on_first_retry(self, extractor: TistoryApiExtractor) -> None:
        resp_500 = make_response(500, {})
        resp_ok = make_response(200, ok_body({"url": "x"}))
        with patch("tistory_migrator.extractor.api.time.sleep") as mock_sleep, \
             patch.object(extractor._session, "get", side_effect=[resp_500, resp_ok]):
            extractor._request("/post/list", {"blogName": "testblog", "page": "1"})
        assert mock_sleep.call_args_list == [call(0.0), call(_RETRY_DELAYS[0])]

    def test_sleeps_increasing_delays_on_multiple_retries(
        self, extractor: TistoryApiExtractor
    ) -> None:
        resp_500 = make_response(500, {})
        resp_ok = make_response(200, ok_body({"url": "x"}))
        with patch("tistory_migrator.extractor.api.time.sleep") as mock_sleep, \
             patch.object(
                 extractor._session, "get", side_effect=[resp_500, resp_500, resp_ok]
             ):
            extractor._request("/post/list", {"blogName": "testblog", "page": "1"})
        assert mock_sleep.call_args_list == [
            call(0.0),
            call(_RETRY_DELAYS[0]),
            call(_RETRY_DELAYS[1]),
        ]

    def test_retry_delays_are_exponential(self) -> None:
        assert _RETRY_DELAYS == [1, 2, 4]


# ---------------------------------------------------------------------------
# _request: auth errors
# ---------------------------------------------------------------------------

class TestRequestAuthErrors:
    def test_http_401_raises_api_auth_error(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(401, {})
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            with pytest.raises(ApiAuthError):
                extractor._request("/post/list", {"blogName": "testblog", "page": "1"})

    def test_body_status_401_raises_api_auth_error(self, extractor: TistoryApiExtractor) -> None:
        body = {"tistory": {"status": "401", "error_message": "token expired"}}
        resp = make_response(200, body)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            with pytest.raises(ApiAuthError):
                extractor._request("/post/list", {"blogName": "testblog", "page": "1"})


# ---------------------------------------------------------------------------
# _request: unavailability and retries
# ---------------------------------------------------------------------------

class TestRequestUnavailable:
    def test_5xx_all_retries_raises_api_unavailable(
        self, extractor: TistoryApiExtractor
    ) -> None:
        resp_500 = make_response(500, {})
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(
                 extractor._session, "get", return_value=resp_500
             ):
            with pytest.raises(ApiUnavailableError):
                extractor._request("/post/list", {"blogName": "testblog", "page": "1"})

    def test_5xx_then_success_returns_data(self, extractor: TistoryApiExtractor) -> None:
        resp_500 = make_response(500, {})
        resp_ok = make_response(200, ok_body({"url": "x"}))
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", side_effect=[resp_500, resp_ok]):
            result = extractor._request("/category/list", {"blogName": "testblog"})
        assert result.get("item") == {"url": "x"}

    def test_timeout_all_retries_raises_api_unavailable(
        self, extractor: TistoryApiExtractor
    ) -> None:
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(
                 extractor._session, "get", side_effect=requests.Timeout
             ):
            with pytest.raises(ApiUnavailableError):
                extractor._request("/post/list", {"blogName": "testblog", "page": "1"})

    def test_timeout_then_success_returns_data(self, extractor: TistoryApiExtractor) -> None:
        resp_ok = make_response(200, ok_body({"url": "x"}))
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(
                 extractor._session, "get", side_effect=[requests.Timeout, resp_ok]
             ):
            result = extractor._request("/category/list", {"blogName": "testblog"})
        assert result.get("item") == {"url": "x"}

    def test_connection_error_all_retries_raises_api_unavailable(
        self, extractor: TistoryApiExtractor
    ) -> None:
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(
                 extractor._session, "get", side_effect=requests.ConnectionError
             ):
            with pytest.raises(ApiUnavailableError):
                extractor._request("/category/list", {"blogName": "testblog"})

    def test_5xx_retries_exactly_4_times(self, extractor: TistoryApiExtractor) -> None:
        resp_500 = make_response(500, {})
        mock_get = MagicMock(return_value=resp_500)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            with pytest.raises(ApiUnavailableError):
                extractor._request("/post/list", {"blogName": "testblog", "page": "1"})
        assert mock_get.call_count == 4


# ---------------------------------------------------------------------------
# _request: params
# ---------------------------------------------------------------------------

class TestRequestParams:
    def test_includes_access_token_in_params(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(200, ok_body({}))
        mock_get = MagicMock(return_value=resp)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            extractor._request("/category/list", {"blogName": "testblog"})
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["access_token"] == "TOKEN"

    def test_includes_output_json_in_params(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(200, ok_body({}))
        mock_get = MagicMock(return_value=resp)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            extractor._request("/category/list", {"blogName": "testblog"})
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["output"] == "json"

    def test_extra_params_merged(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(200, ok_body({}))
        mock_get = MagicMock(return_value=resp)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            extractor._request("/post/list", {"blogName": "testblog", "page": "2"})
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["page"] == "2"


# ---------------------------------------------------------------------------
# _get_category_map
# ---------------------------------------------------------------------------

class TestGetCategoryMap:
    def _mock_category_request(
        self, extractor: TistoryApiExtractor, categories: list[dict]
    ) -> dict[str, str]:
        resp = make_response(200, category_list_body(categories))
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            return extractor._get_category_map()

    def test_maps_id_to_name(self, extractor: TistoryApiExtractor) -> None:
        result = self._mock_category_request(
            extractor, [{"id": "10", "name": "Python"}, {"id": "20", "name": "Django"}]
        )
        assert result == {"10": "Python", "20": "Django"}

    def test_single_category_as_dict(self, extractor: TistoryApiExtractor) -> None:
        # API may return single item as dict instead of list
        body = ok_body({"categories": {"category": {"id": "10", "name": "Python"}}})
        resp = make_response(200, body)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            result = extractor._get_category_map()
        assert result == {"10": "Python"}

    def test_unavailable_returns_empty_dict(self, extractor: TistoryApiExtractor) -> None:
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", side_effect=requests.Timeout):
            result = extractor._get_category_map()
        assert result == {}

    def test_auth_error_propagates(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(401, {})
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            with pytest.raises(ApiAuthError):
                extractor._get_category_map()

    def test_empty_categories(self, extractor: TistoryApiExtractor) -> None:
        result = self._mock_category_request(extractor, [])
        assert result == {}


# ---------------------------------------------------------------------------
# _extract_images
# ---------------------------------------------------------------------------

class TestExtractImages:
    def test_double_quote_src(self) -> None:
        html = '<img src="https://example.com/photo.jpg" alt="test">'
        assert TistoryApiExtractor._extract_images(html) == ["https://example.com/photo.jpg"]

    def test_single_quote_src(self) -> None:
        html = "<img src='https://example.com/photo.jpg'>"
        assert TistoryApiExtractor._extract_images(html) == ["https://example.com/photo.jpg"]

    def test_no_images(self) -> None:
        assert TistoryApiExtractor._extract_images("<p>No images</p>") == []

    def test_multiple_images(self) -> None:
        html = '<img src="a.jpg"><p>text</p><img src="b.jpg">'
        assert TistoryApiExtractor._extract_images(html) == ["a.jpg", "b.jpg"]


# ---------------------------------------------------------------------------
# _parse_post
# ---------------------------------------------------------------------------

class TestParsePost:
    def test_basic_fields(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item()
        post = extractor._parse_post(item, {"10": "Python"})
        assert post.id == "1"
        assert post.title == "Test Post"
        assert post.content_html == "<p>Hello</p>"
        assert post.category == "Python"
        assert post.url == "https://testblog.tistory.com/1"

    def test_tags_as_list(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(tags=["Python", "Flask"])
        post = extractor._parse_post(item, {})
        assert post.tags == ["Python", "Flask"]

    def test_tags_as_single_string(self, extractor: TistoryApiExtractor) -> None:
        # API may return single tag as string instead of list
        item = make_post_item()
        item["tags"] = {"tag": "Python"}
        post = extractor._parse_post(item, {})
        assert post.tags == ["Python"]

    def test_tags_empty_list(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(tags=[])
        post = extractor._parse_post(item, {})
        assert post.tags == []

    def test_tags_none(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item()
        item["tags"] = None
        post = extractor._parse_post(item, {})
        assert post.tags == []

    def test_title_fallback_for_empty_title(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(title="")
        post = extractor._parse_post(item, {})
        assert post.title == "untitled-1"

    def test_date_fromisoformat(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(date="2024-06-15T10:30:00+09:00")
        post = extractor._parse_post(item, {})
        assert post.published_at.year == 2024
        assert post.published_at.month == 6
        assert post.published_at.day == 15

    def test_date_strptime_fallback(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(date="2024-01-15 10:30:00")
        post = extractor._parse_post(item, {})
        assert post.published_at == datetime(2024, 1, 15, 10, 30, 0)

    def test_date_invalid_falls_back_to_min(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(date="not-a-date")
        post = extractor._parse_post(item, {})
        assert post.published_at == datetime.min

    def test_category_from_map(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(category_id="42")
        post = extractor._parse_post(item, {"42": "Backend"})
        assert post.category == "Backend"

    def test_category_missing_from_map(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(category_id="99")
        post = extractor._parse_post(item, {"10": "Python"})
        assert post.category == ""

    def test_images_extracted_from_content(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(content='<img src="https://img.example.com/a.jpg"><p>text</p>')
        post = extractor._parse_post(item, {})
        assert post.images == ["https://img.example.com/a.jpg"]

    def test_posturl_field(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item(url="https://testblog.tistory.com/42")
        post = extractor._parse_post(item, {})
        assert post.url == "https://testblog.tistory.com/42"

    def test_url_field_fallback(self, extractor: TistoryApiExtractor) -> None:
        item = make_post_item()
        del item["postUrl"]
        item["url"] = "https://testblog.tistory.com/99"
        post = extractor._parse_post(item, {})
        assert post.url == "https://testblog.tistory.com/99"


# ---------------------------------------------------------------------------
# _fetch_post_ids
# ---------------------------------------------------------------------------

class TestFetchPostIds:
    def test_single_page(self, extractor: TistoryApiExtractor) -> None:
        body = post_list_body([{"id": "1"}, {"id": "2"}], count=10, total=2)
        resp = make_response(200, body)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            result = extractor._fetch_post_ids()
        assert result == ["1", "2"]

    def test_pagination_two_pages(self, extractor: TistoryApiExtractor) -> None:
        page1_body = post_list_body(
            [{"id": "1"}, {"id": "2"}], count=2, total=3
        )
        page2_body = post_list_body(
            [{"id": "3"}], count=2, total=3
        )
        responses = [make_response(200, page1_body), make_response(200, page2_body)]
        mock_get = MagicMock(side_effect=responses)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            result = extractor._fetch_post_ids()
        assert result == ["1", "2", "3"]

    def test_page_param_increments(self, extractor: TistoryApiExtractor) -> None:
        page1_body = post_list_body([{"id": "1"}], count=1, total=2)
        page2_body = post_list_body([{"id": "2"}], count=1, total=2)
        responses = [make_response(200, page1_body), make_response(200, page2_body)]
        mock_get = MagicMock(side_effect=responses)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            extractor._fetch_post_ids()
        call1_params = mock_get.call_args_list[0][1]["params"]
        call2_params = mock_get.call_args_list[1][1]["params"]
        assert call1_params["page"] == "1"
        assert call2_params["page"] == "2"

    def test_single_post_as_dict(self, extractor: TistoryApiExtractor) -> None:
        # API may return single post as dict instead of list
        body = ok_body({
            "posts": {"post": {"id": "1"}},
            "count": "10",
            "totalCount": "1",
        })
        resp = make_response(200, body)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            result = extractor._fetch_post_ids()
        assert result == ["1"]

    def test_empty_post_list(self, extractor: TistoryApiExtractor) -> None:
        body = ok_body({"posts": {"post": []}, "count": "0", "totalCount": "0"})
        resp = make_response(200, body)
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            result = extractor._fetch_post_ids()
        assert result == []

    def test_auth_error_propagates(self, extractor: TistoryApiExtractor) -> None:
        resp = make_response(401, {})
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", return_value=resp):
            with pytest.raises(ApiAuthError):
                extractor._fetch_post_ids()


# ---------------------------------------------------------------------------
# extract()
# ---------------------------------------------------------------------------

class TestExtract:
    def _setup_responses(
        self,
        extractor: TistoryApiExtractor,
        category_resp: MagicMock,
        list_resp: MagicMock,
        read_resps: list[MagicMock],
    ) -> MagicMock:
        responses = [category_resp, list_resp, *read_resps]
        return MagicMock(side_effect=responses)

    def test_extract_returns_posts(self, extractor: TistoryApiExtractor) -> None:
        cat_resp = make_response(200, category_list_body([{"id": "10", "name": "Python"}]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read_resp = make_response(200, post_read_body(make_post_item()))

        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read_resp])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract()

        assert len(posts) == 1
        assert isinstance(posts[0], TistoryPost)
        assert posts[0].id == "1"

    def test_extract_auth_error_from_list_propagates(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(401, {})
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            with pytest.raises(ApiAuthError):
                extractor.extract()

    def test_extract_auth_error_from_read_propagates(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read_resp = make_response(401, {})
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read_resp])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            with pytest.raises(ApiAuthError):
                extractor.extract()

    def test_extract_unavailable_post_is_skipped(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body(
            [{"id": "1"}, {"id": "2"}], count=10, total=2
        ))
        # Post 1 fails, post 2 succeeds
        read_fail = make_response(500, {})
        read_ok = make_response(200, post_read_body(make_post_item(post_id="2")))
        mock_get = MagicMock(side_effect=[cat_resp, list_resp, read_fail, read_fail, read_fail, read_fail, read_ok])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract()
        assert len(posts) == 1
        assert posts[0].id == "2"

    def test_extract_filter_after_inclusive(self, extractor: TistoryApiExtractor) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body(
            [{"id": "1"}, {"id": "2"}], count=10, total=2
        ))
        # post 1: 2024-01-10, post 2: 2024-01-15
        read1 = make_response(200, post_read_body(make_post_item(post_id="1", date="2024-01-10 00:00:00")))
        read2 = make_response(200, post_read_body(make_post_item(post_id="2", date="2024-01-15 00:00:00")))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1, read2])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract(after=datetime(2024, 1, 15))
        assert len(posts) == 1
        assert posts[0].id == "2"

    def test_extract_filter_before_inclusive(self, extractor: TistoryApiExtractor) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body(
            [{"id": "1"}, {"id": "2"}], count=10, total=2
        ))
        read1 = make_response(200, post_read_body(make_post_item(post_id="1", date="2024-01-10 00:00:00")))
        read2 = make_response(200, post_read_body(make_post_item(post_id="2", date="2024-01-20 00:00:00")))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1, read2])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract(before=datetime(2024, 1, 15))
        assert len(posts) == 1
        assert posts[0].id == "1"

    def test_extract_filter_on_exact_boundary_date(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read1 = make_response(200, post_read_body(make_post_item(date="2024-01-15 00:00:00")))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            # After and before on same date — inclusive so post included
            posts = extractor.extract(
                after=datetime(2024, 1, 15), before=datetime(2024, 1, 15)
            )
        assert len(posts) == 1

    def test_extract_filter_category_case_insensitive(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([{"id": "10", "name": "Python"}]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read1 = make_response(200, post_read_body(make_post_item(category_id="10")))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract(category="PYTHON")
        assert len(posts) == 1
        assert posts[0].category == "Python"

    def test_extract_filter_category_mismatch_excluded(
        self, extractor: TistoryApiExtractor
    ) -> None:
        cat_resp = make_response(200, category_list_body([{"id": "10", "name": "Python"}]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read1 = make_response(200, post_read_body(make_post_item(category_id="10")))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract(category="Django")
        assert posts == []

    def test_extract_empty_post_list(self, extractor: TistoryApiExtractor) -> None:
        cat_resp = make_response(200, category_list_body([]))
        list_resp = make_response(200, post_list_body([], count=10, total=0))
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract()
        assert posts == []

    def test_extract_category_map_unavailable_gives_empty_category(
        self, extractor: TistoryApiExtractor
    ) -> None:
        # Category map unavailable → category field is ""
        cat_fail = make_response(500, {})  # triggers unavailable after retries
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read1 = make_response(200, post_read_body(make_post_item(category_id="10")))
        # Need 4 failures for _get_category_map (3 retries + initial), then list + read
        mock_get = MagicMock(
            side_effect=[cat_fail, cat_fail, cat_fail, cat_fail, list_resp, read1]
        )
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract()
        assert len(posts) == 1
        assert posts[0].category == ""

    def test_extract_all_filters(self, extractor: TistoryApiExtractor) -> None:
        cat_resp = make_response(200, category_list_body([{"id": "10", "name": "Python"}]))
        list_resp = make_response(200, post_list_body([{"id": "1"}], count=10, total=1))
        read1 = make_response(
            200,
            post_read_body(make_post_item(date="2024-06-15 00:00:00", category_id="10")),
        )
        mock_get = self._setup_responses(extractor, cat_resp, list_resp, [read1])
        with patch("tistory_migrator.extractor.api.time.sleep"), \
             patch.object(extractor._session, "get", mock_get):
            posts = extractor.extract(
                category="python",
                after=datetime(2024, 1, 1),
                before=datetime(2024, 12, 31),
            )
        assert len(posts) == 1
