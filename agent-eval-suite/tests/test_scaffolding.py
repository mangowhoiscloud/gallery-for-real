"""Verify the package scaffolding is set up correctly."""

from agent_eval import __version__


def test_version_importable() -> None:
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_backends_package_importable() -> None:
    import agent_eval.backends  # noqa: F401


def test_report_package_importable() -> None:
    import agent_eval.report  # noqa: F401
