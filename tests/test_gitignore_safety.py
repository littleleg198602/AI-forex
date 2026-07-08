from pathlib import Path


def test_gitignore_blocks_raw_csv_and_secret_files():
    text = Path(".gitignore").read_text()
    required_patterns = ["data/raw/*", "!data/raw/.gitkeep", "!data/raw/README.md", ".env", ".env.*", "*.key", "secrets.*", "credentials.*"]
    for pattern in required_patterns:
        assert pattern in text
