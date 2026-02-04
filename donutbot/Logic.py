from enum import StrEnum, auto
import json
from pathlib import Path

from Config import config
from Data import Data

class Source(StrEnum):
    MANUAL = auto()
    AI = auto()
    ADMIN = auto()

class Logic:
    data: Data
    cache: dict[str, int]
    common_names: dict[str, str]

    def __init__(self, data: Data):
        self.data = data
        self.cache = data.summarize()

        self.common_names = {}

        if Path(config.settings["files"]["names"]).exists():
            with open(config.settings["files"]["names"], encoding="utf-8") as f:
                self.common_names = json.load(f)

    def add(self, username: str, number: int, source: Source):
        name = self.normalize_name(username)
        number = abs(number)

        if name in self.cache:
            self.cache[name] += number
        else:
            self.cache[name] = number

        self.data.add(name, number)
        print(f"Added {number} to {username}. Source: {source}.")

    def remove(self, username: str, number: int, source: Source):
        name = self.normalize_name(username)
        number = abs(number)

        if name in self.cache:
            self.cache[name] -= number

        self.data.remove(name, number)
        print(f"Removed {number} from {username}. Source: {source}.")

    def normalize_name(self, username: str) -> str:
        return self.common_names.get(username, username)

    def denormalize_name(self, name: str) -> str:
        return next((username for username, common_name in self.common_names.items() if common_name == name), name)

    def get_top(self) -> dict[str, int]:
        print("Requested top")
        return dict(sorted(self.cache.items(), key=lambda item: item[1], reverse=True))

    def get_score(self, username: str) -> int:
        print("Requested score")
        if username in self.cache.keys():
            return self.cache[username]
        else:
            return 0
