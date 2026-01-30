from typing import Any
import toml

class Config:
    CONFIG_PATH = "/var/data/donuts/config.toml"

    settings: dict[str, Any]

    def __init__(self) -> None:
        try:
            with open(self.CONFIG_PATH, encoding="utf-8") as f:
                self.settings = toml.load(f)

        except FileNotFoundError:
            print("Config file not found. Add a copy of config.sample.toml to /var/data/donuts/, rename it to config.toml, and add the missing API keys inside.")
            exit(1)
        except Exception as e:
            print(f"Issue with config file: {e}")
            exit(2)

config = Config()
