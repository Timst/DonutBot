from enum import StrEnum, auto
import json
from pathlib import Path
from datetime import datetime

from attr import dataclass

from Config import config
from Data import Data

class Source(StrEnum):
    MANUAL = auto()
    AI = auto()
    ADMIN = auto()

@dataclass
class Stats:
    donuts: int
    percentage: int
    rate: float
    projection: int
    calories: int
    server_donuts: int
    server_calories: int
    projection_calories: int
    days_remaining: int


class Logic:
    data: Data
    cache: dict[str, int]
    rates_cache: dict[str, float]
    refresh_rates: bool
    common_names: dict[str, str]

    def __init__(self, data: Data):
        self.data = data
        self.cache = data.summarize()
        self.data.clean_records()
        self.data.estimate_rates()
        self.rates_cache = data.summarize_rates()
        self.refresh_rates = False

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
        self.refresh_rates = True
        print(f"Added {number} to {username}. Source: {source}.")

    def remove(self, username: str, number: int, source: Source):
        name = self.normalize_name(username)
        number = abs(number)

        if name in self.cache:
            self.cache[name] -= number

        self.data.remove(name, number)
        self.refresh_rates = True
        print(f"Removed {number} from {username}. Source: {source}.")

    def normalize_name(self, username: str) -> str:
        return self.common_names.get(username, username)

    def denormalize_name(self, name: str) -> str:
        return next((username for username, common_name in self.common_names.items() if common_name == name), name)

    def get_top(self) -> dict[str, int]:
        print("Requested top")
        sorted_results = dict(sorted(self.cache.items(), key=lambda item: item[1], reverse=True))
        return dict(filter(lambda item: item[1] > 0, sorted_results.items()))

    def get_score(self, username: str) -> int:
        print("Requested score")
        if username in self.cache.keys():
            return self.cache[username]
        else:
            return 0
        
    def get_estimated_rate(self, username: str) -> float:
        print("Requested rate estimate")
        if self.refresh_rates:
            print("Refreshing rates...?")
            self.rates_cache = self.data.summarize_rates()
            self.refresh_rates = False
        if username in self.rates_cache.keys():
            print('Summary rate: {}'.format(self.rates_cache[username]))
            return self.rates_cache[username]
        else:
            return 0

    def get_stats_by_display_name(self, display_name: str) -> Stats:
        return self.get_stats(self.denormalize_name(display_name))

    def get_stats(self, username: str) -> Stats:
        donuts = self.get_score(self.normalize_name(username))
        all_donuts = self.get_top()
        total_donuts = sum(all_donuts.values())
        total_calories = total_donuts * 250
        percentage = round(donuts/total_donuts * 100)

        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1)
        start_of_year_delta = now - start_of_year
        end_of_year = datetime(now.year, 12, 31)
        end_of_year_delta = end_of_year - now
        rate_old = round(donuts / start_of_year_delta.days, 2)
        print('Old rate: {}'.format(rate_old))
        rate = self.get_estimated_rate(self.normalize_name(username))
        print('Rate: {}'.format(rate))
        projection = int(rate * end_of_year_delta.days) + donuts
        calories = donuts * 250
        projection_calories = projection * 250

        return Stats(donuts, percentage, rate, projection, calories, total_donuts, total_calories, projection_calories, end_of_year_delta.days)
