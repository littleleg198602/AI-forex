from pathlib import Path

IGNORED_DIR_PARTS = {
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "site-packages",
    "dist",
    "build",
}
CHECKED_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".bat", ".ps1"}
# Quality review is a generated human-facing report that intentionally states
# which safety terms were reviewed. Keep the code scan strict elsewhere.
ALLOWED_TEXT_PATHS = {Path("reports/quality_review.md")}


def should_scan(path: Path) -> bool:
    if not path.is_file() or path.suffix not in CHECKED_SUFFIXES:
        return False
    if any(part in IGNORED_DIR_PARTS for part in path.parts):
        return False
    if path in ALLOWED_TEXT_PATHS:
        return False
    return True


def test_mt5_exporter_has_no_order_placement_call():
    text = Path("scripts/export_mt5_history.py").read_text()
    forbidden = "order" + "_" + "send"
    assert forbidden not in text


def test_project_has_no_execution_or_sensitive_markers_outside_allowed_texts():
    forbidden_fragments = [
        "order" + "_" + "send",
        "API" + "_" + "KEY",
        "SEC" + "RET",
        "PASS" + "WORD",
        "TO" + "KEN",
        "live" + " " + "executor",
        "broker" + " " + "executor",
    ]
    for path in Path(".").rglob("*"):
        if not should_scan(path):
            continue
        text = path.read_text(errors="ignore")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"Forbidden fragment {fragment} found in {path}"


def test_safety_scan_ignores_virtualenv_and_build_directories():
    ignored = [
        Path(".venv/Lib/site-packages/example.py"),
        Path("venv/Lib/site-packages/example.py"),
        Path("env/Lib/site-packages/example.py"),
        Path("build/generated.py"),
        Path("dist/generated.py"),
    ]
    for path in ignored:
        assert not should_scan(path)
