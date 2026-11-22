from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    with (ROOT / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)
