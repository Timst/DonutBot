import json
from pathlib import Path
from Data import Data

class Logic:
    NAMES_PATH = "/var/data/donuts/names.json"

    data: Data
    cache: dict[str, int]
    common_names: dict[str, str]

    def __init__(self, data: Data):
        self.data = data
        self.cache = data.summarize()

        self.common_names = {}

        if Path(self.NAMES_PATH).exists():
            with open(self.NAMES_PATH, encoding="utf-8") as f:
                self.common_names = json.load(f)

    def add(self, username: str, number: int):
        name = self.normalize_name(username)

        if name in self.cache:
            self.cache[name] += number
        else:
            self.cache[name] = number

        self.data.add(name, number)

    def remove(self, username, number: int):
        name = self.normalize_name(username)

        if name in self.cache:
            self.cache[name] -= number

        self.data.remove(name, number)

    def normalize_name(self, username) -> str:
        if username in self.common_names:
            return self.common_names[username]
        else:
            return username

    def get_top(self):
        return sorted(self.cache.items(), key=lambda item: item[1], reverse=True)
