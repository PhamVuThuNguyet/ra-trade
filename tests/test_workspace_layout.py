"""Contracts for the src/ layout: packages, explorer isolation, path discovery."""

from pathlib import Path

from project_paths import PROJECT_ROOT, SRC_DIR

ANALYSIS_PACKAGES = (
    "baci",
    "baci_characteristics",
    "comtrade_characteristics",
    "comtrade_download",
    "event_context",
    "trade_anomaly",
    "trade_discrepancy",
    "trade_influence",
)


def test_project_root_is_the_repository():
    assert (PROJECT_ROOT / "pyproject.toml").is_file()
    assert (PROJECT_ROOT / "scripts").is_dir()
    assert SRC_DIR == PROJECT_ROOT / "src"


def test_python_packages_live_under_src():
    for name in (*ANALYSIS_PACKAGES, "explorer_catalog"):
        assert (SRC_DIR / name / "__init__.py").is_file()
        assert not (PROJECT_ROOT / name).exists()


def test_explorer_tool_is_ui_only():
    explorer = PROJECT_ROOT / "explorer-tool"
    assert (explorer / "package.json").is_file()
    assert not (explorer / "explorer_catalog").exists()
    for folder in ("app", "components", "lib"):
        assert list((explorer / folder).rglob("*.py")) == []


def test_calendar_stays_with_event_context():
    calendar = SRC_DIR / "event_context" / "pic_event_calendar.csv"
    assert calendar.is_file()
