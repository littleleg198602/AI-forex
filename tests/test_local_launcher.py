from pathlib import Path

import yaml

import run_menu


def test_windows_launcher_files_exist():
    assert Path("run_menu.py").exists()
    assert Path("START_WINDOWS.bat").exists()
    assert Path("START_WINDOWS.ps1").exists()


def test_run_menu_has_no_forbidden_sensitive_or_execution_terms():
    text = Path("run_menu.py").read_text()
    forbidden = [
        "order" + "_" + "send",
        "live" + " " + "executor",
        "API" + " " + "key",
        "API" + "_" + "KEY",
        "pass" + "word",
        "sec" + "ret",
    ]
    lowered = text.lower()
    for term in forbidden:
        haystack = lowered if term.islower() else text
        needle = term if not term.islower() else term.lower()
        assert needle not in haystack


def test_local_launcher_config_has_defaults():
    config_path = Path("config/local_launcher.yaml")
    assert config_path.exists()
    config = yaml.safe_load(config_path.read_text())
    assert config["default_pairs"]
    assert config["default_timeframes"]
    assert config["default_from"]
    assert config["default_to"]
    assert config["output_dir"] == "data/raw"


def test_small_mt5_export_uses_recent_date_range(monkeypatch):
    commands = []

    monkeypatch.setattr(run_menu, "mt5_notice", lambda: None)
    monkeypatch.setattr(run_menu, "run_command", lambda command: commands.append(command) or 0)

    run_menu.export_mt5_small()

    assert commands
    command = commands[0]
    assert command[command.index("--from") + 1] == "2026-06-30"
    assert command[command.index("--to") + 1] == "2026-07-08"
    assert "2023-01-01" not in command
