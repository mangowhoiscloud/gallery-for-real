from datetime import datetime, timezone

from tistory_migrator.models import FailedPost, MigrationResult, TistoryPost


class TestTistoryPost:
    def test_create_basic(self) -> None:
        post = TistoryPost(
            id="1",
            title="Test Post",
            content_html="<p>Hello</p>",
            category="Python",
            tags=["python", "flask"],
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            url="https://blog.tistory.com/1",
            images=["https://img.tistory.com/photo.jpg"],
        )
        assert post.id == "1"
        assert post.title == "Test Post"
        assert post.content_html == "<p>Hello</p>"
        assert post.category == "Python"
        assert post.tags == ["python", "flask"]
        assert post.published_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert post.url == "https://blog.tistory.com/1"
        assert post.images == ["https://img.tistory.com/photo.jpg"]

    def test_empty_tags(self) -> None:
        post = TistoryPost(
            id="2",
            title="No Tags",
            content_html="<p>Body</p>",
            category="",
            tags=[],
            published_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            url="https://blog.tistory.com/2",
            images=[],
        )
        assert post.tags == []
        assert post.images == []
        assert post.category == ""

    def test_korean_title(self) -> None:
        post = TistoryPost(
            id="3",
            title="파이썬 개발 팁",
            content_html="<p>내용</p>",
            category="개발",
            tags=["파이썬"],
            published_at=datetime(2024, 3, 10, tzinfo=timezone.utc),
            url="https://blog.tistory.com/3",
            images=[],
        )
        assert post.title == "파이썬 개발 팁"
        assert post.tags == ["파이썬"]

    def test_equality(self) -> None:
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        p1 = TistoryPost("1", "T", "<p></p>", "C", [], dt, "url", [])
        p2 = TistoryPost("1", "T", "<p></p>", "C", [], dt, "url", [])
        assert p1 == p2

    def test_inequality(self) -> None:
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        p1 = TistoryPost("1", "T", "<p></p>", "C", [], dt, "url", [])
        p2 = TistoryPost("2", "T", "<p></p>", "C", [], dt, "url", [])
        assert p1 != p2


class TestFailedPost:
    def test_create(self) -> None:
        fp = FailedPost(id="42", title="Bad Post", reason="empty content")
        assert fp.id == "42"
        assert fp.title == "Bad Post"
        assert fp.reason == "empty content"

    def test_equality(self) -> None:
        fp1 = FailedPost("1", "T", "r")
        fp2 = FailedPost("1", "T", "r")
        assert fp1 == fp2

    def test_korean_fields(self) -> None:
        fp = FailedPost(id="5", title="글 제목", reason="빈 내용")
        assert fp.title == "글 제목"
        assert fp.reason == "빈 내용"


class TestMigrationResult:
    def _make_result(self, **kwargs) -> MigrationResult:
        defaults = {
            "blog": "myblog",
            "strategy": "api",
            "migrated_at": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            "total_posts": 100,
            "converted_posts": 98,
            "failed_posts": [],
            "categories": ["Python", "Web"],
            "tags": ["flask", "django"],
            "total_images": 50,
            "failed_images": 2,
            "duration_seconds": 42.5,
        }
        defaults.update(kwargs)
        return MigrationResult(**defaults)

    def test_create_basic(self) -> None:
        r = self._make_result()
        assert r.blog == "myblog"
        assert r.strategy == "api"
        assert r.total_posts == 100
        assert r.converted_posts == 98
        assert r.failed_posts == []
        assert r.categories == ["Python", "Web"]
        assert r.total_images == 50
        assert r.failed_images == 2
        assert r.duration_seconds == 42.5

    def test_to_dict_basic(self) -> None:
        r = self._make_result()
        d = r.to_dict()
        assert d["blog"] == "myblog"
        assert d["strategy"] == "api"
        assert d["total_posts"] == 100
        assert d["converted_posts"] == 98
        assert d["failed_posts"] == []
        assert d["categories"] == ["Python", "Web"]
        assert d["tags"] == ["flask", "django"]
        assert d["total_images"] == 50
        assert d["failed_images"] == 2
        assert d["duration_seconds"] == 42.5

    def test_to_dict_migrated_at_iso8601(self) -> None:
        r = self._make_result(
            migrated_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        d = r.to_dict()
        # Must be ISO 8601 string
        assert isinstance(d["migrated_at"], str)
        assert "2024-06-15" in d["migrated_at"]
        assert "12:00:00" in d["migrated_at"]

    def test_to_dict_failed_posts_serialized(self) -> None:
        fp = FailedPost(id="7", title="Bad Post", reason="parse error")
        r = self._make_result(failed_posts=[fp])
        d = r.to_dict()
        assert len(d["failed_posts"]) == 1
        assert d["failed_posts"][0] == {"id": "7", "title": "Bad Post", "reason": "parse error"}

    def test_to_dict_multiple_failed_posts(self) -> None:
        fps = [
            FailedPost("1", "Post A", "empty content"),
            FailedPost("2", "Post B", "download error"),
        ]
        r = self._make_result(failed_posts=fps)
        d = r.to_dict()
        assert len(d["failed_posts"]) == 2
        assert d["failed_posts"][0]["id"] == "1"
        assert d["failed_posts"][1]["id"] == "2"

    def test_to_dict_zero_values(self) -> None:
        r = self._make_result(
            total_posts=0,
            converted_posts=0,
            failed_posts=[],
            categories=[],
            tags=[],
            total_images=0,
            failed_images=0,
            duration_seconds=0.0,
        )
        d = r.to_dict()
        assert d["total_posts"] == 0
        assert d["converted_posts"] == 0
        assert d["failed_posts"] == []
        assert d["categories"] == []
        assert d["tags"] == []
        assert d["total_images"] == 0
        assert d["failed_images"] == 0
        assert d["duration_seconds"] == 0.0

    def test_strategy_values(self) -> None:
        for strategy in ("api", "xml", "scraping"):
            r = self._make_result(strategy=strategy)
            assert r.to_dict()["strategy"] == strategy

    def test_to_dict_returns_new_dict(self) -> None:
        r = self._make_result()
        d1 = r.to_dict()
        d2 = r.to_dict()
        assert d1 == d2
        assert d1 is not d2

    def test_to_dict_keys(self) -> None:
        r = self._make_result()
        d = r.to_dict()
        expected_keys = {
            "blog", "strategy", "migrated_at", "total_posts", "converted_posts",
            "failed_posts", "categories", "tags", "total_images", "failed_images",
            "duration_seconds",
        }
        assert set(d.keys()) == expected_keys

    def test_korean_blog_name(self) -> None:
        r = self._make_result(blog="내블로그")
        d = r.to_dict()
        assert d["blog"] == "내블로그"
