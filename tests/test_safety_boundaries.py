from pathlib import Path


def test_mt5_exporter_has_no_order_placement_call():
    text = Path("scripts/export_mt5_history.py").read_text()
    forbidden = "order" + "_" + "send"
    assert forbidden not in text


def test_project_has_no_execution_or_secret_markers():
    forbidden_fragments = ["live" + "_" + "executor", "broker" + "_" + "executor", "API" + "_" + "KEY", "PASS" + "WORD", "SEC" + "RET"]
    checked_suffixes = {".py", ".md", ".yaml", ".yml", ".txt", ".toml"}
    for path in Path(".").rglob("*"):
        if ".git" in path.parts or not path.is_file() or path.suffix not in checked_suffixes:
            continue
        text = path.read_text(errors="ignore")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"Forbidden fragment {fragment} found in {path}"
