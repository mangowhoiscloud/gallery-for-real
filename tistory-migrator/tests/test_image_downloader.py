"""Tests for image_downloader module.

All HTTP calls are mocked — no real network calls.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import requests

from tistory_migrator.image_downloader import (
    ImageDownloadResult,
    ImageDownloader,
    _resolve_collision,
    _url_to_filename,
)


# ---------------------------------------------------------------------------
# _url_to_filename
# ---------------------------------------------------------------------------

class TestUrlToFilename:
    def test_simple_filename(self):
        assert _url_to_filename("https://img.example.com/photo.jpg") == "photo.jpg"

    def test_path_with_directories(self):
        assert _url_to_filename("https://img.example.com/thumb/R800x0/photo.png") == "photo.png"

    def test_url_ending_with_slash_falls_back(self):
        # CDN URLs sometimes end with a slash, basename would be ''
        assert _url_to_filename("https://img.daumcdn.net/thumb/R800x0/") == "image.jpg"

    def test_no_path_component_falls_back(self):
        assert _url_to_filename("https://img.example.com") == "image.jpg"

    def test_query_string_ignored(self):
        # urlparse separates query from path, so filename is just the path part
        assert _url_to_filename("https://img.example.com/photo.jpg?q=90") == "photo.jpg"

    def test_fragment_ignored(self):
        assert _url_to_filename("https://img.example.com/photo.jpg#section") == "photo.jpg"

    def test_preserves_extension(self):
        assert _url_to_filename("https://img.example.com/img.gif") == "img.gif"

    def test_no_extension(self):
        assert _url_to_filename("https://img.example.com/imagefile") == "imagefile"

    def test_tistory_cdn_url(self):
        url = "https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fphoto.jpg"
        # basename of the URL path is empty after last slash
        result = _url_to_filename(url)
        # The path ends with '' after '?' is stripped — depends on urlparse
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# _resolve_collision
# ---------------------------------------------------------------------------

class TestResolveCollision:
    def test_no_collision(self, tmp_path):
        used: set[Path] = set()
        base = tmp_path / "photo.jpg"
        result = _resolve_collision(base, used)
        assert result == base

    def test_first_collision(self, tmp_path):
        used: set[Path] = {tmp_path / "photo.jpg"}
        base = tmp_path / "photo.jpg"
        result = _resolve_collision(base, used)
        assert result == tmp_path / "photo-1.jpg"

    def test_second_collision(self, tmp_path):
        used: set[Path] = {tmp_path / "photo.jpg", tmp_path / "photo-1.jpg"}
        base = tmp_path / "photo.jpg"
        result = _resolve_collision(base, used)
        assert result == tmp_path / "photo-2.jpg"

    def test_collision_on_already_numbered_stem(self, tmp_path):
        # "image-1.jpg" collides → "image-1-1.jpg"
        used: set[Path] = {tmp_path / "image-1.jpg"}
        base = tmp_path / "image-1.jpg"
        result = _resolve_collision(base, used)
        assert result == tmp_path / "image-1-1.jpg"

    def test_no_extension(self, tmp_path):
        used: set[Path] = {tmp_path / "imagefile"}
        base = tmp_path / "imagefile"
        result = _resolve_collision(base, used)
        assert result == tmp_path / "imagefile-1"

    def test_multiple_collisions_resolved_in_order(self, tmp_path):
        used: set[Path] = set()
        base = tmp_path / "photo.jpg"

        p1 = _resolve_collision(base, used)
        assert p1 == base
        used.add(p1)

        p2 = _resolve_collision(base, used)
        assert p2 == tmp_path / "photo-1.jpg"
        used.add(p2)

        p3 = _resolve_collision(base, used)
        assert p3 == tmp_path / "photo-2.jpg"


# ---------------------------------------------------------------------------
# ImageDownloadResult
# ---------------------------------------------------------------------------

class TestImageDownloadResult:
    def test_creation(self):
        r = ImageDownloadResult(mapping={"a": "b"}, total=3, succeeded=2, failed=1)
        assert r.mapping == {"a": "b"}
        assert r.total == 3
        assert r.succeeded == 2
        assert r.failed == 1

    def test_zero_urls(self):
        r = ImageDownloadResult(mapping={}, total=0, succeeded=0, failed=0)
        assert r.total == 0


# ---------------------------------------------------------------------------
# ImageDownloader — construction
# ---------------------------------------------------------------------------

class TestImageDownloaderInit:
    def test_default_params(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path)
        assert d.rate_limit_sleep == 0.5
        assert d.no_images is False

    def test_custom_params(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=1.0, no_images=True)
        assert d.rate_limit_sleep == 1.0
        assert d.no_images is True


# ---------------------------------------------------------------------------
# ImageDownloader — no_images mode
# ---------------------------------------------------------------------------

class TestNoImagesMode:
    def test_no_images_returns_immediately(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path, no_images=True)
        urls = ["https://img.example.com/a.jpg", "https://img.example.com/b.jpg"]
        result = d.download_for_post(urls, slug="my-post")
        assert result.total == 2
        assert result.failed == 2
        assert result.succeeded == 0
        assert result.mapping == {}

    def test_no_images_empty_urls(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path, no_images=True)
        result = d.download_for_post([], slug="my-post")
        assert result.total == 0
        assert result.failed == 0

    def test_no_images_does_not_create_directories(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path, no_images=True)
        d.download_for_post(["https://img.example.com/a.jpg"], slug="my-post")
        assert not (tmp_path / "images" / "my-post").exists()


# ---------------------------------------------------------------------------
# ImageDownloader — successful downloads
# ---------------------------------------------------------------------------

class TestSuccessfulDownloads:
    def _make_ok_response(self, content: bytes = b"img_data") -> Mock:
        resp = Mock()
        resp.status_code = 200
        resp.content = content
        resp.raise_for_status = Mock()
        return resp

    def test_single_url_success(self, tmp_path):
        session = MagicMock()
        session.get.return_value = self._make_ok_response(b"jpeg_data")

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(["https://img.example.com/photo.jpg"], slug="my-post")

        assert result.total == 1
        assert result.succeeded == 1
        assert result.failed == 0
        saved_path = tmp_path / "images" / "my-post" / "photo.jpg"
        assert saved_path.exists()
        assert saved_path.read_bytes() == b"jpeg_data"

    def test_mapping_contains_relative_path(self, tmp_path):
        session = MagicMock()
        session.get.return_value = self._make_ok_response()

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(
                ["https://img.example.com/photo.jpg"], slug="my-post"
            )

        assert "https://img.example.com/photo.jpg" in result.mapping
        assert result.mapping["https://img.example.com/photo.jpg"] == "/images/my-post/photo.jpg"

    def test_multiple_urls_all_success(self, tmp_path):
        session = MagicMock()
        session.get.return_value = self._make_ok_response()

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            urls = [
                "https://img.example.com/a.jpg",
                "https://img.example.com/b.png",
            ]
            result = d.download_for_post(urls, slug="my-post")

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0
        assert (tmp_path / "images" / "my-post" / "a.jpg").exists()
        assert (tmp_path / "images" / "my-post" / "b.png").exists()

    def test_creates_slug_directory(self, tmp_path):
        session = MagicMock()
        session.get.return_value = self._make_ok_response()

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            d.download_for_post(["https://img.example.com/x.jpg"], slug="new-post")

        assert (tmp_path / "images" / "new-post").is_dir()

    def test_empty_url_list(self, tmp_path):
        d = ImageDownloader(output_dir=tmp_path)
        result = d.download_for_post([], slug="my-post")
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.mapping == {}


# ---------------------------------------------------------------------------
# ImageDownloader — collision resolution
# ---------------------------------------------------------------------------

class TestCollisionResolution:
    def _make_ok_response(self) -> Mock:
        resp = Mock()
        resp.status_code = 200
        resp.content = b"data"
        resp.raise_for_status = Mock()
        return resp

    def test_same_filename_two_urls_resolved(self, tmp_path):
        """Two different URLs with the same basename get different local filenames."""
        session = MagicMock()
        session.get.return_value = self._make_ok_response()

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            urls = [
                "https://cdn1.example.com/photo.jpg",
                "https://cdn2.example.com/photo.jpg",
            ]
            result = d.download_for_post(urls, slug="my-post")

        assert result.succeeded == 2
        paths = list(result.mapping.values())
        # Both should be saved but with different local names
        assert len(set(paths)) == 2
        assert "/images/my-post/photo.jpg" in paths
        assert "/images/my-post/photo-1.jpg" in paths

    def test_collision_files_both_written(self, tmp_path):
        session = MagicMock()
        session.get.side_effect = [
            Mock(status_code=200, content=b"img1", raise_for_status=Mock()),
            Mock(status_code=200, content=b"img2", raise_for_status=Mock()),
        ]

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            d.download_for_post(
                ["https://cdn1.example.com/img.jpg", "https://cdn2.example.com/img.jpg"],
                slug="my-post",
            )

        assert (tmp_path / "images" / "my-post" / "img.jpg").read_bytes() == b"img1"
        assert (tmp_path / "images" / "my-post" / "img-1.jpg").read_bytes() == b"img2"


# ---------------------------------------------------------------------------
# ImageDownloader — rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_sleep_not_called_before_first_request(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(
            status_code=200, content=b"data", raise_for_status=Mock()
        )
        sleep_calls: list[float] = []

        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.5, session=session)
            d.download_for_post(["https://img.example.com/a.jpg"], slug="p")

        # sleep should not be called before the first (and only) request
        assert sleep_calls == []

    def test_sleep_called_between_requests(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(
            status_code=200, content=b"data", raise_for_status=Mock()
        )
        sleep_calls: list[float] = []

        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.5, session=session)
            d.download_for_post(
                [
                    "https://img.example.com/a.jpg",
                    "https://img.example.com/b.jpg",
                    "https://img.example.com/c.jpg",
                ],
                slug="p",
            )

        # 3 URLs → sleep called between 2nd and 3rd (not before 1st, yes between rest)
        rate_limit_sleeps = [s for s in sleep_calls if s == 0.5]
        assert len(rate_limit_sleeps) == 2

    def test_custom_sleep_duration(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(
            status_code=200, content=b"data", raise_for_status=Mock()
        )
        sleep_calls: list[float] = []

        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=1.5, session=session)
            d.download_for_post(
                ["https://img.example.com/a.jpg", "https://img.example.com/b.jpg"],
                slug="p",
            )

        rate_limit_sleeps = [s for s in sleep_calls if s == 1.5]
        assert len(rate_limit_sleeps) == 1


# ---------------------------------------------------------------------------
# ImageDownloader — permanent failures (404/410)
# ---------------------------------------------------------------------------

class TestPermanentFailures:
    def test_404_no_retry(self, tmp_path):
        session = MagicMock()
        resp = Mock()
        resp.status_code = 404
        session.get.return_value = resp

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(["https://img.example.com/gone.jpg"], slug="p")

        assert result.failed == 1
        assert result.succeeded == 0
        # Only one attempt, no retries
        assert session.get.call_count == 1

    def test_410_no_retry(self, tmp_path):
        session = MagicMock()
        resp = Mock()
        resp.status_code = 410
        session.get.return_value = resp

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(["https://img.example.com/gone.jpg"], slug="p")

        assert result.failed == 1
        assert session.get.call_count == 1

    def test_404_not_in_mapping(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(status_code=404)

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(["https://img.example.com/gone.jpg"], slug="p")

        assert "https://img.example.com/gone.jpg" not in result.mapping

    def test_mixed_success_and_404(self, tmp_path):
        session = MagicMock()
        session.get.side_effect = [
            Mock(status_code=200, content=b"data", raise_for_status=Mock()),
            Mock(status_code=404),
        ]

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, session=session)
            result = d.download_for_post(
                ["https://img.example.com/ok.jpg", "https://img.example.com/gone.jpg"],
                slug="p",
            )

        assert result.total == 2
        assert result.succeeded == 1
        assert result.failed == 1


# ---------------------------------------------------------------------------
# ImageDownloader — retryable failures (5xx / timeout)
# ---------------------------------------------------------------------------

class TestRetryableFailures:
    def test_5xx_retried_up_to_3_times(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(status_code=500)

        sleep_calls: list[float] = []
        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.0, session=session)
            result = d.download_for_post(["https://img.example.com/flaky.jpg"], slug="p")

        # 1 initial + 3 retries = 4 total attempts
        assert session.get.call_count == 4
        assert result.failed == 1

    def test_5xx_retry_backoff_delays(self, tmp_path):
        session = MagicMock()
        session.get.return_value = Mock(status_code=503)

        sleep_calls: list[float] = []
        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.0, session=session)
            d.download_for_post(["https://img.example.com/flaky.jpg"], slug="p")

        # Retry backoff: 1s, 2s, 4s
        backoff_sleeps = sleep_calls  # rate_limit_sleep=0 so all sleeps are backoff
        assert backoff_sleeps == [1, 2, 4]

    def test_timeout_retried(self, tmp_path):
        session = MagicMock()
        session.get.side_effect = requests.Timeout

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.0, session=session)
            result = d.download_for_post(["https://img.example.com/slow.jpg"], slug="p")

        assert session.get.call_count == 4  # 1 + 3 retries
        assert result.failed == 1

    def test_connection_error_retried(self, tmp_path):
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.0, session=session)
            result = d.download_for_post(["https://img.example.com/unreachable.jpg"], slug="p")

        assert session.get.call_count == 4
        assert result.failed == 1

    def test_succeeds_on_retry_after_5xx(self, tmp_path):
        """Returns success if a retry succeeds."""
        session = MagicMock()
        session.get.side_effect = [
            Mock(status_code=500),
            Mock(status_code=200, content=b"ok", raise_for_status=Mock()),
        ]

        with patch("tistory_migrator.image_downloader.time.sleep"):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.0, session=session)
            result = d.download_for_post(["https://img.example.com/flaky.jpg"], slug="p")

        assert result.succeeded == 1
        assert result.failed == 0
        assert session.get.call_count == 2

    def test_5xx_backoff_independent_of_rate_limit(self, tmp_path):
        """Rate limit sleep is applied between URLs; backoff is only during retries."""
        session = MagicMock()
        # First URL: 500 then success; Second URL: success
        session.get.side_effect = [
            Mock(status_code=500),
            Mock(status_code=200, content=b"ok1", raise_for_status=Mock()),
            Mock(status_code=200, content=b"ok2", raise_for_status=Mock()),
        ]

        sleep_calls: list[float] = []
        with patch(
            "tistory_migrator.image_downloader.time.sleep",
            side_effect=lambda s: sleep_calls.append(s),
        ):
            d = ImageDownloader(output_dir=tmp_path, rate_limit_sleep=0.5, session=session)
            result = d.download_for_post(
                ["https://img.example.com/a.jpg", "https://img.example.com/b.jpg"],
                slug="p",
            )

        assert result.succeeded == 2
        # sleep(1) from backoff, sleep(0.5) between URLs
        assert 1 in sleep_calls
        assert 0.5 in sleep_calls


# ---------------------------------------------------------------------------
# ImageDownloader — uses a new Session if none provided
# ---------------------------------------------------------------------------

class TestSessionManagement:
    def test_creates_session_if_not_provided(self, tmp_path):
        with patch("tistory_migrator.image_downloader.requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            mock_session_instance.get.return_value = Mock(
                status_code=200, content=b"x", raise_for_status=Mock()
            )
            MockSession.return_value = mock_session_instance

            with patch("tistory_migrator.image_downloader.time.sleep"):
                d = ImageDownloader(output_dir=tmp_path)
                d.download_for_post(["https://img.example.com/x.jpg"], slug="p")

            MockSession.assert_called_once()
