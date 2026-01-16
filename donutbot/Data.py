import sqlite3
import datetime
from enum import StrEnum
from pathlib import Path

class Operation(StrEnum):
    ADD = "add"
    DELETE = "delete"

class Data:
    DB_PATH = "/var/data/donuts/donuts.db"
    connection: sqlite3.Connection

    insert_query = """
        INSERT INTO Records (username, number, time, operation)
        VALUES(?, ?, ?, ?)
    """

    create_query = """
        CREATE TABLE Records (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            number INTEGER NOT NUll,
            time TIMESTAMP NOT NULL,
            operation TEXT NOT NULL);
    """

    def __init__(self):
        first_run = not Path(self.DB_PATH).exists()

        self.connection = sqlite3.connect(self.DB_PATH)

        if first_run:
            cursor = self.connection.cursor()
            cursor.execute(self.create_query)
            self.connection.commit()

    def add(self, username: str, number: int):
        self.insert_record(username, number, Operation.ADD)

    def remove(self, username: str, number: int):
        self.insert_record(username, number, Operation.DELETE)

    def insert_record(self, username: str, number: int, operation: Operation):
        cursor = self.connection.cursor()
        cursor.execute(self.insert_query, (username, number, datetime.datetime.now(), operation))
        self.connection.commit()

    def clear(self):
        cursor = self.connection.cursor()
        cursor.execute("TRUNCATE TABLE Records")
        self.connection.commit()


    def summarize(self) -> dict[str, int]:
        result: dict[str, int] = {}

        cursor = self.connection.cursor()
        cursor.execute("SELECT username, number, operation FROM Records")

        for username, number, operation in cursor:
            if username in result:
                if operation == Operation.ADD:
                    result[username] += int(number)
                else:
                    result[username] -= int(number)
            else:
                result[username] = (int(number) * 1 if operation == Operation.ADD else -1)

        return result